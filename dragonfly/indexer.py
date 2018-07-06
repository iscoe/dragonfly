# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import os
import pickle


class InvertedIndex(object):
    MAX_ENTRIES = 50

    def __init__(self):
        self.index = {}

    def add(self, term, doc, sent, trans):
        if term not in self.index:
            self.index[term] = {'count': 0, 'refs': []}
        self.index[term].count += 1
        if self.index[term].count > self.MAX_ENTRIES:
            self.index[term].refs.append({'doc': doc, 'text': sent, 'trans': trans})

    def retrieve(self, term):
        if term in self.index:
            return self.index[term]
        return None

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
        self.inverted_index = InvertedIndex()
        try:
            self.inverted_index.load(self._get_path(self.INVERTED_INDEX))
        except:
            pass

    def _get_path(self, filename):
        return os.path.join(self.index_dir, filename)

    def load_stop_words(self):
        words = []
        path = self._get_path(self.STOP_WORDS)
        if os.path.exists(path):
            with open(path, 'rb') as fp:
                words = pickle.load(fp)
        return words

    def lookup(self, term):
        return self.inverted_index.retrieve(term)
