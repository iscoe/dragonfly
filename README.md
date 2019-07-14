[![Build Status](https://travis-ci.com/iscoe/dragonfly.svg?branch=master)](https://travis-ci.com/iscoe/dragonfly)

Dragonfly Annotation Tool
============================
Dragonfly is a tool for performing named entity annotations.
It has been designed to especially support and accelerate annotating
low resource languages by non-speakers.

This requires python3 for unicode support. 
Some operating systems make python and pip available as pip3 and python3.

License and Copyright
----------------------
Copyright 2017-2019 Johns Hopkins University Applied Physics Laboratory

Licensed under the Apache License, Version 2.0


Install
---------------
```
pip3 install -r requirements.txt
```

Running in Annotation Mode
---------------
To annotate a directory of tsv files:
```
python3 annotate.py [lang] [data dir]
```

`lang` is the ISO 639 language code (recommend 639-3).
A complete list is available on the [SIL website](https://iso639-3.sil.org/code_tables/639/data).

By default, annotations are saved in a sub-directory called annotations where the input files are located.
To change this:
```
python3 annotate.py -o [annotation dir] [lang] [data dir]
```

Once the server is running, direct your browser to http://localhost:5000/
(Additional instances can be run concurrently by selecting a different port with the -p option.)

Dragonfly creates a `.dragonfly` directory in the user's home directory.
It saves settings and translation dictionaries to this directory.

The tag types can be specified on the command line using the -t option:
```
python3 annotate.py -t PER,ORG,LOC,MISC [lang] [data_dir]
```
The default tag set is PER, ORG, GPE, LOC in support of LoReHLT. O is the tag applied to
tokens that are outside of named entities.

### Data Formats
Dragonfly expects tab separated value files which we will call CoNLL format.
The first column are the tokens to be annotated.
Additional columns provide context for the tokens and could include
transliterations, translations, or other semantic information.
Sentences should be followed by an empty line.

If the first column of the first row has a value of 'TOKEN', the first row is treated as a header.

The output is a two column tsv file of token and tag.

### Running multiple sites
The port of the server is selected with the `-p` option:

```bash
python3 annotate.py --port 8888 [lang] [data_dir]
```

To run more than one site on the same port, configure a reverse proxy server with
each Dragonfly instance responding to a different URL prefix:

```bash
python3 annotate.py --prefix deu [lang] [data_dir]
```

Annotate
-------------------
### Single token tagging
1. Select the tag type by pressing the number associated with the type (first tag type is 1 and so on).
2. Click on a token for a B tag.
3. Continue clicking tokens for that tag type. Select a different letter for a different entity type.

### Cascade
The cascade will tag all matching tokens in the document unless that token has been previously tagged.

Toggle the cascade through its checkbox in the navigation bar or by pressing 'c'.
To persist the cascade setting between documents, use the Settings dialog.

### Multi-token tagging
1. Select tag mode as with single token tagging.
2. Hold down the control key on Linux and Windows or option key on MacOSX and click the first token and then last token.
3. If cascade is on, it will not cascade to tags that have already been tagged.

Multi-token tags cannot span sentences.

### Selecting tokens
To copy tokens to your clipboard, press 's' to enter select mode.
Then click on the first and the last token to copy in a single sentence.
Clicking the same token twice copies that token.

### Other commands
* To delete a token tagging, select delete mode ('d') and click on the token.
* To undo an action, press 'u'.
* To advance to the next sentences for a document, press the spacebar or scroll.
* To save the annotations, click the save button.
* To move to the next document in the directory, click the next button (or previous button for the previous file).
* To skip to a particular file, type the filename as part of the url: http://localhost:5000/IL5_SN_0001.txt

### Translation Dictionaries
The annotation tool supports user-maintained translation dictionaries.
Language-specific files are used to highlight tokens that have been translated.
Only single tokens may be translated at a time.

#### Adding to the dictionary
 1. Right click on a token and a dialog will appear to set the translation.
 2. If that token has been tagged, the entity type will already be set.
 3. For non-tagged tokens, you will need to enter the entity type or leave it blank for a non-entity.
 4. Submit the form and you should see a success message.

#### Importing and Exporting
The tools window provides the capability to import and export translation dictionaries.
The json object is a dictionary with tokens as the keys and a list of translation and type as the value.
Importing a dictionary will not overwrite anything that you have already translated.

### Hints
Annotation hints can be configured in the tools dialog.
Hints are represented as two columns with the first column being regular expressions
and the second column is text that explains the hint.
The row for the hints is configured in the settings.
An example from Amharic would be:
```
^ba	prefix that represents a preposition 'in' or 'on'
```

Anything that matches the hint is highlighted.
The regular expressions are processed from top to bottom and only the first match is used.

### Translation
When annotating the file `x.txt`, if there is a file in the same directory with the name `x.txt.eng`, 
it is loaded and displayed above the token row. The file should be a sentence segmented file with one
sentence per line that matches the divisions in the CoNLL formatted input file.

### Suggestions
The tool will suggest words with a light brown background that you have been frequently tagging.
To customize your suggestions, add an additional column to the input files and tell the tool
to use a particular column:

```bash
python3 annotate.py --suggest ENTROPY [lang] [data_dir]
```

Settings
------------
Settings are persisted between annotation sessions.
Most take effect immediately upon a change.
The exception is column width which requires a page reload.

Additional Modes
-----------------
The behavior of Dragonfly can be changed by passing mode information.
To view the progress of an annotator, view the URL they are using with the URL parameter
`view=true` set. The ability to save is removed and if the site is configured for auto save
you can reload the page to see their annotations.

Passing the `--rtl` flag on the command line, changes the display to Right To Left.

Setting `--simple` on the command line removes parts of the UI to help prevent distracting new annotators.

Finally, the `--debug` flag is useful during development or working through errors.

Adjudication
--------------
Once you have annotations from more than one annotator on the same set of files,
you may want to compare and adjudicate among them.

```
python3 adjudicate.py -o [output dir] [lang] [data dir] [annotation dir1] [annotation dir2] ...
```
The default tags come from the first annotation directory specified on the command line.
The adjudicated annotations are stored to the output directory (a required argument).
The UI works the same as annotating.

Test
------------
To run the unit tests:
```
nosetests tests/python
```
