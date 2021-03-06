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
from .data import Document, InputReader
from .recommend import RecommendConfig
from .renderer import AdjudicateAttacher, AnnotateAttacher, DocumentRenderer
from .search import DocumentStats
from .settings import GlobalSettingsManager, LocalSettingsManager


@app.context_processor
def inject_dragonfly_context():
    version = __version__
    if app.debug:
        version += '.' + ''.join(random.choice(string.ascii_uppercase) for _ in range(8))
    tags = app.config.get('dragonfly.tags')
    locator = app.locator
    dict_available = locator.dictionary_search.available
    phrases_available = locator.phrases_search.available
    return {
        'df_version': version,
        'df_locator': locator,
        'df_settings': locator.settings,
        'df_tags': tags,
        'df_dict_avail': dict_available,
        'df_phrases_avail': phrases_available,
    }


@app.route('/', defaults={'filename': None})
@app.route('/<filename>')
def view(filename):
    modes = list(app.config.get('dragonfly.modes'))
    if flask.request.args.get('view', default=False, type=bool):
        modes.append('viewer')
    if app.config.get('dragonfly.cmd') == 'annotate':
        attacher = AnnotateAttacher()
    else:
        attacher = AdjudicateAttacher(app.config.get('dragonfly.annotation_dirs'))
    dr = DocumentRenderer(attacher, modes)
    file_index = flask.request.args.get('index')
    content = dr.render(app, filename, file_index)
    if not content:
        return flask.render_template('404.html', title="Error", modes=[]), 404
    return content


@app.route('/save', methods=['POST'])
def save():
    data = flask.request.form['json']
    if not data:
        results = {'success': False, 'message': 'The server did not receive any data.'}
    else:
        annotations = json.loads(data)
        lister = app.config.get('dragonfly.input')
        if lister.in_directory(annotations['filename']):
            app.locator.tag_frequencies.update(annotations)
            app.locator.output_writer.write(annotations)
            app.logger.info('Saving annotations for %s', annotations['filename'])
            results = {'success': True, 'message': 'Annotations saved.'}
        else:
            results = {'success': False, 'message': 'Wrong document for this server.'}
    return flask.jsonify(results)


@app.route('/translations/add', methods=['POST'])
def translation():
    data = flask.request.get_json('true')
    app.locator.translation_manager.add(data['lang'], data['source'], data['translation'], data['type'])
    results = {'success': True, 'message': 'Translation saved.'}
    app.logger.info('Saved %s to the %s translation dictionary', data['source'], data['lang'])
    return flask.jsonify(results)


@app.route('/translations/delete', methods=['POST'])
def delete_translation():
    data = flask.request.get_json('true')
    if app.locator.translation_manager.delete(data['lang'], data['source']):
        app.logger.info('Deleted %s from the %s translation dictionary', data['source'], data['lang'])
        results = {'success': True, 'message': 'Translation deleted.'}
    else:
        results = {'success':  False, 'message': 'Not in dictionary.'}
    return flask.jsonify(results)


@app.route('/translations/get/<lang>')
def get_translations(lang):
    trans = app.locator.translation_manager.get(lang)
    return flask.jsonify(trans)


@app.route('/translations/export/<lang>')
def export_translations(lang):
    filename = lang + '.json'
    file = app.locator.translation_manager.get_filename(lang)
    if not os.path.exists(file):
        file = io.BytesIO(b'{}')
    app.logger.info('Exported %s for %s', filename, lang)
    return flask.send_file(file, as_attachment=True, attachment_filename=filename, cache_timeout=0, add_etags=False)


@app.route('/translations/import/<lang>', methods=['POST'])
def import_translations(lang):
    file = flask.request.files['dict']
    data = file.read().decode('utf-8')
    try:
        trans_dict = json.loads(data)
        num_new_items = app.locator.translation_manager.import_json(lang, trans_dict)
        results = {'success': True, 'message': '{} items added'.format(num_new_items)}
        app.logger.info('Imported %s for %s', file.filename, lang)
    except json.JSONDecodeError:
        results = {'success': False, 'message': 'Unrecognized format'}
    return flask.jsonify(results)


@app.route('/search/local', methods=['POST'])
def search_local():
    term = flask.request.form['term']
    use_wildcards = False
    if flask.request.form['manual'] == 'true':
        use_wildcards = any(ch in term for ch in ['*', '?', '[', ']'])
    results = app.locator.local_search.retrieve(term, use_wildcards)
    app.logger.info('Returned %d results from local search for %s', len(results['refs']), term)
    return flask.render_template('search/inverse.html', results=results)


@app.route('/search/local/build', methods=['POST'])
def build_index():
    app.locator.local_search.build_index(True)
    results = {'success': True, 'message': 'Command queued'}
    return flask.jsonify(results)


@app.route('/search/geonames', methods=['POST'])
def search_geonames():
    term = flask.request.form['term']
    fuzzy = float(flask.request.form['fuzzy'])
    results = app.locator.geonames_search.retrieve(term, fuzzy)
    if results is None:
        return '<p class="text-danger">Error getting response from geonames</p>'
    app.logger.info('Returned %d results from geonames for %s', len(results['geonames']), term)
    return flask.render_template('search/geonames.html', results=results)


@app.route('/search/dict', methods=['POST'])
def search_dict():
    term = flask.request.form['term']
    column = flask.request.form['column']
    results = app.locator.dictionary_search.retrieve(term, int(column))
    app.logger.info('Returned %d results from dictionary search for %s', len(results), term)
    return flask.render_template('search/dictionary.html', results=results)


@app.route('/search/dict/autocomplete', methods=['GET'])
def autocomplete_dict():
    term = flask.request.args.get('term')
    column = flask.request.args.get('column')
    results = app.locator.dictionary_search.suggest(term, int(column))
    return flask.jsonify(results)


@app.route('/search/dict/import', methods=['POST'])
def import_combodict():
    file = flask.request.files['combodict']
    data = file.read().decode('utf-8')
    app.locator.dictionary_search.copy(data)
    results = {'success': True, 'message': 'Loaded the bilingual dictionary for search'}
    app.logger.info('Imported combodict %s', file.filename)
    return flask.jsonify(results)


@app.route('/search/phrases', methods=['POST'])
def search_phrases():
    term = flask.request.form['term']
    results = app.locator.phrases_search.retrieve(term)
    for result in results:
        result['il'] = result['il'].replace(term, '<span class="df-result-highlight">' + term + '</span>')
    app.logger.info('Returned %d results from phrases search for %s', len(results), term)
    return flask.render_template('search/phrases.html', results=results)


@app.route('/search/phrases/import', methods=['POST'])
def import_phrases():
    file = flask.request.files['phrases']
    data = file.read().decode('utf-8')
    app.locator.phrases_search.copy(data)
    results = {'success': True, 'message': 'Loaded the phrases file for search'}
    app.logger.info('Imported phrases %s', file.filename)
    return flask.jsonify(results)


@app.route('/hints', methods=['GET', 'POST'])
def hints():
    if flask.request.method == 'GET':
        return flask.jsonify(app.locator.hints.load())
    else:
        app.locator.hints.save(flask.request.form['hints'])
        results = {'success': True, 'message': 'Hints saved. Page must be reloaded to take affect.'}
        return flask.jsonify(results)


@app.route('/marker', methods=['POST'])
def marker():
    manager = app.locator.marker_manager
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
    stats_data = app.locator.stats
    stats_data.collect(app.config.get('dragonfly.output'))
    return flask.render_template('modals/stats.html', stats=stats_data)


@app.route('/notes', methods=['POST'])
def notes():
    app.locator.notepad.save(flask.request.form['filename'], flask.request.form['notes'])
    results = {'success': True, 'message': 'Notes saved'}
    return flask.jsonify(results)


@app.route('/tools')
def tools():
    lang = app.config.get('dragonfly.lang')
    return flask.render_template('modals/tools.html', lang=lang, recommender=app.locator.recommender)


@app.route('/recommend/build', methods=['POST'])
def build_recommendations():
    name = flask.request.form['name']
    config = RecommendConfig(flask.request.form)
    app.locator.recommender.build(name, config)
    results = {'success': True, 'message': '{} recommendation built'.format(name)}
    app.logger.info('Completed building recommendations for %s', name)
    return flask.jsonify(results)


@app.route('/recommend/get')
def get_recommendations():
    rec_name = flask.request.args.get('recommendation')
    recommendation = app.locator.recommender.get(rec_name)
    render = flask.get_template_attribute('macros.html', 'render_recommendation')
    return render(recommendation)


@app.route('/word_cloud/<doc>')
def word_cloud(doc):
    lister = app.config.get('dragonfly.input')
    filename = lister.get_path(doc)
    reader = InputReader(filename)
    document = Document(filename, reader.sentences, reader.terminal_blank_line)
    index = app.locator.local_search.index
    doc_stats = DocumentStats(document, index)
    words = []
    user_trans = app.locator.translation_manager.get(app.config.get('dragonfly.lang'))
    dict_search = app.locator.dictionary_search
    for word, tfidf in doc_stats.get_top_words().items():
        if word.lower() in user_trans:
            word = user_trans[word.lower()][0]
        elif dict_search.available:
            results = dict_search.retrieve(word, 0)
            if results:
                word = results[0][1]
        words.append({'text': word, 'weight': tfidf})
    return flask.jsonify(words)
