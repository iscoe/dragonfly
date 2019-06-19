import unittest
from dragonfly.search import InvertedIndex


class InvertedTest(unittest.TestCase):

    def test_retrieve(self):
        index = InvertedIndex()
        index.add('doc1', ['hello', 'world'], None)
        index.add('doc2', ['hello', 'nurse'], None)
        index.add('doc3', ['good', 'morning'], None)

        results = index.retrieve('hello')
        self.assertEqual(2, results['count'])
        self.assertEqual({'hello'}, results['terms'])
        self.assertEqual({'doc1', 'doc2'}, set([x['doc'] for x in results['refs']]))

    def test_retrieve_with_case(self):
        index = InvertedIndex()
        index.add('doc1', ['Hello', 'world'], None)
        results = index.retrieve('hello')
        self.assertEqual(1, results['count'])
        self.assertEqual({'hello'}, results['terms'])

    def test_retrieve_with_wildcard(self):
        index = InvertedIndex()
        index.add('doc1', ['hello', 'Maryland'], None)
        index.add('doc2', ['hello', 'mary'], None)
        index.add('doc3', ['good', 'morning'], None)

        results = index.retrieve('mary*', True)
        self.assertEqual(2, results['count'])
        self.assertEqual({'mary', 'maryland'}, results['terms'])
        self.assertEqual({'doc1', 'doc2'}, set([x['doc'] for x in results['refs']]))
