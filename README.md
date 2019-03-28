Dragonfly Annotation Tool
============================
Dragonfly is a tool for performing named entity annotations.
It has been designed to especially support and accelerate annotating
low resource languages by non-speakers.

This requires python3 for unicode support. 
Some operating systems make python and pip available as pip3 and python3.

License and Copyright
----------------------
Copyright 2017-2018 Johns Hopkins University Applied Physics Laboratory

Licensed under the Apache License, Version 2.0


Install
---------------
```
pip3 install -r requirements.txt
```

Run
---------------
To annotate a single tsv file:
```
python3 run.py lang filename
```

`lang` is the ISO 639 language code (recommend 639-3).
A complete list is available on the [SIL website](https://iso639-3.sil.org/code_tables/639/data).

To annotate all the files in a directory:
```
python3 run.py lang directory
```

By default, annotations are saved in a directory called annotations where the input files are located.
To change this:
```
python3 run.py -o my_annotation_dir lang tsv_filename
```

To load previous annotations from a file or directory:
```
python3 run.py -a annotation_path lang tsv_filename
```
By default, it will load annotations that are available in the current output directory.

If the first column of the first row has a value of 'TOKEN', the first row is treated as a header.

The output is a two column tsv file of token and tag.

Once the server is running, direct your browser to http://localhost:5000/
(Additional instances can be run concurrently by selecting a different port with the -p option.)

Dragonfly creates a `.dragonfly` directory in the user's home directory.
It saves settings and translation dictionaries to this directory.

The tag types can be specified on the command line using the -t option:
```
python3 run.py -t PER,ORG,LOC,MISC lang directory
```
The default tag set is PER, ORG, GPE, LOC in support of LoReHLT. O is the tag applied to
tokens that are outside of named entities.

Annotate
-------------------
### Single token tagging
1. Select the tag type by pressing the number associated with the type (first tag type is 1 and so on).
2. Click on a token for a B tag.
3. Continue clicking tokens for that tag type. Select a different letter for a different entity type.


### Cascade
Toggle the cascade through its checkbox in the navigation bar or by pressing 'c'.

The cascade will tag all matching tokens in the document unless that token has been previously tagged.

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
Language-specific files are used to highlight tokens that belong to a translated phrase.
The entire phrase is made available as a tooltip when mousing over the outlined token.

#### Adding to the dictionary
 1. Right click on a token and a form will appear to set the translation

 2. If that token has been tagged and is the first token in the tag, it will apply the translation to the entire phrase. It will also auto-set the entity type.

 3. For non-tagged tokens, you only need to enter the first letter of the entity type. If you want to translate a non-entity token, set the type to 'n' for none. If you want to type out 'PER' or 'per' or 'none', those all work too.

 4. Submit the form and you should see a success message.

Note that if you translate phrases that include articles or prepositions, those tokens will be highlighted.

#### Importing and Exporting
A translation dictionary can be exported like so: `./scripts/export.py [lang]` where lang is the three letter ISO code.
The script will write out a lang.tsv file in the directory where you ran the script.

To import a dictionary, `./scripts/import.py [lang] [dict tsv file]`.
Importing will not overwrite any phrase that you have already translated.

### Hints
A hints file can be loaded and displayed. It is a two column tsv file with the first column being regular expressions
and the second column is text that explains the hint. It is matched with the words in the 2nd row (transliteration).
An example from Amharic would be:
```
^ba	prefix that represents a preposition 'in' or 'on'
```

Anything that matches the hint is highlighted.
The regular expressions are processed from top to bottom and only the first match is used.

The hints file is loaded on the command line with the --hints or -d option (d for dictionary):

```
python3 run.py --hints il5_hints.tsv lang il5_to_be_annotated
```

### Translation
When annotating the file `x.txt`, if there is a file in the same directory with the name `x.txt.eng`, 
it is loaded and displayed above the token row. The file should be a sentence segmented file with one
sentence per line that matches the divisions in the conll formatted input file.

Settings
------------
Settings are persisted between annotation sessions.
Most take effect immediately upon a change.
The exception is column width.
This is server-side and requires a page reload.

Test
------------
To run the unit tests:
```
nosetests python/tests
```
