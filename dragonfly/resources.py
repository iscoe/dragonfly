# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import copy
from .components import Hints, Notepad, SentenceMarkerManager, Stats
from .data import OutputWriter
from .recommend import Recommender, TaggedTokenFrequencies
from .search import DictionarySearch, GeonamesSearch, LocalSearch, PhrasesSearch
from .settings import GlobalSettingsManager, LocalSettingsManager
from .translations import TranslationDictManager


class ResourceLocator:
    """
    Gets a resource for dependency injection or other uses.

    Understands how to create resources based on configuration.
    Understands when to create a new instance and when to use a cached instance
    """
    def __init__(self, config):
        self.config = config
        self.hints = Hints(config.get('dragonfly.local_md_dir'))
        self.notepad = Notepad(config.get('dragonfly.local_md_dir'))
        self.output_writer = OutputWriter(config.get('dragonfly.output'))
        self.tag_frequencies = TaggedTokenFrequencies(config.get('dragonfly.local_md_dir'))
        self._dictionary_search = None
        self._phrases_search = None
        self._local_search = None
        self._recommender = None
        self._translation_manager = None
        self._marker_manager = None

    @property
    def stats(self):
        return Stats()

    @property
    def settings(self):
        # not cached as as settings can change during runtime
        global_md_dir = self.config.get('dragonfly.global_md_dir')
        gsm = GlobalSettingsManager(global_md_dir)
        gsm.load()
        local_md_dir = self.config.get('dragonfly.local_md_dir')
        lsm = LocalSettingsManager(local_md_dir)
        lsm.load()
        all_settings = copy.copy(gsm.settings)
        all_settings.update(lsm.settings)
        return all_settings

    @property
    def dictionary_search(self):
        # cached
        if self._dictionary_search is None:
            self._dictionary_search = DictionarySearch(self.config.get('dragonfly.local_md_dir'))
        return self._dictionary_search

    @property
    def phrases_search(self):
        # cached
        if self._phrases_search is None:
            self._phrases_search = PhrasesSearch(self.config.get('dragonfly.local_md_dir'))
        return self._phrases_search

    @property
    def geonames_search(self):
        # not cached as user may change country settings
        settings = self.settings
        countries = []
        if settings['Geonames County Codes']:
            countries = [code.strip().upper() for code in settings['Geonames County Codes'].split(',')]
        return GeonamesSearch(settings['Geonames Username'], countries=countries)

    @property
    def local_search(self):
        # cached
        if self._local_search is None:
            data_dir = self.config.get('dragonfly.data_dir')
            local_md_dir = self.config.get('dragonfly.local_md_dir')
            self._local_search = LocalSearch(data_dir, local_md_dir)
        return self._local_search

    @property
    def recommender(self):
        # cached
        if self._recommender is None:
            input_files = self.config.get('dragonfly.input').filenames
            anno_dir = self.config.get('dragonfly.output')
            md_dir = self.config.get('dragonfly.local_md_dir')
            self._recommender = Recommender(input_files, anno_dir, md_dir)
        return self._recommender

    @property
    def translation_manager(self):
        # cached
        if self._translation_manager is None:
            self._translation_manager = TranslationDictManager(self.config.get('dragonfly.global_md_dir'))
        return self._translation_manager

    @property
    def marker_manager(self):
        # cached
        if self._marker_manager is None:
            self._marker_manager = SentenceMarkerManager(self.config.get('dragonfly.local_md_dir'))
        return self._marker_manager
