import unittest
import shutil
import tempfile
import os
import glob
from dragonfly.adjudicate import AdjudicationManager
from dragonfly.data import InputReader, Document


class AdjudicateTest(unittest.TestCase):
    def setUp(self):
        self.output_dir_with_headers = tempfile.mkdtemp()
        self.output_dir_without_headers = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir_with_headers)
        shutil.rmtree(self.output_dir_without_headers)

    def test_input_with_headers(self):
        input_dir = "data/adjudicate/input-with-headers"
        reference_annotations = "annotations"
        tsv_file_extension = ".txt"
        annotation_dir_prefix = "annotations-"
        output_dir = self.output_dir_with_headers

        manager = AdjudicationManager(input_dir, output_dir,
                                      tsv_file_extension, annotation_dir_prefix,
                                      reference_annotations)

        self.assertEquals(manager.reference_annotations, reference_annotations)

        expected_annotation_dirs = ["annotations-1", "annotations-2"]
        self._test_annotation_directories(manager, expected_annotation_dirs)

        annotations_lookup_by_directory, tsv_files_with_annotations = manager.load_annotation_directories()

        tsv_file_paths = glob.glob(input_dir + "/*" + tsv_file_extension)
        tsv_files = [os.path.basename(tsv_file_path) for tsv_file_path in tsv_file_paths]
        tsv_files_with_annotations = [tsv_file for tsv_file in tsv_files if tsv_file in tsv_files_with_annotations]
        tsv_files_without_annotations = [tsv_file for tsv_file in tsv_files if
                                         tsv_file not in tsv_files_with_annotations]

        self.assertEqual(len(tsv_files), (len(tsv_files_with_annotations) + len(tsv_files_without_annotations)))

        manager.copy_reference_annotation_files()
        manager.rewrite_tsv_files_with_annotations(tsv_files_with_annotations, annotations_lookup_by_directory)
        manager.copy_tsv_files_without_annotations(tsv_files_without_annotations)

        original_filename = os.path.join(output_dir, 'input_with_headers_file_1.txt')
        annotations_filename = os.path.join(os.path.join(output_dir, "annotations"),
                                            'input_with_headers_file_1.txt.anno')
        document = Document(original_filename, InputReader(original_filename).sentences)
        annotations = InputReader(annotations_filename).sentences
        document.attach(annotations)

        self.assertEqual('O', document.sentences[0].columns[0].annotations[1])
        self.assertEqual('B-PER', document.sentences[0].columns[0].annotations[3])

    def test_input_without_headers(self):
        input_dir = "data/adjudicate/input-without-headers"
        reference_annotations = "annos_a"
        tsv_file_extension = ".txt"
        annotation_dir_prefix = "annos_"
        output_dir = self.output_dir_without_headers

        manager = AdjudicationManager(input_dir, output_dir,
                                      tsv_file_extension, annotation_dir_prefix,
                                      reference_annotations)

        self.assertEquals(manager.reference_annotations, reference_annotations)

        expected_annotation_dirs = ["annos_b", "annos_c"]
        self._test_annotation_directories(manager, expected_annotation_dirs)

        annotations_lookup_by_directory, tsv_files_with_annotations = manager.load_annotation_directories()

        tsv_file_paths = glob.glob(input_dir + "/*" + tsv_file_extension)
        tsv_files = [os.path.basename(tsv_file_path) for tsv_file_path in tsv_file_paths]
        tsv_files_with_annotations = [tsv_file for tsv_file in tsv_files if tsv_file in tsv_files_with_annotations]
        tsv_files_without_annotations = [tsv_file for tsv_file in tsv_files if
                                         tsv_file not in tsv_files_with_annotations]

        self.assertEqual(len(tsv_files), (len(tsv_files_with_annotations) + len(tsv_files_without_annotations)))

        manager.copy_reference_annotation_files()
        manager.rewrite_tsv_files_with_annotations(tsv_files_with_annotations, annotations_lookup_by_directory)
        manager.copy_tsv_files_without_annotations(tsv_files_without_annotations)

        original_filename = os.path.join(output_dir, 'input_without_headers_file_a.txt')
        annotations_filename = os.path.join(os.path.join(output_dir, "annotations"),
                                            'input_without_headers_file_a.txt.anno')

        document = Document(original_filename, InputReader(original_filename).sentences)
        annotations = InputReader(annotations_filename).sentences
        document.attach(annotations)

        self.assertEqual('O', document.sentences[0].columns[0].annotations[0])
        self.assertEqual('B-PER', document.sentences[0].columns[0].annotations[1])

    def test_get_identifier_from_annotation_dir(self):
        input_dir = "data/adjudicate/input-with-headers"
        reference_annotations = "annotations-2"
        tsv_file_extension = "conll.txt"
        annotation_dir_prefix = "annotations-"
        output_dir = "output-test"
        manager = AdjudicationManager(input_dir, output_dir,
                                      tsv_file_extension, annotation_dir_prefix,
                                      reference_annotations)

        self.assertEquals(manager.get_identifier_from_annotation_dir(reference_annotations), "2")

    def _test_annotation_directories(self, manager, expected_anno_dirs):
        annotation_dirs = manager.annotation_directories
        annotation_dirs.sort()
        expected_anno_dirs.sort()
        self.assertListEqual(annotation_dirs, expected_anno_dirs)
        annotations_lookup_by_directory, tsv_files_with_annotations = manager.load_annotation_directories()
        self.assertListEqual(list(annotations_lookup_by_directory.keys()), expected_anno_dirs)
