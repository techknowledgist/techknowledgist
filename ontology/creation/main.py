
"""

Script to process all documents in a corpus. Will initialize the corpus if
needed. Combines what is done in the two scripts step1_initialize.py and
step2_document_processing.py, but simplifies the process a bit.

USAGE
   % python corpus.py OPTIONS

OPTIONS
   --language en|cn      language, default is 'en'
   --filelist PATH       a file with a list of source files
   --corpus PATH         a directory where the corpus is created
   -n INTEGER            number of files to process, defaults to all files
   
You must run this script from the directory it is in.

Typical invocation:

   % python main.py \
       --language en \
       --corpus data/patents/test \
       --filelist filelist.txt

This creates a directory data/patents/test, in which the corpus will be
initialized. The directory will include config/ and data/ subdirectories and
several files in the config/ subdirectory. The script copies filelist.txt to
en/config/files.txt so there is always a local copy of the list with all input
files. Note that the -n option is not given and therefore all documents will be
processed.

For the --filelist option, the system expects that FILE has two or three columns
with year, source file and an optional target file, which is the filepath in the
corpus starting at the target directory handed in with the --corpus option. If
there is no third column than the source and target file will be the same as the
source file, except that a leading path separator will be stripped.

The directory tree created inside the target directory is as follows:

    |-- config
    |   |-- files.txt
    |   |-- general.txt
    |   `-- pipeline-default.txt
    `-- data
        |-- d0_xml         'import of XML data'
        |-- d1_txt         'results of document structure parser'
        |-- d2_seg         'segmenter results'
        |-- d2_tag         'tagger results '
        |-- d3_phr_feats   'results from candidate selection and feature extraction'
        |-- o1_index       'term indexes'
        |-- o2_matcher     'results of the pattern matcher'
        |-- o3_selector    'results of the selector'
        |-- t0_annotate    'input for annotation effort'
        |-- t1_train       'vectors for the classifier and classifier models'
        |-- t2_classify    'classification results'
        |-- t3_test        'test and evaluation area'
        `-- workspace      'work space area'

This script only performs document-level processing and fills in d0_xml, d1_txt,
d2_seg (Chinese only), d2_tag and d3_phr_feats. All files are compressed. The
directory structures mirror each other and look as follows (this example only
has two files listed):

    `-- 01
        |-- state
        |   |-- processed.txt
        |   `-- processing-history.txt
        |-- config
        |   |-- pipeline-head.txt
        |   `-- pipeline-trace.txt
        `-- files
            |-- 1985
            |   ` US4523055A.xml.gz
            `-- 19986
                ` US4577022A.xml.gz

The structure under the files directory is determined by the third column in the
file list.

"""


import os, sys, getopt

import config

from corpus import Corpus
from corpus import POPULATE, XML2TXT, TXT2TAG, TXT2SEG, SEG2TAG, TAG2CHK
from ontology.utils.batch import RuntimeConfig


if __name__ == '__main__':

    options = ['language=', 'corpus=', 'filelist=', 'verbose']
    (opts, args) = getopt.getopt(sys.argv[1:], 'n:', options)

    source_file = None
    corpus_path = None
    verbose = False
    language = config.LANGUAGE
    source = 'LEXISNEXIS'
    limit = None

    pipeline = config.DEFAULT_PIPELINE
    if language == 'cn':
            pipeline = config.DEFAULT_PIPELINE_CN
    pipeline_file = 'pipeline-default.txt'

    for opt, val in opts:
        if opt == '--language': language = val
        if opt == '--filelist': source_file = val
        if opt == '--corpus': corpus_path = val
        if opt == '--verbose': verbose = True
        if opt == '-n': limit = int(val)
        
    c = Corpus(language, source_file, None, corpus_path, pipeline, None)
    rconfig = RuntimeConfig(corpus_path, None, None, language, pipeline_file)
    if limit is None:
        limit = len([f for f in open(rconfig.filenames).readlines() if len(f.split()) > 1])

    c.populate(rconfig, limit, verbose)
    c.xml2txt(rconfig, limit, {}, source, verbose)
    if language == 'en':
        c.txt2tag(rconfig, limit, {}, verbose)
    elif language == 'cn':
        c.txt2seg(rconfig, limit, {}, verbose)
        c.seg2tag(rconfig, limit, {}, verbose)
    c.tag2chk(rconfig, limit, {}, verbose)

