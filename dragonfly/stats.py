# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import collections
import csv
import glob
import os


class TypeStats(object):
    def __init__(self, entity_type):
        self.type = entity_type
        self.num_entities = 0
        self.entities = collections.Counter()

    def add(self, name):
        self.num_entities += 1
        self.entities.update({name: 1})


class Stats(object):
    OUTSIDE = 'O'
    TOKEN = 0
    TAG = 1

    def __init__(self):
        self.num_tokens = 0
        self.num_tagged_tokens = 0
        self.entities = {}
        self.num_files = 0

    def collect(self, path):
        filenames = [x for x in glob.glob(os.path.join(path, "*.anno")) if os.path.isfile(x)]
        for filename in filenames:
            with open(filename, 'r', encoding='utf8') as ifp:
                self.num_files += 1
                in_tag = False
                tag_rows = []
                reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    if in_tag:
                        # tag end (end of sentence, O, or new B-)
                        if len(row) < 2 or not row[Stats.TOKEN] or row[Stats.TAG][0] != 'I':
                            self.add(tag_rows)
                            in_tag = False
                            tag_rows = []

                    # sentence separator
                    if len(row) < 2 or not row[Stats.TOKEN]:
                        continue

                    self.increment_tokens()

                    if row[Stats.TAG][0] == 'B':
                        in_tag = True
                        tag_rows = [row]
                    elif row[Stats.TAG][0] == 'I':
                        tag_rows.append(row)

                # catch tag at end of file
                if in_tag:
                    self.add(tag_rows)

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
        return 100 * self.num_tagged_tokens / self.num_tokens

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
