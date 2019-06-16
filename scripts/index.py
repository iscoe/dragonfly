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
import os
import sys

# don't assume the user has installed dragonfly
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import dragonfly.search as search

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))

parser = argparse.ArgumentParser()
parser.add_argument("input", help="directory being annotated")
args = parser.parse_args()

if not os.path.isdir(args.input):
    sys.exit("Not a directory")

indexer = search.Indexer(args.input)
indexer.build()
indexer.save()
