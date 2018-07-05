/**
 * Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
 * All rights reserved.
 * Distributed under the terms of the Apache 2.0 License.
 */

var dragonFly =  dragonFly || {};

/**
 * Show status message.
 * @param {string} type - 'success' or 'danger'.
 * @param {string} text - The text to display.
 */
dragonFly.showStatus = function(type, text) {
    $(".alerts").append('<div class="alert alert-' + type + ' alert-dismissable">' +
            '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>' +
            text +'</div>');
    if (type == "success") {
        $(".alerts").children().delay(4000).fadeTo(1000, 0, function() {
            $(this).alert('close');
        });
    }
};

dragonFly.Settings = class Settings {
    constructor(annotationSaver) {
        this.settings = {};
        this.timerId = null;
        this.annotationSaver = annotationSaver;
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

    /**
     * Load settings from server.
     * This uses ajax to load the settings object.
     */
    load() {
        var self = this;
        $.ajax({
            url: '/settings',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                self.settings = data;
                self.generateHtml();
                self.applySettings();
            },
            error: function(xhr) {
                dragonFly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Generate the html for the settings form.
     */
    generateHtml() {
        var textParent = $("#df-settings-section-text");
        var textTemplate = textParent.children().first();
        textTemplate.remove();

        var checkboxParent = $("#df-settings-section-checkbox");
        var checkboxTemplate = checkboxParent.children().first();
        checkboxTemplate.remove();

        var textSettings = [];
        var boolSettings = [];
        for (var prop in this.settings) {
            if (typeof this.settings[prop] === 'boolean') {
                boolSettings.push({label: prop, value: this.settings[prop]});
            } else {
                textSettings.push({label: prop, value: this.settings[prop]});
            }
        }

        for (var i = 0; i < textSettings.length; i++) {
            var setting = textSettings[i];
            var item = textTemplate.clone();
            item.find("label").text(setting.label);
            item.find("input").attr("name", setting.label);
            item.find("input").val(setting.value);
            textParent.append(item);
        }

        for (var i = 0; i < boolSettings.length; i++) {
            var setting = boolSettings[i];
            var item = checkboxTemplate.clone();
            item.find("span").html(setting.label);
            item.find("input").attr("name", setting.label);
            if (setting.value) {
                item.find("input:checkbox").prop('checked', true);
            }
            checkboxParent.append(item);
        }
    }

    /**
     * Apply the current settings to the page
     */
    applySettings() {
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
    }

    /**
     * Save the settings object through ajax to server.
     */
    save() {
        var self = this;
        this.settings = this.convertToObject($("#df-settings-form").serializeArray());
        $.ajax({
            url: '/settings',
            type: 'POST',
            data: {json: JSON.stringify(this.settings)},
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    dragonFly.showStatus('success', response.message);
                    self.applySettings();
                } else {
                    dragonFly.showStatus('danger', response.message);
                }
            },
            error: function(xhr) {
                dragonFly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Convert the array that represents the form to a settings object.
     * @param {array} array - Array from serializeArray().
     * @return {object}
     */
    convertToObject(array) {
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

dragonFly.ContextMenu = class ContextMenu {
    // TODO probably replace with a custom event
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

    getSource(token) {
        var result = {'type': null};
        var tag = token.data('tag');
        if (tag == null || tag == 'O') {
            result['text'] = token.html();
        } else {
            if (tag.includes('I-')) {
                dragonFly.showStatus('danger', "You must click the first tag of a sequence");
                return null;
            }
            var text = token.html();
            var tagString = tag.replace('B', 'I');
            result['type'] = tag.replace('B-', '');
            var idChunks = token.attr("id").split("-");
            while (true) {
                idChunks[idChunks.length - 1]++;
                var nextToken = $("#" + idChunks.join("-"));
                if (nextToken.length) {
                    if (nextToken.data('tag') == tagString) {
                        text = text.concat(' ', nextToken.html());
                    } else {
                        break;
                    }
                } else {
                    break;
                }
            }
            result['text'] = text;
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
            'lang': dragonFly.lang
        };
        $.ajax({
            url: '/translation',
            type: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            success: function(response) {
                if (response.success) {
                    dragonFly.showStatus('success', response.message);
                    self.hide();
                    self.translationManager.update(data.source, data.translation);
                } else {
                    dragonFly.showStatus('danger', response.message);
                }
            },
            error: function(xhr) {
                dragonFly.showStatus('danger', 'Error contacting the server');
            }
        });
    }
};

dragonFly.UndoLevel = class UndoLevel {
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

dragonFly.Undo = class Undo {
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
        this.items.unshift(new dragonFly.UndoLevel());
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

dragonFly.Hints = class Hints {
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
                dragonFly.showStatus('danger', 'Error contacting the server');
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
                dragonFly.showStatus('danger', 'Invalid hint regex: ' + escapeHtml(this.hints[i].regex));
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

dragonFly.Translations = class Translations {
    /**
     * Create a translations manager.
     */
    constructor(lang) {
        this.lang = lang;
        this.translations = [];
        this.stopWords = [];
        this.transMap = new Map();
    }

    /**
     * Load the translations and stop words from the server and apply them to the page.
     */
    load() {
        // daisy chain load stop words, load translations, and process
        this.loadStopWords();
    }

    /**
     * Load the stop words and kick off translations loading.
     */
    loadStopWords() {
        var self = this;
        $.ajax({
            url: '/stop_words',
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                self.stopWords = data;
                self.loadTranslations();
            },
            error: function(xhr) {
                dragonFly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Load the translations and kick off web page update
     */
    loadTranslations() {
        var self = this;
        $.ajax({
            url: '/translations/' + this.lang,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                self.translations = data;
                self.createMap();
                self.apply();
            },
            error: function(xhr) {
                dragonFly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Create a source token -> gloss map
     */
    createMap() {
        for (var source in this.translations) {
            this.add(source, this.translations[source][0])
        }
    }

    /**
     * Add a source -> gloss pair to the translation map
     * @param {string} source - Source string.
     * @param {string} gloss - A translation for the source string.
     */
    add(source, gloss) {
        var sourceTokens = source.toLowerCase().split(' ');
        for (var i = 0; i < sourceTokens.length; i++) {
            // only add tokens that are not stop words for translation lookup
            if (!this.stopWords.includes(sourceTokens[i])) {
                this.transMap.set(sourceTokens[i], gloss);
            }
        }
    }

    /**
     * Apply the translations to the web page.
     */
    apply() {
        var self = this;
        $(".df-token").each(function() {
            var token = $(this).html().toLowerCase();
            if (self.transMap.has(token)) {
                $(this).addClass('df-in-dict');
                $(this).data('translation', self.transMap.get(token));
                $(this).attr('title', self.transMap.get(token));
                $(this).attr('data-toggle', 'tooltip');
                $(this).tooltip({delay: 200});
            }
        });
    }

    /**
     * Update the translation web display with a new translation pair
     * @param {string} source - Source string.
     * @param {string} gloss - A translation for the source string.
     */
    update(source, gloss) {
        this.add(source, gloss);
        this.apply();
    }
};

/**
 * Enum for click mode.
 * @readonly
 * @enum {number}
 */
dragonFly.Mode = {DEL: 0, TAG: 1, SELECT: 2, CONCORDANCE: 3};

/** Class representing a tag type. */
dragonFly.Tag = class Tag {
    /**
     * Create a tag type
     * @param {string} type - The tag name
     */
    constructor(type) {
        this.type = type.toLowerCase();
        this.start = "B-" + type;
        this.inside = "I-" + type;
    }
};

/** Class that holds the tag types. */
dragonFly.Tags = class Tags {
    constructor() {
        this.per = new dragonFly.Tag("PER");
        this.org = new dragonFly.Tag("ORG");
        this.gpe = new dragonFly.Tag("GPE");
        this.loc = new dragonFly.Tag("LOC");
        this.tags = [this.per, this.org, this.gpe, this.loc];
    }

    /**
     * Get the tag type from a tag string.
     * @param {string} value - The tag string like 'B-PER'.
     * @return {dragonFly.Tag} Tag object or null if no match.
     */
    getTag(value) {
        if (value == null || value == "O") {
            return;
        }
        var tagType = value;
        tagType = tagType.slice(2);
        for (var i = 0; i < this.tags.length; i++) {
            if (this.tags[i].type == tagType.toLowerCase()) {
                return this.tags[i];
            }
        }
        return;
    }
};

dragonFly.MultiTokenTag = class MultiTokenTag {
    /**
     * Create a multi-token tag.
     * @param {Tags} tags - Tags object with all possible tags.
     * @param {Tag} startTag - Tag object that represents the entity type.
     */
    constructor(tags, startTag) {
        this.elements = [];
        this.tags = tags;
        this.tag = startTag;
    }

    /**
     * Add an additional token.
     * @param {jQuery} element - A token element.
     */
    update(element) {
        this.elements.push(element);
    }

    /**
     * Change the entity type.
     * @param {Tag} tag - Tag object that represents the entity type.
     */
    setTag(tag) {
        this.tag = tag;
    }

    /**
     * Get the number of tokens in the tag.
     * @return {int}
     */
    size() {
        return this.elements.length;
    }
};

dragonFly.Concordance = class Concordance {
    /**
     * Search the concordance
     */
    search(word) {
        $('.df-search').val(word);
        this.postSearch(word);
    }

    /**
     * Submit a concordance search to the server
     */
    postSearch(word) {
        var self = this;
        $.ajax({
            url: '/search',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                self.displayResults(word, data);
            },
            error: function(xhr) {
                dragonFly.showStatus('danger', 'Error contacting the server');
            }
        });
    }

    /**
     * Update the results display box
     *
     */
    displayResults(word, results) {
        var html = ''
        for (var i=0; i<results.length; i++) {
            html += '<div class="df-result">';
            for (var j=0; j<results[i].source.length; j++){
                html += '<div class="df-section df-row">';
                if (word == results[i].source[j]) {
                    html += '<div class="df-result-highlight">' + results[i].source[j] + '</div>';
                } else {
                    html += '<div>' + results[i].source[j] + '</div>';
                }
                html += '<div>' + results[i].trans[j] + '</div>';
                html += "</div>";
            }
            html += "</div>";
        }
        $('.df-results').html(html);
    }
};

dragonFly.Highlighter = class Highlighter {
    /**
     * Create the highlighter manager.
     * @param {Tags} tags - A representation of the tag types.
     */
    constructor(tags, concordance) {
        this.tags = tags;
        this.concordance = concordance;
        this.isCascade = true;
        this.tagMode = dragonFly.Mode.TAG;
        this.prevTagMode = dragonFly.Mode.TAG;
        this.currentTag = tags.per;
        this.controlKeyDown = false;
        this.multiTokenTag = new dragonFly.MultiTokenTag(this.tags);
        this.anyTaggingPerformed = false;
        this.selectStart = null;
        this.undo = new dragonFly.Undo(10);
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
     * Change the internal state for multi-token tagging to on.
     */
    setControlKeyDown() {
        // only change the state if in tag mode
        if (this.tagMode == dragonFly.Mode.TAG) {
            if (this.controlKeyDown == true) {
                // Windows continually fires the down event and we want to ignore those after first
                return;
            }
            this.controlKeyDown = true;
            this.multiTokenTag = new dragonFly.MultiTokenTag(this.tags, this.currentTag);
        }
    }

    /**
     * Change the internal state for multi-token tagging to off.
     */
    setControlKeyUp() {
        // only change the state if in tag mode
        if (this.tagMode == dragonFly.Mode.TAG) {
            this.controlKeyDown = false;
            // done tagging so apply cascade if on
            if (this.multiTokenTag.size() > 0 && this.isCascade) {
                this.cascadeMultiTokenTag(this.multiTokenTag);
            }
            this.multiTokenTag = new dragonFly.MultiTokenTag(this.tags, this.currentTag);
        }
    }

    /**
     * Get the current tag type.
     * @return {Tag}
     */
    getCurrentTag() {
        return this.currentTag;
    }

    /**
     * Update the navbar indicator of mode and tag type.
     */
    highlightTypeAndMode() {
        $(".df-type").removeClass('df-type-active');
        if (this.tagMode == dragonFly.Mode.TAG) {
            var className = ".df-" + this.currentTag.type.toLowerCase();
            $(".df-type" + className).addClass('df-type-active');
        } else if (this.tagMode == dragonFly.Mode.DEL) {
            $(".df-del").addClass('df-type-active');
        } else if (this.tagMode == dragonFly.Mode.SELECT) {
            $(".df-sel").addClass('df-type-active');
        } else {
            $(".df-find").addClass('df-type-active');
        }
    }

    /**
     * Apply previous annotations for visualization.
     */
    initializeHighlight() {
        var self = this;
        $(".df-token").each(function() {
            var tagValue = $(this).data("tag");
            if (tagValue != null && tagValue != "O") {
                var tag = self.tags.getTag(tagValue);
                self.highlightToken($(this), tag, tagValue, false);
            }
        });
        // don't let people undo the loaded annotations so turn on undo after we're done
        this.undoActive = true;
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
            case 'n':
            case '0':
            case 'd':
                // enter into delete mode
                this.tagMode = dragonFly.Mode.DEL;
                this.highlightTypeAndMode();
                break;
            case 'r':
                // reset the state of the ui
                this.controlKeyDown = false;
                break;
            case 's':
                // enter into select mode
                this.prevTagMode = this.tagMode;
                this.tagMode = dragonFly.Mode.SELECT;
                this.highlightTypeAndMode();
                break;
            case 'f':
                // concordance mode
                this.tagMode = dragonFly.Mode.CONCORDANCE;
                this.highlightTypeAndMode();
                break;
            case 'u':
                // undo the previous action
                var undoAction = this.undo.pop();
                if (undoAction != null) {
                    undoAction.apply();
                }
                break;
            case 'p':
            case '1':
            case 'o':
            case '2':
            case 'g':
            case '3':
            case 'l':
            case '4':
                // change the tag type
                this.setTagType(letter);
                break;
        }
    }

    /**
     * Set the current tag type.
     * @param {string} letter - a letter or number representing the tag type.
     */
    setTagType(letter) {
        var tag = null;
        switch (letter) {
            case 'p':
            case '1':
                tag = this.tags.per;
                break;
            case 'o':
            case '2':
                tag = this.tags.org;
                break;
            case 'g':
            case '3':
                tag = this.tags.gpe;
                break;
            case 'l':
            case '4':
                tag = this.tags.loc;
                break;
        }

        if (tag) {
            this.tagMode = dragonFly.Mode.TAG;
            this.currentTag = tag;
            this.highlightTypeAndMode();
        }
    }

    /**
     * Process a token click.
     * The result depends on what mode we are in (tagging, delete, select).
     * @param {jQuery} element - Token element clicked.
     */
    clickToken(element) {
        if (this.tagMode == dragonFly.Mode.DEL) {
            this.undo.start();
            this.undo.add(element);
            this.deleteTag(element);
        } else if (this.tagMode == dragonFly.Mode.SELECT) {
            this.select(element);
        } else if (this.tagMode == dragonFly.Mode.CONCORDANCE) {
            this.concordance.search(element.html());
        } else {
            // set this so we know whether to prevent user navigating away
            this.anyTaggingPerformed = true;
            var tag = this.currentTag;
            if (this.controlKeyDown) {
                if (this.multiTokenTag.size() == 0) {
                    this.undo.start();
                }
                this.multiTokenTag.update(element);
                this.highlightMultiTokenTag(this.multiTokenTag);
            } else {
                this.undo.start();
                this.highlightToken(element, tag, tag.start, this.isCascade);
            }
        }
    }

    /**
     * Highlight a token and possibly perform a cascade to other tokens.
     * @param {jQuery} token - The token element to highlight.
     * @param {Tag} tag - The tag type to apply.
     * @param {string} string - The tag string (B-PER, I-ORG).
     * @param {boolean} cascade - Whether to cascade this to matching tokens.
     * @param {boolean} inferred - Is this a result of a cascade?
     * @return {boolean} Was the token highlighted?
     */
    highlightToken(token, tag, string, cascade, inferred=false) {
        var self = this;
        if (inferred && token.data("inferred") != null && !token.data("inferred")) {
            return false;
        }

        if (this.undoActive) {
            this.undo.add(token);
        }

        token.data("tag", string);
        token.data("inferred", inferred);

        var classes = "df-token";
        if (string.charAt(0) == 'B') {
            classes += " df-b-tag";
        }
        classes += " df-" + tag.type;
        token.attr('class', classes);

        var tokenText = token.html().toLowerCase();
        var count = 0;
        if (cascade) {
            $(".df-token").each(function() {
                if (tokenText == $(this).html().toLowerCase()) {
                    if (self.highlightToken($(this), tag, string, false, true)) {
                        count += 1;
                    }
                }
            });
            dragonFly.showStatus('success', 'Cascade: ' + parseInt(count));
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
                this.highlightToken(tag.elements[i], tag.tag, tag.tag.start, false);
            } else {
                this.highlightToken(tag.elements[i], tag.tag, tag.tag.inside, false);
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
                var newTag = new dragonFly.MultiTokenTag(self.tags);
                newTag.update($(this));
                newTag.setTag(tag.tag);
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
        dragonFly.showStatus('success', 'Cascade: ' + parseInt(count));
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
            this.tagMode = this.prevTagMode;
            this.highlightTypeAndMode();
            dragonFly.showStatus('success', 'Copied');
        }
    }
};

dragonFly.AnnotationSaver = class AnnotationSaver {
    /**
     * Create an annotation saver.
     * @param {string} filename - The filename being edited.
     */
    constructor(filename) {
        this.filename = filename;
        this.saveClicked = false;
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
                        dragonFly.showStatus('success', response.message);
                    }
                } else {
                    dragonFly.showStatus('danger', response.message);
                }
            },
            error: function(xhr) {
                dragonFly.showStatus('danger', 'Error contacting the server');
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
        return tokens;
    }
};

$(document).ready(function() {
    // According to http://unixpapa.com/js/key.html, shift = 16, control = 17, alt = 18, caps lock = 20
    if (/Mac/.test(window.navigator.platform)) {
        // Option key on Macs
        dragonFly.multiTagKey = "18";
    } else {
        // Control key for Windows and Linux
        dragonFly.multiTagKey = "17";
    }

    // set the margin to account for varying navbar sizes due to viewport
    $('body').css('margin-top', $('#df-nav').height() + 10);

    dragonFly.lang = $("meta[name=lang]").attr("content");
    dragonFly.tags = new dragonFly.Tags();
    dragonFly.concordance = new dragonFly.Concordance();
    dragonFly.highlighter = new dragonFly.Highlighter(dragonFly.tags, dragonFly.concordance);
    dragonFly.highlighter.initializeHighlight();
    dragonFly.annotationSaver = new dragonFly.AnnotationSaver($("#df-filename").html());
    dragonFly.hints = new dragonFly.Hints(1);
    dragonFly.hints.run();
    dragonFly.translations = new dragonFly.Translations(dragonFly.lang);
    dragonFly.translations.load();
    dragonFly.settings = new dragonFly.Settings(dragonFly.annotationSaver);
    dragonFly.settings.load();
    dragonFly.contextMenu = new dragonFly.ContextMenu(dragonFly.highlighter, dragonFly.translations);

    $('[data-toggle=tooltip]').tooltip({delay: 200});

    $("input[id = 'cascade']").on("click", function() {
        dragonFly.highlighter.toggleCascade();
    });

    $(".df-token").on("click", function(event) {
        dragonFly.highlighter.clickToken($(this));
    });

    $(document).on("keypress", function(event) {
        dragonFly.highlighter.pressKey(String.fromCharCode(event.which));
    });

    $(document).on("keydown", function(event) {
        if (event.which == dragonFly.multiTagKey) {
            dragonFly.highlighter.setControlKeyDown();
        }
    });

    $(document).on("keyup", function(event) {
        if (event.which == dragonFly.multiTagKey) {
            dragonFly.highlighter.setControlKeyUp();
        }
    });

    // change the mode or tag type by clicking on navbar
    $(".df-type").on("click", function(event) {
        var letter = $(this).attr("title");
        dragonFly.highlighter.pressKey(letter);
    });

    // user can indicate which sentences have been reviewed
    $(".df-sentence-badge").on("click", function(event) {
        $(this).toggleClass("df-complete");
    });

    $("#df-save").on("click", function(event) {
        dragonFly.annotationSaver.save($(this));
        $(this).blur();
    });

    $("#df-settings-save").on("click", function(event) {
        $('#df-settings-modal').modal('hide');
        dragonFly.settings.save();
    });

    // leaving focus on settings button is distracting so we remove it
    $('#df-settings-modal').on('shown.bs.modal', function(event) {
        $('#df-settings-button').one('focus', function(event) {
            $(this).blur();
        });
    });

    $(".df-token").on("contextmenu", function(event) {
        dragonFly.contextMenu.show($(this), event);
    });

    $("#df-context-menu-submit").on('click', function(event) {
        dragonFly.contextMenu.save();
        event.preventDefault();
    });

    $(window).on("beforeunload", function() {
        if (dragonFly.highlighter.anyTaggingPerformed && !dragonFly.annotationSaver.saveClicked) {
            return "Changes have not been saved.";
        }
    });

    // keep the sentence IDs in same location as user horizontally scrolls if desired
    $(window).scroll(function() {
        if (dragonFly.settings.isSentenceIdAutoScroll()) {
            $('.df-sentence-id').css({
                'left': $(this).scrollLeft(),
                'height': ($(".df-sentence").height() - 5) + 'px'
            });
        }
    });

    $('.df-concordance').resizable({
        handleSelector: '.df-resize-bar',
        resizeWidth: false,
        resizeHeightFrom: 'top',
    });
});
