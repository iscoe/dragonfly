#!/usr/bin/env python3

# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import argparse
import csv
import glob
import os
import sys

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))


parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=
"""
Correct annotation files based on a transform file.
The transform file should be 2 columns tab separated with the first being the string of interest.
Case is ignored and the first column can be a multi-token phrase.
The 2nd column is the tag type (Default types are O, PER, ORG, LOC, GPE).
Example:
New York\tGPE
Pastafarian\tO
""")
parser.add_argument("input", help="filename or directory with annotations")
parser.add_argument("transform", help="2 column annotation transform definition")
parser.add_argument("output", help="output directory (will be created if does not exist)")
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

for filename in [args.input, args.transform]:
    if not os.path.exists(filename):
        sys.exit("Error: {} does not exist".format(filename))

if not os.path.exists(args.output):
    os.makedirs(args.output)
elif not os.path.isdir(args.output):
    sys.exit("Error: {} must be a directory".format(args.output))

if os.path.isdir(args.input):
    filenames = [x for x in glob.glob(os.path.join(args.input, "*")) if os.path.isfile(x)]
else:
    filenames = [args.input]


TOKEN = 0
TAG = 1


class Transform(object):
    SEP = '\u2620'

    def __init__(self, row):
        self.string = row[TOKEN]
        self.change = self.set_change(row[TAG])
        self.apply_count = 0

    def set_change(self, value):
        value = value.strip().upper()
        if value in ['DEL', 'DELETE', 'RM', 'REMOVE']:
            value = 'O'
        return value

    def apply(self, rows):
        self.apply_count += 1
        count = 0
        for row in rows:
            if self.change == 'O':
                row[TAG] = self.change
            else:
                if count == 0:
                    row[TAG] = "B-" + self.change
                else:
                    row[TAG] = "I-" + self.change
                count += 1

    def __repr__(self):
        return "Transform({}: {})".format(self.string, self.change)

    @staticmethod
    def key_from_string(string):
        return Transform.SEP.join(string.split(' ')).lower()

    @staticmethod
    def key_from_rows(rows):
        return Transform.SEP.join([x[TOKEN] for x in rows]).lower()


# load transforms
transforms = {}
with open(args.transform, 'r') as fp:
    reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
    for row in reader:
        if len(row) == 2:
            transforms[Transform.key_from_string(row[TOKEN])] = Transform(row)
        elif len(row) != 0:
            print("Unexpected row {}".format(row))

# process each file, writing out as the original is read in
changes_count = 0
for filename in filenames:
    rel_filename = os.path.basename(filename)
    output_filename = os.path.join(args.output, rel_filename)
    with open(filename, 'r') as ifp, open(output_filename, 'w') as ofp:
        in_tag = False
        tag_rows = []
        reader = csv.reader(ifp, delimiter='\t', quoting=csv.QUOTE_NONE)
        writer = csv.writer(ofp, delimiter='\t', lineterminator='\n', quotechar='', quoting=csv.QUOTE_NONE)
        for row in reader:
            if in_tag:
                # tag end (end of sentence, O, or new B-)
                if len(row) < 2 or not row[TAG] or row[TAG][0] != 'I':
                    key = Transform.key_from_rows(tag_rows)
                    if key in transforms:
                        changes_count += 1
                        transforms[key].apply(tag_rows)
                    for r in tag_rows:
                        writer.writerow(r)
                    in_tag = False
                    tag_rows = []

            # sentence separator
            if len(row) < 2 or not row[TAG]:
                writer.writerow([])
                continue

            # write out O rows and store tag rows
            if row[TAG][0] == 'B':
                in_tag = True
                tag_rows = [row]
            elif row[TAG][0] == 'I':
                tag_rows.append(row)
            else:
                writer.writerow(row)

        # catch tag at end of file
        if in_tag:
            key = Transform.key_from_rows(tag_rows)
            if key in transforms:
                changes_count += 1
                transforms[key].apply(tag_rows)
                for r in tag_rows:
                    writer.writerow(r)

print("{} files processed".format(len(filenames)))
print("{} changes".format(changes_count))
for transform in transforms.values():
    print("{}: {}".format(transform.string, transform.apply_count))
