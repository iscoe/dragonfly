# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import argparse
import os
from dragonfly import app
from dragonfly.data import FileLister
from dragonfly.indexer import Indexer


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("lang", help="language code")
    parser.add_argument("data", help="directory of tsv files to annotate")
    parser.add_argument("-o", "--output", help="optional output directory for annotations (default is data/annotations")
    parser.add_argument("-d", "--hints", help="optional hints displayed on the transliterations")
    parser.add_argument("-p", "--port", help="optional port to use (default is 5000)")
    parser.add_argument("-e", "--ext", help="optional file extension to match (default is .txt)")
    parser.add_argument("-t", "--tags", help="optional list of tags (default is PER,ORG,GPE,LOC)")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print("Error: {} does not exist".format(args.data))
        quit()
    if not os.path.isdir(args.data):
        print("Error: {} is not a directory".format(args.data))
        quit()

    if not args.output:
        args.output = os.path.join(args.data, 'annotations')
    if not os.path.exists(args.output):
        os.makedirs(args.output)

    if not args.port:
        args.port = 5000

    if not args.ext:
        args.ext = '.txt'

    if not args.tags:
        args.tags = 'PER,ORG,GPE,LOC'
    args.tags = [x.strip().upper() for x in args.tags.split(',')]

    app.config['dragonfly.lang'] = args.lang.lower()
    app.config['dragonfly.input'] = FileLister(args.data, args.ext)
    app.config['dragonfly.output'] = args.output
    app.config['dragonfly.hints'] = args.hints
    app.config['dragonfly.tags'] = args.tags

    # load index - this may take a few seconds with a large index
    index_dir = os.path.join(args.data, '.index')
    app.dragonfly_index = Indexer(index_dir)

    app.logger.info('Loading from {} and saving to {}'.format(args.data, args.output))
    app.run(debug=True, host='0.0.0.0', port=int(args.port))
