import tempfile
import unittest
from pathlib import Path
from io import BytesIO
from PIL import Image
from tests import pdf_fixtures as pdf
from sources import extract_pdf, repair_crops, CAPTION
from materials import extract_embedded, accept_image, normalize_image


def png(color='red'):
    im=Image.new('RGB',(300,180),color);b=BytesIO();im.save(b,format='PNG');return b.getvalue()


class MaterialTests(unittest.TestCase):
    def test_caption_no_punctuation_discovery_preserves_manual(self):
        self.assertTrue(CAPTION.match('Figure 1 Overview of our method'))
        self.assertFalse(CAPTION.match('Table 2 compares our results'))
        with tempfile.TemporaryDirectory() as tmp,pdf.open() as d:
            p=d.new_page();p.draw_rect((80,100,500,270));p.insert_text((80,300),'Figure 1 Overview of the system')
            s=extract_pdf(d.tobytes(),tmp)
            self.assertEqual(len(s['figures']),1)
            original=s['figures'][0];original.update(reviewed=True,crop_status='manual')
            before=(Path(tmp)/original['image']).read_bytes()
            repair_crops(tmp,s)
            self.assertEqual(len(s['figures']),1);self.assertEqual((Path(tmp)/original['image']).read_bytes(),before)
            s['figures']=[];repair_crops(tmp,s)
            self.assertEqual(len(s['figures']),1);self.assertFalse(s['figures'][0]['selected'])

    def test_embedded_resolution_and_repeat_pages(self):
        with tempfile.TemporaryDirectory() as tmp,pdf.open() as d:
            p=d.new_page();xref=p.insert_image((80,80,230,170),stream=png())
            d.new_page().insert_image((80,80,230,170),xref=xref)
            Path(tmp,'source.pdf').write_bytes(d.tobytes())
            c=extract_embedded(tmp)
            self.assertEqual(len(c['items']),1)
            it=c['items'][0];self.assertEqual(it['pages'],[1,2]);self.assertEqual([it['width'],it['height']],[300,180])
            with Image.open(Path(tmp)/it['image']) as im:self.assertEqual(im.getpixel((1,1))[:3],(255,0,0))

    def test_import_replace_keeps_id_and_recovers_old_pixels(self):
        with tempfile.TemporaryDirectory() as tmp,pdf.open() as d:
            d.new_page();s=extract_pdf(d.tobytes(),tmp)
            accept_image(tmp,s,png(),caption='A local complete figure')
            f=s['figures'][0];fid=f['id'];f.update(selected=True,reviewed=True)
            before=(Path(tmp)/f['image']).read_bytes()
            accept_image(tmp,s,png('blue'),replace_id=fid,page=1)
            f=s['figures'][0]
            self.assertEqual(f['id'],fid);self.assertFalse(f['reviewed']);self.assertTrue(f['selected'])
            self.assertEqual(next((Path(tmp)/'image-history').iterdir()).read_bytes(),before)
            self.assertEqual(f['caption'],'A local complete figure')
            with self.assertRaises(ValueError):accept_image(tmp,s,png(),page=999)
            with self.assertRaises(ValueError):normalize_image(b'not an image')

    def test_transparent_png_preserves_pixels(self):
        im=Image.new('RGBA',(200,100),(255,0,0,128));b=BytesIO();im.save(b,format='PNG')
        data,size=normalize_image(b.getvalue());self.assertEqual(size,[200,100])
        with Image.open(BytesIO(data)) as out:self.assertEqual(out.getpixel((1,1)),(255,0,0,128))

    def test_replace_rescan_retains_caption_anchor_and_validates_pages(self):
        from tests.test_sources import fixture_pdf
        from tests.test_writing import fixture_article
        from writing import validate_article
        with tempfile.TemporaryDirectory() as tmp:
            s=extract_pdf(fixture_pdf(),tmp);old=dict(s['figures'][0]);a=fixture_article(s)
            accept_image(tmp,s,png(),replace_id=old['id'])
            repair_crops(tmp,s)
            self.assertEqual(len(s['figures']),1)
            self.assertEqual(s['figures'][0]['original_caption'],old['original_caption'])
            figure=a['sections'][2]['figures'][0];figure['pages']=[];validate_article(a,s)
            figure['pages']='not-a-list'
            with self.assertRaisesRegex(ValueError,'pages'):validate_article(a,s)
            figure['pages']=[999]
            audit=validate_article(a,s)
            self.assertTrue(any('页码' in i['message'] for i in audit['issues']))

    def test_borderless_ruled_table_does_not_take_body_text(self):
        with tempfile.TemporaryDirectory() as tmp,pdf.open() as d:
            p=d.new_page()
            p.insert_text((60,110),'Table 1 Training Configuration')
            for y in (125,150,280):p.draw_line((60,y),(500,y))
            p.insert_text((70,142),'Component');p.insert_text((300,142),'Configuration')
            for y in range(170,280,20):
                p.insert_text((70,y),'Setting');p.insert_text((300,y),'Value')
            p.insert_text((60,330),'Unrelated body paragraph after the table.')
            s=extract_pdf(d.tobytes(),tmp);f=s['figures'][0]
            self.assertEqual(f['crop_status'],'table_detected')
            self.assertGreaterEqual(f['bbox'][3],280);self.assertLess(f['bbox'][3],320)

    def test_catalog_candidate_does_not_use_local_upload_cap(self):
        from unittest.mock import patch
        from materials import accept_candidate
        with tempfile.TemporaryDirectory() as tmp,pdf.open() as d:
            p=d.new_page();p.insert_image((60,100,360,280),stream=png())
            s=extract_pdf(d.tobytes(),tmp);c=extract_embedded(tmp)
            with patch('materials.MAX_UPLOAD',1):
                with self.assertRaises(ValueError):accept_image(tmp,s,png())
                accept_candidate(tmp,s,{'id':c['items'][0]['id']})
            self.assertEqual(s['figures'][-1]['origin'],'pdf_embedded')
