# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import sys
from dragonfly.command import Runner

MIN_PYTHON = (3, 0)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.\n".format(*MIN_PYTHON))

if __name__ == '__main__':
    cmd = Runner()
    try:
        cmd.annotate()
    except RuntimeError as e:
        print("Error: {}".format(str(e)))
