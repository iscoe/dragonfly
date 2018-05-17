/**
 * Copyright 2017-2018, The Johns Hopkins University Applied Physics Laboratory LLC
 * All rights reserved.
 * Distributed under the terms of the Apache 2.0 License.
 */

/**
 * Get the mode of an array.
 * Sorts the array by occurrence frequency and then returns the most frequent
 */
function get_mode(array){
    return array.sort(function(a, b) {
        return array.filter(function(entry){ return entry===a }).length
            - array.filter(function(entry){ return entry===b }).length
    }).pop();
};

// from mustache.js
// MIT License, https://github.com/janl/mustache.js/blob/master/LICENSE
var entityMap = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;'
};

function escapeHtml(string) {
  return String(string).replace(/[&<>"'`=\/]/g, function (s) {
    return entityMap[s];
  });
};

// https://github.com/zenorocha/select/blob/master/src/select.js
// MIT License, Copyright Zeno Rocha
function select(element) {
    var selectedText;

    if (element.nodeName === 'SELECT') {
        element.focus();

        selectedText = element.value;
    }
    else if (element.nodeName === 'INPUT' || element.nodeName === 'TEXTAREA') {
        var isReadOnly = element.hasAttribute('readonly');

        if (!isReadOnly) {
            element.setAttribute('readonly', '');
        }

        element.select();
        element.setSelectionRange(0, element.value.length);

        if (!isReadOnly) {
            element.removeAttribute('readonly');
        }

        selectedText = element.value;
    }
    else {
        if (element.hasAttribute('contenteditable')) {
            element.focus();
        }

        var selection = window.getSelection();
        var range = document.createRange();

        range.selectNodeContents(element);
        selection.removeAllRanges();
        selection.addRange(range);

        selectedText = selection.toString();
    }

    return selectedText;
}

// https://github.com/zenorocha/clipboard.js/blob/master/src/clipboard-action.js
// MIT License, Copyright Zeno Rocha
function copyToClipboard(text) {
        const isRTL = document.documentElement.getAttribute('dir') == 'rtl';

        var fakeElem = document.createElement('textarea');
        // Prevent zooming on iOS
        fakeElem.style.fontSize = '12pt';
        // Reset box model
        fakeElem.style.border = '0';
        fakeElem.style.padding = '0';
        fakeElem.style.margin = '0';
        // Move element out of screen horizontally
        fakeElem.style.position = 'absolute';
        fakeElem.style[ isRTL ? 'right' : 'left' ] = '-9999px';
        // Move element to the same position vertically
        let yPosition = window.pageYOffset || document.documentElement.scrollTop;
        fakeElem.style.top = `${yPosition}px`;

        fakeElem.setAttribute('readonly', '');
        fakeElem.value = text;

        document.body.appendChild(fakeElem);

        var selectedText = select(fakeElem);
        succeeded = document.execCommand("Copy");
        document.body.removeChild(fakeElem);
}
