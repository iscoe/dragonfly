#!/usr/bin/env python3

# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

#
# Usage: python3 scripts/stats.py [annotations directory]
#
# Use -v to get a count over mentions
#

import argparse
import collections
import csv
import glob
import os
import sys

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))

TOKEN = 0
TAG = 1

parser = argparse.ArgumentParser()
parser.add_argument("input", help="directory with .anno files")
parser.add_argument("-v", "--verbose", help="verbose output", action='store_true', default=False)
args = parser.parse_args()

for filename in [args.input]:
    if not os.path.exists(filename):
        sys.exit("Error: {} does not exist".format(filename))

if os.path.isdir(args.input):
    filenames = [x for x in glob.glob(os.path.join(args.input, "*")) if os.path.isfile(x)]
else:
    filenames = [args.input]


class TypeStats(object):
    def __init__(self, entity_type):
        self.type = entity_type
        self.num_entities = 0
        self.entities = collections.Counter()

    def add(self, name):
        self.num_entities += 1
        self.entities.update({name: 1})


class Stats(object):
    OTHER = 'O'

    def __init__(self):
        self.num_tokens = 0
        self.num_tagged_tokens = 0
        self.entities = {}

    def add(self, rows):
        self.num_tagged_tokens += len(rows)
        entity_type = Stats.get_type(rows)
        if entity_type != self.OTHER:
            if entity_type not in self.entities:
                self.entities[entity_type] = TypeStats(entity_type)
            self.entities[entity_type].add(Stats.get_name(rows))

    def increment_tokens(self):
        self.num_tokens += 1

    @property
    def num_entities(self):
        return sum([s.num_entities for s in self.entities.values()])

    @property
    def num_unique_entities(self):
        return sum([len(s.entities) for s in self.entities.values()])

    @staticmethod
    def get_type(rows):
        return rows[0][TAG][2:].upper()

    @staticmethod
    def get_name(rows):
        return ' '.join([row[TOKEN] for row in rows]).lower()


stats = Stats()
for filename in filenames:
    with open(filename, 'r') as ifp:
        in_tag = False
        tag_rows = []
        reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
        for row in reader:
            if in_tag:
                # tag end (end of sentence, O, or new B-)
                if len(row) < 2 or not row[TOKEN] or row[TAG][0] != 'I':
                    stats.add(tag_rows)
                    in_tag = False
                    tag_rows = []

            # sentence separator
            if len(row) < 2 or not row[TOKEN]:
                continue

            stats.increment_tokens()

            # write out O rows and store tag rows
            if row[TAG][0] == 'B':
                in_tag = True
                tag_rows = [row]
            elif row[TAG][0] == 'I':
                tag_rows.append(row)

        # catch tag at end of file
        if in_tag:
            stats.add(tag_rows)

print("{} Documents".format(len(filenames)))
print("{} Tokens".format(stats.num_tokens))
print("{} Tagged Tokens".format(stats.num_tagged_tokens))
print("{} Entity Tags".format(stats.num_entities))
print("{} Unique Entity Tags".format(stats.num_unique_entities))
for s in stats.entities.values():
    print("{}: {} Entities".format(s.type, s.num_entities))
    print("{}: {} Unique Entities".format(s.type, len(s.entities)))
if args.verbose:
    print("---------------------------------")
    for s in stats.entities.values():
        print()
        print(s.type)
        print("-------------------")
        for name, count in s.entities.most_common(len(s.entities)):
            print("{}\t{}".format(name, count))
