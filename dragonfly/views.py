# Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

from dragonfly import app
import flask
import json
import os
from .data import InputReader, Document, OutputWriter, AnnotationLoader, HintLoader, TranslationLoader
from .indexer import Indexer
from .settings import SettingsManager
from .translations import TranslationDictManager


@app.route('/', defaults={'filename': None})
@app.route('/<filename>')
def index(filename):
    lang = app.config.get('dragonfly.lang')
    lister = app.config.get('dragonfly.input')
    annotations_path = app.config.get('dragonfly.annotations')
    home_dir = app.config.get('dragonfly.home_dir')
    settings_manager = SettingsManager(home_dir)
    settings_manager.load()

    index, next_index = get_file_indexes(flask.request, lister, filename)
    if index is None:
        return flask.render_template('404.html'), 404
    filename = lister.get_filename(index)
    app.logger.info('Serving ' + filename)
    document = Document(filename, InputReader(filename).sentences)

    if annotations_path:
        if lister.is_dir:
            loader = AnnotationLoader(annotations_path)
            annotations_filename = loader.get(filename)
            if annotations_filename:
                document.attach(InputReader(annotations_filename).sentences)
        else:
            document.attach(InputReader(annotations_path).sentences)

    if lister.is_dir:
        trans_loader = TranslationLoader(lister.path)
    else:
        trans_loader = TranslationLoader(os.path.dirname(lister.path))
    translation = trans_loader.get(filename)
    if translation:
        document.attach_translation(translation)

    # remove any path information
    title = os.path.basename(filename)

    return flask.render_template('index.html', title=title, document=document, index=index, next_index=next_index, sm=settings_manager, lang=lang)


def get_file_indexes(request, lister, filename):
    index = request.args.get('index')
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


@app.route('/save', methods=['POST'])
def save():
    data = flask.request.form['json']
    if not data:
        results = {'success': False, 'message': 'The server did not receive any data.'}
    else:
        writer = OutputWriter(app.config.get('dragonfly.output'))
        response = json.loads(data)
        writer.write(response)
        app.logger.info('Saving annotations for ' + response['filename'])
        results = {'success': True, 'message': 'Annotations saved.'}
    return flask.jsonify(results)


@app.route('/hints', methods=['GET'])
def hints():
    if app.config.get('dragonfly.hints'):
        hint_loader = HintLoader(app.config.get('dragonfly.hints'))
        hints = hint_loader.hints
    else:
        hints = []
    return flask.jsonify(hints)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    home_dir = app.config.get('dragonfly.home_dir')
    manager = SettingsManager(home_dir)
    manager.load()
    if flask.request.method == 'GET':
        return flask.jsonify(manager.settings)
    else:
        settings = json.loads(flask.request.form['json'])
        manager.save(settings)
        results = {'success': True, 'message': 'Settings saved.'}
        return flask.jsonify(results)


@app.route('/translation', methods=['POST'])
def translation():
    home_dir = app.config.get('dragonfly.home_dir')
    data = flask.request.get_json('true')
    manager = TranslationDictManager(home_dir)
    manager.add(**data)
    results = {'success': True, 'message': 'Translation saved.'}
    return flask.jsonify(results)


@app.route('/translations/<lang>')
def translations(lang):
    home_dir = app.config.get('dragonfly.home_dir')
    manager = TranslationDictManager(home_dir)
    trans = manager.get(lang)
    return flask.jsonify(trans)


@app.route('/stop_words')
def stop_words():
    index_dir = app.config.get('dragonfly.index_dir')
    if index_dir:
        indexer = Indexer(index_dir)
        words = indexer.load_stop_words()
    else:
        words = []
    return flask.jsonify(words)
