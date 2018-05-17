import unittest
from dragonfly.translations import TranslationDictManager


class TranslationsTest(unittest.TestCase):

    def test_hamming_distance(self):
        self.assertEqual(1, TranslationDictManager._get_hamming_distance('OR', 'ORG'))
        self.assertEqual(1, TranslationDictManager._get_hamming_distance('PWR', 'PER'))
        self.assertEqual(3, TranslationDictManager._get_hamming_distance('PER', 'PERSON'))
        self.assertEqual(1, TranslationDictManager._get_hamming_distance('GPE', 'GPED'))

    def test_guess_type(self):
        manager = TranslationDictManager('')
        self.assertEqual('ORG', manager._guess_type('O'))
        self.assertEqual('ORG', manager._guess_type('OR'))
        self.assertEqual('ORG', manager._guess_type('ORGANIZATION'))
