# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

from dragonfly.command import Runner


if __name__ == '__main__':
    cmd = Runner()
    try:
        cmd.annotate()
    except RuntimeError as e:
        print("Error: {}".format(str(e)))
