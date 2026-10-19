import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import pdf_fixtures as pdf
from sources import parse_arxiv, extract_pdf, crop_figure, download_arxiv


def fixture_pdf():
    doc = pdf.open()
    p = doc.new_page()
    p.insert_text((50, 55), 'Source-grounded driving paper fixture', fontsize=19)
    p.insert_textbox(pdf.Rect(50, 90, 540, 210), 'Research fixture only. We evaluate a planning policy on a fixed split. The reported success rate is 83.2 percent. The baseline is 75.0 percent. These numbers are artificial test data, not published research. ' * 3, fontsize=11)
    p.draw_rect(pdf.Rect(60, 230, 500, 350), color=(.1, .5, .7), fill=(.9, .95, 1))
    p.insert_text((80, 280), 'Sensor input -> Planner -> Action', fontsize=16)
    p.insert_text((60, 380), 'Figure 1: Fixture planning architecture.', fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


class SourceTests(unittest.TestCase):
    def test_arxiv_forms_and_rejection(self):
        for value, aid in [('2212.10156v2', '2212.10156v2'), ('https://arxiv.org/pdf/2212.10156.pdf', '2212.10156'), ('https://arxiv.org/abs/cs/0601001', 'cs/0601001')]:
            self.assertEqual(parse_arxiv(value), aid)
        for value in ['https://evil.test/abs/2212.10156', 'http://127.0.0.1/x', 'https://arxiv.org.evil/abs/2212.10156', 'https://arxiv.org:443/abs/2212.10156']:
            with self.assertRaises(ValueError): parse_arxiv(value)

    def test_extraction_and_crop(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = extract_pdf(fixture_pdf(), Path(tmp) / 'fixture')
            self.assertTrue(m['can_generate'])
            self.assertEqual(m['figures'][0]['page'], 1)
            self.assertIn('83.2', m['pages'][0]['text'])
            self.assertTrue((Path(tmp) / 'fixture' / m['figures'][0]['image']).is_file())
            m = crop_figure(Path(tmp) / 'fixture', m, 1, [.05, .25, .95, .5], 'Reviewed crop')
            self.assertTrue(m['figures'][-1]['reviewed'])
            with self.assertRaises(ValueError): crop_figure(Path(tmp) / 'fixture', m, 1, [.9, 0, .1, 1])

    def test_empty_scan_and_bad_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = pdf.open(); doc.new_page()
            m = extract_pdf(doc.tobytes(), Path(tmp)); doc.close()
            self.assertFalse(m['can_generate'])
            with self.assertRaises(ValueError): extract_pdf(b'<html>not a PDF</html>', Path(tmp))

    def test_arxiv_metadata_fallback(self):
        with patch('sources.fetch_arxiv_bytes', side_effect=[fixture_pdf(), RuntimeError('offline')]):
            data, meta = download_arxiv('2212.10156')
            self.assertTrue(data.startswith(b'%PDF'))
            self.assertEqual(meta['arxiv_id'], '2212.10156')
            self.assertIn('metadata_note', meta)


if __name__ == '__main__': unittest.main()
