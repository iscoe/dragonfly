import unittest
import os
from dragonfly.data import InputReader, Document


def get_filename(filename):
    return os.path.join(os.path.dirname(__file__), filename)


class InputReaderTest(unittest.TestCase):

    def test_basic_file(self):
        filename = get_filename('data/input_basic.tsv')
        reader = InputReader(filename)
        self.assertEqual(2, len(reader.sentences))
        self.assertEqual(0, reader.sentences[0].id)
        self.assertEqual(1, reader.sentences[1].id)
        self.assertEqual('TOKEN', reader.sentences[0].columns[0].label)
        self.assertEqual('acantilado', reader.sentences[0].columns[0].strings[2])
        self.assertEqual('TRANSLATION', reader.sentences[0].columns[1].label)
        self.assertEqual('the cliff', reader.sentences[0].columns[1].strings[2])
        self.assertEqual(0, reader.sentences[1].columns[0].id)
        self.assertEqual(1, reader.sentences[1].columns[1].id)
        self.assertEqual(True, reader.terminal_blank_line)

    def test_with_no_final_empty_line(self):
        filename = get_filename('data/input_with_no_last_line.tsv')
        reader = InputReader(filename)
        self.assertEqual(1, len(reader.sentences))
        self.assertEqual(False, reader.terminal_blank_line)

    def test_with_conll(self):
        filename = get_filename('data/input_conll.tsv')
        reader = InputReader(filename)
        self.assertEqual(3, len(reader.sentences))


class DocumentTest(unittest.TestCase):
    def test_applying_annotations(self):
        original_filename = get_filename('data/input_no_annotations.tsv')
        annotations_filename = get_filename('data/input_with_annotations.tsv')
        document = Document(original_filename, InputReader(original_filename).sentences)
        annotations = InputReader(annotations_filename).sentences
        document.attach(annotations)

        self.assertEqual('B-GPE', document.sentences[0].columns[0].annotations[5])

    def test_applying_annotations_with_wrong_length(self):
        original_filename = get_filename('data/input_no_annotations.tsv')
        annotations_filename = get_filename('data/input_with_wrong_annotations_length.tsv')
        document = Document(original_filename, InputReader(original_filename).sentences)
        annotations = InputReader(annotations_filename).sentences
        with self.assertRaises(ValueError) as context:
            document.attach(annotations)

    def test_applying_annotations_with_wrong_words(self):
        original_filename = get_filename('data/input_no_annotations.tsv')
        annotations_filename = get_filename('data/input_with_wrong_annotations.tsv')
        document = Document(original_filename, InputReader(original_filename).sentences)
        annotations = InputReader(annotations_filename).sentences
        with self.assertRaises(ValueError) as context:
            document.attach(annotations)
