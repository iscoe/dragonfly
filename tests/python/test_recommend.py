import unittest
from dragonfly.recommend import Recommender


class RecommenderTest(unittest.TestCase):
    def test_prepare_words(self):
        test_string = 'Test one  two\t three\r\nfour'
        self.assertEqual(['test', 'one', 'two', 'three', 'four'], Recommender._prepare_words(test_string))
