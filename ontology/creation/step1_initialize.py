"""

Script to initialize a working directory for patent processing. It does the
following things:

    (1) initialize the directory structure for the corpus,

    (2) import or create a file config/files.txt with all external files to
        process,

    (3) create a file config/pipeline-default.txt with default settings for the
        pipeline,

    (4) create a file config/general.txt with settings used by this script.


USAGE
   % python step1_initialize.py OPTIONS

OPTIONS
   --language en|de|cn      language, default is 'en'
   --filelist PATH          a file with a list of source files
   --source-directory PATH  a directory with all the source files
   --corpus PATH            a directory where the corpus is initialized
   --shuffle                randomly sort config/files.txt, used with the
                             --source-dirrectory option


There is are two typical invocations, one where a file list is given to
initialize the corpus and one where a source directory is given:

  % python step1_initialize.py \
      --language en \
      --corpus data/patents/test \
      --filelist filelist.txt

  % python step1_initialize.py \
      --language en \
      --corpus data/patents/test \
      --source-directory ../external/US \
      --shuffle

Both commands create a directory data/patents/test, in which the corpus will be
initialized. It will include config/ and data/ subdirectories and several files
mentioned above in the config/ subdirectory. The first form copies filelist.txt
to en/config/files.txt. The second form traverses the directory ../external/US,
takes all file paths, randomly shuffles them, and then saves the result to
en/config/files.txt.

When the --filelist options is used, the system expects that FILE has two or
three columns with year, source file and an optional target file, which is the
filepath in the corpus starting at the target directory handed in with the
--corpus option. If there is no third column that the source and target file
will be the same as the source file, except that a leading path separator will
be stripped.

With the --source-directory option, the source and target will always be the
same and the year will always be set to 0000. It is up to the user to change
this if needed.


NOTES

Paths in config/general.txt can be either relative or absolute. Initially, all
settings are from this initialization script, but other configuration settings
could be added later.

The pipeline-default.txt file is tricky. It contains all default settings for
arguments handed over to individual components (tagger, chunker, maxent model
trainer etcetera). If more arguments are added, then this file should be updated
manually and it should then also be used to fill in default values for past
processing jobs (assuming that there is a default that makes sense).

The directory tree created inside the target directory is as follows:

    |-- config
    |   |-- files.txt
    |   |-- general.txt
    |   |-- pipeline-default.txt
    `-- data
        |-- d0_xml         'import of XML data'
        |-- d1_txt         'results of document structure parser'
        |-- d2_seg         'segmenter results'
        |-- d2_tag         'tagger results '
        |-- d3_phr_feats   'results from candidate selection'
        |-- d3_phr_occ     'results from candidate selection'
        |-- d4_doc_feats   'results from merging phrase features'
        |-- o1_index       'term indexes'
        |-- o2_matcher     'results of the pattern matcher'
        |-- o3_selector    'results of the selector'
        |-- t0_annotate    'input for annotation effort'
        |-- t1_train       'vectors for the classifier and classifier models'
        |-- t2_classify    'classification results'
        |-- t3_test        'test and evaluation area'
        `-- workspace      'work space area'

Note that the processing stages are grouped using prefixes, where the features
carry some meaning:

   d -- document level processing
   t -- processing for the technology classifier
   o -- processing for the ontology creator (this is used by a downstream script)

No existing files or directories will be overwritten, except for the files in
the config directory that are listed above (general.txt, files.txt,
pipeline-default.txt).


TODO

- Filenames like files.txt and general.txt are defined in the code, should be
  put up front; the same holds for names of processing stages and input and
  output directories like d2_tag.

- Add option to grow an already initialized corpus. One question to answer here
  is whether you just add lines to config/files.txt or also add some lines
  saying that x files were added at time t.

"""


import os, sys, shutil, getopt, errno, random, time

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

import config
from ontology.utils.file import ensure_path, get_file_paths, read_only



def init(language, source_file, source_path, target_path, pipeline_config,
         shuffle_file):

    """Creates a directory named target_path and all subdirectories and files in
    there needed for further processing. See the module docstring for more
    details."""

    settings = ["timestamp    =  %s\n" % time.strftime("%x %X"),
                "language     =  %s\n" % language,
                "source_file  =  %s\n" % source_file,
                "source_path  =  %s\n" % source_path,
                "target_path  =  %s\n" % target_path,
                "shuffle      =  %s\n" % str(shuffle_file)]
    
    print "\n[--init] initializing %s" % (target_path)
    print "\n   %s" % ("   ".join(settings))
    
    if os.path.exists(target_path):
        sys.exit("[--init] ERROR: %s already exists" % target_path)
    data_path = os.path.join(target_path, 'data')
    conf_path = os.path.join(target_path, 'config')
    
    create_directories(target_path, conf_path, data_path)
    create_general_config_file(conf_path, settings)
    create_default_pipeline_config_file(pipeline_config, conf_path)
    create_filelist(source_file, source_path, conf_path, shuffle_file)
    print
    

def create_directories(target_path, conf_path, data_path):
    """Create subdirectory structure in target_path."""
    print "[--init] creating directory structure in %s" % (target_path)
    ensure_path(conf_path)
    for subdir in config.PROCESSING_AREAS:
        subdir_path = data_path + os.sep + subdir
        ensure_path(subdir_path)

def create_filelist(source_file, source_path, conf_path, shuffle_file):
    """Create a list of files either by copying a given list or by traversing a
    given directory."""
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
        sys.exit("[--init] ERROR: " +
                 "need to define input with --filelist or " +
                 "--source-directory option, aborting")
    read_only(file_list)

def create_general_config_file(conf_path, settings):
    filename = os.path.join(conf_path, 'general.txt')
    print "[--init] creating %s" % (filename)
    fh = open(filename, 'w')
    fh.write("".join(settings))
    read_only(filename)

def create_default_pipeline_config_file(pipeline_config, conf_path):
    filename = os.path.join(conf_path, 'pipeline-default.txt')
    print "[--init] creating %s" % (filename)
    fh = open(filename, 'w')
    fh.write(pipeline_config.lstrip())
    read_only(filename)



if __name__ == '__main__':

    options = ['language=', 'corpus=',
               'filelist=', 'source-directory=', 'shuffle']
    (opts, args) = getopt.getopt(sys.argv[1:], '', options)

    source_file = None
    source_path = None
    target_path = config.WORKING_PATENT_PATH
    language = config.LANGUAGE
    shuffle_file = False
    pipeline_config = config.DEFAULT_PIPELINE
    
    for opt, val in opts:
        if opt == '--language': language = val
        if opt == '--filelist': source_file = val
        if opt == '--source-directory': source_path = val
        if opt == '--corpus': target_path = val
        if opt == '--shuffle': shuffle_file = True

    if language == 'cn':
            pipeline_config = config.DEFAULT_PIPELINE_CN

    init(language, source_file, source_path, target_path, pipeline_config,
         shuffle_file)
