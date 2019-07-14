/**
 * Copyright 2017-2019, The Johns Hopkins University Applied Physics Laboratory LLC
 * All rights reserved.
 * Distributed under the terms of the Apache 2.0 License.
 */

var dragonfly = dragonfly || {};

/**
 * Show status message.
 * @param {string} type - 'success' or 'danger'.
 * @param {string} text - The text to display.
 */
dragonfly.showStatus = function(type, text) {
    $(".alerts").append('<div class="alert alert-' + type + ' alert-dismissable">' +
            '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>' +
            text + '</div>');
    if (type == "success") {
        $(".alerts").children().delay(4000).fadeTo(1000, 0, function() {
            $(this).alert('close');
        });
    }
};

dragonfly.Events = {
    SET_TAG_MODE: 'df:set_tag_mode',
    SET_DELETE_MODE: 'df:set_delete_mode',
    SET_SELECT_MODE: 'df:set_select_mode',
    SET_FIND_MODE: 'df:set_find_mode',
    TOGGLE_CASCADE: 'df:toggle_cascade',
    UNDO: 'df:undo',
    SAVE: 'df:save',
    NEXT: 'df:next',
    PREVIOUS: 'df:previous',
    CHANGE_SETTINGS: 'df:change_settings',
    LEAVE: 'df:leave',
};

dragonfly.EventDispatcher = class EventDispatcher {
    constructor(tagTypes) {
        var self = this;
        this.tagTypes = tagTypes;

        $(document).on("keypress", function(event) {
            if ($(event.target).is("body")) {
                var key = String.fromCharCode(event.which);
                self.processKeyPress(key);
            }
        });

        // change the click mode or tag type by clicking on navbar
        $(".df-type").on("click", function(event) {
            var letter = $(this).attr("title");
            self.processKeyPress(letter);
        });

        $("input[id = 'cascade']").on("click", function() {
            $(window).trigger(dragonfly.Events.TOGGLE_CASCADE);
        });

        $("#df-save").on("click", function(event) {
            $(window).trigger(dragonfly.Events.SAVE);
            $(this).blur();
        });

        // ctrl+s for save annotations and ctrl+arrow for navigation
        $(document).on("keydown", function(event) {
            if (event.ctrlKey || event.metaKey) {
                if (String.fromCharCode(event.which).toLowerCase() == 's') {
                    event.preventDefault();
                    $(window).trigger(dragonfly.Events.SAVE);
                } else if (event.which == 37) {
                    // left arrow
                    $(window).trigger(dragonfly.Events.PREVIOUS);
                } else if (event.which == 39) {
                    // right arrow
                    $(window).trigger(dragonfly.Events.NEXT);
                }
            }
        });
    }

    processKeyPress(key) {
        switch (key) {
            case 'c':
                $(window).trigger(dragonfly.Events.TOGGLE_CASCADE);
                break;
            case '0':
            case 'd':
                $(window).trigger(dragonfly.Events.SET_DELETE_MODE);
                break;
            case 's':
                $(window).trigger(dragonfly.Events.SET_SELECT_MODE);
                break;
            case 'f':
                $(window).trigger(dragonfly.Events.SET_FIND_MODE);
                break;
            case 'u':
                $(window).trigger(dragonfly.Events.UNDO);
                break;
            default:
                if (this.tagTypes.isTagType(key)) {
                    $(window).trigger(dragonfly.Events.SET_TAG_MODE, [key]);
                }
                break;
        }
    }
};

dragonfly.Settings = class Settings {
    /**
     * Create a Settings object
     * @param {object} settings - Settings object
     */
    constructor(settings) {
        this.settings = settings;
        this._initializeHandlers();
    }

    _initializeHandlers() {
        var self = this;

        $('#df-settings-modal').on('show.bs.modal', function(event) {
            var body = $(this).find('.modal-body');
            body.load('settings');
            $('#df-settings-button').one('focus', function(event) {
                $(this).blur();
            });
        });

        $("#df-settings-save").on("click", function(event) {
            $('#df-settings-modal').modal('hide');
            self._save();
        });

        // leaving focus on settings button is distracting so we remove it
        $('#df-settings-modal').on('shown.bs.modal', function(event) {
            $('#df-settings-button').one('focus', function(event) {
                $(this).blur();
            });
        });
    }

    isSentenceIdAutoScroll() {
        return this.settings['Auto Scrolling Sentence IDs'];
    }

    isDisplayRowLabels() {
        return this.settings['Display Row Labels'];
    }

    isAutoSave() {
        return this.settings['Auto Save'];
    }

    isAutoSaveOnNav() {
        return this.settings['Auto Save On Nav'];
    }

    isCascadeOn() {
        return this.settings['Cascade By Default'];
    }

    areNotesDocumentSpecific() {
        return this.settings['Document Specific Notes'];
    }

    getFooterHeight() {
        return this.settings['Footer Height'];
    }

    isFooterOpenDefault() {
        return this.settings['Footer Starts Open'];
    }

    getGMapsKey() {
        return this.settings['GMaps Key'];
    }

    getGMapsParams() {
        var values = this.settings['GMaps Params'].split(',');
        values = values.map(s => parseFloat(s.trim()));
        if (values.length != 3) {
            values = [0, 0, 1];
        }
        return values;
    }

    getHintsRow() {
        return this.settings['Hint Row'];
    }

    /**
     * Apply changed settings to the page
     */
    apply() {
        if (!this.isDisplayRowLabels()) {
            $(".df-column-labels").hide();
        } else {
            $(".df-column-labels").show().css('display', 'inline-block');
        }
    }

    /**
     * Save the settings object through ajax to server.
     */
    _save() {
        var self = this;
        this.settings = this._convertToObject($("#df-settings-form").serializeArray());
        $.ajax({
            url: 'settings',
            type: 'POST',
            data: {json: JSON.stringify(this.settings)},
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    dragonfly.showStatus('success', response.message);
                    $(window).trigger(dragonfly.Events.CHANGE_SETTINGS);
                    self.apply();
                } else {
                    dragonfly.showStatus('danger', response.message);
                }
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Convert the array that represents the form to a settings object.
     * @param {array} array - Array from serializeArray().
     * @return {object}
     */
    _convertToObject(array) {
        var obj = {};
        $.each(array, function() {
            if (this.value === "true" || this.value === "false") {
                this.value = (this.value == "true");
            }
            obj[this.name] = this.value;
        });
        return obj;
    }
};

dragonfly.Hints = class Hints {
    /**
     * Create a hints manager.
     * @param {string} row - One-based index of row to apply hints to.
     */
    constructor(row) {
        this.row = row;
        this.hints = [];
    }

    /**
     * Load the hints from the server and apply them to the page.
     */
    run() {
        var self = this;
        $.ajax({
            url: 'hints',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                self.hints = data;
                self.process();
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });

    }

    /**
     * Apply the hints to the web page.
     * If more than one hint matches a string, only the first one is applied.
     */
    process() {
        var self = this;
        for (var i = 0; i < this.hints.length; i++) {
            try {
                this.hints[i].regex = new RegExp(this.hints[i].regex);
            } catch (e) {
                dragonfly.showStatus('danger', 'Invalid hint regex: ' + escapeHtml(this.hints[i].regex));
                this.hints[i].regex = null;
            }
        }

        var selector = ".df-main .df-row > div:nth-child(" + this.row + ")";
        $(selector).each(function() {
            for (var i = 0; i < self.hints.length; i++) {
                var text = $(this).text();
                var match = text.match(self.hints[i].regex);
                if (match != null) {
                    var new_text = '<span class="df-hint" data-toggle="tooltip" title="' + self.hints[i].comment + '">' + match[0] + '</span>';
                    $(this).html(text.replace(match[0], new_text));
                    return;
                }
            }
        });

        $(".df-hint").tooltip({delay: 200, placement: 'auto top'});
    }
};

dragonfly.Markers = class Markers {

    /**
     * User clicks the sentence badge to toggle or presses delete key to clear
     */
    constructor() {
        var self = this;

        // user can indicate which sentences have been reviewed
        $(".df-sentence-badge").on("click", function(event) {
            self.toggle([this]);
        });
    }

    /**
     * Toggle the marker.
     * @param {array} elements - Marker DOM elements to being toggled.
     */
    toggle(elements) {
        var ids = [];
        elements.forEach(function(element) {
            $(element).toggleClass("df-marked");
            ids.push($(element).data('index'));
        });

        $.ajax({
            url: 'marker',
            type: 'POST',
            data: {'document': dragonfly.filename, 'sentence': ids},
            dataType: 'json',
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }
};

/**
 * Manage notes on documents/annotations
 */
dragonfly.Notepad = class Notepad {
    /**
     * Create the notepad
     * @param {string} filename - The file being annotated
     * @param {boolean} isDocumentSpecific - Do the notes apply to current document only
     */
    constructor(filename, isDocumentSpecific) {
        var self = this;
        this.filename = filename;
        this.isDocumentSpecific = isDocumentSpecific;
        this.changed = false;

        $(window).on(dragonfly.Events.LEAVE, function() {
            if (self.changed) {
                var formData = new FormData();
                if (self.isDocumentSpecific) {
                    formData.append('filename', self.filename);
                } else {
                    formData.append('filename', '');
                }
                formData.append('notes', $('textarea[name="df-notes"]').val());
                $.ajax({
                    url: 'notes',
                    type: 'POST',
                    data: formData,
                    processData: false,
                    contentType: false,
                    dataType: 'json',
                });
            }
        });

        $('textarea[name="df-notes"]').one('change', function() {
            self.changed = true;
        });

        // capture tabs rather than using them for ui navigation
        $('textarea[name="df-notes"]').on('keydown', function(event) {
            if (event.which == 9) {
                event.preventDefault();
                var offset = this.selectionStart;
                $(this).val(function(i, str) {
                    return str.substring(0, offset) + "\t" + str.substring(this.selectionEnd)
                });
                this.selectionEnd = offset + 1;
            }
        });

        $("#df-notes-link").one('click', function() {
            $.getScript('static/js/jqcloud.min.js')
                .done(function() {
                    $.ajax({
                        url: 'word_cloud/' + dragonfly_filename,
                        type: 'GET',
                        dataType: 'json',
                        success: function(data) {
                            $('#df-cloud').jQCloud(data);
                        },
                        error: function(xhr) {
                            dragonfly.showStatus('danger', 'Error contacting the server');
                        }
                    });
                })
                .fail(function(jqxhr, settings, exception) {
                    dragonfly.showStatus('danger', 'Unable to load word cloud');
            });
        });

        $("#df-notes-link").on('click', function(event) {
            event.preventDefault();
            $("#df-notes").toggle();
            $("#df-cloud").toggle();
        });
    }
};

/**
 * Search mode configuration
 */
dragonfly.SearchMode = class SearchMode {
    constructor(name, initializeFunc = null) {
        this.name = name;
        this.initializeFunc = initializeFunc;
        this.initialized = initializeFunc == null;
        this.button = '#df-search-use-' + name;
        this.searchBox = '.df-searchbox-' + name;
        this.results = '.df-results-' + name;
    }
};

/**
 * Search window
 */
dragonfly.Search = class Search {
    /**
     * Create a Search object
     * @param {Settings} settings - Settings manager
     */
    constructor(settings) {
        var self = this;
        this.settings = settings;
        this.modes = {
            'local': new dragonfly.SearchMode('local'),
            'wikipedia': new dragonfly.SearchMode('wikipedia', function() {self.initializeWikipedia();}),
            'gmaps': new dragonfly.SearchMode('gmaps', function() {self.initializeGMaps();}),
            'geonames': new dragonfly.SearchMode('geonames'),
            'dict': new dragonfly.SearchMode('dict'),
        };
        this._initializeHandlers();

        // we load javascript libraries on demand and want to cache them
        $.ajaxSetup({cache: true});
    }

    _initializeHandlers() {
        var self = this;
        // support resizing the footer window with the mouse
        $('.df-footer').resizable({
            handleSelector: '.df-resize-bar-h',
            resizeWidth: false,
            resizeHeightFrom: 'top',
        });

        $('.df-footer-sidebar').resizable({
            handleSelector: '.df-resize-bar-v',
            resizeHeight: false,
            resizeWidthFrom: 'left',
        });

        $('#df-footer-minimize').on('click', function() {
            self.hide();
            $(this).blur();
            dragonfly.highlighter.revertClickMode(dragonfly.ClickMode.FINDER);
        });

        // manual editing of search form and submission
        $('#df-search-local-form').on('submit', function(event) {
            event.preventDefault();
            self.searchFiles($(this).find('input[name="term"]').val(), true);
        });

        $('#df-search-geonames-form').on('submit', function(event) {
            event.preventDefault();
            $(this).find('button').blur();
            var term = $(this).find('input[name="term"]').val();
            var fuzzy = parseFloat($(this).find('input[name="fuzzy"]').val());
            // geonames wants 0 as very fuzzy and 1 as not fuzzy so we flip and normalize
            self.searchGeonames(term, (10.0 - fuzzy) / 10.0);
        });

        $('.gmaps-form').on('submit', function(event) {
            event.preventDefault();
        });

        $('#df-search-dict-form').on('submit', function(event) {
            event.preventDefault();
            $(this).find('button').blur();
            var term = $(this).find('input[name="term"]').val();
            var column = parseInt($(this).find('input[name="dict-column"]:checked').val());
            self.searchDictionary(term, column);
        });

        // autocomplete for bilingual dictionary
        $('#df-search-dict-term').typeahead({minLength: 2}, {
            name: 'dict',
            async: true,
            limit: 10,
            source: function(query, syncResults, asyncResults) {
                var column = parseInt($('input[name="dict-column"]:checked').val());
                $.get('/search/dict/autocomplete', {term: query, column: column}, function(data) {
                    return asyncResults(data);
                });
            }
        });

        // when selects from autocomplete suggestions, submit
        $('#df-search-dict-term').on('typeahead:selected', function(event, term) {
            var column = parseInt($('input[name="dict-column"]:checked').val());
            self.searchDictionary(term, column);
        });

        Object.values(this.modes).forEach(mode => {
            $(mode.button).on('click', function() {
                $(this).blur();
                self.use(mode);
            });
        });
    }

    /**
     * Show the footer
     */
    show() {
        var cw = $('.df-footer');
        if (cw.height() < 100) {
            cw.height(this.settings.getFooterHeight());
        }
    }

    /**
     * Hide the footer
     */
    hide() {
        $('.df-footer').height('6px');
    }

    /**
     * Toggle between search modes
     * @param {Mode} selected_mode - Search mode
     */
    use(selected_mode) {
        if (!selected_mode.initialized) {
            selected_mode.initialized = true;
            selected_mode.initializeFunc();
        }
        Object.values(this.modes).forEach(mode => {
            if (selected_mode == mode) {
                $(mode.searchBox).show().css('display', 'inline-block');
                $(mode.results).show();
            } else {
                $(mode.searchBox).hide();
                $(mode.results).hide();
            }
            $(mode.button).on('click', function() {
                $(this).blur();
            });
        });
     }

    /**
     * Search the local index
     * @param {string} word - Search term.
     * @param {bool} manual - Whether the user manually typed the term.
     */
    searchFiles(word, manual) {
        var self = this;
        if (!manual) {
            $('#df-search-local-form').find('input[name="term"]').val(word);
        }
        $.ajax({
            url: 'search/local',
            type: 'POST',
            data: {'term': word, 'manual': manual},
            dataType: 'html',
            success: function(html) {
                $('.df-results-local').html(html);
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Search Geonames
     * @param {string} word - Search term.
     * @param {float} fuzzy - Fuzziness on scale of 0 to 1.
     */
    searchGeonames(word, fuzzy) {
        var self = this;
        $.ajax({
            url: 'search/geonames',
            type: 'POST',
            data: {'term': word, 'fuzzy': fuzzy},
            dataType: 'html',
            success: function(html) {
                $('.df-results-geonames').html(html);
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Search a bilingual dictionary
     * @param {string} word - Search term
     * @param {int} - Column of dictionary to search
     */
    searchDictionary(word, column) {
        var self = this;
        $.ajax({
            url: '/search/dict',
            type: 'POST',
            data: {'term': word, 'column': column},
            dataType: 'html',
            success: function(html) {
                $('.df-results-dict').html(html);
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Load the custom Google search engine for Wikipedia
     */
    initializeWikipedia() {
        var cx = '003899999982319279749:whnyex5nm1c';
        var src = 'https://cse.google.com/cse.js?cx=' + cx;
        $.getScript(src)
            .fail(function(jqxhr, settings, exception) {
                dragonfly.showStatus('danger', 'Unable to contact Google Search');
        });
    }

    /**
     * Load the Google Maps places engine
     */
    initializeGMaps() {
        var key = this.settings.getGMapsKey();
        var src = 'https://maps.googleapis.com/maps/api/js?key=' + key;
        src += '&libraries=places&callback=dragonfly.search.initializeGMapsCallback';
        $.getScript(src)
            .fail(function(jqxhr, settings, exception) {
                dragonfly.showStatus('danger', 'Unable to contact Google Maps');
        });
    }

    /**
     * Callback when initializing GMaps
     */
    initializeGMapsCallback() {
        self = this;

        var params = this.settings.getGMapsParams();
        var map = new google.maps.Map(document.getElementById('gmaps'), {
            center: {lat: params[0], lng: params[1]},
            zoom: Math.round(params[2]),
            mapTypeId: 'roadmap',
            mapTypeControl: false,
            streetViewControl: false,
            fullscreenControl: false,
        });
        var input = document.getElementById('gmaps-input');
        var searchBox = new google.maps.places.SearchBox(input);

        // bias search results
        map.addListener('bounds_changed', function() {
          searchBox.setBounds(map.getBounds());
        });

        var markers = [];
        searchBox.addListener('places_changed', function() {
          self.updateGMaps(map, searchBox, markers);
        });
    }

    /**
     * Update the map based on search
     * @param {Map} map
     * @param {SearchBox} searchBox
     * @param {array} markers
     */
    updateGMaps(map, searchBox, markers) {
        var places = searchBox.getPlaces();
        if (places.length == 0) {
          return;
        }

        // Clear out the old markers.
        markers.forEach(function(marker) {
          marker.setMap(null);
        });
        markers = [];

        // Draw new marker and zoom the map
        var bounds = new google.maps.LatLngBounds();
        places.forEach(function(place) {
          if (!place.geometry) {
            return;
          }

          markers.push(new google.maps.Marker({
            map: map,
            title: place.name,
            position: place.geometry.location
          }));

          if (place.geometry.viewport) {
            bounds.union(place.geometry.viewport);
          } else {
            bounds.extend(place.geometry.location);
          }
        });
        map.fitBounds(bounds);
    }
};

/**
 * Context menu for managing user-created translations
 */
dragonfly.ContextMenu = class ContextMenu {
    constructor(translationManager) {
        var self = this;
        this.modal = $("#df-context-menu");
        this.translationManager = translationManager;

        $(".df-token").on("contextmenu", function(event) {
            self._show($(this), event);
        });

        $("#df-context-menu-submit").on('click', function(event) {
            self._save();
            event.preventDefault();
        });

        $("#df-context-menu-delete").on('click', function(event) {
            self._remove();
            event.preventDefault();
        });
    }

    /**
     * Show the context menu.
     * @param {jQuery} token - The token element clicked on.
     * @param {Event} event - The click event for location information.
     */
    _show(token, event) {
        var self = this;
        event.preventDefault();

        var tokenInfo = this._getTokenInfo(token);
        $("#df-trans-source").html(tokenInfo['text']);
        $("#df-tfidf").html(tokenInfo['tfidf']);
        $("input[name = 'entity-type']").val(tokenInfo['type']);
        $("input[name = 'translation']").val(tokenInfo['trans']);

        var position = this._getPosition(event);
        this.modal.css({top: position.top, left: position.left, position:'absolute'});
        this.modal.show();
        $("input[name = 'translation']").focus();

        // don't want to hide context menu when clicking on it
        this.modal.on('click', function(event) {
            event.stopPropagation();
        });

        // documentElement to work around bug in firefox
        // https://bugzilla.mozilla.org/show_bug.cgi?id=184051
        $(document.documentElement).one("click", function(event) {
            self._hide();
        });
    }

    /**
     * Get position to show context menu
     * @param {event} event - Right click event
     * @return {object}
     */
    _getPosition(event) {
        var position = {top: event.pageY, left: event.pageX};
        var viewport = {
            top: $(window).scrollTop(),
            left: $(window).scrollLeft()
        };
        viewport.right = viewport.left + $(window).width();
        viewport.bottom = viewport.top + $(window).height();

        var modalRight = position.left + this.modal.outerWidth();
        if (modalRight > viewport.right) {
            position.left -= (modalRight - viewport.right);
        }
        var modalBottom = position.top + this.modal.outerHeight();
        if (modalBottom > viewport.bottom) {
            position.top -= (modalBottom - viewport.bottom);
        }

        return position;
    }

    /**
     * Get the information about the token like text, tag type, and translation
     * @param {jQuery} token - Token element for tag
     * @return {object}
     */
    _getTokenInfo(token) {
        var result = {text: token.attr('data-token'), type: null, trans: null, tfidf: token.data('tfidf')};
        var tag = token.data('tag');
        if (tag != null && tag != 'O') {
            // B-GPE for example
            result['type'] = tag.slice(2);
        }
        var info = this.translationManager.get(result['text']);
        if (info) {
            result['trans'] = info['trans'];
            // current tag type takes precedence
            if (!result['type']) {
                result['type'] = info['type'];
            }
        }
        return result;
    }

    /**
     * Hide the context menu and clear input.
     */
    _hide() {
        this.modal.hide();
        $("input[name = 'translation']").val('');
        $("input[name = 'entity-type']").val('');
    }

    /**
     * Save the translation through ajax to server.
     */
    _save() {
        var self = this;
        var translation = $("input[name = 'translation']").val();
        var entityType = $("input[name = 'entity-type']").val();
        if (translation.length == 0) {
            this._hide();
            return;
        }
        var data = {
            'source': $("#df-trans-source").html(),
            'translation': translation,
            'type': entityType,
            'lang': dragonfly.lang
        };
        $.ajax({
            url: 'translations/add',
            type: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    dragonfly.showStatus('success', response.message);
                    self._hide();
                    self.translationManager.add(data.source, {'trans': data.translation, 'type': data.type});
                } else {
                    dragonfly.showStatus('danger', response.message);
                }
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Remove the translation through ajax to server.
     */
    _remove() {
        var self = this;
        var data = {
            'source': $("#df-trans-source").html(),
            'lang': dragonfly.lang,
        };
        $.ajax({
            url: 'translations/delete',
            type: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            success: function(response) {
                self._hide();
                if (response.success) {
                    dragonfly.showStatus('success', response.message);
                    self.translationManager.remove(data.source);
                }
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }
};

dragonfly.Translations = class Translations {
    /**
     * Create a translations manager.
     */
    constructor(lang) {
        this.lang = lang;
        this.transMap = new Map();
    }

    /**
     * Load the translations and apply them to the page.
     */
    load() {
        var self = this;
        $.ajax({
            url: 'translations/get/' + this.lang,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                self.createMap(data);
                self.apply();
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Create a source token -> gloss map
     * @param {object} translations - JSON object of translations.
     */
    createMap(translations) {
        for (var source in translations) {
            this.transMap.set(source.toLowerCase(), {'trans': translations[source][0], 'type': translations[source][1]});
        }
    }

    /**
     * Get the info for this source.
     * @param {string} source - Source language string
     * @return {object} - trans and type or null
     */
    get(source) {
        if (this.transMap.has(source.toLowerCase())) {
            return this.transMap.get(source.toLowerCase());
        } else {
            return null;
        }
    }

    /**
     * Add a new translation pair to the translation manager.
     * @param {string} source - Source string.
     * @param {object} info - Object with keys trans and type.
     */
    add(source, info) {
        this.transMap.set(source.toLowerCase(), info);
        this.addDisplay(source.toLowerCase(), info.trans, info.type);
    }

    /**
     * Remove a source from the translation manager.
     * @param {string} source - Source string.
     */
    remove(source) {
        this.transMap.delete(source.toLowerCase());
        this.removeDisplay(source.toLowerCase());
    }

    /**
     * Apply the translations to the web page.
     */
    apply() {
        var self = this;
        $(".df-token").each(function() {
            var token = $(this).attr('data-token').toLowerCase();
            if (self.transMap.has(token)) {
                if (self.transMap.get(token).type) {
                    var title = self.transMap.get(token).type + ' : ' + self.transMap.get(token).trans;
                } else {
                    var title = self.transMap.get(token).trans;
                }
                $(this).addClass('df-in-dict');
                $(this).attr('title', title);
                $(this).attr('data-toggle', 'tooltip');
            }
        });
        // this does all tooltips including in non-token rows
        $('[data-toggle=tooltip]').tooltip({delay: 200, placement: 'auto left', container: 'body'});
    }

    /**
     * Add display elements for token in dictionary.
     * @param {string} source - Source string.
     * @param {string} translation - English translation.
     * @param {string} type - Entity type.
     */
    addDisplay(source, translation, type) {
        if (type) {
            var title = type + ' : ' + translation;
        } else {
            var title = translation;
        }
        $(".df-token").each(function() {
            var token = $(this).attr('data-token').toLowerCase();
            if (token == source) {
                $(this).addClass('df-in-dict');
                $(this).attr('title', title);
                if (this.hasAttribute('data-toggle')) {
                    // bootstrap is a little funky with tooltip updates
                    $(this).attr('title', title).tooltip('fixTitle');
                } else {
                    $(this).attr('data-toggle', 'tooltip');
                    $(this).tooltip({delay: 200, placement: 'auto left', container: 'body'});
                }
            }
        });
    }

    /**
     * Remove display elements for token.
     * @param {string} source - Source string.
     */
    removeDisplay(source) {
        $(".df-token").each(function() {
            var token = $(this).attr('data-token').toLowerCase();
            if (token == source) {
                $(this).removeClass('df-in-dict');
                $(this).removeAttr('title');
                $(this).removeAttr('data-toggle');
                $(this).tooltip('destroy');
            }
        });
    }
};

dragonfly.UndoLevel = class UndoLevel {
    constructor() {
        this.elements = [];
    }

    /**
     * Add a jQuery object representing a token to an undo level.
     * @param {jQuery} element - A token element before a change.
     */
    add(element) {
        if (!this.contains(element)) {
            this.elements.push({
                key: element.attr('id'),
                value: element.clone(true)
            });
        }
    }

    /**
     * Does this undo level already contain this token?
     * @param {jQuery} element - A token element.
     */
    contains(element) {
        var id = element.attr('id');
        for (var i = 0; i < this.elements.length; i++) {
            if (id == this.elements[i].key) {
                return true;
            }
        }
        return false;
    }

    /**
     * Restore the token objects to their original state.
     */
    apply() {
        for (var i = 0; i < this.elements.length; i++) {
            $("#" + this.elements[i].key).replaceWith(this.elements[i].value);
        }
    }
};

dragonfly.Undo = class Undo {
    /**
     * Create an Undo manager.
     * @param {int} capacity - Maximum number of undo levels.
     */
    constructor(capacity) {
        this.capacity = capacity;
        this.items = [];
    }

    /**
     * Start a new undo level.
     */
    start() {
        this.items.unshift(new dragonfly.UndoLevel());
        if (this.items.length > this.capacity) {
            this.items.length = this.capacity;
        }
    }

    /**
     * Remove the latest undo level and return it.
     * @return UndoLevel
     */
    pop() {
        return this.items.shift();
    }

    /**
     * Add a token object to the current undo level.
     * @param {jQuery} element - A token element that is about to be changed.
     */
    add(element) {
        this.items[0].add(element);
    }
};

/** Class representing a tag type. */
dragonfly.TagType = class TagType {
    /**
     * Create a tag type
     * @param {string} name - The tag type name
     */
    constructor(id, name) {
        this.id = id;
        this.name = name;
        this.class = "df-tag-" + id;
        this.start = "B-" + name;
        this.inside = "I-" + name;
    }
};

dragonfly.TagTypes = class TagTypes {
    /**
     * Create all tag types
     * @param {array} tagTypes - Array of tag names
     */
    constructor(tagTypes) {
        this.typeMap = {};
        this.typeList = [];
        for (var i = 0; i < tagTypes.length; i++) {
            var index = '' + (i + 1)
            var object = new dragonfly.TagType(index, tagTypes[i]);
            this.typeMap[index] = object;
            this.typeList.push(object);
        }
    }

    /**
     * Is this a tag type?
     * @param {string} id - Tag type id
     * @return boolean
     */
    isTagType(id) {
        // test if integer
        if (id >>> 0 !== parseFloat(id)) {
            return false;
        }
        return Number(id) <= this.typeList.length;
    }

    /**
     * Get tag type object
     * @param {string} id - Tag type id
     * @return TagType
     */
    getTagType(id) {
        return this.typeMap[id];
    }

    /**
     * Get initial tag type object
     * @return TagType
     */
    getStartTagType() {
        // 1 is the first tag type id
        return this.getTagType('1');
    }

    /**
     * Get tag type object from the full tag string
     * @param {string} value - Tag string
     * @return TagType
     */
    getTagTypeFromString(value) {
        if (value == null || value == "O") {
            return;
        }
        var tagType = value;
        tagType = tagType.slice(2);
        for (var i = 0; i < this.typeList.length; i++) {
            if (this.typeList[i].name == tagType) {
                return this.typeList[i];
            }
        }
    }

    /**
     * Get a map of tag -> integer id
     * @return Object
     */
    getReversedMap() {
        var map = {};
        for (var code in this.typeMap) {
            map[this.typeMap[code].start] = code;
            map[this.typeMap[code].inside] = code;
        }
        return map;
    }
};

dragonfly.MultiTokenTag = class MultiTokenTag {
    /**
     * Create a multi-token tag.
     * @param {TagTypes} tagTypes - TagTypes object with all possible tag types.
     * @param {TagType} tagType - TagType object that represents the entity type.
     */
    constructor(tagTypes, tagType) {
        this.elements = [];
        this.tagTypes = tagTypes;
        this.tagType = tagType;
    }

    /**
     * Add an additional token.
     * @param {jQuery} element - A token element.
     */
    update(element) {
        this.elements.push(element);
    }

    /**
     * Get first element
     * @return {jQuery}
     */
    first() {
        return this.elements[0];
    }

    /**
     * Change the entity type.
     * @param {TagType} tagType - TagType object that represents the entity type.
     */
    setTagType(tagType) {
        this.tagType = tagType;
    }

    /**
     * Get the number of tokens in the tag.
     * @return {int}
     */
    size() {
        return this.elements.length;
    }

};

/**
 * Enum for click mode.
 * @readonly
 * @enum {number}
 */
dragonfly.ClickMode = {DEL: 0, TAG: 1, SELECT: 2, FINDER: 3};

dragonfly.Highlighter = class Highlighter {
    /**
     * Create the highlighter manager.
     * @param {TagTypes} tagTypes - A representation of the tag types.
     * @param {Search} search - Object that manages search.
     */
    constructor(tagTypes, search) {
        this.tagTypes = tagTypes;
        this.search = search;
        this.isCascade = true;
        this.clickMode = dragonfly.ClickMode.TAG;
        this.prevClickMode = dragonfly.ClickMode.TAG;
        this.currentTagType = this.tagTypes.getStartTagType();
        this.multiTokenTag = null;
        this.multiTokenClickCount = 0;
        this.anyTaggingPerformed = false;
        this.selectStart = null;
        this.undo = new dragonfly.Undo(10);
        this.undoActive = false;

        // According to http://unixpapa.com/js/key.html, shift = 16, control = 17, alt = 18, caps lock = 20
        if (/Mac/.test(window.navigator.platform)) {
            // Option key on Macs
            this.multiTokenKey = '18';
            this.multiTokenEventKey = 'altKey';
        } else {
            // Control key for Windows and Linux
            this.multiTokenKey = '17';
            this.multiTokenEventKey = 'ctrlKey';
        }
        this._initializeHandlers();
    }

    _initializeHandlers() {
        var self = this;

        $(".df-token").on("click", function(event) {
            self.clickToken($(this), event);
        });

        $(document).on("keyup", function(event) {
            if (event.which == self.multiTokenKey) {
                self.setControlKeyUp();
            }
        });

        $(window).on(dragonfly.Events.SET_TAG_MODE, function(event, number) {
            self.clickMode = dragonfly.ClickMode.TAG;
            self.currentTagType = self.tagTypes.getTagType(number);
            self.highlightTypeAndClickMode();
        });

        $(window).on(dragonfly.Events.TOGGLE_CASCADE, function() {
            self.toggleCascade();
        });

        $(window).on(dragonfly.Events.UNDO, function() {
            self.processUndo();
        });

        $(window).on(dragonfly.Events.SET_DELETE_MODE, function() {
            self.clickMode = dragonfly.ClickMode.DEL;
            self.highlightTypeAndClickMode();
        });

        $(window).on(dragonfly.Events.SET_SELECT_MODE, function() {
            self.prevClickMode = self.clickMode;
            self.clickMode = dragonfly.ClickMode.SELECT;
            self.highlightTypeAndClickMode();
        });

        $(window).on(dragonfly.Events.SET_FIND_MODE, function() {
            self.prevClickMode = self.clickMode;
            self.clickMode = dragonfly.ClickMode.FINDER;
            self.highlightTypeAndClickMode();
            self.search.show();
        });

        $(window).on(dragonfly.Events.SAVE, function() {
            self.anyTaggingPerformed = false;
        });

        $(window).on(dragonfly.Events.LEAVE, function(event) {
            // if any tagging, return false on leaving the page
            event.result = !self.anyTaggingPerformed;
        });
    }

    /**
     * Toggle the tagging cascade off or on.
     */
    toggleCascade() {
        this.isCascade = !this.isCascade;
        $("#cascade").prop("checked", this.isCascade);
    }

    /**
     * Is the user holding down the multi-token mode key?
     * @param {Event} event - The click event.
     * @return {boolean}
     */
    isMultiTokenOn(event) {
        return event[this.multiTokenEventKey];
    }

    /**
     * Change the internal state for multi-token tagging to off.
     */
    setControlKeyUp() {
        this.multiTokenClickCount = 0;
        // clear incomplete multi-token tag
        if (this.multiTokenTag && this.multiTokenTag.size() > 0) {
            this.processUndo();
        }
        this.multiTokenTag = null;
    }

    /**
     * Get the current tag type.
     * @return {TagType}
     */
    getCurrentTagType() {
        return this.currentTagType;
    }

    /**
     * Update the navbar indicator of click mode and tag type.
     */
    highlightTypeAndClickMode() {
        $(".df-type").removeClass('df-type-active');
        if (this.clickMode == dragonfly.ClickMode.TAG) {
            var className = ".df-tag-" + this.currentTagType.id;
            $(".df-type" + className).addClass('df-type-active');
        } else if (this.clickMode == dragonfly.ClickMode.DEL) {
            $(".df-del").addClass('df-type-active');
        } else if (this.clickMode == dragonfly.ClickMode.SELECT) {
            $(".df-sel").addClass('df-type-active');
        } else {
            $(".df-find").addClass('df-type-active');
        }
    }

    /**
     * Revert to the previous click mode
     * @param {ClickMode} currentMode - only revert if the current click mode is this
     */
    revertClickMode(currentMode) {
        if (this.clickMode == currentMode) {
            this.clickMode = this.prevClickMode;
            this.highlightTypeAndClickMode();
        }
    }

    /**
     * Undo the previous action
     */
    processUndo() {
        var undoAction = this.undo.pop();
        if (undoAction != null) {
            undoAction.apply();
        }
    }

    /**
     * Apply previous annotations for visualization.
     */
    initializeHighlight() {
        var self = this;
        var mismatchedTags = new Set();
        $(".df-token").each(function() {
            var tagValue = $(this).data("tag");
            if (tagValue != null && tagValue != "O") {
                var tagType = self.tagTypes.getTagTypeFromString(tagValue);
                if (typeof tagType !== 'undefined') {
                    self.highlightToken($(this), tagType, tagValue, false);
                } else {
                    // we're loading data with a different tag set
                    mismatchedTags.add(tagValue);
                }
            }
        });
        // don't let people undo the loaded annotations so turn on undo after we're done
        this.undoActive = true;

        if (mismatchedTags.size > 0) {
            var tags = Array.from(mismatchedTags).join(', ');
            dragonfly.showStatus('danger', 'Incompatible saved annotations: ' + tags);
        }

        this.initializeAdjudicationHighlight();
    };

    /**
     * Highlight adjudication rows
     */
    initializeAdjudicationHighlight() {
        var map = this.tagTypes.getReversedMap();
        $(".df-adjudicate").each(function() {
            var value = $(this).text();
            if (value in map) {
                $(this).addClass("df-tag-" + map[value]);
                if (value.charAt(0) == 'B') {
                    $(this).addClass("df-b-tag");
                }
            }
        });
    };

    /**
     * Process a token click.
     * The result depends on what click mode we are in (tagging, delete, select).
     * @param {jQuery} element - Token element clicked.
     * @param {Event} event - The click event.
     */
    clickToken(element, event) {
        if (this.clickMode == dragonfly.ClickMode.DEL) {
            // set this so we know whether to prevent user navigating away
            this.anyTaggingPerformed = true;
            this.undo.start();
            this.undo.add(element);
            this.deleteTag(element);
        } else if (this.clickMode == dragonfly.ClickMode.SELECT) {
            this.select(element);
        } else if (this.clickMode == dragonfly.ClickMode.FINDER) {
            this.search.searchFiles(element.attr('data-token'), false);
        } else {
            // set this so we know whether to prevent user navigating away
            this.anyTaggingPerformed = true;

            if (this.isMultiTokenOn(event)) {
                this.handleMultiTokenClick(element);
            } else {
                this.undo.start();
                var tagType = this.currentTagType;
                this.highlightToken(element, tagType, tagType.start, this.isCascade);
            }
        }
    }

    /**
     * Handle the clicks when the control/option key is down for multi-token tagging
     * @param {jQuery} element - Token div that was clicked
     */
    handleMultiTokenClick(element) {
        this.multiTokenClickCount = this.multiTokenClickCount + 1;

        if (this.multiTokenClickCount == 1) {
            this.undo.start();
            // first click in multi-token tag
            this.multiTokenTag = new dragonfly.MultiTokenTag(this.tagTypes, this.currentTagType);
            this.multiTokenTag.update(element);
            this.highlightMultiTokenTag(this.multiTokenTag);
        } else if (this.multiTokenClickCount == 2) {
            // final click in multi-token tag
            var firstElement = this.multiTokenTag.first();
            var lastElement = element;

            // df-token-[row]-[col]
            var firstElementRow = parseInt($(firstElement).attr('id').split("-")[2])
            var firstElementCol = parseInt($(firstElement).attr('id').split("-")[3])
            var lastElementRow = parseInt($(lastElement).attr('id').split("-")[2])
            var lastElementCol = parseInt($(lastElement).attr('id').split("-")[3])

            if (firstElementRow == lastElementRow && firstElementCol < lastElementCol) {
                for (var i = firstElementCol + 1; i <= lastElementCol; i++) {
                    var elementId = '#df-token-' + firstElementRow + '-' + i;
                    this.multiTokenTag.update($(elementId));
                }

                if (this.isCascade) {
                    this.highlightMultiTokenTag(this.multiTokenTag);
                    this.cascadeMultiTokenTag(this.multiTokenTag);
                } else {
                    this.highlightMultiTokenTag(this.multiTokenTag);
                }
                this.multiTokenTag = null;
            } else {
                dragonfly.showStatus('danger', "Tagging must be left to right on the same line. Invalid tag cleared.");
            }
        }
    }

    /**
     * Highlight a token and possibly perform a cascade to other tokens.
     * @param {jQuery} token - The token element to highlight.
     * @param {TagType} tagType - The tag type to apply.
     * @param {string} string - The tag string (B-PER, I-ORG).
     * @param {boolean} cascade - Whether to cascade this to matching tokens.
     * @param {boolean} inferred - Is this a result of a cascade?
     * @return {boolean} Was the token highlighted?
     */
    highlightToken(token, tagType, string, cascade, inferred=false) {
        var self = this;
        if (inferred && token.data("inferred") != null && !token.data("inferred")) {
            return false;
        }

        if (this.undoActive) {
            this.undo.add(token);
        }

        token.data("tag", string);
        token.data("inferred", inferred);

        var in_dict = token.attr('class').indexOf('df-in-dict') !== -1;

        var classes = "df-token";
        if (string.charAt(0) == 'B') {
            classes += " df-b-tag";
        }
        classes += " df-tag-" + tagType.id;
        if (in_dict) {
            classes += " df-in-dict";
        }
        token.attr('class', classes);

        var tokenText = token.attr('data-token').toLowerCase();
        var count = 0;
        if (cascade) {
            $(".df-token").each(function() {
                if (tokenText == $(this).attr('data-token').toLowerCase()) {
                    if (self.highlightToken($(this), tagType, string, false, true)) {
                        count += 1;
                    }
                }
            });
            dragonfly.showStatus('success', 'Cascade: ' + parseInt(count));
        }

        return true;
    }

    /**
     * Highlight a multi-token tag.
     * @param {MultiTokenTag} tag - Object with all the token elements.
     */
    highlightMultiTokenTag(tag) {
        for (var i = 0; i < tag.elements.length; i++) {
            if (i == 0) {
                this.highlightToken(tag.elements[i], tag.tagType, tag.tagType.start, false);
            } else {
                this.highlightToken(tag.elements[i], tag.tagType, tag.tagType.inside, false);
            }
        }
    }

    /**
     * Cascade a multi-token tag.
     * @param {MultiTokenTag} tag - Object with all the token elements.
     */
    cascadeMultiTokenTag(tag) {
        var self = this;
        var firstTokenText = tag.elements[0].attr('data-token').toLowerCase();
        var count = 0;
        $(".df-token").each(function() {
            if (firstTokenText == $(this).attr('data-token').toLowerCase()) {
                if (tag.elements[0].attr("id") == $(this).attr("id")) {
                    return;
                }
                var tagValue = $(this).data("tag");
                // this checks for any entity tag (but not untagged or O tags)
                if (tagValue != null && tagValue.indexOf("-") != -1) {
                    return;
                }
                // start building the multi-token tag as we match so far
                var newTag = new dragonfly.MultiTokenTag(self.tagTypes, tag.tagType);
                newTag.update($(this));
                // get the next token
                var idChunks = $(this).attr("id").split("-");
                for (var i = 1; i < tag.elements.length; i++) {
                    idChunks[idChunks.length - 1]++;
                    var nextToken = $("#" + idChunks.join("-"));
                    if (nextToken.length) {
                        var tagValue = nextToken.data("tag");
                        // this checks for any entity tag (but not untagged or O tags)
                        if (tagValue != null && tagValue.indexOf("-") != -1) {
                            return;
                        }
                        var tokenText = tag.elements[i].attr('data-token').toLowerCase();
                        if (tokenText != nextToken.attr('data-token').toLowerCase()) {
                            return;
                        }
                        newTag.update(nextToken);
                    } else {
                        return;
                    }
                }
                self.highlightMultiTokenTag(newTag);
                count += 1;
            }
        });
        dragonfly.showStatus('success', 'Cascade: ' + parseInt(count));
    }

    /**
     * Delete a tag.
     * @param {jQuery} token - The token element to remove tagging from.
     */
    deleteTag(token) {
        token.removeData("tag");
        token.removeAttr("data-tag");
        token.removeData("inferred");
        token.attr('class', 'df-token');
    }

    /**
     * Select a token or token range to copy.
     * @param {jQuery} token - Token element selected for copying.
     */
    select(token) {
        if (this.selectStart == null) {
            this.selectStart = token.parent();
        } else {
            // copy text from the child of each df-section
            var text = this.selectStart.children().first().attr('data-token');
            if (!this.selectStart.is(token.parent())) {
                this.selectStart.nextUntil(token.parent()).each(function() {
                    text = text.concat(' ', $(this).children().first().attr('data-token'));
                });
                text = text.concat(' ', token.attr('data-token'));
            }
            copyToClipboard(text);
            this.selectStart = null;
            this.revertClickMode(dragonfly.ClickMode.SELECT);
            dragonfly.showStatus('success', 'Copied');
        }
    }
};

dragonfly.AnnotationSaver = class AnnotationSaver {
    /**
     * Create an annotation saver.
     * @param {string} filename - The filename being edited.
     * @param {Settings} settings - Dragonfly settings.
     * @param {Highlighter} highlighter - Dragonfly highlighter.
     * @param {boolean} terminalBlankLine - Whether to write blank line to end of file.
     * @param {boolean} viewOnly - In view only mode, there is no saving.
     */
    constructor(filename, settings, highlighter, terminalBlankLine, viewOnly) {
        this.filename = filename;
        this.settings = settings;
        this.highlighter = highlighter;
        this.terminalBlankLine = terminalBlankLine;
        this.viewOnly = viewOnly;
        this.saveClicked = false;
        this.timerId = null;

        var self = this;

        $(window).on(dragonfly.Events.SAVE, function() {
            self.save();
        });

        // prevent user from navigating away with unsaved annotations
        if (!this.viewOnly) {
            $(window).on("beforeunload", function() {
                // ask if we can leave this page (return false to stop)
                var event = jQuery.Event(dragonfly.Events.LEAVE);
                $(window).trigger(event);
                if (!event.result) {
                    if (self.settings.isAutoSaveOnNav()) {
                        self.save(false);
                    } else {
                        // this actual text may not display depending on browser
                        return "Changes have not been saved.";
                    }
                }
            });
        }

        self._configureAutoSave();
        $(window).on(dragonfly.Events.CHANGE_SETTINGS, function() {
            self._configureAutoSave();
        });
    }

    /**
     * Save the annotations.
     * @param {boolean} notify - Whether to notify the user the annotations have been saved.
     */
    save(notify = true) {
        if (this.viewOnly) {
            return;
        }

        var self = this;
        this.saveClicked = true;
        var data = {
            filename: this.filename,
            tokens: this._collectAnnotations()
        };
        $.ajax({
            url: 'save',
            type: 'POST',
            data: {json: JSON.stringify(data)},
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    if (notify) {
                        dragonfly.showStatus('success', response.message);
                    }
                } else {
                    dragonfly.showStatus('danger', response.message);
                }
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Collect annotations from the DOM.
     * @return {array} An array of token tag information.
     */
    _collectAnnotations() {
        var tokens = [];
        // df-sentence only used for annotation text
        $(".df-sentence").each(function() {
            $(this).find(".df-token").each(function() {
                var tagValue = $(this).data('tag');
                var tokenText = $(this).attr('data-token');
                if (tagValue != null) {
                    var token = {token: tokenText, tag: tagValue }
                } else {
                    var token = {token: tokenText, tag: 'O'}
                }
                tokens.push(token);
            });
            // end of sentence gets a blank line
            tokens.push({});
        });
        if (!this.terminalBlankLine) {
            tokens.pop();
        }
        return tokens;
    }

    _configureAutoSave() {
        if (this.settings.isAutoSave()) {
            if (this.timerId == null) {
                // save once a minute
                var self = this;
                this.timerId = window.setInterval(function() {self.save(false)}, 60*1000);
            }
        } else {
            if (this.timerId != null) {
                window.clearInterval(this.timerId);
                this.timerId = null;
            }
        }
    }
};

$(document).ready(function() {
    dragonfly.lang = $("meta[name=lang]").attr("content");
    dragonfly.filename = dragonfly_filename;
    var view_only = $(".df-body").hasClass('df-mode-viewer');
    dragonfly.tagTypes = new dragonfly.TagTypes(dragonfly_tags);
    dragonfly.eventDispatcher = new dragonfly.EventDispatcher(dragonfly.tagTypes);
    dragonfly.settings = new dragonfly.Settings(dragonfly_settings);
    dragonfly.search = new dragonfly.Search(dragonfly.settings);
    dragonfly.highlighter = new dragonfly.Highlighter(dragonfly.tagTypes, dragonfly.search);
    dragonfly.highlighter.initializeHighlight();
    dragonfly.annotationSaver = new dragonfly.AnnotationSaver(dragonfly.filename, dragonfly.settings,
        dragonfly.highlighter, dragonfly_terminal_blank_line, view_only);
    dragonfly.translations = new dragonfly.Translations(dragonfly.lang);
    dragonfly.translations.load();
    dragonfly.contextMenu = new dragonfly.ContextMenu(dragonfly.translations);
    dragonfly.hints = new dragonfly.Hints(dragonfly.settings.getHintsRow());
    dragonfly.hints.run();
    dragonfly.markers = new dragonfly.Markers();
    dragonfly.notepad = new dragonfly.Notepad(dragonfly.filename, dragonfly.settings.areNotesDocumentSpecific());

    $(window).on(dragonfly.Events.NEXT, function() {
        var url = $('#df-next-doc').attr('href');
        if (url) {
            window.location.href = url;
        }
    });

    $(window).on(dragonfly.Events.PREVIOUS, function() {
        var url = $('#df-prev-doc').attr('href');
        if (url) {
            window.location.href = url;
        }
    });

    // keep the sentence IDs in same location as user horizontally scrolls if desired
    $('.df-main').scroll(function() {
        if (dragonfly.settings.isSentenceIdAutoScroll()) {
            $('.df-sentence-id').css({
                'left': $(this).scrollLeft(),
                'height': ($(".df-sentence").height()) + 'px'
            });
        }
    });

    $('#df-stats-modal').on('show.bs.modal', function(event) {
        var body = $(this).find('.modal-body');
        body.load('stats');
        $('#df-stats-button').one('focus', function(event) {
            $(this).blur();
        });
    });

    $('#df-tools-modal').on('show.bs.modal', function(event) {
        var body = $(this).find('.modal-body');
        body.load('tools');
        $('#df-tools-button').one('focus', function(event) {
            $(this).blur();
        });
    });
});
