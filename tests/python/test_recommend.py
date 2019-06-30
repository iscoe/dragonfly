import unittest
import collections
import shutil
import tempfile
from dragonfly.recommend import Recommender, TaggedTokenFrequencies


class RecommenderTest(unittest.TestCase):
    def test_prepare_words(self):
        test_string = 'Test one  two\t three\r\nfour'
        self.assertEqual(['test', 'one', 'two', 'three', 'four'], Recommender._prepare_words(test_string))


class TaggedTokenFrequenciesTest(unittest.TestCase):
    # 5 sentence document with 6 unique tags
    DATA1 = {'filename': 'IL3_NW_020005_20150728_G004007SS.conll.txt', 'tokens': [{'token': 'ميۇنخېندىكى', 'tag': 'O'}, {'token': 'ئۇيغۇرلار', 'tag': 'O'}, {'token': 'خىتاي', 'tag': 'B-GPE'}, {'token': 'كونسۇلخانىسى', 'tag': 'O'}, {'token': 'ئالدىدا', 'tag': 'O'}, {'token': 'يەكەن', 'tag': 'B-GPE'}, {'token': 'ۋەقەسىنىڭ', 'tag': 'O'}, {'token': 'بىر', 'tag': 'O'}, {'token': 'يىللىقى', 'tag': 'O'}, {'token': 'مۇناسىۋىتى', 'tag': 'O'}, {'token': 'بىلەن', 'tag': 'O'}, {'token': 'نامايىش', 'tag': 'O'}, {'token': 'قىلدى', 'tag': 'O'}, {}, {'token': 'د', 'tag': 'O'}, {'token': 'ئۇ', 'tag': 'O'}, {'token': 'ق', 'tag': 'O'}, {'token': 'نىڭ', 'tag': 'O'}, {'token': 'چاقىرىقى', 'tag': 'O'}, {'token': '،', 'tag': 'O'}, {'token': 'ياۋرۇپا', 'tag': 'B-LOC'}, {'token': 'شەرقىي', 'tag': 'B-GPE'}, {'token': 'تۈركىستان', 'tag': 'I-GPE'}, {'token': 'بىرلىكى', 'tag': 'O'}, {'token': 'تەشكىلاتىنىڭ', 'tag': 'O'}, {'token': 'ئورۇنلاشتۇرۇشى', 'tag': 'O'}, {'token': 'بىلەن', 'tag': 'O'}, {'token': '28', 'tag': 'O'}, {'token': '-', 'tag': 'O'}, {'token': 'ئىيۇل', 'tag': 'O'}, {'token': 'كۈنى', 'tag': 'O'}, {'token': 'گېرمانىيىنىڭ', 'tag': 'O'}, {'token': 'ميۇنخېن', 'tag': 'B-GPE'}, {'token': 'شەھىرىدىكى', 'tag': 'O'}, {'token': 'خىتاي', 'tag': 'B-GPE'}, {'token': 'كونسۇلخانىسى', 'tag': 'O'}, {'token': 'ئالدىدا', 'tag': 'O'}, {'token': 'يەكەن', 'tag': 'B-GPE'}, {'token': 'ۋەقەسىنىڭ', 'tag': 'O'}, {'token': 'بىر', 'tag': 'O'}, {'token': 'يىللىقى', 'tag': 'O'}, {'token': 'مۇناسىۋىتى', 'tag': 'O'}, {'token': 'بىلەن', 'tag': 'O'}, {'token': 'نامايىش', 'tag': 'O'}, {'token': 'ئېلىپ', 'tag': 'O'}, {'token': 'بېرىلدى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}, {}, {'token': 'بۇ', 'tag': 'O'}, {'token': 'نامايىشقا', 'tag': 'O'}, {'token': 'ميۇنخېن', 'tag': 'B-GPE'}, {'token': 'شەھىرى', 'tag': 'O'}, {'token': 'ۋە', 'tag': 'O'}, {'token': 'ئەتراپ', 'tag': 'O'}, {'token': 'رايونلاردىكى', 'tag': 'O'}, {'token': 'ئۇيغۇر', 'tag': 'O'}, {'token': 'جامائىتىدىن', 'tag': 'O'}, {'token': 'باشقا', 'tag': 'O'}, {'token': '،', 'tag': 'O'}, {'token': 'تۈرك', 'tag': 'O'}, {'token': 'تەشكىلاتلىرى', 'tag': 'O'}, {'token': 'ۋەكىللىرى', 'tag': 'O'}, {'token': 'ھەمدە', 'tag': 'O'}, {'token': 'بىر', 'tag': 'O'}, {'token': 'قىسىم', 'tag': 'O'}, {'token': 'كىشىلىك', 'tag': 'O'}, {'token': 'ھوقۇق', 'tag': 'O'}, {'token': 'تەشكىلاتلىرىنىڭ', 'tag': 'O'}, {'token': 'ئەزالىرىمۇ', 'tag': 'O'}, {'token': 'قاتناشتى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}, {}, {'token': 'نامايىش', 'tag': 'O'}, {'token': 'سائەت', 'tag': 'O'}, {'token': '14:00', 'tag': 'O'}, {'token': 'دىن', 'tag': 'O'}, {'token': '16:00', 'tag': 'O'}, {'token': 'گىچە', 'tag': 'O'}, {'token': 'ئىككى', 'tag': 'O'}, {'token': 'سائەت', 'tag': 'O'}, {'token': 'داۋاملاشتى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}, {}, {'token': 'نامايىشچىلار', 'tag': 'O'}, {'token': 'يەكەن', 'tag': 'B-GPE'}, {'token': 'ۋەقەسىدە', 'tag': 'O'}, {'token': 'قەتلى', 'tag': 'O'}, {'token': 'قىلىنغان', 'tag': 'O'}, {'token': 'شېھىتلارنى', 'tag': 'O'}, {'token': 'ئەسلەپ', 'tag': 'O'}, {'token': '،', 'tag': 'O'}, {'token': 'خىتاينىڭ', 'tag': 'O'}, {'token': 'قانلىق', 'tag': 'O'}, {'token': 'قىرغىنچىلىقىنى', 'tag': 'O'}, {'token': 'ئەيىبلىدى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}]}
    # same doc as above, removed one instance of a tag that appeared 3 times and added new tag
    # removes a sentence from set of tagged sentences
    DATA2 = {'filename': 'IL3_NW_020005_20150728_G004007SS.conll.txt', 'tokens': [{'token': 'ميۇنخېندىكى', 'tag': 'O'}, {'token': 'ئۇيغۇرلار', 'tag': 'O'}, {'token': 'خىتاي', 'tag': 'B-GPE'}, {'token': 'كونسۇلخانىسى', 'tag': 'O'}, {'token': 'ئالدىدا', 'tag': 'O'}, {'token': 'يەكەن', 'tag': 'B-GPE'}, {'token': 'ۋەقەسىنىڭ', 'tag': 'O'}, {'token': 'بىر', 'tag': 'O'}, {'token': 'يىللىقى', 'tag': 'O'}, {'token': 'مۇناسىۋىتى', 'tag': 'O'}, {'token': 'بىلەن', 'tag': 'O'}, {'token': 'نامايىش', 'tag': 'O'}, {'token': 'قىلدى', 'tag': 'O'}, {}, {'token': 'د', 'tag': 'O'}, {'token': 'ئۇ', 'tag': 'O'}, {'token': 'ق', 'tag': 'O'}, {'token': 'نىڭ', 'tag': 'O'}, {'token': 'چاقىرىقى', 'tag': 'O'}, {'token': '،', 'tag': 'O'}, {'token': 'ياۋرۇپا', 'tag': 'B-LOC'}, {'token': 'شەرقىي', 'tag': 'B-GPE'}, {'token': 'تۈركىستان', 'tag': 'I-GPE'}, {'token': 'بىرلىكى', 'tag': 'O'}, {'token': 'تەشكىلاتىنىڭ', 'tag': 'O'}, {'token': 'ئورۇنلاشتۇرۇشى', 'tag': 'O'}, {'token': 'بىلەن', 'tag': 'O'}, {'token': '28', 'tag': 'O'}, {'token': '-', 'tag': 'O'}, {'token': 'ئىيۇل', 'tag': 'O'}, {'token': 'كۈنى', 'tag': 'O'}, {'token': 'گېرمانىيىنىڭ', 'tag': 'O'}, {'token': 'ميۇنخېن', 'tag': 'B-GPE'}, {'token': 'شەھىرىدىكى', 'tag': 'O'}, {'token': 'خىتاي', 'tag': 'B-GPE'}, {'token': 'كونسۇلخانىسى', 'tag': 'O'}, {'token': 'ئالدىدا', 'tag': 'O'}, {'token': 'يەكەن', 'tag': 'B-GPE'}, {'token': 'ۋەقەسىنىڭ', 'tag': 'O'}, {'token': 'بىر', 'tag': 'O'}, {'token': 'يىللىقى', 'tag': 'O'}, {'token': 'مۇناسىۋىتى', 'tag': 'O'}, {'token': 'بىلەن', 'tag': 'O'}, {'token': 'نامايىش', 'tag': 'O'}, {'token': 'ئېلىپ', 'tag': 'O'}, {'token': 'بېرىلدى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}, {}, {'token': 'بۇ', 'tag': 'O'}, {'token': 'نامايىشقا', 'tag': 'O'}, {'token': 'ميۇنخېن', 'tag': 'B-GPE'}, {'token': 'شەھىرى', 'tag': 'O'}, {'token': 'ۋە', 'tag': 'O'}, {'token': 'ئەتراپ', 'tag': 'O'}, {'token': 'رايونلاردىكى', 'tag': 'O'}, {'token': 'ئۇيغۇر', 'tag': 'B-PER'}, {'token': 'جامائىتىدىن', 'tag': 'O'}, {'token': 'باشقا', 'tag': 'O'}, {'token': '،', 'tag': 'O'}, {'token': 'تۈرك', 'tag': 'O'}, {'token': 'تەشكىلاتلىرى', 'tag': 'O'}, {'token': 'ۋەكىللىرى', 'tag': 'O'}, {'token': 'ھەمدە', 'tag': 'O'}, {'token': 'بىر', 'tag': 'O'}, {'token': 'قىسىم', 'tag': 'O'}, {'token': 'كىشىلىك', 'tag': 'O'}, {'token': 'ھوقۇق', 'tag': 'O'}, {'token': 'تەشكىلاتلىرىنىڭ', 'tag': 'O'}, {'token': 'ئەزالىرىمۇ', 'tag': 'O'}, {'token': 'قاتناشتى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}, {}, {'token': 'نامايىش', 'tag': 'O'}, {'token': 'سائەت', 'tag': 'O'}, {'token': '14:00', 'tag': 'O'}, {'token': 'دىن', 'tag': 'O'}, {'token': '16:00', 'tag': 'O'}, {'token': 'گىچە', 'tag': 'O'}, {'token': 'ئىككى', 'tag': 'O'}, {'token': 'سائەت', 'tag': 'O'}, {'token': 'داۋاملاشتى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}, {}, {'token': 'نامايىشچىلار', 'tag': 'O'}, {'token': 'يەكەن', 'tag': 'O'}, {'token': 'ۋەقەسىدە', 'tag': 'O'}, {'token': 'قەتلى', 'tag': 'O'}, {'token': 'قىلىنغان', 'tag': 'O'}, {'token': 'شېھىتلارنى', 'tag': 'O'}, {'token': 'ئەسلەپ', 'tag': 'O'}, {'token': '،', 'tag': 'O'}, {'token': 'خىتاينىڭ', 'tag': 'O'}, {'token': 'قانلىق', 'tag': 'O'}, {'token': 'قىرغىنچىلىقىنى', 'tag': 'O'}, {'token': 'ئەيىبلىدى', 'tag': 'O'}, {'token': '.', 'tag': 'O'}]}
    # one sentence document with a new tagged token
    DATA3 = {'filename': 'IL3_SN_000370_20160127_G0T0004NM.conll.txt', 'tokens': [{'token': 'خىتاينىڭ', 'tag': 'B-GPE'}, {'token': 'چاغان', 'tag': 'O'}, {'token': 'بايرىمىنى', 'tag': 'O'}, {'token': 'ئۇيغۇرلارنى', 'tag': 'O'}, {'token': 'ئۇسۇلغا', 'tag': 'O'}, {'token': 'سېلىش', 'tag': 'O'}, {'token': 'بىلەن', 'tag': 'O'}, {'token': 'تەبرىكلىمەكتە', 'tag': 'O'}, {'token': '.', 'tag': 'O'}, {'token': 'شەرقىي', 'tag': 'B-GPE'}, {'token': 'تۈركىستان', 'tag': 'I-GPE'}, {'token': 'تەشۋىقات', 'tag': 'O'}, {'token': 'مەركىزى', 'tag': 'O'}, {'token': 'https://t.co/PRzzEUIwsp', 'tag': 'O'}]}

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_first_update(self):
        freq = TaggedTokenFrequencies(self.test_dir)
        corpus_data = freq.update(self.DATA1)
        self.assertEqual(6, len(corpus_data.tagged_counts))
        tags = collections.Counter({'يەكەن': 3, 'خىتاي': 2, 'ميۇنخېن': 2, 'ياۋرۇپا': 1, 'شەرقىي': 1, 'تۈركىستان': 1})
        self.assertEqual(tags, corpus_data.tagged_counts)
        self.assertEqual(3, corpus_data.counts['.'])

    def test_update_on_same_doc(self):
        freq = TaggedTokenFrequencies(self.test_dir)
        freq.update(self.DATA1)
        corpus_data = freq.update(self.DATA2)
        self.assertEqual(7, len(corpus_data.tagged_counts))
        tags = collections.Counter({'خىتاي': 2, 'يەكەن': 2, 'ميۇنخېن': 2, 'ياۋرۇپا': 1, 'شەرقىي': 1, 'تۈركىستان': 1, 'ئۇيغۇر': 1})
        self.assertEqual(tags, corpus_data.tagged_counts)
        self.assertEqual(2, corpus_data.counts['.'])

    def test_update_on_new_doc(self):
        freq = TaggedTokenFrequencies(self.test_dir)
        freq.update(self.DATA1)
        corpus_data = freq.update(self.DATA3)
        self.assertEqual(7, len(corpus_data.tagged_counts))
        self.assertEqual(4, corpus_data.counts['.'])

    def test_update_on_new_doc_with_no_tags(self):
        freq = TaggedTokenFrequencies(self.test_dir)
        freq.update(self.DATA1)
        corpus_data = freq.update({'filename': 'test', 'tokens': [{'token': 'a', 'tag': 'O'}, {'token': '.', 'tag': 'O'}]})
        self.assertEqual(6, len(corpus_data.tagged_counts))
        self.assertEqual(3, corpus_data.counts['.'])
