#!/usr/bin/env python3

# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

#
# Build an index over the files
#
# usage: index.py files_dir
#
# Creates a hidden .index directory
#

import argparse
import collections
import csv
import glob
import pickle
import os
import sys

# don't assume the user has install dragonfly
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import dragonfly.indexer

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))

parser = argparse.ArgumentParser()
parser.add_argument("input", help="directory being annotated")
parser.add_argument("--stop-words", help="number of stop words", default=500, type=int)
args = parser.parse_args()

if not os.path.isdir(args.input):
    quit()

index_dir = os.path.join(args.input, '.index')
if not os.path.exists(index_dir):
    os.makedirs(index_dir)

TOKEN = 0
TRANSLIT = 1
tokens = collections.Counter()
inverted_index = dragonfly.indexer.InvertedIndex()

filenames = sorted([x for x in glob.glob(os.path.join(args.input, "*")) if os.path.isfile(x)])
for filename in filenames:
    with open(filename, 'r', encoding='utf8') as ifp:
        reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
        sentence = []
        trans = []
        translit_avail = False
        for row in reader:
            # skip header and sentence breaks
            if not row or not row[TOKEN]:
                if translit_avail:
                    inverted_index.add(filename, sentence, trans)
                else:
                    inverted_index.add(filename, sentence, None)
                sentence = []
                trans = []
                continue
            if row[TOKEN] == 'TOKEN':
                if row[TRANSLIT] == 'ROMAN':
                    translit_avail = True
                continue

            # stop word update
            token = row[TOKEN].lower()
            tokens.update({token: 1})

            # inverted index update
            sentence.append(token)
            if translit_avail:
                trans.append(row[TRANSLIT])

# save stop words
stop_words = [word_count_pair[0] for word_count_pair in tokens.most_common(args.stop_words)]
stop_words_filename = os.path.join(index_dir, 'stop_words.pkl')
with open(stop_words_filename, 'wb') as ofp:
    pickle.dump(stop_words, ofp)

# save inverted index
filename = os.path.join(index_dir, 'inverted_index.pkl')
inverted_index.save(filename)
