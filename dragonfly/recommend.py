# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import collections
import copy
import csv
import fnmatch
import glob
import os
import pickle
import random


FileStat = collections.namedtuple('FileStat', 'sentences words')

Recommendation = collections.namedtuple('Recommendation', 'name config items')

RecommendItem = collections.namedtuple('RecommendItem', 'doc path sentences words score')


class RecommendConfig:
    def __init__(self, form):
        self.words = form['words']
        self.length_penalty = 'length_penalty' in form
        self.exact_match = 'exact_match' in form
        self.news_only = 'news_only' in form

    def export(self):
        return dict(
            words=self.words,
            length_penalty=self.length_penalty,
            exact_match=self.exact_match,
            news_only=self.news_only
        )

    @classmethod
    def get_empty(cls):
        return RecommendConfig({'words': []})


class Recommender:
    """
    Recommendations of what documents to annotate next.

    Two default recommendations are random and natural.
    """
    FILE_STATS = '.file.stats'
    FILE_LATEST = '.latest'
    LATEST = 'Latest'
    NATURAL = 'Natural'
    RANDOM = 'Random'
    NEWS_ID = '_NW_'

    def __init__(self, filenames, annotation_dir, metadata_dir):
        self.content_files = filenames
        self.annotations_dir = annotation_dir
        self.rec_dir = os.path.join(metadata_dir, 'recommendations')
        if not os.path.exists(self.rec_dir):
            os.mkdir(self.rec_dir)
        self._list = []

    @property
    def list(self):
        if not self._list:
            self._load_rec_list()
        return self._list

    def get_latest(self, include_complete=False):
        name = self._get_latest()
        if name:
            return self.get(name, include_complete)
        else:
            return self.get(self.NATURAL, include_complete)

    def get(self, name, include_complete=False):
        """
        Get a recommendation
        :param name: Name of a recommendation
        :param include_complete: Whether to include already annotated files
        :return: Recommendation
        """
        rec = self._load_rec(name)
        if not rec:
            rec = self._load_rec(self.NATURAL)
        if not include_complete:
            annotated_files = [os.path.basename(x)[:-5] for x in glob.glob(os.path.join(self.annotations_dir, '*.anno'))]
            rec = Recommendation(rec.name, rec.config, [x for x in rec.items if x.doc not in annotated_files])
        self._set_latest(rec.name)
        return rec

    def build(self, name, config):
        config_words = self._prepare_words(config.words)
        stats = self._get_file_stats()
        items = []
        for filename in self.content_files:
            score = 0
            tokens = []
            with open(filename, 'r', encoding='utf8') as fp:
                if config.news_only and self.NEWS_ID not in filename:
                    continue
                reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row in reader:
                    # sentence separator
                    if len(row) < 1:
                        continue
                    tokens.append(row[0].lower())
            for word in config_words:
                matches = fnmatch.filter(tokens, word)
                score += len(matches)
            if not config.exact_match:
                for word in config_words:
                    matches = fnmatch.filter(tokens, word + '*')
                    score += (len(matches) / 2)
            score /= len(tokens)
            score *= 100
            if config.length_penalty:
                score = self._penalize_score(score, stats[filename].sentences)
            item = RecommendItem(os.path.basename(filename), filename, stats[filename].sentences, stats[filename].words, score)
            items.append(item)
        items.sort(key=lambda x: x.score, reverse=True)
        rec = Recommendation(name, config, items)
        rec_filename = os.path.join(self.rec_dir, name + '.rec')
        with open(rec_filename, 'wb') as fp:
            pickle.dump(rec, fp)
        self._list = []

    def _get_file_stats(self):
        stats = {}
        stats_filename = os.path.join(self.rec_dir, self.FILE_STATS)
        if os.path.exists(stats_filename):
            with open(stats_filename, 'rb') as fp:
                stats = pickle.load(fp)
        if len(stats) != len(self.content_files):
            for filename in self.content_files:
                with open(filename, 'r', encoding='utf8') as fp:
                    reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
                    num_words = 0
                    num_sentences = 1
                    for row in reader:
                        # sentence separator
                        if len(row) < 1:
                            num_sentences += 1
                            continue
                        num_words += 1
                    stats[filename] = FileStat(num_sentences, num_words)
            with open(stats_filename, 'wb') as fp:
                pickle.dump(stats, fp)
        return stats

    def _set_latest(self, name):
        with open(os.path.join(self.rec_dir, self.FILE_LATEST), 'w') as fp:
            fp.write(name)

    def _get_latest(self):
        path = os.path.join(self.rec_dir, self.FILE_LATEST)
        if os.path.exists(path):
            with open(path, 'r') as fp:
                return fp.read()

    def _load_rec_list(self):
        self._list = [self.NATURAL, self.RANDOM]
        self._list.extend(sorted([os.path.basename(x)[:-4] for x in glob.glob(os.path.join(self.rec_dir, '*.rec'))], key=str.lower))

    def _load_rec(self, name):
        if name == self.NATURAL:
            stats = self._get_file_stats()
            items = [RecommendItem(os.path.basename(file), file, stats[file].sentences, stats[file].words, 0) for file in self.content_files]
            rec = Recommendation(name, RecommendConfig.get_empty(), items)
        elif name == self.RANDOM:
            stats = self._get_file_stats()
            file_list = copy.copy(self.content_files)
            random.shuffle(file_list)
            items = [RecommendItem(os.path.basename(file), file, stats[file].sentences, stats[file].words, 0) for file in file_list]
            rec = Recommendation(name, RecommendConfig.get_empty(), items)
        else:
            with open(os.path.join(self.rec_dir, name + '.rec'), 'rb') as fp:
                rec = pickle.load(fp)
        return rec

    @staticmethod
    def _prepare_words(s):
        return [x.lower() for x in s.split()]

    @staticmethod
    def _penalize_score(score, num_sentences):
        if num_sentences > 20:
            # score divided in half when 50 sentences
            return score / (1 + (num_sentences - 20) / 30)
        else:
            return score
