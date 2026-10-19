import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests import pdf_fixtures as pdf
from sources import guess_title, extract_pdf, refresh_identity
from server import Studio
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from sources import caption_box
from covers import generate_cover
from wechat_review import prepare, approve, is_approved, CHECKS
from PIL import Image
from formatting import compact_baoyu, current_baoyu, layout_markdown
from sources import write_json
from exporting import markdown, article_html


class IdentityLibraryTests(unittest.TestCase):
    def test_rotated_watermark_is_not_title_and_local_id_enriches(self):
        with tempfile.TemporaryDirectory() as tmp, pdf.open() as doc:
            page=doc.new_page()
            page.insert_text((30,650),'arXiv:2609.29166v1 [cs.RO] 24 Sep 2026',fontsize=22,rotate=90)
            page.insert_text((60,80),'A Real Research Paper',fontsize=18)
            self.assertEqual(guess_title(page,{},'paper.pdf'),'A Real Research Paper')
            source=extract_pdf(doc.tobytes(),tmp)
            source['paper_info']={'title':'My manually checked title'}
            with patch('sources.arxiv_metadata',return_value={'title':'Official Research Title','authors':['Author'], 'arxiv_id':'2609.29166v1','url':'https://arxiv.org/abs/2609.29166v1'}) as fetch:
                source=refresh_identity(tmp,source)
            fetch.assert_called_once_with('2609.29166v1')
            self.assertEqual(source['title'],'Official Research Title')
            self.assertEqual(source['paper_info']['title'],'My manually checked title')

    def test_library_reversible_and_persistent_without_touching_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio=Studio(tmp)
            try:
                ident=studio.create('Original title')
                folder=studio.folder(ident);source=extract_pdf(fixture_pdf(),folder)
                before=(folder/'source.pdf').read_bytes()
                studio.library_update(ident,{'display_name':'Readable alias','pinned':True,'trashed':True})
                self.assertEqual(json.loads((folder/'status.json').read_text())['display_name'],'Readable alias')
                studio.library_update(ident,{'trashed':False})
                self.assertEqual((folder/'source.pdf').read_bytes(),before)
                self.assertEqual(studio.load(ident)['title'],source['title'])
                studio.update(ident,status='running')
                with self.assertRaises(ValueError):studio.library_update(ident,{'trashed':True})
            finally:studio.close()


class CropCoverTests(unittest.TestCase):
    def test_caption_width_does_not_force_white_margins_or_unrelated_panel(self):
        with pdf.open() as doc:
            p=doc.new_page(width=600,height=800)
            p.draw_rect((40,60,260,140),color=(0,0,0))
            p.draw_rect((170,320,420,470),color=(0,0,0))
            caption=(40,490,560,520,'Figure 1. Wide caption',0,0)
            box,status=caption_box(p,caption,[caption])
            self.assertEqual(status,'figure_detected')
            self.assertGreater(box[0],150);self.assertGreater(box[1],300)
            self.assertLess(box[2],440);self.assertLess(box[3],490)

    def test_cover_variants_work_in_exact_review_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);s=extract_pdf(fixture_pdf(),folder);a=fixture_article(s)
            covers=generate_cover(folder,s,a,{'title':'理解世界，再做决策','theme':'blue'})
            sizes=[]
            for f in covers:
                with Image.open(folder/f['image']) as image:sizes.append(image.size)
            self.assertEqual(sizes,[(1200,510),(800,800)])
            options={'title':'论文解读','digest':'研究摘要','cover_id':covers[0]['id']}
            p=prepare(folder,a,s,options,{'appid':'test'})
            approve(folder,p,{k:True for k in CHECKS})
            self.assertTrue(is_approved(folder,p))
            options['cover_id']=covers[1]['id']
            self.assertFalse(is_approved(folder,prepare(folder,a,s,options,{'appid':'test'})))


class FormattingTests(unittest.TestCase):
    def test_baoyu_payload_preserves_text_images_and_blocks_stale_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);s=extract_pdf(fixture_pdf(),folder);a=fixture_article(s)
            name=s['figures'][0]['image'];fid=s['figures'][0]['id']
            html='<html><head><title>Not body</title></head><body><section><h2>Method</h2><p style="color:#123;position:fixed" onclick="bad()">Evidence</p><img src="'+name+'" data-local-path="private"><script>bad()</script></section></body></html>'
            content=compact_baoyu(html,s)
            self.assertIn('Evidence',content);self.assertIn('src="'+name+'"',content)
            for unwanted in ['script','onclick','private','position','Not body']:self.assertNotIn(unwanted,content)
            options={'title':a['title'],'digest':a['digest'],'cover_id':fid,'theme':'baoyu'}
            write_json(folder/'baoyu-layout.json',{'markdown':layout_markdown(a,s,options),'content':content})
            p=prepare(folder,a,s,options,{'appid':'test'})
            self.assertEqual(p['content'],content)
            approve(folder,p,{k:True for k in CHECKS})
            a['lead']='An edited introduction'
            with self.assertRaisesRegex(ValueError,'重新应用'):prepare(folder,a,s,options,{'appid':'test'})

    def test_figures_render_between_paragraphs_in_all_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=extract_pdf(fixture_pdf(),tmp);a=fixture_article(s)
            sec=a['sections'][0];sec['paragraphs']=[{'text':'Before figure','pages':[1]},{'text':'After figure','pages':[1]}]
            sec['figures']=[{'id':s['figures'][0]['id'],'caption':'Matched figure','pages':[1],'after_paragraph':1}]
            from wechat_review import render_content
            for value in [markdown(a,s),article_html(a,s,tmp),render_content(a,s,{'theme':'ink','digest':a['digest']})]:
                self.assertLess(value.index('Before figure'),value.index('Matched figure'))
                self.assertLess(value.index('Matched figure'),value.index('After figure'))
