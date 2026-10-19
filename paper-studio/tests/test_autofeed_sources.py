import base64
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from tests import pdf_fixtures as fitz
from feed_sources import parse_feed,discover_recent,verify_resources,stable_id
from feed_sources import repository_record,topic_labels,QUERIES
from figure_plan import build_plan,coverage,adaptive_style
from writing import chat_json,provider_config,editorial_instruction,generate_article
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from sources import extract_pdf,caption_box

FEED=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2610.12345v2</id><title>Robot World Model</title><published>2026-10-18T00:00:00Z</published><summary>Embodied world model</summary><author><name>A</name></author></entry><entry><id>http://arxiv.org/abs/2501.12345</id><title>Old world model</title><published>2025-01-01T00:00:00Z</published></entry></feed>'''

class DiscoveryTests(unittest.TestCase):
    def test_cancel_during_native_html_does_not_fetch_images(self):
        from native_figures import improve_native_figures
        calls=[]
        source={'arxiv_id':'2610.12345','figures':[]}
        def fetch(url,limit):
            calls.append(url)
            return b'<figure><img src="x.png">Figure 1: architecture</figure>'
        def progress(_):
            if calls:raise ValueError('Fixture stopped')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'stopped'):improve_native_figures(source,tmp,progress,fetch)
        self.assertEqual(calls,['https://arxiv.org/html/2610.12345'])
        self.assertNotIn('native_figures_checked',source)

    def test_cancel_during_fetch_still_publishes_the_returned_titles(self):
        updates=[];calls=[]
        def fetch(url,limit):calls.append(url);return FEED
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'暂停'):
                discover_recent(tmp,datetime(2026,10,19,tzinfo=timezone.utc),fetch,lambda _:None,on_update=lambda p:updates.append(p),cancelled=lambda:bool(calls))
        self.assertEqual(len(calls),1)
        self.assertEqual(updates[-1]['items'][0]['id'],'2610.12345')

    def test_titles_are_published_before_following_queries_and_cancel_preserves_them(self):
        updates=[];calls=[]
        def fetch(url,limit):
            if calls:self.assertTrue(any(u['items'] for u in updates))
            calls.append(url);return FEED
        with tempfile.TemporaryDirectory() as tmp:
            discover_recent(tmp,datetime(2026,10,19,tzinfo=timezone.utc),fetch,lambda _:None,on_update=lambda p:updates.append(p))
            self.assertEqual(len(calls),len(QUERIES))
            self.assertEqual(updates[-1]['queries_done'],len(QUERIES))
        updates=[];calls=[]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'暂停'):
                discover_recent(tmp,datetime(2026,10,19,tzinfo=timezone.utc),fetch,lambda _:None,on_update=lambda p:updates.append(p),cancelled=lambda:bool(updates and updates[-1].get('queries_done',0)==1))
            self.assertEqual(len(calls),1);self.assertTrue(updates[-1]['items'])

    def test_github_web_fallback_uses_rendered_readme_and_directory_data(self):
        def fetch(url,limit):
            if url.startswith('https://api.github.com'):raise ValueError('DNS blocked fixture')
            payload={'payload':{'codeViewRepoRoute':{'path':'/','refInfo':{'name':'main'},'tree':{'items':[
                {'name':'train.py','path':'train.py','contentType':'file'},
                {'name':'hidden.py','path':'unpublished/deep/hidden.py','contentType':'file'}]}}}}
            html='<script>not research evidence</script><article>Driving on Registers 2601.05083</article>'
            html+='<a href="https://arxiv.org/abs/2999.99999">unrelated global identity</a>'
            html+='<script type="application/json" data-target="react-app.embeddedData">'+json.dumps(payload)+'</script>'
            return html.encode(),'text/html',url
        readme,entries=repository_record('lab/repo',fetch)
        self.assertIn('Driving on Registers',readme)
        self.assertNotIn('not research evidence',readme)
        self.assertNotIn('2999.99999',readme)
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0]['name'],'train.py')

    def test_readme_only_source_link_does_not_prove_released_code(self):
        def fetch(url,limit):
            if url.startswith('https://api.github.com'):raise ValueError('DNS blocked fixture')
            return b'<article>Robot World Model <a href="/lab/repo/blob/main/unpublished/deep/train.py">soon</a></article>','text/html',url
        readme,entries=repository_record('lab/repo',fetch)
        self.assertIn('Robot World Model',readme)
        self.assertEqual(entries,[])

    def test_agent_and_rsi_are_independent_topics(self):
        self.assertIn('agents',topic_labels('Planning for LLM Agents','tool use and reasoning'))
        self.assertIn('rsi',topic_labels('Recursive Self-Improvement','Self-evolving agents'))
        self.assertIn('rsi',topic_labels('Self-Refinement for Reasoning Agents','iterative learning'))

    def test_dates_topics_stable_identity_and_cache(self):
        now=datetime(2026,10,19,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            fetch=Mock(return_value=FEED); sleep=Mock()
            a=discover_recent(tmp,now,fetch,sleep); b=discover_recent(tmp,now,fetch,sleep)
            self.assertEqual(a,b);self.assertEqual(len(a['items']),1)
            self.assertEqual(a['items'][0]['id'],'2610.12345')
            self.assertEqual(fetch.call_count,len(QUERIES));self.assertEqual(sleep.call_count,len(QUERIES)-1)
            self.assertEqual(stable_id('https://arxiv.org/abs/2610.12345v3'),'2610.12345')

    def test_resource_verification_requires_both_identity_and_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc=fitz.open();page=doc.new_page();page.insert_text((50,50),'Robot World Model')
            page.insert_link({'kind':fitz.LINK_URI,'from':fitz.Rect(50,50,200,60),'uri':'https://robot.example/project'})
            rawpdf=doc.tobytes();doc.close()
            item=parse_feed(FEED,datetime(2026,10,19,tzinfo=timezone.utc))[0]
            code=True
            def fetch(url,limit):
                if url=='https://robot.example/project':return b'<h1>Robot World Model 2610.12345</h1><a href="https://github.com/lab/robot">Code</a>','text/html',url
                if url.endswith('/readme'):return json.dumps({'content':base64.b64encode(b'Robot World Model 2610.12345').decode()}).encode(),'application/json',url
                if url.endswith('/contents'):return json.dumps([{'name':'train.py' if code else 'README.md','type':'file'}]).encode(),'application/json',url
                raise ValueError('unexpected')
            self.assertTrue(verify_resources(item,tmp,fetch,lambda *x:rawpdf)['verified'])
            code=False
            self.assertFalse(verify_resources(item,tmp,fetch,lambda *x:rawpdf)['verified'])

class IllustratedWritingTests(unittest.TestCase):
    def test_side_by_side_panels_retain_the_entire_right_panel(self):
        with fitz.open() as doc:
            page=doc.new_page(width=612,height=792)
            page.draw_rect(fitz.Rect(317,484,423,588),color=(0,0,1),fill=(.8,.8,1))
            page.draw_rect(fitz.Rect(447,484,553,588),color=(1,0,0),fill=(1,.8,.8))
            caption=(315,610,554,640,'Figure 1. Qualitative comparison.',0,0)
            box,status=caption_box(page,caption,[caption])
            self.assertEqual(status,'figure_detected')
            self.assertLessEqual(box[0],317);self.assertGreaterEqual(box[2],553)

    def test_trajectory_decoder_is_not_a_qualitative_result(self):
        p=build_plan({'figures':[
            {'id':'fig-001','caption':'Figure 1. Architecture with trajectory decoder and generated tokens','crop_status':'figure_detected'},
            {'id':'fig-002','caption':'Figure 2. Qualitative comparison of generated trajectories','crop_status':'figure_detected'},
            {'id':'fig-003','caption':'Figure 3. Visualization of failure cases','crop_status':'figure_detected'}]})
        self.assertEqual(p['required']['method'],'fig-001')
        self.assertEqual(p['required']['qualitative'],'fig-002')
        self.assertIn('fig-003',p['ids'])

    def test_role_plan_and_real_figure_repair_after_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=extract_pdf(fixture_pdf(),Path(tmp));f=m['figures'][0]
            f.update(caption='Figure 1. Overall architecture',original_caption='Figure 1. Overall architecture',crop_status='figure_detected')
            a=fixture_article(m);a['sections'][2]['figures'][0]['pages']=[1]
            missing=json.loads(json.dumps(a));missing['sections'][2]['figures']=[]
            opts={'base_url':'http://localhost:9999/v1','model':'test','auto_figures':True,'style':'adaptive','length':0}
            with patch('writing.chat_json',side_effect=[{'facts':[]},a,missing,a]) as call:
                article,_,audit=generate_article(m,Path(tmp),opts)
            self.assertEqual(call.call_count,4);self.assertFalse(audit['figure_coverage']['missing'])
            self.assertIn('不设字数目标',editorial_instruction(m,opts,[f]))
            self.assertEqual(adaptive_style({'title':'KV cache inference engine'})[0],'systems')

    def test_continuation_preserves_prefix_and_no_secret_in_fragments(self):
        responses=[]
        for text,finish in [('{"sections":[{"text":"hello','length'),(' world"}]}','stop')]:
            response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
            response.read.return_value=json.dumps({'choices':[{'message':{'content':text},'finish_reason':finish}]}).encode();responses.append(response)
        partial=Mock()
        with patch('writing.urllib.request.build_opener') as op:
            op.return_value.open.side_effect=responses
            result=chat_json(provider_config({'base_url':'http://localhost:9999','model':'test'}),'JSON',partial=partial)
            second=json.loads(op.return_value.open.call_args.args[0].data)
        self.assertEqual(result['sections'][0]['text'],'hello world')
        self.assertEqual(second['messages'][-2]['content'],'{"sections":[{"text":"hello')
        self.assertEqual(partial.call_count,2)

    def test_full_page_never_auto_selected(self):
        p=build_plan({'figures':[{'id':'fig-001','caption':'Architecture','crop_status':'page_fallback'},
                                  {'id':'fig-002','caption':'Qualitative results','crop_status':'figure_detected'}]})
        self.assertEqual(p['ids'],['fig-002'])
        self.assertTrue(coverage({'sections':[]},p))

if __name__=='__main__':unittest.main()
