import copy
import unittest
from wechat_fields import adapt_fields, short_digest


class FieldTests(unittest.TestCase):
    def test_augustus_summary_keeps_complete_method_sentence(self):
        first='AUGUstus把扩散式动作生成与自回归CoT理解放进同一个Transformer：训练时CoT读动作，动作不读CoT，推理只输出动作。'
        original=first+'论文报告NAVSIMv1 94.6 PDMS、NAVSIMv2 90.7 EPDMS，并在内部评测与初步实车测试中报告部署时延。'*3
        values={'title':'AUGUstus：让CoT监督动作','digest':original,'author':'Rtwotwo'}
        before=copy.deepcopy(values)
        fitted,changes=adapt_fields(values,{})
        self.assertEqual(fitted['digest'],first)
        self.assertEqual(values,before);self.assertEqual(changes[0]['before'],original)
        self.assertEqual(fitted['author'],'Rtwotwo')

    def test_in_range_unicode_digest_and_title_are_preserved(self):
        values={'title':'AUGUstus','digest':'📚'*120}
        fitted,changes=adapt_fields(values,{})
        self.assertEqual(fitted,values);self.assertEqual(changes,[])

    def test_long_unbroken_sentence_never_cuts_numeric_claim(self):
        text='一'*116+'94.6 PDMS compared with the baseline.'
        digest,reason=short_digest(text,'论文研读')
        self.assertNotIn('94',digest);self.assertLessEqual(len(digest),120)
        self.assertIn('首句过长',reason)

    def test_title_uses_existing_alternative_and_never_modifies_article(self):
        article={'title':'x'*100,'title_options':['y'*50,'可读的论文题目'],'digest':'原稿摘要'}
        before=copy.deepcopy(article)
        fitted,changes=adapt_fields({},article)
        self.assertEqual(fitted['title'],'可读的论文题目');self.assertEqual(article,before)
        self.assertEqual(changes[0]['before'],'x'*100)
        self.assertEqual(adapt_fields({'title':'x'*100},{})[0]['title'],'论文研读')

    def test_decimal_does_not_count_as_sentence_boundary(self):
        first='The experiment reports 94.6 PDMS under the stated evaluation protocol.'
        digest,_=short_digest(first+' More conditions and results are described here.'*4,'Study')
        self.assertTrue(digest.startswith(first));self.assertTrue(digest.endswith('.'))
        self.assertLessEqual(len(digest),120)


if __name__=='__main__':unittest.main()
