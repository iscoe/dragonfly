# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

import flask
import os
import timeit
from .components import SentenceMarkerManager
from .data import InputReader, Document, AnnotationLoader, EnglishTranslationLoader
from .search import DocumentStats


class AnnotateAttacher:
    """
    Attach a single set of annotations when annotating
    """
    def attach(self, document, output_path, filename):
        loader = AnnotationLoader(output_path)
        annotations_filename = loader.get(filename)
        if annotations_filename:
            document.attach_annotations(InputReader(annotations_filename).sentences)


class AdjudicateAttacher:
    """
    Attach multiple sets of annotations when adjudicating
    """
    def __init__(self, annotations_dirs):
        self.annotations_dirs = annotations_dirs

    def attach(self, document, output_path, filename):
        # todo How to handle partially complete dir of adjudicated files
        loader = AnnotationLoader(output_path)
        annotations_filename = loader.get(filename)
        if annotations_filename:
            document.attach_annotations(InputReader(annotations_filename).sentences)
        else:
            display_annotation_dir = self.annotations_dirs[0]
            loader = AnnotationLoader(display_annotation_dir)
            annotations_filename = loader.get(filename)
            if annotations_filename:
                document.attach_annotations(InputReader(annotations_filename).sentences)

        self.annotations_dirs.reverse()
        for annotations_dir in self.annotations_dirs:
            loader = AnnotationLoader(annotations_dir)
            annotations_filename = loader.get(filename)
            if annotations_filename:
                name = os.path.basename(annotations_dir)
                document.attach_adj_annotations(name, InputReader(annotations_filename).sentences)


class DocumentRenderer:
    def __init__(self, attacher, modes):
        self.attacher = attacher
        self.modes = modes

    def render(self, app, filename, index):
        start_time = timeit.default_timer()
        lang = app.config.get('dragonfly.lang')
        lister = app.config.get('dragonfly.input')
        output_path = app.config.get('dragonfly.output')
        suggest = app.config.get('dragonfly.suggest')

        settings = app.locator.settings
        lister.reload()
        # if clicking next with rec order on, only use those files
        if filename is None and settings['Use Recommendation Order']:
            rec = app.locator.recommender.get_latest(True)
            lister.filenames = [x.path for x in rec.items]
        index, next_index = self._get_file_indexes(index, lister, filename)
        if index is None:
            return None
        filename = lister.get_filename(index)
        # remove any path information
        local_filename = os.path.basename(filename)

        reader = InputReader(filename)
        document = Document(filename, reader.sentences, reader.terminal_blank_line)

        self.attacher.attach(document, output_path, filename)

        trans_loader = EnglishTranslationLoader(lister.path)
        translation = trans_loader.get(filename)
        if translation:
            document.attach_translation(translation)

        marker_manager = SentenceMarkerManager(app.config.get('dragonfly.local_md_dir'))
        document.attach_markers(marker_manager.get(local_filename))

        if suggest:
            document.convert_row_to_suggestions(suggest)
        else:
            freqs = app.locator.tag_frequencies
            for sentence in document.sentences:
                row = sentence.rows[0]
                row.set_suggestions([freqs.get_percentage(x) for x in row.strings])

        if app.locator.local_search.loaded:
            try:
                doc_stats = DocumentStats(document, app.locator.local_search.index)
            except RuntimeError as e:
                return str(e)
        else:
            doc_stats = None

        content = flask.render_template('annotate.html', title=local_filename, document=document,
                                        index=index, next_index=next_index, lang=lang, modes=self.modes,
                                        filename=local_filename, doc_stats=doc_stats)
        total_time = timeit.default_timer() - start_time
        app.logger.info('Serving %s in %1.2fs', filename, total_time)
        return content

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
