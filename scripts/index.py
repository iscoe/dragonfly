#!/usr/bin/env python3

# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import argparse
import collections
import csv
import glob
import json
import os
import sys

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
tokens = collections.Counter()
filenames = sorted([x for x in glob.glob(os.path.join(args.input, "*")) if os.path.isfile(x)])
for filename in filenames:
    with open(filename, 'r') as ifp:
        reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            # skip header and sentence breaks
            if not row or not row[TOKEN]:
                continue
            if row[TOKEN] == 'TOKEN':
                continue

            token = row[TOKEN].lower()
            tokens.update({token: 1})

stop_words = [word_count_pair[0] for word_count_pair in tokens.most_common(args.stop_words)]
stop_words_filename = os.path.join(index_dir, 'stop_words')
with open(stop_words_filename, 'w') as ofp:
    json.dump(stop_words, ofp)
