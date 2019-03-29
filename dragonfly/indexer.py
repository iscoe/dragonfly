# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import os
import pickle


class InvertedIndex(object):
    MAX_ENTRIES = 25

    def __init__(self):
        self.index = {}

    def add(self, doc, sent, trans):
        doc = os.path.basename(doc)
        for word in sent:
            if word not in self.index:
                self.index[word] = {'count': 0, 'refs': []}
            self.index[word]['count'] += 1
            if self.index[word]['count'] < self.MAX_ENTRIES:
                self.index[word]['refs'].append({'doc': doc, 'text': sent, 'trans': trans})

    def retrieve(self, term):
        term = term.lower()
        if term in self.index:
            return self.index[term]
        return {'count': 0, 'refs': []}

    def save(self, filename):
        with open(filename, 'wb') as fp:
            pickle.dump(self.index, fp)

    def load(self, filename):
        with open(filename, 'rb') as fp:
            self.index = pickle.load(fp)


class Indexer(object):
    STOP_WORDS = "stop_words.pkl"
    INVERTED_INDEX = "inverted_index.pkl"

    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.stop_words = []
        self.inverted_index = InvertedIndex()
        try:
            self.inverted_index.load(self._get_path(self.INVERTED_INDEX))
        except:
            pass
        stop_words_path = self._get_path(self.STOP_WORDS)
        if os.path.exists(stop_words_path):
            with open(stop_words_path, 'rb') as fp:
                self.stop_words = pickle.load(fp)

    def _get_path(self, filename):
        return os.path.join(self.index_dir, filename)

    def lookup(self, term):
        return self.inverted_index.retrieve(term.lower())
