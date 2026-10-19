from html.parser import HTMLParser
import unittest
from formatting import compact_content, compact_baoyu


class ContentSignature(HTMLParser):
    def __init__(self,html):
        super().__init__(convert_charrefs=True);self.text=[];self.items=[];self.feed(html)
    def handle_data(self,s):self.text.append(s)
    def handle_starttag(self,t,a):
        v=dict(a)
        if t in {'table','thead','tbody','tr','td','th','img','a','pre','code','strong','em','sup','sub'}:
            self.items.append((t,[(k,v[k]) for k in ['src','href','colspan','rowspan'] if k in v]))
    def signature(self):return ''.join(self.text),self.items


class FormatBudgetTests(unittest.TestCase):
    def test_long_baoyu_preserves_all_content_and_contrast(self):
        s={'figures':[{'image':'images/fig-001.png'}]}
        h='<section style="font-size:16px">'+''.join('<section><h2 style="color:#fff;text-align:center;font-size:calc(16px * 1.3)">标题</h2><p>'+'中文内容。'*120+'</p></section>' for _ in range(30))+'<table><thead><tr><th colspan="2">指标</th></tr></thead><tbody><tr><td>A</td><td>1.2</td></tr></tbody></table><p><strong>Alpha</strong> <em>Beta</em></p><img src="images/fig-001.png"><a href="https://arxiv.org/abs/2609.06055">论文</a><pre>a  b\n c</pre></section>'
        self.assertGreater(len(h),19500)
        c=compact_content(h,s)
        self.assertLess(len(c),len(h)-1000)
        self.assertEqual(ContentSignature(h).signature(),ContentSignature(c).signature())
        self.assertNotIn('color:#fff',c)
        self.assertEqual(compact_content(c,s),c)
        self.assertIn('</strong> <em>',c)

    def test_small_markup_keeps_theme(self):
        h='<section style="background-color:#234d43"><h2 style="color:#fff">标题</h2></section>'
        self.assertEqual(compact_content(h,{'figures':[]}),h)
