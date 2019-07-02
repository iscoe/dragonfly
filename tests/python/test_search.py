import unittest
from dragonfly.search import InvertedIndex


class InvertedIndexTest(unittest.TestCase):

    def test_add(self):
        index = InvertedIndex()
        index.add('doc1', [['hello', 'world'], ['this', 'is', 'a', 'test'], ['goodbye', 'world']], None)
        self.assertEqual(2, index._index.get('world')['count'])

    def test_add_with_transliterations(self):
        sentences = [['hello', 'world'], ['this', 'is', 'a', 'test'], ['goodbye', 'world']]
        trans = [['bonjour', 'world'], ['this', 'is', 'a', 'test'], ['goodbye', 'world']]
        index = InvertedIndex()
        index.add('doc1', sentences, trans)
        self.assertEqual('bonjour', index._index.get('hello')['refs'][0]['trans'][0])

    def test_retrieve(self):
        index = InvertedIndex()
        index.add('doc1', [['hello', 'world']], [])
        index.add('doc2', [['hello', 'nurse']], [])
        index.add('doc3', [['good', 'morning']], [])

        results = index.retrieve('hello')
        self.assertEqual(2, results['count'])
        self.assertEqual({'hello'}, results['terms'])
        self.assertEqual({'doc1', 'doc2'}, set([x['doc'] for x in results['refs']]))
        self.assertIsNone(results['refs'][0]['trans'])

    def test_retrieve_with_case(self):
        index = InvertedIndex()
        index.add('doc1', [['Hello', 'world']], None)
        results = index.retrieve('hello')
        self.assertEqual(1, results['count'])
        self.assertEqual({'hello'}, results['terms'])

    def test_retrieve_with_wildcard(self):
        index = InvertedIndex()
        index.add('doc1', [['hello', 'Maryland']], None)
        index.add('doc2', [['hello', 'mary']], None)
        index.add('doc3', [['good', 'morning']], None)

        results = index.retrieve('mary*', True)
        self.assertEqual(2, results['count'])
        self.assertEqual({'mary', 'maryland'}, results['terms'])
        self.assertEqual({'doc1', 'doc2'}, set([x['doc'] for x in results['refs']]))
