# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import argparse
import json
import logging
import os
import re
from . import app
from .data import FileLister
from .resources import ResourceLocator


class PrefixMiddleware(object):

    def __init__(self, web_app, prefix=''):
        self.app = web_app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["Bad request. Check configuration.".encode()]


class Runner:
    ANNOTATE = 0
    ADJUDICATE = 1

    def __init__(self):
        self.cmd = None

    def annotate(self):
        self.cmd = Runner.ANNOTATE
        args = self._parse_args()
        args = self._process_args(args)
        self._prepare_app(args)
        self._run(args)

    def adjudicate(self):
        self.cmd = Runner.ADJUDICATE
        args = self._parse_args()
        args = self._process_args(args)
        self._prepare_app(args)
        self._run(args)

    def _parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("lang", help="language code")
        parser.add_argument("data", help="directory of tsv files to annotate")
        if self.cmd == self.ANNOTATE:
            parser.add_argument("-o", "--output", help="optional output directory for annotations (default is data/annotations")
        else:
            parser.add_argument('annotations', nargs='*', help="directories with annotation files")
            parser.add_argument("-o", "--output", help="output directory to store annotations", required=True)
        parser.add_argument("-p", "--port", help="optional port to use (default is 5000)")
        parser.add_argument("-e", "--ext", help="optional file extension to match (default is .txt)")
        parser.add_argument("-t", "--tags", help="optional list of tags (default is PER,ORG,GPE,LOC)")
        parser.add_argument("--prefix", help="optional URL prefix for web server")
        parser.add_argument("--rtl", action='store_true', help="option to display text RTL")
        parser.add_argument("--simple", action='store_true', help="optionally simplify UI")
        parser.add_argument("--debug", action='store_true', help="option to run in debug mode")
        parser.add_argument("--suggest", help="optional row to turn into suggestions")
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

        if self.cmd == self.ADJUDICATE:
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
        app.config['dragonfly.data_dir'] = args.data
        app.config['dragonfly.input'] = FileLister(args.data, args.ext)
        app.config['dragonfly.output'] = args.output
        app.config['dragonfly.tags'] = args.tags
        app.config['dragonfly.suggest'] = args.suggest

        modes = set()
        if args.rtl:
            modes.add('rtl')
        if args.simple:
            modes.add('simple')
        app.config['dragonfly.modes'] = modes

        # if we're running in a sub-directory
        if args.prefix:
            prefix = args.prefix
            if prefix[0] != '/':
                prefix = '/' + prefix
            app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=prefix)

        # make a global .dragonfly metadata directory for storing settings and dictionaries
        global_md_dir = os.path.join(os.path.expanduser("~"), '.dragonfly')
        if not os.path.exists(global_md_dir):
            os.makedirs(global_md_dir)
        app.config['dragonfly.global_md_dir'] = global_md_dir

        # make a local .dragonfly metadata directory for storing search index, settings, and other dataset items
        local_md_dir = os.path.join(os.path.expanduser(app.config['dragonfly.data_dir']), '.dragonfly')
        if not os.path.exists(local_md_dir):
            os.makedirs(local_md_dir)
        app.config['dragonfly.local_md_dir'] = local_md_dir

        if self.cmd == self.ADJUDICATE:
            app.config['dragonfly.cmd'] = 'adjudicate'
            app.config['dragonfly.annotation_dirs'] = args.annotations
        else:
            app.config['dragonfly.cmd'] = 'annotate'

        app.locator = ResourceLocator(app.config)
        app.locator.local_search.load_index(bg=True, build=True)

        self.suppress_dict_labels = app.locator.settings['Suppress Dictionary Labels']
        app.jinja_env.filters['preprocess_text'] = self._preprocess_text
        app.jinja_env.filters['convert_to_json'] = self._convert_to_json
        app.jinja_env.filters['regex_replace'] = self._regex_replace
        app.jinja_env.globals.update(calc_column_width=self._calc_column_width)

    @staticmethod
    def _config_debug_logging():
        # this matches the werkzeug format
        handler = logging.StreamHandler()
        f = logging.Formatter('127.0.0.1 - - [%(asctime)s] %(levelname)s: %(message)s', datefmt='%d/%b/%Y %H:%M:%S')
        handler.setFormatter(f)
        handler.setLevel(logging.INFO)
        for logger in [logging.getLogger('flask.app'), logging.getLogger('dragonfly')]:
            logger.addHandler(handler)

    @staticmethod
    def _convert_to_json(value):
        return json.dumps(value)

    @staticmethod
    def _regex_replace(s, pattern, repl):
        return re.sub(pattern, repl, s)

    def _preprocess_text(self, value):
        if self.suppress_dict_labels:
            value = re.sub(r'BEN_[^|]*', '', value)
            value = re.sub(r'[A-Z]{2,3}_', '', value)
            value = value.replace(' | |', '')
        return value

    @staticmethod
    def _calc_column_width(rows, index, max_column_width):
        token_length = len(rows[0].strings[index])
        widest_value = max([len(x.strings[index]) for x in rows])
        return min([int(3 * token_length), max_column_width])

    def _run(self, args):
        if self.cmd == self.ANNOTATE:
            print(" * Annotating {}".format(args.data))
            app.logger.info("Running annotate command")
        else:
            print(" * Adjudicating {}".format(args.data))
            app.logger.info("Running adjudicate command")
        app.logger.info('Loading from %s and saving to %s', args.data, args.output)
        if args.debug:
            self._config_debug_logging()
            # working around a bug in flask that prevents template reloading in debug mode
            app.jinja_env.auto_reload = True
        app.run(debug=args.debug, host='0.0.0.0', port=int(args.port))
