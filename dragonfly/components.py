# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import collections
import csv
import glob
import json
import os


class Hints:
    FILE = 'hints'

    def __init__(self, metadata_dir):
        self.filename = os.path.join(metadata_dir, self.FILE)

    def load(self):
        hints = []
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf8') as fp:
                reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    hints.append({'regex': row[0], 'comment': row[1]})
        return hints

    def load_raw(self):
        text = ''
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf8') as fp:
                text = fp.read()
        return text

    def save(self, text):
        with open(self.filename, 'w', encoding='utf8') as fp:
            fp.write(text)


class Notepad:
    """
    Maintain notes related to annotating
    """
    DIR = 'notes'
    GLOBAL = 'all'

    def __init__(self, metadata_dir):
        self.dir = os.path.join(metadata_dir, self.DIR)
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

    def save(self, filename, notes):
        """
        :param filename: filename or empty string for global notes
        :param notes: notes text
        """
        filename = filename if filename else self.GLOBAL
        filename = os.path.join(self.dir, filename)
        with open(filename, 'w', encoding='utf8') as fp:
            fp.write(notes)

    def load(self, filename):
        """
        :param filename: filename or empty string for global notes
        """
        filename = filename if filename else self.GLOBAL
        filename = os.path.join(self.dir, filename)
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf8') as fp:
                return fp.read()
        return ''


class SentenceMarkerManager:
    """
    Manage sentence markers

    The markers dictionary is document -> list of sentence ids (0-based index)
    """
    def __init__(self, metadata_dir):
        self.path = os.path.join(metadata_dir, 'markers')
        self.markers = self._load(self.path)

    def toggle(self, document, sentence):
        sentence = int(sentence)
        if document not in self.markers:
            self.markers[document] = []
            self.markers[document].append(sentence)
        elif sentence not in self.markers[document]:
            self.markers[document].append(sentence)
        else:
            self.markers[document].remove(sentence)
        self._save(self.path, self.markers)

    def get(self, document):
        markers = []
        if document in self.markers:
            markers = self.markers[document]
        return markers

    @staticmethod
    def _load(path):
        markers = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf8') as fp:
                markers = json.load(fp)
        return markers

    @staticmethod
    def _save(path, markers):
        with open(path, 'w', encoding='utf8') as fp:
            json.dump(markers, fp)


class StopWords:
    """
    Calculate a list of stop words from a corpus
    """
    CACHE_FILE = 'stop_words.json'
    TOKEN_INDEX = 0

    def __init__(self, data_dir, metadata_dir, size=50):
        self.words = set()
        self.cache_filename = os.path.join(metadata_dir, self.CACHE_FILE)
        if not os.path.exists(self.cache_filename):
            self.build(data_dir, size)
            self._save()
        else:
            self._load()

    def build(self, data_dir, size):
        counts = collections.Counter()
        filenames = sorted([x for x in glob.glob(os.path.join(data_dir, "*.*")) if os.path.isfile(x)])
        for filename in filenames:
            with open(filename, 'r', encoding='utf8') as fp:
                reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    # sentence separator
                    if len(row) < 1:
                        continue
                    counts.update({row[self.TOKEN_INDEX].lower(), 1})
        self.words = {x[0] for x in counts.most_common(size)}

    def _load(self):
        with open(self.cache_filename, 'r', encoding='utf8') as fp:
            words = json.load(fp)
        self.words = set(words)

    def _save(self):
        with open(self.cache_filename, 'w', encoding='utf8') as fp:
            json.dump(list(self.words), fp)


class TypeStats:
    def __init__(self, entity_type):
        self.type = entity_type
        self.num_entities = 0
        self.entities = collections.Counter()

    def add(self, name):
        self.num_entities += 1
        self.entities.update({name: 1})


class Stats:
    OUTSIDE = 'O'
    TOKEN = 0
    TAG = 1

    def __init__(self):
        self.num_tokens = 0
        self.num_tagged_tokens = 0
        self.num_tokens_in_tagged_sentences = 0
        self.entities = {}
        self.num_files = 0
        self.num_sentences = 0
        self.num_sentences_with_tags = 0

    def collect(self, path):
        filenames = [x for x in glob.glob(os.path.join(path, "*.anno")) if os.path.isfile(x)]
        for filename in filenames:
            with open(filename, 'r', encoding='utf8') as ifp:
                self.num_files += 1
                in_tag = False
                sentence_tagged = False
                new_sentence = False
                sentence_length = 0
                tag_rows = []
                reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    new_sentence = True
                    if in_tag:
                        # tag end (end of sentence, O, or new B-)
                        if len(row) < 2 or not row[Stats.TOKEN] or row[Stats.TAG][0] != 'I':
                            self.add(tag_rows)
                            in_tag = False
                            tag_rows = []

                    # sentence separator
                    if len(row) < 2 or not row[Stats.TOKEN]:
                        self.num_sentences += 1
                        if sentence_tagged:
                            self.num_sentences_with_tags += 1
                            self.num_tokens_in_tagged_sentences += sentence_length
                        sentence_tagged = False
                        new_sentence = False
                        sentence_length = 0
                        continue

                    self.increment_tokens()
                    sentence_length += 1

                    if row[Stats.TAG][0] == 'B':
                        in_tag = True
                        sentence_tagged = True
                        tag_rows = [row]
                    elif row[Stats.TAG][0] == 'I':
                        tag_rows.append(row)

                # catch tag at end of file
                if in_tag:
                    self.add(tag_rows)

                # catch sentence with no trailing blank line at end of document
                if new_sentence:
                    self.num_sentences += 1
                    if sentence_tagged:
                        self.num_sentences_with_tags += 1
                        self.num_tokens_in_tagged_sentences += sentence_length

    def add(self, rows):
        self.num_tagged_tokens += len(rows)
        entity_type = Stats.get_type(rows)
        if entity_type != self.OUTSIDE:
            if entity_type not in self.entities:
                self.entities[entity_type] = TypeStats(entity_type)
            self.entities[entity_type].add(Stats.get_name(rows))

    def increment_tokens(self):
        self.num_tokens += 1

    @property
    def percentage_tagged(self):
        if self.num_tokens == 0:
            return 0
        return 100 * self.num_tagged_tokens / self.num_tokens

    @property
    def percentage_of_tokens_in_tagged_sentences(self):
        # for the sentences that are tagged, what percentage of tokens are tagged
        if self.num_tokens == 0:
            return 0
        return 100 * self.num_tagged_tokens / self.num_tokens_in_tagged_sentences

    @property
    def num_entities(self):
        return sum([s.num_entities for s in self.entities.values()])

    @property
    def num_unique_entities(self):
        return sum([len(s.entities) for s in self.entities.values()])

    @staticmethod
    def get_type(rows):
        return rows[0][Stats.TAG][2:].upper()

    @staticmethod
    def get_name(rows):
        return ' '.join([row[Stats.TOKEN] for row in rows]).lower()
