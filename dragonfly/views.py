# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

from dragonfly import app
import flask
import json
from .data import OutputWriter, HintLoader, SentenceMarkerManager
from .mode import ModeManager
from .settings import SettingsManager
from .stats import Stats
from .translations import TranslationDictManager


@app.route('/', defaults={'filename': None})
@app.route('/<filename>')
def index(filename):
    mode = app.config.get('dragonfly.mode')
    manager = ModeManager(mode)
    file_index = flask.request.args.get('index')
    content = manager.render(app, filename, file_index)
    if not content:
        return flask.render_template('404.html', title="Error"), 404
    return content


@app.route('/save', methods=['POST'])
def save():
    data = flask.request.form['json']
    if not data:
        results = {'success': False, 'message': 'The server did not receive any data.'}
    else:
        writer = OutputWriter(app.config.get('dragonfly.output'))
        response = json.loads(data)
        writer.write(response)
        app.logger.info('Saving annotations for %s', response['filename'])
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


@app.route('/marker', methods=['POST'])
def marker():
    manager = SentenceMarkerManager(app.config.get('dragonfly.data_dir'))
    document = flask.request.form['document']
    sentence = flask.request.form['sentence']
    manager.toggle(document, sentence)
    results = {'success': True, 'message': 'Marker saved.'}
    return flask.jsonify(results)


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


@app.route('/search', methods=['POST'])
def search():
    term = flask.request.form['term']
    results = app.dragonfly_index.lookup(term)
    return flask.jsonify(results)


@app.route('/stats')
def stats():
    output_dir = app.config.get('dragonfly.output')
    stats = Stats()
    stats.collect(output_dir)
    return flask.render_template('stats.html', stats=stats)
