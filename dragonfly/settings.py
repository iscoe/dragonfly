# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import collections
import os
import json


class SettingsManager:
    # these strings are synced with the javascript
    DEFAULTS = [
        ('GMaps Key', ''),
        ('GMaps Params', '8.6, 80.1, 8'),
        ('Geonames Username', ''),
        ('Column Width', 40),
        ('Finder Height', 200),
        ('Finder Starts Open', False),
        ('Auto Save', False),
        ('Auto Save On Nav', False),
        ('Auto Scrolling Sentence IDs', True),
        ('Display Row Labels', True),
        ('Cascade By Default', True),
    ]

    SETTINGS_FILENAME = 'settings.json'

    def __init__(self, base_dir):
        self.filename = os.path.join(base_dir, self.SETTINGS_FILENAME)
        if not os.path.exists(self.filename):
            self.save(self.DEFAULTS)
        self.settings = {}

    def load(self):
        self.settings = collections.OrderedDict([(item[0], item[1]) for item in self.DEFAULTS])
        with open(self.filename, 'r') as fp:
            local_settings = json.load(fp)
            for key in self.settings.keys():
                if key in local_settings:
                    self.settings[key] = local_settings[key]

    def save(self, settings):
        with open(self.filename, 'w') as fp:
            string = json.dumps(settings, sort_keys=True, indent=4, separators=(',', ': '))
            fp.write(string)

    def get_column_width(self):
        return int(self.settings['Column Width'])

    def get_gmaps_key(self):
        return self.settings['GMaps Key']

    def get_geonames_username(self):
        return self.settings['Geonames Username']
