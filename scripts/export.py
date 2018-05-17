#!/usr/bin/env python3

# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

#
# Export a translation dictionary
#
# usage: export.py lang
#
# It writes the file lang.tsv to the current directory.
# The file has 3 columns: source, translation, entity type
#

import argparse
import os
import sys

# forgive me father, for I have sinned
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import dragonfly

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))

parser = argparse.ArgumentParser()
parser.add_argument("lang", help="3 letter language code")
parser.add_argument("-f", "--force", help="force an overwrite of local file", action="store_true")
args = parser.parse_args()

args.lang = args.lang.lower()
output_filename = "{}.tsv".format(args.lang)
if os.path.exists(output_filename) and not args.force:
    sys.exit("Error: {} already exists. Run with -f to force it to overwrite".format(output_filename))

home_dir = os.path.join(os.path.expanduser("~"), '.dragonfly')
tdm = dragonfly.TranslationDictManager(home_dir)
num_items = tdm.export(args.lang, output_filename)
print("Exported {} items".format(num_items))
