import json,tempfile,threading,time,unittest,urllib.request,urllib.error
from pathlib import Path
from server import Studio,make_server
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from tests.test_wechat_api import FakeAPI
from sources import extract_pdf
from wechat_review import CHECKS

class WechatServerTests(unittest.TestCase):
    def test_manual_fit_save_preserves_original_and_requires_new_review(self):
        self.call('/api/wechat/config',{'appid':'wx'+'1'*16,'secret':'FAKE_SECRET_1234567890'})
        options={'title':'待审稿','digest':'原始短摘要','cover_id':self.source['figures'][0]['id']}
        self.call(self.endpoint('wechat-options'),options)
        self.call(self.endpoint('wechat-approve'),{'checks':{k:True for k in CHECKS}})
        before=(self.studio.folder(self.job)/'article.json').read_bytes()
        options['digest']='方法通过共享表示连接视觉理解与动作输出，并使用统一协议评估结果。'+'详细实验条件和结果在正文介绍。'*12
        fitted=self.call(self.endpoint('wechat-fit'),{'title':options['title'],'digest':options['digest']})
        self.assertLessEqual(len(fitted['options']['digest']),120)
        self.assertFalse((self.studio.folder(self.job)/'wechat-field-adjustments.json').exists())
        self.assertTrue(self.call(self.endpoint('wechat'))['approved'])
        state=self.call(self.endpoint('wechat-options'),options)
        self.assertFalse(state['approved']);self.assertEqual(state['blocker'],'')
        self.assertEqual(state['field_adjustments'][0]['before'],options['digest'])
        self.assertEqual((self.studio.folder(self.job)/'article.json').read_bytes(),before)
        self.assertFalse(self.fake.calls)

    def test_preview_does_not_replace_saved_digest_provenance(self):
        self.call('/api/wechat/config',{'appid':'wx'+'1'*16,'secret':'FAKE_SECRET_1234567890'})
        original='方法连接视觉表示与动作输出，并在统一协议下评估。'+'详细实验与消融条件见正文。'*20
        options={'title':'待审稿','digest':original,'cover_id':self.source['figures'][0]['id']}
        saved=self.call(self.endpoint('wechat-options'),options)
        options=saved['options']
        report=self.studio.folder(self.job)/'wechat-field-adjustments.json'
        before=report.read_bytes()
        fitted=self.call(self.endpoint('wechat-fit'),{'title':'标题'*50,'digest':options['digest']})
        self.assertEqual(report.read_bytes(),before)
        self.assertEqual(self.call(self.endpoint('wechat'))['field_adjustments'][0]['before'],original)
        options.update(fitted['options']);options['field_adjustments']=fitted['field_adjustments']
        saved=self.call(self.endpoint('wechat-options'),options)
        originals={c['field']:c['before'] for c in saved['field_adjustments']}
        self.assertEqual(originals,{'digest':original,'title':'标题'*50})

    def test_fitted_preview_provenance_saved_only_when_matching(self):
        self.call('/api/wechat/config',{'appid':'wx'+'1'*16,'secret':'FAKE_SECRET_1234567890'})
        original='方法连接视觉表示与动作输出，并在统一协议下评估。'+'结果与条件见正文。'*25
        fitted=self.call(self.endpoint('wechat-fit'),{'title':'研究','digest':original})
        values={**fitted['options'],'cover_id':self.source['figures'][0]['id'],'field_adjustments':fitted['field_adjustments']}
        saved=self.call(self.endpoint('wechat-options'),values)
        self.assertEqual(saved['field_adjustments'][0]['before'],original)
        values.update(digest='用户自行修改的短摘要',field_adjustments=[{'field':'digest','before':original,'after':'用户自行修改的短摘要','reason':'fake'}])
        saved=self.call(self.endpoint('wechat-options'),values)
        self.assertEqual(saved['field_adjustments'],[])

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.studio=Studio(Path(self.tmp.name)/'data')
        self.studio.desktop=True;self.fake=FakeAPI();self.studio.wechat.request=self.fake
        self.server=make_server(self.studio,0);threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
        self.job=self.studio.create('Fixture');self.source=extract_pdf(fixture_pdf(),self.studio.folder(self.job))
        self.article=fixture_article(self.source);self.studio.save_article(self.job,self.article)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.studio.pool.shutdown(wait=True);self.tmp.cleanup()
    def call(self,path,body=None,auth=True):
        data=json.dumps(body).encode() if body is not None else None
        headers={'X-Studio-Token':self.studio.token,'Content-Type':'application/json'}
        if auth:headers['Cookie']='studio_session='+self.studio.cookie
        with urllib.request.urlopen(urllib.request.Request(self.url+path,data=data,headers=headers),timeout=10) as r:
            raw=r.read();return json.loads(raw) if r.headers.get_content_type()=='application/json' else raw
    def endpoint(self,x):return f'/api/jobs/{self.job}/'+x
    def test_review_upload_and_repeat_guard_through_http(self):
        with self.assertRaises(urllib.error.HTTPError):self.call('/api/wechat',auth=False)
        c=self.call('/api/wechat/config',{'appid':'wx'+'1'*16,'secret':'FAKE_SECRET_1234567890','remember':False,'name':'Test'})
        self.assertNotIn('secret',c);self.call('/api/wechat/check',{})
        self.call(self.endpoint('wechat-options'),{'title':'待审稿','digest':'摘要','cover_id':self.source['figures'][0]['id']})
        with self.assertRaises(urllib.error.HTTPError):self.call(self.endpoint('wechat-submit'),{})
        self.call(self.endpoint('wechat-approve'),{'checks':{k:True for k in CHECKS}})
        self.assertTrue(self.call(self.endpoint('wechat'))['approved'])
        preview=self.call(self.endpoint('wechat-preview'));self.assertIn(b'data:image',preview)
        self.article['lead']+='changed';self.call(self.endpoint('article'),self.article)
        self.assertFalse(self.call(self.endpoint('wechat'))['approved'])
        with self.assertRaises(urllib.error.HTTPError):self.call(self.endpoint('wechat-submit'),{})
        self.call(self.endpoint('wechat-approve'),{'checks':{k:True for k in CHECKS}})
        self.call(self.endpoint('wechat-submit'),{})
        for _ in range(100):
            if self.studio.jobs[self.job]['status'] not in {'running','queued'}:break
            time.sleep(.03)
        r=self.call(self.endpoint('wechat'));self.assertEqual(r['submission']['state'],'submitted')
        with self.assertRaises(urllib.error.HTTPError):self.call(self.endpoint('wechat-submit'),{})
        self.assertEqual(sum(x[0]=='draft/add' for x in self.fake.calls),1)
    def test_account_switch_invalidates_review_and_busy_config_rejected(self):
        self.call('/api/wechat/config',{'appid':'wx'+'1'*16,'secret':'FAKE_SECRET_1234567890'})
        self.call(self.endpoint('wechat-options'),{'title':'待审稿','digest':'摘要','cover_id':self.source['figures'][0]['id']})
        self.call(self.endpoint('wechat-approve'),{'checks':{k:True for k in CHECKS}})
        self.call('/api/wechat/config',{'appid':'wx'+'2'*16,'secret':'OTHER_FAKE_SECRET_1234567890'})
        self.assertFalse(self.call(self.endpoint('wechat'))['approved'])
        self.studio.jobs[self.job].update(status='running',operation='wechat-submit')
        with self.assertRaises(urllib.error.HTTPError):self.call('/api/wechat/config',{'clear':True})

if __name__=='__main__':unittest.main()
