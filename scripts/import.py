#!/usr/bin/env python3

# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

#
# Import a translation dictionary
#
# usage: import.py lang filename
# example: ./import.py tir tir.tsv
#
# TSV file is 3 columns separated by tabs: phrase, translation, entity type
# "None" can be used as an entity type.
#

import argparse
import os
import sys

# don't assume the user has install dragonfly
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, 'dragonfly'))
import translations

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))

parser = argparse.ArgumentParser()
parser.add_argument("lang", help="3 letter language code")
parser.add_argument("filename", help="tsv filename")
args = parser.parse_args()

if not os.path.exists(args.filename):
    sys.exit("Error: {} does not exist".format(args.filename))

args.lang = args.lang.lower()
home_dir = os.path.join(os.path.expanduser("~"), '.dragonfly')
tdm = translations.TranslationDictManager(home_dir)
num_items = tdm.import_tsv(args.lang, args.filename)
print("Imported {} items".format(num_items))
