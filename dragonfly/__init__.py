# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

from flask import Flask
import logging.config
import os

__version__ = '1.4.dev'


# log to file in dragonfly/logs directory
log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir, 'logs')
log_dir = os.path.abspath(log_dir)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = os.path.join(log_dir, 'dragonfly.log')

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'basic': {
            'format': '%(message)s',
        },
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'basic',
        },
        'dragonfly.log': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': log_filename,
            'maxBytes': 1 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'INFO',
        },
    },
    'loggers': {
        'flask.app': {
            'handlers': ['dragonfly.log'],
        },
        'dragonfly': {
            'handlers': ['dragonfly.log'],
        },
        'werkzeug': {
            'handlers': ['console'],
        }
    },
    'root': {
        'level': 'INFO',
    },
})

app = Flask(__name__)

# make a .dragonfly directory for storing settings, dictionaries, and indexes
home_dir = os.path.join(os.path.expanduser("~"), '.dragonfly')
if not os.path.exists(home_dir):
    os.makedirs(home_dir)
app.config['dragonfly.home_dir'] = home_dir

from .views import *
