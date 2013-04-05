"""

Script to initialize a working directory for patent processing. It does the
following things: (1) initialize the directory structure for a language, (2)
import or create a file config/files.txt with all external files to process,
(3) create a file config/pipeline-default.txt with default settings for the
pipeline, and (4) create a file config/general.txt with settings used by this
script.

USAGE
   % python step1_initialize.py OPTIONS

OPTIONS
   -l en|de|cn   --  language
   -f FILE       --  input: use external FILE and copy it to config/files.txt
   -s DIRECTORY  --  input: generate config/files.txt from DIRECTORY
   -t DIRECTORY  --  output: target directory where the language directory is put
   --shuffle     --  performs a random sort of config/files.txt, used with the -s option

Typical invocations:
    % python step1_initialize.py -l en -t data/patents -f filelist.txt
    % python step1_initialize.py -l en -t data/patents -s ../external/US --shuffle

    Both commands create a directory en/ inside of data/patents/, with config/
    and data/ subdirectories and several files mentioned above in the config/
    subdirectory. The first form copies filelist.txt to en/config/files.txt. The
    second form traverses the directory ../external/US, takes all file paths,
    randomly shuffles them, and then saves the result to en/config/files.txt.

    When the -f options is used, the system expects that FILE has two or three
    columns with year, source file and an optional target file, which is the
    filepath in the corpus starting at the target directory handed in with the
    -t option. If there is no third column that the source and target file will
    be the same as the source file, except that a leading path separator will be
    stripped.

    With the -s option, the source and target will alwasy be the same and the
    year will always be set to 0000. It is up to the user to change this if
    needed.


NOTES

Paths in config/general.txt can be either relative or absolute. Initially, all
settings are from this initialization script, but other configuration settings could be
added later.

The pipeline-default.txt file is tricky. It contains all default settings for arguments
handed over to individual components (tagger, chunker, maxent model trainer etcetera). If
more arguments are added, then this file should be updated manually and it should then
also be used to fill in default values for past processing jobs (assuming that there is a
default that makes sense).

The directory tree created inside the language directory is as follows:

    |-- config
    |   |-- files.txt
    |   |-- general.txt
    |   |-- pipeline-default.txt
    `-- data
        |-- d0_xml            'import of XML data'
        |-- d1_txt            'results of document structure parser'
        |-- d2_seg            'segmenter results'
        |-- d2_tag            'tagger results '
        |-- d3_phr_feats      'results from candidate selection'
        |-- d3_phr_occ        'results from candidate selection'
        |-- d4_doc_feats      'results from merging phrase features intro doc features'
        |-- o1_index          'term indexes'
        |-- o2_matcher        'results of the pattern matcher'
        |-- o3_selector       'results of the selector'
        |-- t0_annotate       'input for annotation effort'
        |-- t1_train          'vectors for the classifier and classifier models'
        |-- t2_classify       'classification results'
        |-- t3_test           'test and evaluation area'
        `-- workspace         'work space area'

Note that the processing stages are grouped using prefixes, where the features carry some
meaning:

   d -- document level processing
   t -- processing for the technology classifier
   o -- processing for the ontology creator (this is used by a downstream script)

No existing files or directories will be overwritten, except for the files in the config
directory that are listed above (general.txt, files.txt, pipeline-default.txt, etcetera).


TODO
- filenames like files.txt and general.txt are defined in the code, should be put up front
- same with names of processing stages
- same with input and output directories like d2_tag

"""


import os, sys, shutil, getopt, errno, random, time

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

import config_data
from ontology.utils.file import ensure_path, get_lines, get_file_paths


# definition of the default pipeline configurations

DEFAULT_PIPELINE = """
# This file contains the default pipeline configuration settings. Settings in here can be
# overruled by handing the step2_document_processing script the identifier for another
# configuration file. All pipeline configuration files live inside of the config directory
# configuration file.

--populate
--xml2txt
--txt2tag
--tag2chk --candidate-filter=off --chunker-rules=en
--pf2dfeats
"""

DEFAULT_PIPELINE_CN = """
# This file contains the default pipeline configuration settings for Chinese. Settings in
# here can be overruled by handing the step2_document_processing script the identifier for
# another configuration file. All pipeline configuration files live inside of the config
# directory configuration file.

--populate
--xml2txt
--txt2seg
--seg2tag
--tag2chk --candidate-filter=off --chunker-rules=en
--pf2dfeats
"""

# definition of sub directory names for processing stages
DATA_TYPES = \
    ['d0_xml', 'd1_txt', 'd2_tag', 'd2_seg', 'd3_phr_occ', 'd3_phr_feats', 'd4_doc_feats']
PROCESSING_AREAS = \
    DATA_TYPES + ['t0_annotate', 't1_train', 't2_classify', 't3_test',
                  'o1_index', 'o2_matcher', 'o3_selector', 'workspace' ]


def init(language, source_file, source_path, target_path, pipeline_config, shuffle_file):

    """Creates a directory named target_path/language and all subdirectories and files in
    there needed for further processing. See the module docstring for more details."""

    settings = ["timestamp    =  %s\n" % time.strftime("%x %X"),
                "language     =  %s\n" % language,
                "source_file  =  %s\n" % source_file,
                "source_path  =  %s\n" % source_path,
                "target_path  =  %s\n" % target_path,
                "shuffle      =  %s\n" % str(shuffle_file)]
    
    print "\n[--init] initializing %s/%s" % (target_path, language)
    print "\n   %s" % ("   ".join(settings))
    
    lang_path = os.path.join(target_path, language)
    if os.path.exists(lang_path):
        sys.exit("[--init] ERROR: %s already exists" % lang_path)
    data_path = os.path.join(lang_path, 'data')
    conf_path = os.path.join(lang_path, 'config')
    
    create_directories(lang_path, conf_path, data_path)
    create_general_config_file(conf_path, settings)
    create_default_pipeline_config_file(pipeline_config, conf_path)
    create_filelist(source_file, source_path, conf_path, shuffle_file)
    print
    

def create_directories(lang_path, conf_path, data_path):
    """Create subdirectory structure in target_path."""
    print "[--init] creating directory structure in %s" % (lang_path)
    ensure_path(conf_path)
    for subdir in PROCESSING_AREAS:
        subdir_path = data_path + os.sep + subdir
        ensure_path(subdir_path)

def create_filelist(source_file, source_path, conf_path, shuffle_file):
    """Create a list of files either by copying a given list or by traversing a given
    directory."""
    print "[--init] creating %s/files.txt" % (conf_path)
    file_list = os.path.join(conf_path, 'files.txt')
    if source_file is not None:
        shutil.copyfile(source_file, file_list)
    elif source_path is not None:
        filenames = get_file_paths(source_path)
        if shuffle_file:
            random.shuffle(filenames)
        with open(file_list, 'w') as fh:
            for fname in filenames:
                fh.write("0000\t" + fname + "\n")
    else:
        sys.exit("[--init] ERROR: need to define input with -f or -s option, aborting")

def create_general_config_file(conf_path, settings):
    print "[--init] creating %s/general.txt" % (conf_path)
    settings_file = open(os.path.join(conf_path, 'general.txt'), 'w')
    settings_file.write("".join(settings))

def create_default_pipeline_config_file(pipeline_config, conf_path):
    fh = open(os.path.join(conf_path, 'pipeline-default.txt'), 'w')
    print "[--init] creating %s" % (fh.name)
    fh.write(pipeline_config.lstrip())
    fh.close()


if __name__ == '__main__':

    (opts, args) = getopt.getopt(sys.argv[1:], 'l:s:f:t:', ['shuffle'])

    source_file = None
    source_path = None
    target_path = config_data.working_patent_path
    language = config_data.language
    shuffle_file = False
    pipeline_config = DEFAULT_PIPELINE
    
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-f': source_file = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '--shuffle': shuffle_file = True

    if language == 'cn':
            pipeline_config = DEFAULT_PIPELINE_CN

    init(language, source_file, source_path, target_path, pipeline_config, shuffle_file)
