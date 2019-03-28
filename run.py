# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
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
    parser.add_argument("path", help="tsv filename or directory of tsv files to annotate")
    parser.add_argument("-o", "--output", help="optional output directory to store annotations")
    parser.add_argument("-a", "--annotations", help="optional saved annotations for the file or directory")
    parser.add_argument("-d", "--hints", help="optional hints displayed on the transliterations")
    parser.add_argument("-p", "--port", help="optional port to use (default is 5000)")
    parser.add_argument("-e", "--ext", help="optional file extension to match (default is .txt)")
    parser.add_argument("-t", "--tags", help="optional list of tags (default is PER,ORG,GPE,LOC)")
    args = parser.parse_args()

    if args.output:
        output_dir = args.output
    else:
        if os.path.isdir(args.path):
            output_dir = os.path.join(args.path, 'annotations')
        else:
            output_dir = os.path.join(os.path.dirname(args.path), 'annotations')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    if not os.path.exists(args.path):
        print("Error: {} does not exist".format(args.path))
        quit()

    if not args.annotations and os.path.isdir(args.path):
        args.annotations = output_dir

    if not args.port:
        args.port = 5000

    if not args.ext:
        args.ext = '.txt'

    if not args.tags:
        args.tags = 'PER,ORG,GPE,LOC'
    tags = [x.strip().upper() for x in args.tags.split(',')]

    if os.path.isdir(args.path):
        index_dir = os.path.join(args.path, '.index')
    else:
        index_dir = None

    app.config['dragonfly.lang'] = args.lang.lower()
    app.config['dragonfly.output'] = output_dir
    app.config['dragonfly.input'] = FileLister(args.path, args.ext)
    app.config['dragonfly.annotations'] = args.annotations
    app.config['dragonfly.hints'] = args.hints
    app.config['dragonfly.tags'] = tags

    # load index - this may take a few seconds with a large index
    app.dragonfly_index = Indexer(index_dir)

    app.logger.info('Loading from {} and saving to {}'.format(args.path, output_dir))
    app.run(debug=True, host='0.0.0.0', port=int(args.port))
