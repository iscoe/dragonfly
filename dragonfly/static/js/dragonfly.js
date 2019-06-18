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

dragonfly.Settings = class Settings {
    /**
     * Create a Settings object
     * @param {object} settings - Settings object
     * @param {AnnotationSaver} annotationSaver - object for background saving of user annotations
     */
    constructor(settings, annotationSaver) {
        this.settings = settings;
        this.timerId = null;
        this.annotationSaver = annotationSaver;
        this._initializeHandlers();
    }

    _initializeHandlers() {
        var self = this;

        $('#df-settings-modal').on('show.bs.modal', function(event) {
            var body = $(this).find('.modal-body');
            body.load('/settings');
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

    getFinderHeight() {
        return this.settings['Finder Height'];
    }

    isFinderOpenDefault() {
        return this.settings['Finder Starts Open'];
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

    /**
     * Apply the current settings to the page
     * @param {boolean} first - Is this the first run of apply
     */
    apply(first) {
        if (!this.isDisplayRowLabels()) {
            $(".df-column-labels").hide();
        } else {
            $(".df-column-labels").show();
        }
        if (this.isAutoSave()) {
            if (this.timerId == null) {
                var self = this;
                var autoSave = function() {self.annotationSaver.save(false)};
                this.timerId = window.setInterval(autoSave, 60*1000);
            }
        } else {
            if (this.timerId != null) {
                window.clearInterval(this.timerId);
                this.timerId = null;
            }
        }
        if (this.isCascadeOn() != $("#cascade").prop("checked")) {
            $(document).trigger({type: 'keypress', which: 'c'.charCodeAt(0), ctrlKey: false});
        }

        if (first && this.isFinderOpenDefault()) {
            $(window).trigger('df.finder.show');
        }
    }

    /**
     * Save the settings object through ajax to server.
     */
    _save() {
        var self = this;
        this.settings = this._convertToObject($("#df-settings-form").serializeArray());
        $.ajax({
            url: '/settings',
            type: 'POST',
            data: {json: JSON.stringify(this.settings)},
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    dragonfly.showStatus('success', response.message);
                    self.apply(false);
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


/** context menu used for adding user provided translations */
dragonfly.ContextMenu = class ContextMenu {
    // TODO probably replace with a custom event to communicate to highlighter/translations
    constructor(highlighter, translationManager) {
        this.highlighter = highlighter;
        this.translationManager = translationManager;
    }

    /**
     * Show the context menu.
     * @param {jQuery} token - The token element clicked on.
     * @param {Event} event - The click event for location information.
     */
    show(token, event) {
        var self = this;

        event.preventDefault();
        var top = event.pageY;
        var left = event.pageX;
        $("#df-context-menu").css({top: top, left: left, position:'absolute'});
        var sourceInfo = this.getSource(token);
        if (sourceInfo === null) {
            return;
        }
        $("#df-trans-source").html(sourceInfo['text']);
        $("input[name = 'entity-type']").val(sourceInfo['type']);
        $("input[name = 'translation']").val(sourceInfo['trans']);
        $("#df-context-menu").removeClass('hidden');
        $("input[name = 'translation']").focus();

        $(document).one("click", function() {
            self.hide();
        });
        $("#df-context-menu").on('click', function(event) {
            event.stopPropagation();
        });

        this.highlighter.contextMenuActive = true;
    }

    /**
     * Get the information about the tag like type and text
     * @param {jQuery} token - Token element for tag
     * @return {object} - initial values
     */
    getSource(token) {
        var result = {'type': null, 'trans': null};
        var tag = token.data('tag');
        if (tag == null || tag == 'O') {
            result['text'] = token.html();
        } else {
            result['text'] = token.html();
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
    hide() {
        this.highlighter.contextMenuActive = false;
        $("#df-context-menu").addClass('hidden');
        $("input[name = 'translation']").val('');
        $("input[name = 'entity-type']").val('');
    }

    /**
     * Save the translation through ajax to server.
     */
    save() {
        var self = this;
        var translation = $("input[name = 'translation']").val();
        var entityType = $("input[name = 'entity-type']").val();
        if (translation.length == 0) {
            this.hide();
            return;
        }
        var data = {
            'source': $("#df-trans-source").html(),
            'translation': translation,
            'type': entityType,
            'lang': dragonfly.lang
        };
        $.ajax({
            url: '/translation',
            type: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    dragonfly.showStatus('success', response.message);
                    self.hide();
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
    remove() {
        var self = this;
        var data = {
            'source': $("#df-trans-source").html(),
            'lang': dragonfly.lang,
        };
        $.ajax({
            url: '/translation/delete',
            type: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            success: function(response) {
                self.hide();
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

dragonfly.Hints = class Hints {
    /**
     * Create a hints manager.
     * @param {int} row - Zero-based index of row to apply hints to.
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
            url: '/hints',
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
        // TODO row is hard coded to the second row (usually transliteration)
        $(".df-row div:nth-child(2)").each(function() {
            for (var i = 0; i < self.hints.length; i++) {
                var text = $(this).text();
                var match = text.match(self.hints[i].regex);
                if (match != null) {
                    var new_text = '<span class="df-hint" title="' + self.hints[i].comment + '">' + match[0] + '</span>';
                    $(this).html(text.replace(match[0], new_text));
                    return;
                }
            }
        });
    }
};

dragonfly.Markers = class Markers {

    /**
     * Toggle the marker.
     * @param {jQuery} element - Marker being toggled.
     */
    toggle(element) {
        element.toggleClass("df-complete");
        $.ajax({
            url: '/marker',
            type: 'POST',
            data: {'document': dragonfly.filename, 'sentence': element.html()},
            dataType: 'json',
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Clear all markers
     */
    clear() {
        var self = this;
        $(".df-complete").each(function() {
            self.toggle($(this));
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
            url: '/translations/' + this.lang,
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
            var token = $(this).html().toLowerCase();
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
            var token = $(this).html().toLowerCase();
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
            var token = $(this).html().toLowerCase();
            if (token == source) {
                $(this).removeClass('df-in-dict');
                $(this).removeAttr('title');
                $(this).removeAttr('data-toggle');
                $(this).tooltip('destroy');
            }
        });
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

    /**
     * Add tag type buttons to DOM
     */
    injectButtons() {
        for (var i = this.typeList.length - 1; i >= 0; i--) {
            var id = this.typeList[i].id;
            var label = this.typeList[i].name;
            $('.navbar-labels').prepend('<span class="navbar-text label df-type df-tag-' + id + '" title="' + id + '">' + label + '</span>');
        }
        $('.navbar-labels span:first-child').addClass('df-type-active');
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


dragonfly.Finder = class Finder {
    /**
     * Create a Finder object
     * @param {Settings} settings - Settings manager
     */
    constructor(settings) {
        this.Mode = {LOCAL: 0, GOOGLE: 1, GMAPS: 2}
        this.minimizedHeight = $('.df-finder').height();
        this.settings = settings;
        // this casues jQuery to cache inline-block as the default show state
        $('.df-finder-google').hide();
        $('.df-finder-gmaps').hide();

        this.googleInitialized = false;
        this.gmapsInitialized = false;
        this._initializeHandlers();
    }

    /**
     * Search the local index
     */
    search(word) {
        $('input[name=df-finder-term]').val(word);
        this.postSearch(word);
    }

    /**
     * Submit a search to the server
     * @param {string} word - Search term.
     */
    postSearch(word) {
        var self = this;
        $.ajax({
            url: '/search',
            type: 'POST',
            data: {'term': word},
            dataType: 'json',
            success: function(data) {
                self.displayResults(word, data);
            },
            error: function(xhr) {
                dragonfly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    _initializeHandlers() {
        var self = this;
        // support resizing the finder window with the mouse
        $('.df-finder').resizable({
            handleSelector: '.df-resize-bar',
            resizeWidth: false,
            resizeHeightFrom: 'top',
        });

        $(window).on('df.finder.show', function(event) {
            self.show();
        });

        $('#df-finder-local-form').on('submit', function(event) {
            event.preventDefault();
            self.search($('input[name=df-finder-term]').val());
        });

        $('#df-finder-close').on('click', function() {
            self.hide();
            dragonfly.highlighter.revertClickMode();
        });

        $('#df-finder-use-local').on('click', function() {
            self.use(self.Mode.LOCAL);
        });

        $('#df-finder-use-google').on('click', function() {
            self.use(self.Mode.GOOGLE);
        });

        $('#df-finder-use-gmaps').on('click', function() {
            self.use(self.Mode.GMAPS);
        });
    }

    /**
     * Load the custom Google search engine
     */
    initializeGoogle() {
        var cx = '003899999982319279749:whnyex5nm1c';
        var gcse = document.createElement('script');
        gcse.type = 'text/javascript';
        gcse.async = true;
        gcse.src = 'https://cse.google.com/cse.js?cx=' + cx;
        var s = document.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(gcse, s);
    }

    /**
     * Load the Google Maps places engine
     */
    initializeGMaps() {
        var key = this.settings.getGMapsKey();
        var src = "https://maps.googleapis.com/maps/api/js?key=" + key;
        src += "&libraries=places&callback=dragonfly.finder.initializeGMapsCallback";
        var gmse = document.createElement('script');
        gmse.type = 'text/javascript';
        gmse.async = true;
        gmse.src = src;
        var s = document.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(gmse, s);
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

    /**
     * Update the results display box
     * @param {string} word - The search term.
     * @param {array} data - Data object from the local search server.
     */
    displayResults(word, data) {
        word = word.toLowerCase();
        var html = '';
        $('.df-term-count').html("Count: " + data.count);
        var refs = data.refs;
        for (var i=0; i<refs.length; i++) {
            html += '<div class="df-result">';
            html += this.getOpenButton(refs[i].doc);
            for (var j=0; j<refs[i].text.length; j++){
                html += '<div class="df-section df-row">';
                if (word == refs[i].text[j]) {
                    html += '<div class="df-result-highlight">' + refs[i].text[j] + '</div>';
                } else {
                    html += '<div>' + refs[i].text[j] + '</div>';
                }
                if (refs[i].trans != null) {
                    html += '<div>' + refs[i].trans[j] + '</div>';
                }
                html += "</div>";
            }
            html += "</div>";
            html += '<div class="df-result-doc">';
            html += '</div>';
        }
        $('.df-results-local').html(html);
    }

    /**
     * Create an open button
     * @param {string} doc - Document name.
     * @return html string
     */
    getOpenButton(doc) {
        var html = '<div class="df-open">';
        html += '<a class="btn btn-default" title="open in new tab" href="/' + doc + '" target="_blank">';
        html += '<span class="glyphicon glyphicon-new-window" aria-hidden="true" />';
        html += '</a></div>';
        return html;
    }

    /**
     * Show the finder window
     */
    show() {
        var cw = $('.df-finder');
        if (cw.height() < 100) {
            cw.height(this.settings.getFinderHeight());
        }
    }

    /**
     * Hide the finder window
     */
    hide() {
        $('.df-finder').height(this.minimizedHeight);
    }

    /**
     * Toggle between search modes
     * @param {Mode} mode - Search mode
     */
    use(mode) {
        if (mode == this.Mode.LOCAL) {
            $('.df-finder-local').show();
            $('.df-results-local').show();
            $('.df-finder-google').hide();
            $('.df-results-google').hide();
            $('.df-finder-gmaps').hide();
            $('.df-results-gmaps').hide();
        } else if (mode == this.Mode.GOOGLE) {
            if (!this.googleInitialized) {
                this.googleInitialized = true;
                this.initializeGoogle();
            }
            $('.df-finder-local').hide();
            $('.df-results-local').hide();
            $('.df-finder-google').show();
            $('.df-results-google').show();
            $('.df-finder-gmaps').hide();
            $('.df-results-gmaps').hide();
        } else if (mode == this.Mode.GMAPS) {
            if (!this.gmapsInitialized) {
                this.gmapsInitialized = true;
                this.initializeGMaps();
            }
            $('.df-finder-local').hide();
            $('.df-results-local').hide();
            $('.df-finder-google').hide();
            $('.df-results-google').hide();
            $('.df-finder-gmaps').show();
            $('.df-results-gmaps').show();
        }
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
     * @param {Finder} finder - Object that manages search.
     */
    constructor(tagTypes, finder) {
        this.tagTypes = tagTypes;
        this.finder = finder;
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
        this.contextMenuActive = false;
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
        return event[dragonfly.multiTokenEventKey];
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
     */
    revertClickMode() {
        this.clickMode = this.prevClickMode;
        this.highlightTypeAndClickMode();
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
            dragonfly.showStatus('danger', 'Incompatiable saved annotations: ' + tags);
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
     * Process a user key press.
     * @param {string} letter - The letter the user pressed.
     */
    pressKey(letter) {
        if (this.contextMenuActive) {
            return;
        }

        // handle token independent key controls first
        switch (letter) {
            case 'c':
                // toggle cascade
                this.toggleCascade();
                break;
            case '0':
            case 'd':
                // enter into delete mode
                this.clickMode = dragonfly.ClickMode.DEL;
                this.highlightTypeAndClickMode();
                break;
            case 's':
                // enter into select mode
                this.prevClickMode = this.clickMode;
                this.clickMode = dragonfly.ClickMode.SELECT;
                this.highlightTypeAndClickMode();
                break;
            case 'f':
                // finder mode
                this.prevClickMode = this.clickMode;
                this.clickMode = dragonfly.ClickMode.FINDER;
                this.highlightTypeAndClickMode();
                this.finder.show();
                break;
            case 'u':
                this.processUndo();
                break;
            default:
                if (this.tagTypes.isTagType(letter)) {
                    // change the tag type
                    this.clickMode = dragonfly.ClickMode.TAG;
                    this.currentTagType = this.tagTypes.getTagType(letter);
                    this.highlightTypeAndClickMode();
                }
                break;
        }
    }

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
            this.finder.search(element.html());
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

        var tokenText = token.html().toLowerCase();
        var count = 0;
        if (cascade) {
            $(".df-token").each(function() {
                if (tokenText == $(this).html().toLowerCase()) {
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
        var firstTokenText = tag.elements[0].html().toLowerCase();
        var count = 0;
        $(".df-token").each(function() {
            if (firstTokenText == $(this).html().toLowerCase()) {
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
                        var tokenText = tag.elements[i].html().toLowerCase();
                        if (tokenText != nextToken.html().toLowerCase()) {
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
            var text = this.selectStart.children().first().html();
            if (!this.selectStart.is(token.parent())) {
                this.selectStart.nextUntil(token.parent()).each(function() {
                    text = text.concat(' ', $(this).children().first().html());
                });
                text = text.concat(' ', token.html());
            }
            copyToClipboard(text);
            this.selectStart = null;
            this.revertClickMode();
            dragonfly.showStatus('success', 'Copied');
        }
    }
};

dragonfly.AnnotationSaver = class AnnotationSaver {
    /**
     * Create an annotation saver.
     * @param {string} filename - The filename being edited.
     */
    constructor(filename, terminalBlankLine) {
        this.filename = filename;
        this.saveClicked = false;
        this.terminalBlankLine = terminalBlankLine;
    }

    /**
     * Save the annotations.
     */
    save(notify = true) {
        var self = this;
        this.saveClicked = true;
        var data = {
            filename: this.filename,
            tokens: this.collectAnnotations()
        };
        $.ajax({
            url: '/save',
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
    collectAnnotations() {
        var tokens = [];
        $(".df-sentence").each(function() {
            $(this).find(".df-token").each(function() {
                var tagValue = $(this).data('tag');
                if (tagValue != null) {
                    var token = {token: $(this).html(), tag: tagValue }
                } else {
                    var token = {token: $(this).html(), tag: 'O'}
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
};

$(document).ready(function() {
    // According to http://unixpapa.com/js/key.html, shift = 16, control = 17, alt = 18, caps lock = 20
    if (/Mac/.test(window.navigator.platform)) {
        // Option key on Macs
        dragonfly.multiTokenKey = '18';
        dragonfly.multiTokenEventKey = 'altKey';
    } else {
        // Control key for Windows and Linux
        dragonfly.multiTokenKey = '17';
        dragonfly.multiTokenEventKey = 'ctrlKey';
    }

    this.multiTokenTagClickCount = 0;

    dragonfly.lang = $("meta[name=lang]").attr("content");
    dragonfly.filename = dragonfly_filename;
    dragonfly.tagTypes = new dragonfly.TagTypes(dragonfly_tags);
    dragonfly.tagTypes.injectButtons();
    dragonfly.annotationSaver = new dragonfly.AnnotationSaver(dragonfly.filename, dragonfly_terminal_blank_line);
    dragonfly.settings = new dragonfly.Settings(dragonfly_settings, dragonfly.annotationSaver);
    dragonfly.finder = new dragonfly.Finder(dragonfly.settings);
    dragonfly.highlighter = new dragonfly.Highlighter(dragonfly.tagTypes, dragonfly.finder);
    dragonfly.highlighter.initializeHighlight();
    dragonfly.hints = new dragonfly.Hints(1);
    dragonfly.hints.run();
    dragonfly.markers = new dragonfly.Markers();
    dragonfly.translations = new dragonfly.Translations(dragonfly.lang);
    dragonfly.translations.load();
    dragonfly.contextMenu = new dragonfly.ContextMenu(dragonfly.highlighter, dragonfly.translations);
    dragonfly.settings.apply(true);

    $("input[id = 'cascade']").on("click", function() {
        dragonfly.highlighter.toggleCascade();
    });

    $(".df-token").on("click", function(event) {
        dragonfly.highlighter.clickToken($(this), event);
    });

    $(document).on("keypress", function(event) {
        if (!$(event.target).is("input")) {
            dragonfly.highlighter.pressKey(String.fromCharCode(event.which));
        }
    });

    $(document).on("keyup", function(event) {
        if (event.which == dragonfly.multiTokenKey) {
            dragonfly.highlighter.setControlKeyUp();
        }
    });

    // ctrl+s for save annotations and ctrl+arrow for navigation
    $(document).on("keydown", function(event) {
        if (event.ctrlKey || event.metaKey) {
            if (String.fromCharCode(event.which).toLowerCase() == 's') {
                event.preventDefault();
                dragonfly.annotationSaver.save();
            } else if (event.which == 37) {
                // left arrow
                var url = $('#df-prev-doc').attr('href');
                if (url) {
                    window.location.href = url;
                }
            } else if (event.which == 39) {
                // right arrow
                var url = $('#df-next-doc').attr('href');
                if (url) {
                    window.location.href = url;
                }
            }
        } else {
            if (event.which == 46) {
                // delete key
                dragonfly.markers.clear();
            }
        }
    });

    // change the click mode or tag type by clicking on navbar
    $(".df-type").on("click", function(event) {
        var letter = $(this).attr("title");
        dragonfly.highlighter.pressKey(letter);
    });

    // user can indicate which sentences have been reviewed
    $(".df-sentence-badge").on("click", function(event) {
        dragonfly.markers.toggle($(this));
    });

    $("#df-save").on("click", function(event) {
        dragonfly.annotationSaver.save();
        $(this).blur();
    });

    $(".df-token").on("contextmenu", function(event) {
        dragonfly.contextMenu.show($(this), event);
    });

    $("#df-context-menu-submit").on('click', function(event) {
        dragonfly.contextMenu.save();
        event.preventDefault();
    });

    $("#df-context-menu-delete").on('click', function(event) {
        dragonfly.contextMenu.remove();
        event.preventDefault();
    });

    $(window).on("beforeunload", function() {
        if (dragonfly.highlighter.anyTaggingPerformed && !dragonfly.annotationSaver.saveClicked) {
            if (dragonfly.settings.isAutoSaveOnNav()) {
                dragonfly.annotationSaver.save(false);
            } else {
                // this actual text may not display depending on browser
                return "Changes have not been saved.";
            }
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
        body.load('/stats');
        $('#df-stats-button').one('focus', function(event) {
            $(this).blur();
        });
    });

    $('#df-tools-modal').on('show.bs.modal', function(event) {
        var body = $(this).find('.modal-body');
        body.load('/tools');
        $('#df-tools-button').one('focus', function(event) {
            $(this).blur();
        });
    });
});
