# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import os
import pickle


class Indexer(object):
    STOP_WORDS = "stop_words.pkl"

    def __init__(self, index_dir):
        self.index_dir = index_dir

    def load_stop_words(self):
        words = []
        path = os.path.join(self.index_dir, self.STOP_WORDS)
        if os.path.exists(path):
            with open(path, 'rb') as fp:
                words = pickle.load(fp)
        return words
