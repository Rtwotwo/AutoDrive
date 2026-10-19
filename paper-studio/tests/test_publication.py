import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publication import clean_article, clean_public_text, paper_details
from exporting import article_html, markdown
from writing import editorial_instruction, validate_article
from sources import extract_pdf, caption_box, CAPTION, repair_crops, write_json
from tests import pdf_fixtures as pdf
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.source = extract_pdf(fixture_pdf(), self.folder)
        self.article = fixture_article(self.source)

    def tearDown(self): self.temp.cleanup()

    def test_public_text_removes_only_schema_tail_and_keeps_internal_pages(self):
        self.article['sections'][0]['paragraphs'][0].update(text='研究内容。pages: [1, 2]', pages=[1])
        cleaned = clean_article(self.article)
        self.assertEqual(cleaned['sections'][0]['paragraphs'][0]['text'], '研究内容。')
        self.assertEqual(cleaned['sections'][0]['paragraphs'][0]['pages'], [1])
        self.assertEqual(clean_public_text('向量取值为 [1, 2]。'), '向量取值为 [1, 2]。')
        for content in (markdown(self.article, self.source), article_html(self.article, self.source, self.folder)):
            self.assertNotIn('pages:', content)
            self.assertNotIn('原文 p.', content)
            self.assertNotIn('原文第 1 页', content)

    def test_metadata_precedes_prose_and_unknown_links_are_not_invented(self):
        self.source['paper_info'] = {'title': 'Original English Title', 'authors': ['Researcher A'],
            'affiliations': ['Research Lab'], 'paper_url': 'https://arxiv.org/abs/1234.56789',
            'project_url': 'https://example.org/project', 'code_url': 'https://github.com/example/project'}
        html = article_html(self.article, self.source, self.folder)
        self.assertLess(html.index('Original English Title'), html.index(self.article['lead']))
        for text in ('Researcher A', 'Research Lab', 'https://example.org/project', 'https://github.com/example/project'):
            self.assertIn(text, html)
        self.source.pop('paper_info')
        self.article['paper'] = {'code_url': 'https://github.com/invented/repository'}
        self.assertEqual(paper_details(self.article, self.source)['code_url'], '')
        self.assertIn('未核实', article_html(self.article, self.source, self.folder))

    def test_result_tables_are_escaped_and_validated(self):
        self.article['sections'][0]['tables'] = [{'title': 'Fixture summary', 'columns': ['Method', 'Success ↑'],
            'rows': [['A <script>', '83.2']], 'note': 'Synthetic fixed split', 'source_label': 'Table 1 (selected)', 'pages': [1]}]
        validate_article(self.article, self.source)
        html = article_html(self.article, self.source, self.folder)
        self.assertIn('<table ', html); self.assertIn('A &lt;script&gt;', html)
        self.assertIn('Synthetic fixed split', html)
        self.assertIn('| Method | Success ↑ |', markdown(self.article, self.source))
        self.article['sections'][0]['tables'][0]['rows'] = [['missing column']]
        with self.assertRaises(ValueError): validate_article(self.article, self.source)

    def test_reusable_skill_is_part_of_every_generation_prompt(self):
        instruction = editorial_instruction(self.source, {}, self.source['figures'])
        self.assertIn('论文公众号写作规范', instruction)
        self.assertIn('完整作者名单', instruction)
        self.assertIn('严禁出现', instruction)
        self.assertIn('精选结果摘要', instruction)

    def test_table_direction_and_uncertain_fallback(self):
        with pdf.open() as doc:
            page = doc.new_page(width=400, height=600)
            caption = (30, 220, 370, 240, 'Table 1. Test results', 0, 0)
            above = caption_box(page, caption, [caption], [(40, 80, 360, 210)])
            below = caption_box(page, caption, [caption], [(40, 250, 360, 410)])
            self.assertEqual(above[1], 'table_detected'); self.assertLess(above[0][1], 80)
            self.assertGreater(below[0][3], 410)
            for boxes in ([], [(40, 80, 360, 210), (40, 250, 360, 410)]):
                box, status = caption_box(page, caption, [caption], boxes)
                self.assertEqual(status, 'page_fallback'); self.assertEqual(box, list(page.rect))
        self.assertIsNone(CAPTION.match('Fig. 9 shows a turn in the intersection.'))
        self.assertIsNotNone(CAPTION.match('Figure 9. Intersection example'))

    def test_crop_repair_keeps_reviewed_image_and_recovers_links(self):
        f = self.source['figures'][0]
        f['reviewed'] = True
        before = (self.folder / f['image']).read_bytes()
        pdf.add_uri(self.folder / 'source.pdf', 'https://example.org/project')
        repair_crops(self.folder, self.source)
        self.assertEqual(before, (self.folder / f['image']).read_bytes())
        self.assertIn('https://example.org/project', self.source['resource_links'])

    def test_saved_article_is_clean_and_metadata_survives_restart(self):
        from server import Studio
        studio = Studio(self.folder / 'jobs')
        try:
            job = studio.create('Fixture')
            source = extract_pdf(fixture_pdf(), studio.folder(job))
            source['paper_info'] = {'title':'Verified Title', 'affiliations':['Lab']}
            write_json(studio.folder(job) / 'source.json', source)
            article = fixture_article(source)
            article['sections'][0]['paragraphs'][0]['text'] += ' pages: [1]'
            studio.save_article(job, article)
            self.assertNotIn('pages:', studio.load(job, 'article.json')['sections'][0]['paragraphs'][0]['text'])
            self.assertEqual(studio.load(job)['paper_info']['title'], 'Verified Title')
        finally: studio.close()


if __name__ == '__main__': unittest.main()
