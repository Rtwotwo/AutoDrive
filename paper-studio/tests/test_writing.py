import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sources import extract_pdf
from tests.test_sources import fixture_pdf
from writing import validate_article, source_chunks, provider_config, generate_article, prompt_pack
from exporting import export_bundle, article_html


def fixture_article(manifest):
    return {'title': '测试夹具：研究方法解读', 'digest': '仅用于软件测试。', 'lead': '这是测试夹具，不是论文结果。',
            'sections': [{'kind': kind, 'heading': kind, 'paragraphs': [{'text': '测试夹具正文：说明方法、条件与适用边界。', 'pages': [1]}],
                          'figures': [{'id': manifest['figures'][0]['id'], 'caption': '测试图', 'explanation': '人工测试流程图。'}] if kind == 'method' else []}
                         for kind in ['motivation', 'contributions', 'method', 'experiments', 'limitations', 'outlook']],
            'claims': [{'claim': '夹具中的成功率是 83.2。', 'page': 1, 'quote': 'The reported success rate is 83.2 percent.'}],
            'takeaways': ['测试结果不可当作研究结论。']}


class WritingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = Path(self.tmp.name)
        self.m = extract_pdf(fixture_pdf(), self.folder)
        self.a = fixture_article(self.m)

    def tearDown(self): self.tmp.cleanup()

    def test_quote_matching_and_bad_reference(self):
        audit = validate_article(self.a, self.m)
        self.assertTrue(audit['evidence'][0]['quote_found'])
        self.a['claims'][0]['quote'] = 'Invented result not in the source document.'
        self.assertFalse(validate_article(self.a, self.m)['evidence'][0]['quote_found'])
        self.a['sections'][2]['figures'][0]['id'] = 'missing'
        with self.assertRaises(ValueError): validate_article(self.a, self.m)

    def test_export_and_escape(self):
        self.a['title'] = '<script>alert(1)</script>'
        self.a['sections'][0]['paragraphs'][0]['text'] = '<img onerror="alert(1)">'
        fragment = article_html(self.a, self.m, self.folder)
        self.assertNotIn('<script', fragment)
        self.assertIn('&lt;img', fragment)
        with zipfile.ZipFile(io.BytesIO(export_bundle(self.a, self.m, self.folder))) as z:
            self.assertIn('images/fig-001.png', z.namelist())
            self.assertIn('source-dossier.md', z.namelist())
            self.assertNotIn('source.pdf', z.namelist())
            self.assertNotIn('api_key', z.read('article.json').decode())

    def test_pipeline_with_mock_provider(self):
        with patch('writing.chat_json', side_effect=[{'facts': []}, self.a, self.a]) as mocked:
            article, notes, audit = generate_article(self.m, self.folder, {'base_url': 'http://localhost:11434/v1', 'model': 'fixture'})
            self.assertEqual(mocked.call_count, 3)
            self.assertEqual(article['generation']['model'], 'fixture')
            self.assertTrue(audit['evidence'][0]['quote_found'])

    def test_prompt_all_pages_and_endpoint(self):
        pack = prompt_pack(self.m, {})
        self.assertIn('[PDF page 1]', pack)
        self.assertIn('83.2', pack)
        self.assertIn('fig-001', pack)
        with self.assertRaises(ValueError): provider_config({'base_url': 'http://example.com', 'model': 'x', 'api_key': 'secret'})
        self.assertEqual(provider_config({'base_url': 'http://localhost:11434/v1', 'model': 'x'})['url'], 'http://localhost:11434/v1/chat/completions')

    def test_endpoint_key_pairing(self):
        with patch.dict(os.environ, {'PAPER_STUDIO_API_BASE': 'https://provider-a.example/v1', 'PAPER_STUDIO_API_KEY': 'synthetic-secret'}):
            self.assertEqual(provider_config({'model': 'fixture'})['key'], 'synthetic-secret')
            with self.assertRaises(ValueError):
                provider_config({'base_url': 'https://provider-b.example/v1', 'model': 'fixture'})
            self.assertEqual(provider_config({'base_url': 'http://localhost:11434/v1', 'model': 'fixture'})['key'], '')

    def test_page_shape_and_numeric_review(self):
        self.a['sections'][0]['paragraphs'][0]['pages'] = 1
        with self.assertRaises(ValueError): validate_article(self.a, self.m)
        self.a['sections'][0]['paragraphs'][0]['pages'] = [1]
        self.a['sections'][0]['paragraphs'][0]['text'] = 'Unsupported 99.9 percent claim.'
        self.assertTrue(any('含数字' in i['message'] for i in validate_article(self.a, self.m)['issues']))

    def test_cancel_and_invalid_schema(self):
        with self.assertRaises(ValueError): generate_article(self.m, self.folder, {'base_url': 'http://localhost:11434/v1', 'model': 'x'}, cancelled=lambda: True)
        with self.assertRaises(ValueError): validate_article({'title': 'x', 'sections': 'bad'}, self.m)
        self.assertEqual(len(source_chunks(self.m)), 1)


if __name__ == '__main__': unittest.main()
