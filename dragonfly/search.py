# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import collections
import concurrent.futures
import csv
import fnmatch
import glob
import logging
import math
import os
import pickle
import requests

from .data import Sentence

logger = logging.getLogger(__name__)


class InvertedIndex:
    """
    Case insensitive inverted index
    """
    MAX_ENTRIES = 25

    class IndexData:
        # data structure for pickling
        # don't need to normalize since each sentence is reference to list
        def __init__(self, max_entries):
            self.max_entries = max_entries
            self.num_documents = 0
            self.index = {}

        def add(self, word, doc, sentence_id, sentence, trans):
            if word not in self.index:
                # cannot use defaultdict since lambdas cannot be pickled
                self.index[word] = {'count': 0, 'doc_count': 0, 'refs': []}
            self.index[word]['count'] += 1
            if self.index[word]['count'] < self.max_entries:
                self.index[word]['refs'].append({
                    'doc': doc,
                    'sent_id': sentence_id,
                    'text': sentence,
                    'trans': trans,
                })

        def clear(self):
            self.index.clear()

        def words(self):
            return self.index.keys()

        def get(self, word):
            if word in self.index:
                return self.index[word]

    def __init__(self):
        self._index = self.IndexData(self.MAX_ENTRIES)

    @property
    def num_documents(self):
        return self._index.num_documents

    def get_doc_count(self, word):
        word = word.lower()
        if word in self._index.index:
            if 'doc_count' not in self._index.get(word):
                raise RuntimeError("Search index needs to be rebuilt. "
                                   "Delete inverted index in dataset's .dragonfly directory and restart")
            return self._index.get(word)['doc_count']
        else:
            return 0

    def add(self, filename, sentences, transliterations):
        """
        Add a document to the index
        :param filename: Filename of the document
        :param sentences: list of sentences where each sentence is a list of words
        :param transliterations: same structure as sentences or None/empty list
        """
        self._index.num_documents += 1
        words = set()
        doc = os.path.basename(filename)
        for i, sentence in enumerate(sentences):
            for word in sentence:
                word = word.lower()
                words.add(word)
                trans = transliterations[i] if transliterations else None
                self._index.add(word, doc, i, sentence, trans)
        for word in words:
            self._index.index[word]['doc_count'] += 1

    def clear(self):
        self._index.clear()

    def retrieve(self, term, wildcards=False):
        term = term.lower()
        results = {'terms': set(), 'count': 0, 'refs': []}
        if wildcards:
            results = self._retrieve_with_wildcards(term)
        else:
            entry = self._index.get(term)
            if entry:
                results['terms'].add(term)
                results['count'] = entry['count']
                results['refs'] = entry['refs']
        return results

    def _retrieve_with_wildcards(self, term):
        results = {'terms': set(), 'count': 0, 'refs': []}
        matches = fnmatch.filter(self._index.words(), term)
        for match in matches:
            entry = self._index.get(match)
            results['terms'].add(match)
            results['count'] += entry['count']
            results['refs'].extend(entry['refs'])
        return results

    def save(self, filename):
        try:
            with open(filename, 'wb') as fp:
                pickle.dump(self._index, fp)
        except Exception:
            logger.exception('Cannot save search index')

    def load(self, filename):
        try:
            with open(filename, 'rb') as fp:
                self._index = pickle.load(fp)
        except Exception:
            logger.exception('Cannot load search index')


class LocalSearch:
    INVERTED_INDEX = "inverted_index.pkl"
    TOKEN = 0
    TRANSLIT = 1

    def __init__(self, data_dir, metadata_dir):
        self.loaded = False
        self.data_dir = data_dir
        self.index_dir = metadata_dir
        self.index = InvertedIndex()
        self.executor = concurrent.futures.ThreadPoolExecutor(1)

    def load_index(self, bg=False, build=False):
        """
        Load the inverted index from disk
        :param bg: Whether to run this as a background task
        :param build: Whether to build the index if it doesn't exist
        """
        if build and not self._index_exists():
            self.build_index(bg)
        else:
            if bg:
                self.executor.submit(self._load_index)
            else:
                self._load_index()

    def build_index(self, bg=False):
        """
        Build the index
        :param bg: Whether to run this as a background task
        """
        if bg:
            logger.info('Building the search index for %s', self.data_dir)
            self.executor.submit(self._build_index)
            logger.info('Completed the search index for %s', self.data_dir)
        else:
            self._build_index()

    def retrieve(self, term, wildcards=False):
        """
        Retrieve results for a query
        :param term: Query term
        :param wildcards: Whether to use shell-style wildcards
        :return: dictionary of results
        """
        return self.index.retrieve(term.lower(), wildcards)

    def _index_exists(self):
        return os.path.exists(self._get_path(self.INVERTED_INDEX))

    def _load_index(self):
        try:
            self.index.load(self._get_path(self.INVERTED_INDEX))
            self.loaded = True
        except FileNotFoundError:
            # index is not created
            logger.info('No search index created yet')
            self.loaded = False

    def _build_index(self):
        self.index.clear()
        filenames = sorted([x for x in glob.glob(os.path.join(self.data_dir, "*.*")) if os.path.isfile(x)])
        for filename in filenames:
            self._add_doc_to_index(filename)
        self.index.save(self._get_path(self.INVERTED_INDEX))

    def _add_doc_to_index(self, filename):
        with open(filename, 'r', encoding='utf8') as ifp:
            reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
            sentences = []
            transliterations = []
            sentence = []
            translit = []
            translit_avail = False
            for row in reader:
                # skip header and sentence breaks
                if not row or not row[self.TOKEN]:
                    sentences.append(sentence)
                    if translit_avail:
                        transliterations.append(translit)
                    sentence = []
                    translit = []
                    continue

                # header skip
                if row[self.TOKEN] == 'TOKEN':
                    if row[self.TRANSLIT] == 'ROMAN':
                        translit_avail = True
                    continue

                sentence.append(row[self.TOKEN])
                if translit_avail:
                    translit.append(row[self.TRANSLIT])

            # end of document sentence
            if sentence:
                sentences.append(sentence)
                if translit_avail:
                    transliterations.append(translit)

            self.index.add(filename, sentences, transliterations)

    def _get_path(self, filename):
        return os.path.join(self.index_dir, filename)


class GeonamesSearch:
    def __init__(self, username, countries=None):
        """
        :param username: Geonames username
        :param countries: list of country codes
        """
        self.username = username
        self.url = 'http://api.geonames.org/search?q={}&fuzzy={}&username={}&maxRows=20&type=json'
        if countries:
            for country in countries:
                self.url += '&country=' + country

    def retrieve(self, term, fuzzy=0.8):
        """
        Retrieve results from geonames
        :param term: search term
        :param fuzzy: Fuzzy threshold between 0 and 1 (exact match)
        :return: Geonames results object
        """
        try:
            response = requests.get(self.url.format(term, fuzzy, self.username))
            response.raise_for_status()
            return response.json()
        except Exception as err:
            logger.warning('Error occurred: {}'.format(err))
            return None


class DictionarySearch:
    """
    Search over a bilingual dictionary with optional transliteration column
    """
    FILENAME = 'combodict.txt'
    IL = 0
    ENG = 1
    TRANS = 2

    def __init__(self, metadata_dir):
        self.filename = os.path.join(metadata_dir, self.FILENAME)
        self.loaded = False
        self.data = []
        self.il_index = collections.defaultdict(list)
        self.english_index = collections.defaultdict(list)
        self.trans_index = collections.defaultdict(list)
        self.trans_available = None

    @property
    def available(self):
        return os.path.exists(self.filename)

    def retrieve(self, term, column):
        if not self.loaded:
            self._load()
        term = term.lower()
        if column == self.IL:
            return self.il_index[term]
        elif column == self.ENG:
            return self.english_index[term]
        elif column == self.TRANS:
            return self.trans_index[term]

    def suggest(self, term, column):
        if not self.loaded:
            self._load()
        index = {}
        if column == self.IL:
            index = self.il_index
        elif column == self.ENG:
            index = self.english_index
        elif column == self.TRANS:
            index = self.trans_index
        matches = fnmatch.filter(index.keys(), term.lower() + '*')
        results = []
        for match in matches:
            results.append(match)
        results.sort()
        return results

    def _load(self):
        self.loaded = True
        with open(self.filename, 'r', encoding='utf8') as fp:
            reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                if self.trans_available is None:
                    self.trans_available = len(row) == 3
                self.data.append(row)
                self.il_index[row[self.IL].lower()].append(self.data[-1])
                self.english_index[row[self.ENG].lower()].append(self.data[-1])
                if self.trans_available:
                    self.trans_index[row[self.TRANS].lower()].append(self.data[-1])

    def copy(self, data):
        with open(self.filename, 'w') as fp:
            fp.write(data)
            self.loaded = False
            self.trans_available = None
            self.data.clear()
            self.english_index.clear()
            self.il_index.clear()
            self.trans_index.clear()


class DocumentStats:
    """
    Information derived from search index about words in a document
    """
    def __init__(self, document, index):
        self.document = document
        self.index = index
        self._calculate_tfidf()

    def get_top_words(self, n=20):
        return dict(sorted(self.tfidf.items(), key=lambda item: item[1], reverse=True)[:n])

    def get_tfidf(self, word):
        word = word.lower()
        if word in self.tfidf:
            return self.tfidf[word]
        else:
            return 0

    def get_idf(self, word):
        try:
            return math.log(self.index.num_documents / self.index.get_doc_count(word))
        except ZeroDivisionError:
            # this means a document was changed or added so uncounted word
            return 0

    def _calculate_tfidf(self):
        self.word_counts = collections.Counter()
        for sentence in self.document.sentences:
            for word in sentence.rows[Sentence.TOKEN].strings:
                self.word_counts.update({word.lower(): 1})
        self.tfidf = {}
        for word in self.word_counts:
            try:
                self.tfidf[word] = self.word_counts[word] * math.log(self.index.num_documents / self.index.get_doc_count(word))
            except ZeroDivisionError:
                # this means a document was changed or added so uncounted word
                self.tfidf[word] = 0
