import json
import unittest
import urllib.error
from tests import test_server
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from tests.test_materials import png
from wechat_review import prepare, approve, is_approved, CHECKS


class MaterialHTTPTests(unittest.TestCase):
    setUp=test_server.ServerTests.setUp
    tearDown=test_server.ServerTests.tearDown
    call=test_server.ServerTests.call
    ready=test_server.ServerTests.ready
    def test_upload_replace_review_export_and_invalid_upload(self):
        raw,_=self.call('/api/import/pdf',fixture_pdf());job=json.loads(raw)['id'];self.ready(job)
        source=self.studio.load(job);article=fixture_article(source);fid=source['figures'][0]['id']
        self.call(f'/api/jobs/{job}/article',article)
        folder=self.studio.folder(job);opts={'cover_id':fid};account={'appid':'fixture'}
        before=prepare(folder,article,source,opts,account);approve(folder,before,{k:True for k in CHECKS})
        raw,_=self.call(f'/api/jobs/{job}/import-image?replace_id={fid}&filename=local.png&page=1',png())
        source=json.loads(raw);self.assertEqual(source['figures'][0]['id'],fid)
        self.assertFalse(source['figures'][0]['reviewed'])
        with self.assertRaisesRegex(ValueError,'新导入'):prepare(folder,article,source,opts,account)
        self.call(f'/api/jobs/{job}/figures',{'figures':[{'id':fid,'reviewed':True,'selected':True}]})
        prepared=prepare(folder,article,self.studio.load(job),opts,account)
        self.assertFalse(is_approved(folder,prepared))
        raw,_=self.call(f'/api/jobs/{job}/export?format=zip');self.assertTrue(raw.startswith(b'PK'))
        self.assertEqual(self.studio.load(job,'article.json')['sections'],article['sections'])
        with self.assertRaises(urllib.error.HTTPError):self.call(f'/api/jobs/{job}/import-image',b'not an image')
        with self.assertRaises(urllib.error.HTTPError):self.call(f'/api/jobs/{job}/import-image',png(),token=False)
        self.studio.update(job,status='running')
        with self.assertRaises(urllib.error.HTTPError):self.call(f'/api/jobs/{job}/import-image',png())
        self.studio.update(job,status='ready')

    def test_scanner_and_asset_path(self):
        raw,_=self.call('/api/import/pdf',fixture_pdf());job=json.loads(raw)['id'];self.ready(job)
        self.call(f'/api/jobs/{job}/scan-materials',{})
        self.assertEqual(self.ready(job)['status'],'ready')
        raw,_=self.call(f'/api/jobs/{job}/materials');self.assertIn('items',json.loads(raw))
        with self.assertRaises(urllib.error.HTTPError):self.call(f'/api/jobs/{job}/asset?name=materials/../../settings/models.dpapi')
