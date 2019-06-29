# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import csv
import glob
import os


class FileLister:
    """
    Get the name of a file to annotate from a directory
    """
    def __init__(self, path, file_ext):
        self.path = path
        pattern = '*' + file_ext
        self.filenames = [x for x in glob.glob(os.path.join(path, pattern)) if os.path.isfile(x)]
        self.filenames = sorted(self.filenames)
        if self.size() == 0:
            raise ValueError("No files for directory {} with extension {}".format(path, file_ext))

    def get_filename(self, index):
        if index < len(self.filenames):
            return self.filenames[index]
        return None

    def get_index_from_filename(self, filename):
        if filename in self.filenames:
            return self.filenames.index(filename)
        # if filenames include path information, exact string won't be in the list so loop over them
        for index in enumerate(self.filenames):
            if filename in self.filenames[index[0]]:
                return index[0]
        return None

    def size(self):
        return len(self.filenames)

    def has_next(self, index):
        return (index + 1) < len(self.filenames)

    def __contains__(self, key):
        return 0 <= key < len(self.filenames)


class AnnotationLoader:
    def __init__(self, path):
        self.base = path

    def get(self, filename):
        filename = os.path.basename(filename)
        annotation_filename = filename + '.anno'
        path = os.path.join(self.base, annotation_filename)
        if os.path.isfile(path):
            return path
        return None


class EnglishTranslationLoader:
    def __init__(self, path):
        self.base = path

    def get(self, filename):
        filename = os.path.basename(filename)
        translation_filename = filename + '.eng'
        path = os.path.join(self.base, translation_filename)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf8') as ifp:
                return [x for x in ifp]


class Document:
    TOKENS = 0
    ANNOTATIONS = 1

    """
    Contains a list of sentences and optional annotations
    """
    def __init__(self, filename, sentences, terminal_blank_line):
        self.filename = filename
        self.sentences = sentences
        self.num_sentences = len(sentences)
        self.num_tokens = self._count_tokens(sentences)
        self.has_annotations = False
        self.has_translation = False
        self.translation = None
        self.markers = []
        self.terminal_blank_line = terminal_blank_line

    def attach_annotations(self, annotations):
        """annotations are sentences from InputReader"""
        self._validate_annotations(annotations)
        self._set_annotations(annotations)
        self.has_annotations = True

    def attach_adj_annotations(self, name, annotations):
        """adjudication annotations are added as new rows"""
        self._validate_annotations(annotations)
        self._set_adj_annotations(name, annotations)

    def attach_translation(self, translation):
        self.has_translation = True
        self.translation = translation

    def attach_markers(self, markers):
        self.markers = markers

    def _validate_annotations(self, annotations):
        if len(annotations) != self.num_sentences:
            raise ValueError("Annotations and input file are different lengths")
        # first word must match
        first_word_doc = self.sentences[0].rows[Document.TOKENS].strings[0]
        first_word_anno = annotations[0].rows[Document.TOKENS].strings[0]
        if first_word_doc != first_word_anno:
            raise ValueError("Input file and annotations do not match: {} != {}".format(first_word_doc, first_word_anno))

    def _set_annotations(self, annotations):
        for index, sentence in enumerate(self.sentences):
            # tag annotations are stored in the second column of annotation file
            sentence.attach(annotations[index].rows[Document.ANNOTATIONS])

    def _set_adj_annotations(self, name, annotations):
        for index, sentence in enumerate(self.sentences):
            # tag annotations are stored in the second column of annotation file
            sentence.insert_adj_row(name, annotations[index].rows[Document.ANNOTATIONS])

    @staticmethod
    def _count_tokens(sentences):
        total = 0
        for sentence in sentences:
            tokens = sentence.rows[0]
            total += len(tokens.strings)
        return total

    def __repr__(self):
        return "<Document ({}): {}>".format(self.filename, self.sentences)


class Sentence:
    TOKEN = 0

    """
    Represents a single sentence with its multiple rows of information (translations, PoS, gazetteer data, etc.)
    """
    def __init__(self, index):
        self.index = index
        self.rows = []

    @property
    def length(self):
        return len(self.rows[Sentence.TOKEN].strings)

    def add(self, row):
        self.rows.append(row)

    def append(self, index, string):
        """append a new string to a particular row"""
        self.rows[index].append(string)

    def attach(self, annotations):
        """attach annotations to the tokens row"""
        self.rows[Sentence.TOKEN].attach(annotations.strings)

    def insert_adj_row(self, name, row):
        """insert a new row for adjudication"""
        row.label = name
        row.adjudicate = True
        self.rows.insert(Sentence.TOKEN + 1, row)

    def __repr__(self):
        return "<Sentence {}: {}>".format(self.index, self.rows)


class SentenceRow:
    """
    Represents a single row of a sentence: tokens or transliterations or translations or ...

     Args:
        index (int): row index
        label (string): column label
    """
    def __init__(self, index, label):
        self.index = index
        self.label = label
        self.strings = []
        self.annotations = []
        self.adjudicate = False

    def append(self, string):
        self.strings.append(string)

    def attach(self, annotations):
        self.annotations = annotations

    @property
    def length(self):
        return len(self.strings)

    def __repr__(self):
        return "<Row {} ({}): {}>".format(self.index, self.label, self.strings)


class InputReader:
    """
    This parses a tsv file into a list of Sentence objects.
    Each Sentence has a list of SentenceRow objects which correspond to the column data for that sentence.
    The first column in the tsv must be the original tokens.
    If the first row is a header, the first column header must be TOKEN.
    There must be an empty line between sentences.
    The last line could be the last token or a blank line.
    The data in the tsv is organized in columns, but we represent with rows for display purposes.
    """
    def __init__(self, filename):
        self.filename = filename
        self.num_rows = 0
        self.row_labels = []
        self.sentences = []
        self.terminal_blank_line = True
        self._load()

    def _load(self):
        with open(self.filename, 'r', encoding='utf8') as fp:
            reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
            try:
                first_row = next(reader)
            except StopIteration:
                raise ValueError("{} is an empty file".format(self.filename))
            self.num_rows = len(first_row)
            has_header = self._is_header(first_row)
            self.row_labels = self._create_row_labels(first_row, has_header)

            data = [] if has_header else [first_row]
            for row in reader:
                if self._is_data(row):
                    data.append(row)
                elif data:
                    # sentence break
                    self.sentences.append(self._process_sentence(data))
                    data = []
            if data:
                # catch last sentence that does not have an empty line after it
                self.sentences.append(self._process_sentence(data))
                self.terminal_blank_line = False

    @staticmethod
    def _is_header(row):
        return row[0].lower() in ['tok', 'token', 'tokens']

    def _is_data(self, row):
        # Must have right number of columns and have data in one of the columns
        if len(row) != self.num_rows:
            return False
        have_data = False
        for value in row:
            have_data |= bool(value)
        return have_data

    @staticmethod
    def _create_row_labels(row, use_values=True):
        if use_values:
            return [label.strip() for label in row]
        else:
            labels = []
            for index, value in enumerate(row, 1):
                labels.append('row {}'.format(index))
            return labels

    def _process_sentence(self, data):
        sentence = Sentence(len(self.sentences))
        for index, label in enumerate(self.row_labels):
            sentence.add(SentenceRow(index, label))
        for row in data:
            for index, value in enumerate(row):
                sentence.append(index, value)
        return sentence


class OutputWriter:
    """
    Write the annotations
    """
    def __init__(self, directory):
        self.directory = directory

    def write(self, data):
        filename = os.path.join(self.directory, data['filename'] + '.anno')
        with open(filename, 'w', encoding='utf8') as fp:
            for token in data['tokens']:
                if token:
                    fp.write('{}\t{}\n'.format(token['token'], token['tag']))
                else:
                    fp.write('\n')
