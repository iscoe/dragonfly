import unittest
import os
import shutil
import tempfile
from dragonfly.components import StopWords


def get_path(*args):
    return os.path.join(os.path.dirname(__file__), *args)


class StopWordsTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_build(self):
        stop_words = StopWords(get_path('data', 'stop_words'), self.test_dir, 10)
        self.assertIn('the', stop_words.words)

    def test_save_and_load(self):
        stop_words = StopWords(get_path('data', 'stop_words'), self.test_dir, 10)
        stop_words2 = StopWords(get_path('data', 'stop_words'), self.test_dir)
        self.assertEqual(10, len(stop_words2.words))
        self.assertIn('.', stop_words2.words)
