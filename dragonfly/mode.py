# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import flask
import json
import os
from .data import InputReader, Document, AnnotationLoader, EnglishTranslationLoader, SentenceMarkerManager
from .settings import SettingsManager


class ModeManager(object):
    ANNOTATE = "annotate"
    ADJUDICATE = "adjudicate"

    def __init__(self, mode):
        if mode == self.ANNOTATE:
            self.mode = self.ANNOTATE
        else:
            self.mode = self.ADJUDICATE

    def render(self, app, filename, index):
        lang = app.config.get('dragonfly.lang')
        lister = app.config.get('dragonfly.input')
        tags = app.config.get('dragonfly.tags')
        home_dir = app.config.get('dragonfly.home_dir')
        output_path = app.config.get('dragonfly.output')
        rtl = app.config.get('dragonfly.rtl')
        settings_manager = SettingsManager(home_dir)
        settings_manager.load()

        index, next_index = self._get_file_indexes(index, lister, filename)
        if index is None:
            return None
        filename = lister.get_filename(index)
        app.logger.info('Serving ' + filename)
        # remove any path information
        title = os.path.basename(filename)

        reader = InputReader(filename)
        document = Document(filename, reader.sentences, reader.terminal_blank_line)

        if self.mode == self.ANNOTATE:
            self._attach_single_annotations(document, output_path, filename)
        else:
            annotations_dirs = app.config.get('dragonfly.annotation_dirs')
            self._attach_multiple_annotations(document, output_path, filename, annotations_dirs)

        trans_loader = EnglishTranslationLoader(lister.path)
        translation = trans_loader.get(filename)
        if translation:
            document.attach_translation(translation)

        marker_manager = SentenceMarkerManager(app.config.get('dragonfly.data_dir'))
        document.attach_markers(marker_manager.get(title))

        return flask.render_template('annotate.html', title=title, document=document,
                                     index=index, next_index=next_index, rtl=rtl,
                                     sm=settings_manager, lang=lang, tags=json.dumps(tags))

    def _attach_single_annotations(self, document, output_path, filename):
        loader = AnnotationLoader(output_path)
        annotations_filename = loader.get(filename)
        if annotations_filename:
            document.attach_annotations(InputReader(annotations_filename).sentences)

    def _attach_multiple_annotations(self, document, output_path, filename, annotations_dirs):
        # todo How to handle partially complete dir of adjudicated files
        loader = AnnotationLoader(output_path)
        annotations_filename = loader.get(filename)
        if annotations_filename:
            document.attach_annotations(InputReader(annotations_filename).sentences)
        else:
            display_annotation_dir = annotations_dirs[0]
            loader = AnnotationLoader(display_annotation_dir)
            annotations_filename = loader.get(filename)
            if annotations_filename:
                document.attach_annotations(InputReader(annotations_filename).sentences)

        annotations_dirs.reverse()
        for annotations_dir in annotations_dirs:
            loader = AnnotationLoader(annotations_dir)
            annotations_filename = loader.get(filename)
            if annotations_filename:
                name = os.path.basename(annotations_dir)
                document.attach_adj_annotations(name, InputReader(annotations_filename).sentences)

    def _get_file_indexes(self, index, lister, filename):
        # filename takes priority over index
        if filename:
            index = lister.get_index_from_filename(filename)
            if index is None:
                return None, None
        index = int(index) if index is not None else 0
        if index not in lister:
            return None, None
        next_index = None
        if lister.has_next(index):
            next_index = index + 1
        return index, next_index
