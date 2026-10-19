import io, json, socket, tempfile, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from project_media import public_target, MediaParser, import_material, discover
from sources import extract_pdf
from exporting import export_bundle
from writing import validate_article
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from tests import test_server

class MediaTests(unittest.TestCase):
    def test_private_addresses_and_nonstandard_ports_rejected(self):
        for address in ['127.0.0.1','10.1.2.3','::1','169.254.169.254','::ffff:127.0.0.1']:
            with patch('socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',(address,443))]):
                with self.assertRaises(ValueError): public_target('https://project.example/demo')
        with self.assertRaises(ValueError): public_target('https://project.example:8765/')
        with self.assertRaises(ValueError): public_target('file:///private/key')
        with patch('socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443))]):
            self.assertEqual(public_target('https://project.example/demo')[2],'8.8.8.8')

    def test_html_media_discovery_not_scripts_or_credentials(self):
        parser=MediaParser('https://project.example/paper/')
        parser.feed('<img src="fig.png" alt="Method"><img src="fig.png"><img src="logo.svg"><video><source src="demo.mp4"></video><script>secret()</script><img src="file:///key">')
        self.assertEqual(len(parser.items),2)
        self.assertEqual(parser.items[0]['url'],'https://project.example/paper/fig.png')
        self.assertEqual(parser.items[1]['kind'],'video')

    def test_import_image_and_video_export_credit_and_no_fake_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); source=extract_pdf(fixture_pdf(),folder)
            image=io.BytesIO();Image.new('RGB',(80,60),'white').save(image,format='PNG')
            candidate={'id':'a'*16,'kind':'image','url':'https://project.example/figure.png','label':'Fixture image','page_url':'https://project.example/'}
            with patch('project_media.fetch_public',return_value=(image.getvalue(),'image/png',candidate['url'])):
                import_material(folder,source,candidate)
            figure=source['figures'][-1];self.assertIsNone(figure['page']);figure['reviewed']=True
            candidate.update(id='b'*16,kind='video',url='https://project.example/demo.mp4',label='Fixture video')
            video=b'\x00\x00\x00\x18ftypisom'+b'fixture-container'*10
            with patch('project_media.fetch_public',return_value=(video,'video/mp4',candidate['url'])):
                import_material(folder,source,candidate)
            article=fixture_article(source);article['sections'][0]['figures'].append({'id':figure['id'],'caption':'Project image','explanation':'Fixture','pages':[]})
            audit=validate_article(article,source)
            self.assertFalse(any(figure['id']+' 图解缺少' in x['message'] for x in audit['issues']))
            with zipfile.ZipFile(io.BytesIO(export_bundle(article,source,folder))) as z:
                self.assertIn('media/media-'+ 'b'*16 +'.mp4',z.namelist())
                self.assertIn('<video ',z.read('preview.html').decode())
                self.assertNotIn('<video ',z.read('wechat.html').decode())
                self.assertIn('https://project.example/demo.mp4',z.read('wechat.html').decode())
                self.assertIn('图片来源',z.read('wechat.html').decode())

class PublicationHTTPTests(unittest.TestCase):
    setUp=test_server.ServerTests.setUp
    tearDown=test_server.ServerTests.tearDown
    call=test_server.ServerTests.call
    ready=test_server.ServerTests.ready
    def test_metadata_media_routes_and_background_repair(self):
        job=json.loads(self.call('/api/import/pdf',fixture_pdf())[0])['id'];self.ready(job)
        self.call(f'/api/jobs/{job}/paper-info',{'title':'Verified title','authors':['A'],'affiliations':['Lab'],'project_url':'https://project.example/'})
        result=json.loads(self.call(f'/api/jobs/{job}/source')[0]);self.assertEqual(result['publication_info']['authors'],['A'])
        with patch('server.discover',return_value={'requested_url':'https://project.example/','items':[]}):
            self.call(f'/api/jobs/{job}/scan-media',{});self.assertEqual(self.ready(job)['status'],'ready')
            self.assertEqual(json.loads(self.call(f'/api/jobs/{job}/project-media')[0])['items'],[])
        self.call(f'/api/jobs/{job}/repair-crops',{});self.assertEqual(self.ready(job)['status'],'ready')
        self.assertEqual(self.studio.load(job)['paper_info']['title'],'Verified title')

if __name__=='__main__':unittest.main()
