import copy,json,tempfile,unittest
from pathlib import Path
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from sources import extract_pdf
from wechat_review import prepare,approve,is_approved,require_approved,CHECKS,asset_path

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.source=extract_pdf(fixture_pdf(),self.root);self.article=fixture_article(self.source)
        self.options={'title':'论文解读','digest':'摘要','cover_id':self.source['figures'][0]['id']}
        self.account={'appid':'wx'+'1'*16,'name':'Fixture'}
    def tearDown(self):self.tmp.cleanup()
    def payload(self):return prepare(self.root,self.article,self.source,self.options,self.account)
    def test_approval_bound_to_public_content_assets_options_and_account(self):
        p=self.payload()
        with self.assertRaises(ValueError):require_approved(self.root,p)
        with self.assertRaises(ValueError):approve(self.root,p,{'facts':True})
        approve(self.root,p,{k:True for k in CHECKS},'Editor')
        self.assertTrue(is_approved(self.root,self.payload()))
        old=copy.deepcopy(self.article);self.article['lead']+='changed'
        self.assertFalse(is_approved(self.root,self.payload()));self.article=old
        self.options['theme']='blue';self.assertFalse(is_approved(self.root,self.payload()));self.options['theme']='ink'
        self.account['appid']='wx'+'2'*16;self.assertFalse(is_approved(self.root,self.payload()));self.account['appid']='wx'+'1'*16
        path=asset_path(self.root,p['assets'][0]['image']);path.write_bytes(path.read_bytes()+b'changed')
        self.assertFalse(is_approved(self.root,self.payload()))
    def test_limits_and_public_text(self):
        self.article['lead']='说明 pages: [1, 2]'
        p=self.payload();self.assertNotIn('pages:',p['content']);self.assertNotIn('data:image',p['content'])
        self.assertIn('images/fig-',p['content'])
        self.options['title']='a'*33
        with self.assertRaises(ValueError):self.payload()
        self.options['title']='short';self.options['digest']='a'*121
        with self.assertRaises(ValueError):self.payload()
        self.options['digest']='short';self.article['lead']='长'*22000
        with self.assertRaises(ValueError):self.payload()
    def test_invalid_asset_and_unchecked_video_warning(self):
        with self.assertRaises(ValueError):asset_path(self.root,'../secret.png')
        self.source['project_media']=[{'selected':True,'caption':'演示','source_url':'https://example.com/demo.mp4'}]
        self.assertEqual(self.payload()['video_count'],1)

    def test_card_digest_never_replaces_original_body_summary(self):
        from formatting import layout_markdown
        original='完整摘要说明研究方法和评测条件。'*20
        self.article['digest']=original
        self.options['digest']='简短的草稿卡片文案'
        self.assertIn(original,self.payload()['content'])
        rendered=layout_markdown(self.article,self.source,self.options)
        self.assertIn(original,rendered)
        self.assertNotIn(self.options['digest'],rendered)

if __name__=='__main__':unittest.main()
