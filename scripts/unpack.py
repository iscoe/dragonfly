#!/usr/bin/env python3

# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

#
# Unpack annotation files based on original file size
#
# usage: unpack.py input_dir output_dir
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
parser.add_argument("input", help="input directory with annotation files")
parser.add_argument("output", help="output directory to unpack the annotations")
args = parser.parse_args()

if not os.path.isdir(args.input):
    sys.exit("Error: {} does not exist".format(args.input))

if not os.path.exists(args.output):
    os.makedirs(args.output)

metadata_dir = os.path.abspath(os.path.join(args.input, os.pardir))
with open(os.path.join(metadata_dir, '.metadata'), 'r') as mfp:
    metadata = json.load(mfp)
    if metadata is None:
        sys.exit("Error: .metadata is missing")

for filename in sorted(glob.glob(os.path.join(args.input, "*.anno"))):
    orig_filename = filename.replace('.anno', '')
    with open(filename, 'r') as ifp:
        lines = [x for x in ifp]
        for data in metadata[os.path.basename(orig_filename)]:
            new_filename = os.path.join(args.output, data['filename'] + '.anno')
            new_lines = lines[0:data['num_lines']]
            del lines[:data['num_lines']]
            with open(new_filename, 'w') as ofp:
                ofp.writelines(new_lines)
