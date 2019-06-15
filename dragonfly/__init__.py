# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

from flask import Flask
import logging
import logging.handlers
import os


app = Flask(__name__)

# log to file in dragonfly/logs directory
log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'logs')
log_dir = os.path.abspath(log_dir)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = os.path.join(log_dir, 'dragonfly.log')
handler = logging.handlers.RotatingFileHandler(log_filename, 'a', 1 * 1024 * 1024, 5)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.getLevelName('INFO'))

# make a .dragonfly directory for storing settings, dictionaries, and indexes
home_dir = os.path.join(os.path.expanduser("~"), '.dragonfly')
if not os.path.exists(home_dir):
    os.makedirs(home_dir)
app.config['dragonfly.home_dir'] = home_dir

from .views import *
