Code that implements the technpology selector. Includes the following:

* A configuration file
  - config.py defines the base directory where the input and output data 
  - edit this file to set a default directory

* The Indexer
  - python index.py -l LANG -c N
  - Creates a python shelve with frequency counts
  - Takes base_dir/language/phr_occ as input
  - Writes output to base_dir/language/idx

* The Matcher
  - python matcher.py -l LANG
  - Takes base_dir/language/phr_occ as input
  - Creates a file with all matches in base_dir/language/selector/phr_occ2.tab
  - Lines in this file contain the identifier from files embedded in
    base_dir/language/phr_occ and a pattern identifier.
  - Uses patterns.py
  - Simplistic place holder for Olga's code.

* The Classifier
  - python classifier.py -l LANG
  - Takes files in base_dir/language/phr_occ and creates
     base_dir/language/selector/phr_occ3.tab
  - Lines in this file contain the match identfier from phr_occ and nothing else.
  - Simplistic place holder for Peter's code.

* The Selector
  - python selector.py -l LANG
  - Takes the files in base_dir/language/phr_occ and the output of the Classifier and the
    Matcher, and creates base_dir/language/selector/phr_occ4.tab which is a subset of the
    contents of base_dir/language/phr_occ, but has pattern identifiers added.
  - Now simply assumes that the classifier is right, but it does use a list of negative
    examples to reduce false positives.
    
* The Maturity Scorer
  - python maturity.py -l LANG
  - Takes the result of the Selector and creates a file
    base_dir/language/selector/phr_occ5.tab, which has maturity scores added.
  - The output can be consumed by the runtime system.

* The HTML Exporter
  - python create_html.py -l LANG DIRECTORY
