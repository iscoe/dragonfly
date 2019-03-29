import unittest
import os
from dragonfly.data import FileLister


class FileListerTest(unittest.TestCase):
    @staticmethod
    def get_directory():
        return os.path.join(os.path.dirname(__file__), 'data', 'lister')

    def test_init_with_bad_extension(self):
        directory = os.path.join(self.get_directory(), 'not_exist')
        with self.assertRaises(ValueError) as context:
            FileLister(directory, 'txt')

    def test_init_with_bad_directory(self):
        with self.assertRaises(ValueError) as context:
            FileLister(self.get_directory(), 'notxt')

    def test_size(self):
        lister = FileLister(self.get_directory(), 'txt')
        self.assertEqual(3, lister.size())

    def test_get_index_from_filename(self):
        lister = FileLister(self.get_directory(), 'txt')
        self.assertEqual(0, lister.get_index_from_filename('file1.txt'))
        self.assertEqual(2, lister.get_index_from_filename('file3.txt'))

    def test_get_filename(self):
        lister = FileLister(self.get_directory(), 'txt')
        self.assertEqual('file1.txt', os.path.basename(lister.get_filename(0)))
        self.assertEqual('file2.txt', os.path.basename(lister.get_filename(1)))
