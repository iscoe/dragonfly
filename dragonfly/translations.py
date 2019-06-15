# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import os
import json
import csv


class TranslationDictManager(object):
    """
    Translation dictionary manager

    Format of dictionary is a dictionary of lists.
    The key of the dictionary is the source string.
    Each list has two entries: translation string and entity type.
    The entity type may be blank.
    """

    def __init__(self, base_dir):
        self.base_dir = base_dir

    def add(self, lang, source, translation, type):
        source = source.lower()
        type = type.upper()
        trans_dict = self.get(lang)
        trans_dict[source] = [translation, type]
        self.save(lang, trans_dict)

    def delete(self, lang, source):
        source = source.lower()
        trans_dict = self.get(lang)
        if source in trans_dict:
            del trans_dict[source]
            self.save(lang, trans_dict)
            return True
        return False

    def merge(self, lang, td):
        trans_dict = self.get(lang)
        for key in td:
            trans_dict[key] = td[key]

    def get(self, lang):
        trans_dict = {}
        filename = self.get_filename(lang)
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf8') as fp:
                trans_dict = json.load(fp)
        return trans_dict

    def save(self, lang, td):
        filename = self.get_filename(lang)
        with open(filename, 'w', encoding='utf8') as fp:
            json.dump(td, fp)

    def get_filename(self, lang):
        lang = lang.lower()
        return os.path.join(self.base_dir, lang + '.json')

    def export(self, lang, filename):
        trans_dict = self.get(lang)
        count = 0
        with open(filename, 'w', encoding='utf8') as fp:
            for source in trans_dict.keys():
                count += 1
                fp.write("{}\t{}\t{}\n".format(source, *trans_dict[source]))
        return count

    @staticmethod
    def export_external(input_path, output_path):
        filename = input_path
        with open(filename, 'r', encoding='utf8') as ifp, open(output_path, 'w', encoding='utf8') as ofp:
            trans_dict = json.load(ifp)
            count = 0
            for source in trans_dict.keys():
                count += 1
                ofp.write("{}\t{}\t{}\n".format(source, *trans_dict[source]))
        return count

    def import_json(self, lang, data):
        trans_dict = self.get(lang)
        count = 0
        for phrase in data:
            if phrase not in trans_dict:
                trans_dict[phrase] = data[phrase]
                count += 1
        self.save(lang, trans_dict)
        return count

    def import_tsv(self, lang, filename):
        PHRASE, TRANS, TYPE = [0, 1, 2]
        trans_dict = self.get(lang)
        count = 0
        with open(filename, 'r', encoding='utf8') as fp:
            reader = csv.reader(fp, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                if len(row) != 3:
                    print("Warning: row without 3 columns")
                    continue
                if row[PHRASE] not in trans_dict:
                    count += 1
                    trans_dict[row[PHRASE]] = [row[TRANS], row[TYPE]]
        self.save(lang, trans_dict)
        return count
