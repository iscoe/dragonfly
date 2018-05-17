#!/usr/bin/env python3

# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

#
# Pack data to be annotated into larger files
#
# usage: pack.py input_dir output_dir min_num_tokens
#

import argparse
import glob
import json
import os
import sys

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))

parser = argparse.ArgumentParser()
parser.add_argument("input", help="input directory with files to annotate")
parser.add_argument("output", help="output directory to put packed files")
parser.add_argument("min_tokens", help="minimum number of tokens per file", type=int)
args = parser.parse_args()

if not os.path.isdir(args.input):
    sys.exit("Error: {} does not exist".format(args.input))

if not os.path.exists(args.output):
    os.makedirs(args.output)

basename = None
lines = []
files = []
count = 1
metadata = {}
for filename in sorted(glob.glob(os.path.join(args.input, "*.txt"))):
    # grab first 6 characters: IL6_NW
    if basename is None:
        basename = os.path.basename(filename)[0:6]

    with open(filename, 'r') as ifp:
        new_lines = [x for x in ifp]
        # must have an empty line at end of file
        if len(new_lines[-1].split('\t')) > 2:
            new_lines.append('\n')
        # remove tsv header after first file
        if len(lines) > 0 and new_lines[0][0:5] == 'TOKEN':
            del new_lines[0]
        num_lines = len(new_lines)
        # we don't write out header to annotation file
        if len(lines) == 0:
            num_lines -= 1

        files.append({'filename': os.path.basename(filename), 'num_lines': num_lines})
        lines.extend(new_lines)

    if len(lines) > args.min_tokens:
        out_filename = os.path.join(args.output, "{}_{:03d}.txt".format(basename, count))
        with open(out_filename, 'w') as ofp:
            ofp.writelines(lines)
        metadata[os.path.basename(out_filename)] = files
        lines = []
        files = []
        count += 1

with open(os.path.join(args.output, '.metadata'), 'w') as mfp:
    json.dump(metadata, mfp)
