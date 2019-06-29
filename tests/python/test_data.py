import unittest
import os
from dragonfly.data import Document, FileLister, InputReader


def get_path(*args):
    return os.path.join(os.path.dirname(__file__), *args)


class FileListerTest(unittest.TestCase):
    @staticmethod
    def get_directory():
        return get_path('data', 'lister')

    def test_init_with_bad_directory(self):
        directory = os.path.join(self.get_directory(), 'not_exist')
        with self.assertRaises(ValueError) as context:
            FileLister(directory, 'txt')

    def test_init_with_bad_extension(self):
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


class InputReaderTest(unittest.TestCase):
    def test_basic_file(self):
        filename = get_path('data', 'input_basic.tsv')
        reader = InputReader(filename)
        self.assertEqual(2, len(reader.sentences))
        self.assertEqual(0, reader.sentences[0].index)
        self.assertEqual(1, reader.sentences[1].index)
        self.assertEqual('TOKEN', reader.sentences[0].rows[0].label)
        self.assertEqual('acantilado', reader.sentences[0].rows[0].strings[2])
        self.assertEqual('TRANSLATION', reader.sentences[0].rows[1].label)
        self.assertEqual('the cliff', reader.sentences[0].rows[1].strings[2])
        self.assertEqual(0, reader.sentences[1].rows[0].index)
        self.assertEqual(1, reader.sentences[1].rows[1].index)
        self.assertEqual(True, reader.terminal_blank_line)

    def test_with_no_final_empty_line(self):
        filename = get_path('data', 'input_with_no_last_line.tsv')
        reader = InputReader(filename)
        self.assertEqual(1, len(reader.sentences))
        self.assertEqual(False, reader.terminal_blank_line)

    def test_with_conll(self):
        filename = get_path('data', 'input_conll.tsv')
        reader = InputReader(filename)
        self.assertEqual(3, len(reader.sentences))


class DocumentTest(unittest.TestCase):
    def test_applying_annotations(self):
        original_filename = get_path('data', 'input_no_annotations.tsv')
        annotations_filename = get_path('data', 'input_with_annotations.tsv')
        document = Document(original_filename, InputReader(original_filename).sentences, False)
        annotations = InputReader(annotations_filename).sentences
        document.attach_annotations(annotations)

        self.assertEqual('B-GPE', document.sentences[0].rows[0].annotations[5])

    def test_applying_annotations_with_wrong_length(self):
        original_filename = get_path('data', 'input_no_annotations.tsv')
        annotations_filename = get_path('data', 'input_with_wrong_annotations_length.tsv')
        document = Document(original_filename, InputReader(original_filename).sentences, False)
        annotations = InputReader(annotations_filename).sentences
        with self.assertRaises(ValueError) as context:
            document.attach_annotations(annotations)

    def test_applying_annotations_with_wrong_words(self):
        original_filename = get_path('data', 'input_no_annotations.tsv')
        annotations_filename = get_path('data', 'input_with_wrong_annotations.tsv')
        document = Document(original_filename, InputReader(original_filename).sentences, False)
        annotations = InputReader(annotations_filename).sentences
        with self.assertRaises(ValueError) as context:
            document.attach_annotations(annotations)
