# Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
# All rights reserved.
# Distributed under the terms of the Apache 2.0 License.

from dragonfly import app, __version__
import flask
import io
import json
import random
import string
import os
from .data import OutputWriter, HintLoader, SentenceMarkerManager
from .mode import ModeManager
from .recommend import RecommendConfig
from .settings import GlobalSettingsManager, LocalSettingsManager
from .search import GeonamesSearch
from .stats import Stats
from .translations import TranslationDictManager


@app.context_processor
def inject_dragonfly_context():
    version = __version__
    if app.debug:
        version += '.' + ''.join(random.choice(string.ascii_uppercase) for _ in range(8))
    tags = app.config.get('dragonfly.tags')
    locator = app.config.get('dragonfly.locator')
    dict_available = locator.dictionary_search.available
    data = dict(df_version=version, df_settings=locator.settings, df_tags=tags, df_dict_avail=dict_available)
    return data


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


@app.route('/translation', methods=['POST'])
def translation():
    global_md_dir = app.config.get('dragonfly.global_md_dir')
    data = flask.request.get_json('true')
    manager = TranslationDictManager(global_md_dir)
    manager.add(data['lang'], data['source'], data['translation'], data['type'])
    results = {'success': True, 'message': 'Translation saved.'}
    app.logger.info('Saved %s to the %s translation dictionary', data['source'], data['lang'])
    return flask.jsonify(results)


@app.route('/translation/delete', methods=['POST'])
def delete_translation():
    global_md_dir = app.config.get('dragonfly.global_md_dir')
    data = flask.request.get_json('true')
    manager = TranslationDictManager(global_md_dir)
    if manager.delete(data['lang'], data['source']):
        app.logger.info('Deleted %s from the %s translation dictionary', data['source'], data['lang'])
        results = {'success': True, 'message': 'Translation deleted.'}
    else:
        results = {'success':  False, 'message': 'Not in dictionary.'}
    return flask.jsonify(results)


@app.route('/translations/<lang>')
def translations(lang):
    global_md_dir = app.config.get('dragonfly.global_md_dir')
    manager = TranslationDictManager(global_md_dir)
    trans = manager.get(lang)
    return flask.jsonify(trans)


@app.route('/translations/export/<lang>')
def export_translations(lang):
    global_md_dir = app.config.get('dragonfly.global_md_dir')
    manager = TranslationDictManager(global_md_dir)
    filename = lang + '.json'
    file = manager.get_filename(lang)
    if not os.path.exists(file):
        file = io.BytesIO(b'{}')
    app.logger.info('Exported %s for %s', filename, lang)
    return flask.send_file(file, as_attachment=True, attachment_filename=filename, cache_timeout=0, add_etags=False)


@app.route('/translations/import/<lang>', methods=['POST'])
def import_translations(lang):
    global_md_dir = app.config.get('dragonfly.global_md_dir')
    manager = TranslationDictManager(global_md_dir)
    file = flask.request.files['dict']
    data = file.read().decode('utf-8')
    try:
        trans_dict = json.loads(data)
        num_new_items = manager.import_json(lang, trans_dict)
        results = {'success': True, 'message': '{} items added'.format(num_new_items)}
        app.logger.info('Imported %s for %s', file.filename, lang)
    except json.JSONDecodeError:
        results = {'success': False, 'message': 'Unrecognized format'}
    return flask.jsonify(results)


@app.route('/search', methods=['POST'])
def search_local():
    term = flask.request.form['term']
    use_wildcards = False
    if flask.request.form['manual'] == 'true':
        use_wildcards = any(ch in term for ch in ['*', '?', '[', ']'])
    results = app.dragonfly_index.retrieve(term, use_wildcards)
    app.logger.info('Returned %d results from local search for %s', len(results['refs']), term)
    return flask.render_template('search/inverse.html', results=results)


@app.route('/search/geonames', methods=['POST'])
def search_geonames():
    term = flask.request.form['term']
    fuzzy = flask.request.form['fuzzy']
    locator = app.config.get('dragonfly.locator')
    settings = locator.settings
    countries = []
    if settings['Geonames County Codes']:
        countries = [code.strip().upper() for code in settings['Geonames County Codes'].split(',')]
    geonames = GeonamesSearch(settings['Geonames Username'], countries=countries, fuzzy=fuzzy)
    results = geonames.retrieve(term)
    if results is None:
        return '<p class="text-danger">Error getting response from geonames</p>'
    app.logger.info('Returned %d results from geonames for %s', len(results['geonames']), term)
    return flask.render_template('search/geonames.html', results=results)


@app.route('/search/dict', methods=['POST'])
def search_dict():
    term = flask.request.form['term']
    column = flask.request.form['column']
    locator = app.config.get('dragonfly.locator')
    engine = locator.dictionary_search
    results = engine.retrieve(term, int(column))
    app.logger.info('Returned %d results from dictionary search for %s', len(results), term)
    return flask.render_template('search/dictionary.html', results=results)


@app.route('/search/dict/autocomplete', methods=['GET'])
def autocomplete_dict():
    term = flask.request.args.get('term')
    column = flask.request.args.get('column')
    locator = app.config.get('dragonfly.locator')
    engine = locator.dictionary_search
    results = engine.suggest(term, int(column))
    return flask.jsonify(results)


@app.route('/search/dict/import', methods=['POST'])
def import_combodict():
    locator = app.config.get('dragonfly.locator')
    engine = locator.dictionary_search
    file = flask.request.files['combodict']
    data = file.read().decode('utf-8')
    engine.copy(data)
    results = {'success': True, 'message': 'Loaded the bilingual dictionary for search'}
    app.logger.info('Imported combodict %s', file.filename)
    return flask.jsonify(results)


@app.route('/search/build', methods=['POST'])
def build_index():
    app.dragonfly_bg.build_index()
    results = {'success': True, 'message': 'Command queued'}
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
    manager = SentenceMarkerManager(app.config.get('dragonfly.local_md_dir'))
    document = flask.request.form['document']
    sentences = flask.request.form.getlist('sentence[]')
    for sentence in sentences:
        manager.toggle(document, sentence)
    results = {'success': True, 'message': 'Marker changed.'}
    return flask.jsonify(results)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global_md_dir = app.config.get('dragonfly.global_md_dir')
    local_md_dir = app.config.get('dragonfly.local_md_dir')
    gsm = GlobalSettingsManager(global_md_dir)
    lsm = LocalSettingsManager(local_md_dir)
    if flask.request.method == 'GET':
        gsm.load()
        lsm.load()
        return flask.render_template('modals/settings.html', gsm=gsm, lsm=lsm)
    else:
        new_settings = json.loads(flask.request.form['json'])
        gsm.save(new_settings)
        lsm.save(new_settings)
        results = {'success': True, 'message': 'Settings saved.'}
        app.logger.info('Saved settings')
        return flask.jsonify(results)


@app.route('/stats')
def stats():
    output_dir = app.config.get('dragonfly.output')
    stats_data = Stats()
    stats_data.collect(output_dir)
    return flask.render_template('modals/stats.html', stats=stats_data)


@app.route('/tools')
def tools():
    lang = app.config.get('dragonfly.lang')
    locator = app.config.get('dragonfly.locator')
    return flask.render_template('modals/tools.html', lang=lang, recommender=locator.recommender)


@app.route('/recommend/build', methods=['POST'])
def build_recommendations():
    name = flask.request.form['name']
    config = RecommendConfig(flask.request.form)
    recommender = app.config.get('dragonfly.locator').recommender
    recommender.build(name, config)
    results = {'success': True, 'message': '{} recommendation built'.format(name)}
    app.logger.info('Completed building recommendations for %s', name)
    return flask.jsonify(results)


@app.route('/recommend/get')
def get_recommendations():
    rec_name = flask.request.args.get('recommendation')
    recommender = app.config.get('dragonfly.locator').recommender
    recommendation = recommender.get(rec_name)
    return flask.render_template('modals/recommend.html', rec=recommendation)
