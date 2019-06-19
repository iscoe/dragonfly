# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import concurrent.futures
import copy
import csv
import fnmatch
import glob
import os
import pickle


class InvertedIndex:
    MAX_ENTRIES = 25

    def __init__(self):
        self.index = {}

    def add(self, doc, sent, trans):
        doc = os.path.basename(doc)
        for word in sent:
            word = word.lower()
            if word not in self.index:
                self.index[word] = {'count': 0, 'refs': []}
            self.index[word]['count'] += 1
            if self.index[word]['count'] < self.MAX_ENTRIES:
                self.index[word]['refs'].append({'doc': doc, 'text': sent, 'trans': trans})

    def retrieve(self, term, wildcards=False):
        term = term.lower()
        results = {'terms': set(), 'count': 0, 'refs': []}
        if wildcards:
            results = self._retrieve_with_wildcards(term)
        elif term in self.index:
            results['terms'].add(term)
            results['count'] = self.index[term]['count']
            results['refs'] = self.index[term]['refs']
        return results

    def _retrieve_with_wildcards(self, term):
        results = {'terms': set(), 'count': 0, 'refs': []}
        matches = fnmatch.filter(self.index.keys(), term)
        for match in matches:
            results['terms'].add(match)
            results['count'] += self.index[match]['count']
            results['refs'].extend(self.index[match]['refs'])
        return results

    def save(self, filename):
        with open(filename, 'wb') as fp:
            pickle.dump(self.index, fp)

    def load(self, filename):
        with open(filename, 'rb') as fp:
            self.index = pickle.load(fp)


class Indexer:
    INVERTED_INDEX = "inverted_index.pkl"
    TOKEN = 0
    TRANSLIT = 1

    def __init__(self, data_dir):
        self.loaded = False
        self.data_dir = data_dir
        self.index_dir = os.path.join(data_dir, '.index')
        self.index = InvertedIndex()

    def load(self):
        try:
            self.index.load(self._get_path(self.INVERTED_INDEX))
            self.loaded = True
        except FileNotFoundError:
            # index is not created
            self.loaded = False

    def build(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
        filenames = sorted([x for x in glob.glob(os.path.join(self.data_dir, "*.*")) if os.path.isfile(x)])
        for filename in filenames:
            self._add_doc_to_index(filename)

    def save(self):
        self.index.save(self._get_path(self.INVERTED_INDEX))

    def _add_doc_to_index(self, filename):
        with open(filename, 'r', encoding='utf8') as ifp:
            reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
            sentence = []
            trans = []
            translit_avail = False
            for row in reader:
                # skip header and sentence breaks
                if not row or not row[self.TOKEN]:
                    if translit_avail:
                        self.index.add(filename, sentence, trans)
                    else:
                        self.index.add(filename, sentence, None)
                    sentence = []
                    trans = []
                    continue
                if row[self.TOKEN] == 'TOKEN':
                    if row[self.TRANSLIT] == 'ROMAN':
                        translit_avail = True
                    continue

                # inverted index update
                token = row[self.TOKEN].lower()
                sentence.append(token)
                if translit_avail:
                    trans.append(row[self.TRANSLIT])

    def retrieve(self, term, wildcards=False):
        return self.index.retrieve(term.lower(), wildcards)

    def _get_path(self, filename):
        return os.path.join(self.index_dir, filename)


class BackgroundProcess:
    def __init__(self, indexer, logger):
        self.executor = concurrent.futures.ThreadPoolExecutor(1)
        self.indexer = indexer
        self.logger = logger

    def load_index(self):
        self.executor.submit(self._load_index)

    def build_index(self):
        self.executor.submit(self._build_index)
        self.executor.submit(self._load_index)

    def _load_index(self):
        self.indexer.load()

    def _build_index(self):
        self.logger.info('Building the search index for %s', self.indexer.data_dir)
        self.indexer.build()
        self.indexer.save()
        self.indexer.load()
        self.logger.info('Completed the search index for %s', self.indexer.data_dir)
