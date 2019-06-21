# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import collections
import copy
import os
import json

"""
Settings Manager

The settings strings mush be synchronized with the javascript library
"""


class SettingsDefaults:
    GLOBAL = [
        ('GMaps Key', ''),
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

    LOCAL = [
        ('GMaps Params', '0, 0, 2'),
        ('Geonames County Codes', ''),
    ]


class SettingsManager:
    SETTINGS_FILENAME = 'settings.json'

    def __init__(self, base_dir, defaults):
        self.filename = os.path.join(base_dir, self.SETTINGS_FILENAME)
        self.defaults = collections.OrderedDict([(item[0], item[1]) for item in defaults])
        if not os.path.exists(self.filename):
            self.save(self.defaults)
        self.settings = collections.OrderedDict()

    def load(self):
        self.settings = copy.copy(self.defaults)
        with open(self.filename, 'r') as fp:
            loaded_settings = json.load(fp)
            for key in self.settings.keys():
                if key in loaded_settings:
                    self.settings[key] = loaded_settings[key]

    def save(self, settings):
        save_settings = {k: settings[k] for k in self.defaults.keys()}
        with open(self.filename, 'w') as fp:
            string = json.dumps(save_settings, sort_keys=True, indent=4, separators=(',', ': '))
            fp.write(string)

    @property
    def text_settings(self):
        return collections.OrderedDict([(k, v) for k, v in self.settings.items() if type(v) != bool])

    @property
    def bool_settings(self):
        return collections.OrderedDict([(k, v) for k, v in self.settings.items() if type(v) == bool])


class GlobalSettingsManager(SettingsManager):
    def __init__(self, base_dir):
        super().__init__(base_dir, SettingsDefaults.GLOBAL)

    def get_geonames_username(self):
        return self.settings['Geonames Username']


class LocalSettingsManager(SettingsManager):
    def __init__(self, base_dir):
        super().__init__(base_dir, SettingsDefaults.LOCAL)

    def get_geonames_country_codes(self):
        return self.settings['Geonames County Codes']
