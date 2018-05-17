# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import os
import json


class SettingsManager(object):
    # these strings are synced with the javascript
    DEFAULTS = {
        'Column Width': 40,
        'Auto Scrolling Sentence IDs': True,
        'Display Row Labels': True,
        'Auto Save': False
    }

    SETTINGS_FILENAME = 'settings.json'

    def __init__(self, base_dir):
        self.filename = os.path.join(base_dir, self.SETTINGS_FILENAME)
        if not os.path.exists(self.filename):
            self.save(self.DEFAULTS)
        self.settings = {}

    def load(self):
        with open(self.filename, 'r') as fp:
            self.settings = json.load(fp)
            for key in self.DEFAULTS.keys():
                if key not in self.settings:
                    self.settings[key] = self.DEFAULTS[key]

    def save(self, settings):
        with open(self.filename, 'w') as fp:
            string = json.dumps(settings, sort_keys=True, indent=4, separators=(',', ': '))
            fp.write(string)

    def get_column_width(self):
        return int(self.settings['Column Width'])
