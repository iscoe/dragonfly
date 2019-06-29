# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import os


class Notepad:
    """
    Maintain notes related to annotating
    """
    DIR = 'notes'

    def __init__(self, metadata_dir):
        self.dir = os.path.join(metadata_dir, self.DIR)
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

    def save(self, filename, notes):
        filename = os.path.join(self.dir, filename)
        with open(filename, 'w', encoding='utf8') as fp:
            fp.write(notes)

    def load(self, filename):
        filename = os.path.join(self.dir, filename)
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf8') as fp:
                return fp.read()
        return ''
