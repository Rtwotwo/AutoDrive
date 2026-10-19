from pathlib import Path
import io,tempfile,unittest
from PIL import Image
from native_figures import improve_native_figures
from sources import extract_pdf
from tests.test_sources import fixture_pdf

class NativeFiguresTests(unittest.TestCase):
    def test_single_complete_image_replaces_crop_but_multi_panel_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s=extract_pdf(fixture_pdf(),root);s['arxiv_id']='2610.12345'
            s['figures'][0].update(original_caption='Figure 1. Architecture',reviewed=False)
            image=Image.new('RGB',(600,200),'blue');out=io.BytesIO();image.save(out,'PNG')
            html=b'<figure><img src="x1.png"><figcaption>Figure 1: Architecture</figcaption></figure><figure><img src="x2.png"><img src="x3.png"><figcaption>Figure 2: Panels</figcaption></figure>'
            def fetch(url,limit):return html if url.endswith('2610.12345') else out.getvalue()
            improve_native_figures(s,root,fetch=fetch)
            self.assertEqual(s['figures'][0]['origin'],'arxiv_html')
            self.assertEqual(s['figures'][0]['bbox'],[])
            self.assertTrue(list((root/'image-history').glob('*.png')))
            self.assertEqual(s['native_figures_checked']['replaced'],['fig-001'])

    def test_reviewed_image_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s=extract_pdf(fixture_pdf(),root);s['arxiv_id']='2610.12345'
            s['figures'][0].update(original_caption='Figure 1. Architecture',reviewed=True)
            original=(root/s['figures'][0]['image']).read_bytes()
            improve_native_figures(s,root,fetch=lambda *x:b'<figure><img src="x.png"><figcaption>Figure 1: Architecture</figcaption></figure>')
            self.assertEqual(original,(root/s['figures'][0]['image']).read_bytes())

if __name__=='__main__':unittest.main()
