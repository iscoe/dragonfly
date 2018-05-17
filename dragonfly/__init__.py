# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

from flask import Flask
import logging
import logging.handlers
import sys
import os
from .translations import TranslationDictManager


app = Flask(__name__)
try:
    handler = logging.handlers.RotatingFileHandler('logs/dragonfly.log', 'a', 1 * 1024 * 1024, 5)
except FileNotFoundError:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.getLevelName('INFO'))

# make a .dragonfly directory for storing settings, dictionaries, and indexes
home_dir = os.path.join(os.path.expanduser("~"), '.dragonfly')
if not os.path.exists(home_dir):
    os.makedirs(home_dir)
app.config['dragonfly.home_dir'] = home_dir

from .views import *
