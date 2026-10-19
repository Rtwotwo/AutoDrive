from io import BytesIO
import tempfile
from pathlib import Path
import unittest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject
from PIL import Image
import pdf_backend as pdf
from tests.test_sources import fixture_pdf
from tests import pdf_fixtures


class BackendTests(unittest.TestCase):
    def test_cropbox_does_not_expand_or_expose_hidden_margin_text(self):
        from reportlab.pdfgen.canvas import Canvas
        data=BytesIO();canvas=Canvas(data,pagesize=(400,600))
        canvas.drawString(10,550,'OUTSIDE_CROPBOX_CONTENT')
        canvas.drawString(110,300,'VISIBLE_CONTENT')
        canvas.linkURL('https://outside.example/',(10,530,80,555))
        canvas.linkURL('https://inside.example/',(110,280,180,310))
        canvas.showPage();canvas.save()
        reader=PdfReader(BytesIO(data.getvalue()));reader.pages[0].cropbox=RectangleObject((100,200,300,400))
        writer=PdfWriter();writer.append(reader);out=BytesIO();writer.write(out)
        with pdf.open(stream=out.getvalue()) as doc:
            self.assertEqual(tuple(doc[0].rect),(0,0,200,200))
            self.assertNotIn('OUTSIDE',doc[0].get_text());self.assertIn('VISIBLE',doc[0].get_text())
            self.assertEqual(doc[0].get_links(),[{'uri':'https://inside.example/'}])
            pix=doc[0].get_pixmap(pdf.Matrix(1,1));self.assertEqual((pix.width,pix.height),(200,200))

    def test_nested_form_text_is_preserved(self):
        from reportlab.pdfgen.canvas import Canvas
        data=BytesIO();canvas=Canvas(data,pagesize=(400,600))
        canvas.beginForm('inner');canvas.drawString(20,400,'Figure 2: nested architecture label 91.3');canvas.endForm()
        canvas.beginForm('outer');canvas.doForm('inner');canvas.endForm()
        canvas.doForm('outer');canvas.showPage();canvas.save()
        with pdf.open(stream=data.getvalue()) as doc:
            self.assertIn('nested architecture label 91.3',doc[0].get_text())
            self.assertTrue(any('Figure 2' in b[4] for b in doc[0].get_text('blocks')))

    def test_password_is_not_silently_accepted(self):
        writer=PdfWriter();writer.append(PdfReader(BytesIO(fixture_pdf())))
        writer.encrypt('synthetic-fixture-password')
        data=BytesIO();writer.write(data)
        with pdf.open(stream=data.getvalue()) as doc:self.assertTrue(doc.needs_pass)

    def test_crop_pixels_align_with_top_left_layout(self):
        with pdf_fixtures.open() as fixture:
            page=fixture.new_page(width=400,height=600)
            page.draw_rect((100,150,300,250),color=(1,0,0),fill=(1,0,0))
            with pdf.open(stream=fixture.tobytes()) as doc:
                pix=doc[0].get_pixmap(pdf.Matrix(2,2),clip=pdf.Rect(110,160,290,240))
                im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                self.assertEqual(im.size,(360,160));self.assertEqual(im.getpixel((180,80)),(255,0,0))

    def test_native_alpha_and_uri(self):
        with pdf_fixtures.open() as fixture:
            page=fixture.new_page()
            im=Image.new('RGBA',(300,180),(255,0,0,128));buf=BytesIO();im.save(buf,format='PNG')
            page.insert_image((60,100,360,280),stream=buf.getvalue())
            page.insert_link({'from':pdf.Rect(10,10,50,30),'uri':'https://example.org/paper'})
            with pdf.open(stream=fixture.tobytes()) as doc:
                self.assertEqual(doc[0].get_links(),[{'uri':'https://example.org/paper'}])
                image=next(doc[0].embedded_images())
                with Image.open(BytesIO(image['data'])) as out:
                    self.assertEqual(out.size,(300,180));self.assertEqual(out.getpixel((2,2)),(255,0,0,128))

    def test_page_rotation_uses_same_unrotated_coordinate_system(self):
        reader=PdfReader(BytesIO(fixture_pdf()));reader.pages[0].rotate(90)
        writer=PdfWriter();writer.append(reader);buf=BytesIO();writer.write(buf)
        with pdf.open(stream=buf.getvalue()) as doc:
            self.assertEqual(tuple(doc[0].rect),(0,0,595,842))
            self.assertIn('Source-grounded',doc[0].get_text())
            pix=doc[0].get_pixmap(pdf.Matrix(1,1))
            self.assertEqual((pix.width,pix.height),(595,842))
