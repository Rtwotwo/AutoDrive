import unittest
from unittest.mock import patch
from tests import test_autofeed as af
from tests.test_sources import fixture_pdf
from wechat_api import TransportError
from sources import write_json
from urllib.error import URLError

class DirectDraftTests(unittest.TestCase):
    setUp=af.AutoFeedTests.setUp
    tearDown=af.AutoFeedTests.tearDown
    generation=af.AutoFeedTests.generation
    format=af.AutoFeedTests.format

    def test_long_generated_fields_are_adapted_before_draft_without_rewriting_article(self):
        first='模型通过共享表示连接视觉输入与动作预测，并在相同评测条件下比较结果。'
        original_digest=first+'详细结果与消融条件在正文逐项说明。'*12
        def generate(source,*args):
            article,notes,audit=self.generation(source,*args)
            article.update(title='一个超长的研究标题'*8,title_options=['共享表示如何改善动作预测'],digest=original_digest)
            return article,notes,audit
        result=self.execute([self.items[0]['url']],generation=generate)
        folder=self.studio.folder(result['id'])
        article=self.studio.load(result['id'],'article.json')
        self.assertEqual(article['digest'],original_digest);self.assertGreater(len(article['title']),32)
        self.assertEqual(self.api.article['title'],'共享表示如何改善动作预测')
        self.assertLessEqual(len(self.api.article['digest']),120)
        self.assertIn('mmbiz.qpic.cn',self.api.article['content'])
        self.assertTrue((folder/'wechat-field-adjustments.json').exists())
        self.assertFalse((folder/'wechat-review.json').exists())
        self.assertEqual(self.feed.state['selected_queue']['state'],'complete')

    def test_retry_existing_draft_preserves_author_cover_and_original_digest(self):
        result=self.execute([self.items[0]['url']]);job=result['id'];folder=self.studio.folder(job)
        (folder/'wechat-submission.json').unlink()
        options=self.studio.load(job,'wechat-options.json')
        options.update(author='Rtwotwo',digest='研究使用共享表示连接视觉理解与动作输出，并进行同协议的结果比较。'+'其他细节在正文展开。'*15)
        write_json(folder/'wechat-options.json',options)
        article_before=(folder/'article.json').read_bytes()
        self.execute([self.items[0]['url']],generation=lambda *a:(_ for _ in ()).throw(AssertionError('Must reuse article')))
        self.assertEqual((folder/'article.json').read_bytes(),article_before)
        saved=self.studio.load(job,'wechat-options.json')
        self.assertEqual(saved['author'],'Rtwotwo');self.assertEqual(saved['cover_id'],options['cover_id'])
        self.assertLessEqual(len(saved['digest']),120)
        self.assertEqual(self.api.article['author'],'Rtwotwo')

    def test_cancel_during_pdf_failure_does_not_retry_download(self):
        from sources import download_arxiv
        requests=[]
        def fail(request,**kwargs):
            requests.append(request.full_url);self.feed.pause()
            raise URLError('Fixture interrupted')
        with patch('urllib.request.OpenerDirector.open',side_effect=fail),patch('sources.time.sleep'):
            self.execute([self.items[0]['url']],download=download_arxiv)
        self.assertEqual(requests,[self.items[0]['url'].replace('/abs/','/pdf/')])
        self.assertEqual(self.feed.state['selected_queue']['state'],'stopped')
        self.assertFalse(self.api.calls)


    def test_queue_blocks_manual_writes_to_later_selected_jobs(self):
        later=self.feed.selected_job(self.items[1]['url']);attempted=[]
        def generate(source,*args):
            if not attempted:
                with self.assertRaisesRegex(ValueError,'逐篇投递'):
                    self.studio.submit(later,'generate',lambda _:attempted.append('overwritten'))
                with self.assertRaisesRegex(ValueError,'逐篇投递'):
                    self.studio.library_update(later,{'trashed':True})
                attempted.append('blocked')
            return self.generation(source,*args)
        self.execute(generation=generate)
        self.assertEqual(attempted,['blocked'])
        self.assertEqual(self.feed.state['selected_queue']['state'],'complete')
        self.studio.library_update(later,{'display_name':'Editable after queue'})

    def test_explicit_generation_does_not_inherit_daily_vision_or_style(self):
        self.feed.config.update(vision=True,style='brief')
        seen=[]
        def generate(source,folder,options,*args):
            seen.append(options)
            return self.generation(source,folder,options,*args)
        self.execute([self.items[0]['url']],generation=generate)
        self.assertEqual(len(seen),1)
        self.assertFalse(seen[0]['vision']);self.assertNotEqual(seen[0]['style'],'brief')

    def execute(self,urls=None,download=None,generation=None,resume=False):
        self.events=[]
        def get(url,progress):
            self.events.append('download:'+url.rsplit('/',1)[-1])
            return fixture_pdf(),{'arxiv_id':url.rsplit('/',1)[-1],'url':url,'title':'Synthetic Robot World Model','authors':['Fixture Author']}
        with patch('autofeed.download_arxiv',side_effect=download or get),patch('autofeed.generate_article',side_effect=generation or self.generation),patch.object(self.studio,'format_skill',side_effect=self.format):
            result=self.feed.resume_selected() if resume else self.feed.start_links(urls or [i['url'] for i in self.items[:2]])
            if not result.get('existing'):self.feed.future.result(timeout=60)
            return result

    def test_paused_daily_allows_explicit_serial_drafts_without_resource_search(self):
        self.feed.pause();call=self.studio.wechat.call
        def record(path,**kwargs):
            if path=='draft/add':self.events.append('submit')
            return call(path,**kwargs)
        self.studio.wechat.call=record
        with patch('autofeed.verify_resources') as verify:
            self.execute()
        self.assertFalse(verify.called)
        self.assertEqual(self.events,['download:2610.00001','submit','download:2610.00002','submit'])
        self.assertFalse(self.feed.config['enabled']);self.assertEqual(self.feed.status()['today_attempts'],0)
        self.assertEqual(self.feed.state['selected_queue']['state'],'complete')
        for job in self.studio.jobs:self.assertFalse((self.studio.folder(job)/'wechat-review.json').exists())

    def test_finish_current_then_resume_never_predownloads(self):
        call=self.studio.wechat.call
        def stop(path,**kwargs):
            result=call(path,**kwargs)
            if path=='draft/get':self.feed.stop_after_current()
            return result
        self.studio.wechat.call=stop;self.execute()
        self.assertEqual(self.events,['download:2610.00001'])
        self.assertEqual(self.feed.state['selected_queue']['next'],1)
        self.studio.wechat.call=call;self.execute(resume=True)
        self.assertEqual(self.events,['download:2610.00002'])
        self.assertEqual(sum(p=='draft/add' for p,_ in self.api.calls),2)

    def test_cancel_or_failure_stops_without_starting_next_pdf(self):
        def cancel(source,*args):
            self.studio.jobs[source['id']]['cancelled']=True
            return self.generation(source,*args)
        self.execute(generation=cancel)
        self.assertEqual(self.events,['download:2610.00001'])
        self.assertFalse(self.api.calls);self.assertEqual(self.feed.state['selected_queue']['state'],'stopped')

    def test_unknown_receipt_does_not_regenerate_or_resend(self):
        self.api.add_error=TransportError('Fixture timeout')
        urls=[self.items[0]['url']];self.execute(urls)
        result=self.execute(urls)
        self.assertTrue(result['existing']);self.assertEqual(self.events,[])
        self.assertEqual(sum(p=='draft/add' for p,_ in self.api.calls),1)

    def test_existing_saved_article_is_reused(self):
        urls=[self.items[0]['url']];r=self.execute(urls)
        folder=self.studio.folder(r['id']);(folder/'wechat-submission.json').unlink()
        article=self.studio.load(r['id'],'article.json');article['title']='User edited title';self.studio.save_article(r['id'],article)
        with patch('autofeed.generate_article',side_effect=AssertionError('Must preserve article')):
            self.execute(urls,generation=lambda *a:(_ for _ in ()).throw(AssertionError('Must preserve article')))
        self.assertEqual(self.events,[])
        self.assertEqual(self.studio.load(r['id'],'article.json')['title'],'User edited title')

if __name__=='__main__':unittest.main()
