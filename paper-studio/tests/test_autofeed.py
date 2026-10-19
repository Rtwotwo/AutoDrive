import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from server import Studio
from autofeed import today,automatic_checks
from feed_sources import TOPICS
from figure_plan import build_plan
from sources import write_json
from wechat_api import Account,TransportError,submit_draft,submit_automated_draft
from wechat_review import render_content
from formatting import layout_markdown
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from tests.test_wechat_api import FakeAPI

class AutoFeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.studio=Studio(self.root/'data');self.api=FakeAPI()
        self.studio.wechat=Account(None,self.api)
        self.studio.wechat.config={'appid':'wx'+'1'*16,'secret':'SYNTHETIC_NOT_REAL_12345','name':'Fixture'}
        self.studio.wechat.remember=True
        self.studio.profiles={'p':{'model':'fixture','base_url':'http://localhost:9999','api_key':''}}
        self.studio.remember_models=True;self.studio.active_profile='p'
        self.feed=self.studio.autofeed
        self.feed.configure({'enabled':True,'model_profile':'p'})
        self.items=[{'id':f'2610.{i:05}','arxiv_id':f'2610.{i:05}','title':'Synthetic Robot World Model',
                     'abstract':'World model fixture','authors':['Fixture Author'],'topics':['world'],
                     'published':'2026-10-19T00:00:00Z','url':f'https://arxiv.org/abs/2610.{i:05}'} for i in range(1,8)]
    def tearDown(self):
        self.studio.pool.shutdown(wait=True);self.studio.close();self.tmp.cleanup()
    def resources(self,item,folder,**kwargs):
        folder.mkdir(exist_ok=True,parents=True);(folder/(item['id']+'.pdf')).write_bytes(fixture_pdf())
        return {'verified':True,'paper_url':item['url'],'code_url':'https://github.com/lab/fixture','project_url':'https://example.com/fixture'}
    def generation(self,source,*args):
        a=fixture_article(source);a['paper']={'affiliations':['Fixture University']}
        plan=build_plan(source)
        a['sections'][2]['figures']=[{'id':f,'caption':'Fixture figure','explanation':'Synthetic explanation only','pages':[1]} for f in plan['ids']]
        return a,[],{}
    def format(self,job,progress):
        folder=self.studio.folder(job);a=self.studio.load(job,'article.json');s=self.studio.load(job);o=self.studio.load(job,'wechat-options.json')
        write_json(folder/'baoyu-layout.json',{'markdown':layout_markdown(a,s,o),'content':render_content(a,s,dict(o,theme='ink')),'baoyu_theme':o['baoyu_theme']})
    def run_batch(self,items=None):
        with patch('native_figures.improve_native_figures',side_effect=lambda source,*args:source),patch('autofeed.discover_recent',return_value={'items':self.items if items is None else items,'errors':[]}),patch('autofeed.verify_resources',side_effect=self.resources),patch('autofeed.generate_article',side_effect=self.generation),patch.object(self.studio,'format_skill',side_effect=self.format):
            self.feed.start();self.feed.future.result(timeout=90)
    def test_batch_five_limit_dedup_and_no_fake_human_approval(self):
        self.run_batch()
        status=self.feed.status();self.assertEqual(status['today_attempts'],5)
        self.assertEqual(sum(i['state']=='submitted' for i in status['items']),5,status['items'])
        self.assertEqual(sum(p=='draft/add' for p,_ in self.api.calls),5)
        self.run_batch();self.assertEqual(sum(p=='draft/add' for p,_ in self.api.calls),5)
        for job in self.studio.jobs:
            folder=self.studio.folder(job)
            self.assertFalse((folder/'wechat-review.json').exists())
            with self.assertRaises(ValueError):submit_draft(folder,self.studio.wechat_prepared(job),self.studio.wechat)
            p=copy.deepcopy(self.studio.wechat_prepared(job));p['content']+='changed'
            with self.assertRaises(ValueError):submit_automated_draft(folder,p,self.studio.wechat)
        self.assertNotIn('SYNTHETIC_NOT_REAL',json.dumps(status))
    def test_unknown_result_never_resends(self):
        self.api.add_error=TransportError('Fixture timeout')
        self.run_batch(self.items[:1]);self.run_batch(self.items[:1])
        self.assertEqual(sum(p=='draft/add' for p,_ in self.api.calls),1)
        self.assertEqual(self.feed.status()['items'][0]['state'],'unknown')
        self.assertEqual(self.feed.status()['today_attempts'],1)
    def test_no_new_no_model_and_resource_missing_no_attempt(self):
        self.run_batch([]);self.assertEqual(self.feed.status()['today_attempts'],0)
        with patch('autofeed.discover_recent',return_value={'items':self.items[:1],'errors':[]}),patch('autofeed.verify_resources',return_value={'verified':False,'note':'not verified'}),patch('autofeed.generate_article') as model:
            self.feed.start();self.feed.future.result(timeout=10)
            self.assertFalse(model.called)
        self.assertEqual(self.feed.status()['today_attempts'],0)
    def test_persisted_attempts_and_pause(self):
        self.run_batch(self.items[:1]);self.feed.pause()
        with self.assertRaises(ValueError):self.feed.start()
        reopened=Studio(self.root/'data')
        try:
            self.assertEqual(reopened.autofeed.status()['today_attempts'],1)
            self.assertFalse(reopened.autofeed.config['enabled'])
        finally:reopened.close()
    def test_profile_edits_blocked_during_batch(self):
        self.feed.running=True
        with self.assertRaises(ValueError):self.feed.configure({'max_daily':3})
        with self.assertRaises(ValueError):self.studio.configure_models({'clear':True})
        self.feed.running=False

    def test_per_job_cancel_stops_before_external_draft_writes(self):
        original=self.generation
        def cancel_in_model(source,*args):
            self.studio.jobs[source['id']]['cancelled']=True
            return original(source,*args)
        self.generation=cancel_in_model
        self.run_batch(self.items[:1])
        self.assertEqual(self.feed.status()['items'][0]['state'],'held')
        self.assertFalse(self.api.calls)

if __name__=='__main__':unittest.main()
