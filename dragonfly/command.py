# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import argparse
import os
from dragonfly import app
from dragonfly.data import FileLister
from dragonfly.indexer import Indexer


class Runner(object):
    ANNOTATE = 0
    ADJUDICATE = 1

    def __init__(self):
        self.mode = None
        self.debug = False

    def annotate(self):
        self.mode = Runner.ANNOTATE
        args = self._parse_args()
        args = self._process_args(args)
        self._prepare_app(args)
        self._run(args)

    def adjudicate(self):
        self.mode = Runner.ADJUDICATE
        args = self._parse_args()
        args = self._process_args(args)
        self._prepare_app(args)
        self._run(args)

    def _parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("lang", help="language code")
        parser.add_argument("data", help="directory of tsv files to annotate")
        if self.mode == self.ANNOTATE:
            parser.add_argument("-o", "--output",
                            help="optional output directory for annotations (default is data/annotations")
        else:
            parser.add_argument('annotations', nargs='*', help="directories with annotation files")
            parser.add_argument("-o", "--output", help="output directory to store annotations", required=True)
        parser.add_argument("-d", "--hints", help="optional hints displayed on the transliterations")
        parser.add_argument("-p", "--port", help="optional port to use (default is 5000)")
        parser.add_argument("-e", "--ext", help="optional file extension to match (default is .txt)")
        parser.add_argument("-t", "--tags", help="optional list of tags (default is PER,ORG,GPE,LOC)")
        parser.add_argument("--rtl", action='store_true', help="option to display text RTL")
        return parser.parse_args()

    def _process_args(self, args):
        if not os.path.exists(args.data):
            raise RuntimeError("{} does not exist".format(args.data))
        if not os.path.isdir(args.data):
            raise RuntimeError("{} is not a directory".format(args.data))

        if not args.output:
            args.output = os.path.join(args.data, 'annotations')
        if not os.path.exists(args.output):
            os.makedirs(args.output)

        if self.mode == self.ADJUDICATE:
            self._check_adjudicate_args(args)

        if not args.port:
            args.port = 5000

        if not args.ext:
            args.ext = '.txt'

        if not args.tags:
            args.tags = 'PER,ORG,GPE,LOC'
        args.tags = [x.strip().upper() for x in args.tags.split(',')]

        return args

    def _check_adjudicate_args(self, args):
        if len(args.annotations) < 2:
            raise RuntimeError("must specify at least two annotation directories")

        for anno_dir in args.annotations:
            if not os.path.exists(anno_dir):
                raise RuntimeError("directory {} does not exist".format(anno_dir))

    def _prepare_app(self, args):
        app.config['dragonfly.lang'] = args.lang.lower()
        app.config['dragonfly.input'] = FileLister(args.data, args.ext)
        app.config['dragonfly.output'] = args.output
        app.config['dragonfly.hints'] = args.hints
        app.config['dragonfly.tags'] = args.tags
        # for rtl, manually turn off settings for Auto Scrolling Sentence IDs and probably Display Row Labels
        app.config['dragonfly.rtl'] = args.rtl

        if self.mode == self.ADJUDICATE:
            app.config['dragonfly.mode'] = 'adjudicate'
            app.config['dragonfly.annotation_dirs'] = args.annotations
        else:
            app.config['dragonfly.mode'] = 'annotate'

        # load index - this may take a few seconds with a large index
        index_dir = os.path.join(args.data, '.index')
        app.dragonfly_index = Indexer(index_dir)

    def _run(self, args):
        if self.mode == self.ANNOTATE:
            print(" * Annotating {}".format(args.data))
            app.logger.info("Running in annotate mode")
        else:
            print(" * Adjudicating {}".format(args.data))
            app.logger.info("Running in adjudicate mode")
        app.logger.info('Loading from {} and saving to {}'.format(args.data, args.output))
        app.run(debug=self.debug, host='0.0.0.0', port=int(args.port))
