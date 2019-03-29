#!/usr/bin/env python3

# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

#
# Uses the translation dictionary to look for missing tags
#
# usage: missing.py lang annotation_dir
#

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

TOKEN = 0
TAG = 1

parser = argparse.ArgumentParser()
parser.add_argument("lang", help="language code")
parser.add_argument("input", help="filename or directory with annotations")
parser.add_argument("-d", "--dict", help="optional dict to use (default is tool's translation dictionary)")
args = parser.parse_args()

for filename in [args.input]:
    if not os.path.exists(filename):
        sys.exit("Error: {} does not exist".format(filename))

if os.path.isdir(args.input):
    filenames = sorted([x for x in glob.glob(os.path.join(args.input, "*")) if os.path.isfile(x)])
else:
    filenames = [args.input]

args.lang = args.lang.lower()


class DictTree(object):
    def __init__(self):
        self.tree = {}

    def add(self, string):
        tokens = [token.strip().lower() for token in string.split(' ')]
        branch = self.tree
        for token in tokens:
            if token not in branch:
                branch[token] = {}
            branch = branch[token]
        branch[None] = None  # indicates a terminal token for a path through the tree

    def check(self, tokens):
        """
        Check if the phrase is in the dictionary
        :param tokens:
        :return: (path in dictionary, path has a terminal stop)
        """
        tokens = [token.lower() for token in tokens]
        branch = self.tree
        for token in tokens:
            if token not in branch:
                return (False, False)
            branch = branch[token]
        terminal = None in branch
        return (True, terminal)


class PhraseHistogram(object):
    def __init__(self):
        self.phrases = collections.Counter()

    def add(self, phrase_rows):
        name = ' '.join([x[0] for x in phrase_rows])
        self.phrases.update({name: 1})

    def write(self, filename):
        with open(filename, 'w') as fp:
            for phrase, count in self.phrases.most_common():
                fp.write("{}\t\t{}\n".format(phrase, count))


# load translation dictionary
trans_dict = {}
if args.dict:
    if not os.path.exists(args.dict):
        sys.exit("Error: dict {} does not exist".format(args.dict))
    with open(args.dict, 'r') as fp:
        reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            trans_dict[row[0].strip().lower()] = row[1].strip()
else:
    ls_dir = os.path.join(os.path.expanduser("~"), '.dragonfly')
    args.dict = os.path.join(ls_dir, args.lang + '.json')
    if not os.path.exists(args.dict):
        sys.exit("Error: dict {} does not exist".format(args.dict))
    with open(args.dict, 'r') as fp:
        trans_dict = json.load(fp)

tree = DictTree()
for key in trans_dict:
    tree.add(key)

stats = collections.defaultdict(list)
phrases = PhraseHistogram()
for filename in filenames:
    with open(filename, 'r', encoding='utf8') as ifp:
        reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
        in_phrase = False
        phrase_rows = []
        phrase_last_index = -1
        rows = [row for row in reader]
        for i in range(len(rows)):
            if in_phrase:
                # end of sentence ends the phrase
                if not rows[i] or not rows[i][TOKEN] or not rows[i][TAG]:
                    in_phrase = False
                    if phrase_last_index >= 0:
                        stats[filename].append(phrase_rows[0:phrase_last_index+1])
                    continue
                # entering a tagged entity ends the phrase
                if len(rows[i][TAG]) > 1:
                    in_phrase = False
                    if phrase_last_index >= 0:
                        stats[filename].append(phrase_rows[0:phrase_last_index + 1])
                    continue
                phrase_rows.append(rows[i][TOKEN])
                (in_dict, terminal) = tree.check(phrase_rows)
                if in_dict:
                    if terminal:
                        phrase_last_index = len(phrase_rows) - 1
                # no longer in dictionary ends the phrase
                else:
                    in_phrase = False
                    if phrase_last_index >= 0:
                        stats[filename].append(phrase_rows[0:phrase_last_index + 1])
            else:
                if not rows[i] or not rows[i][TOKEN] or not rows[i][TAG]:
                    continue

                # must be non-tag to start a phrase
                if len(rows[i][TAG]) == 1:
                    phrase_rows = [rows[i][TOKEN]]
                    (in_dict, terminal) = tree.check(phrase_rows)
                    if in_dict:
                        in_phrase = True
                        phrase_last_index = -1
                        if terminal:
                            phrase_last_index = 0

for doc in sorted(stats.keys()):
    print("{}\t\t{}".format(doc, ', '.join([' '.join(x) for x in stats[doc]])))
