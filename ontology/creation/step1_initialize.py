"""

Script to initialize a working directory for patent processing. It does the following
things: (1) initialize the directory structure for a language, (2) import or create a file
config/files.txt with all external files to process, (3) create two default files that
define the set of training and test files, (4) create a file config/config-pipeline.txt
with default settings for the pipeline, and (5) create a file config/config-general.txt
with settings used by this script.

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
    % python step1_initialize.py -l en -t data/patents -s ../external/US/Xml --shuffle

    Both commands create a directory en/ inside of data/patents/, with config/ and data/
    subdirectories and several files mentioned above in the config/ subdirectory. The
    first form copies filelist.txt to en/config/files.txt. The second form traverses the
    directory ../external/US/Xml/, takes all file paths, randomly shuffles them, and then
    saves the result to en/config/files.txt.


NOTES

Paths in config/config-general.txt can be either relative or absolute. Initially, all
settings are from this initialization script, but other configuration settings could be
added later.

The config-pipeline.txt file is tricky. It contains all default settings for arguments
handed over to individual components (tagger, chunker, maxent model trainer etcetera). If
more arguments are added, then this file should be updated manually and it should then
also be used to fill in default values for past processing jobs (assuming that there is a
default that makes sense).

The default for creating the training set and test set is to use the first 500 files in
config/files.txt. This was done because it made sense for the 500 sample patents that were
often used. Normally, having identical files for test and training sets is a no no, but
due to the particular nature of how we train and test it was okay. In general though,
non-default versionsof these files will be created.

The directory tree created inside the language directory is as follows:

    |-- config
    |   |-- config-general.txt
    |   |-- config-pipeline.txt
    |   |-- files.txt
    |   |-- testing-files-000000-000500.txt
    |   `-- training-files-000000-000500.txt
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

Note that the processing stages are grouped using prefixes, where the features carry some meaning:

   d -- document level processing
   t -- processing for the technology classifier
   o -- processing for the ontology creator (this is used by a downstream script)

No existing files or directories will be overwritten, except for the files in the config
directory that are listed above (config-general.txt, files.txt, config-pipeline.txt,
stages.txt, testing-files-000000-000500.txt, and training-files-000000-000500.txt).

"""


import os, sys, shutil, getopt, errno, random, time
import config_data


DEFAULT_PIPELINE = """
# This file contains the default pipeline configuration settings. Settings in here can be
# overruled by handing the step2_document_processing script the path to another
# configuration file.

xml2txt
txt2tag
tag2chk chunk_filter=off
pf2dfeats
"""

PROCESSING_AREAS = \
    ['d0_xml', 'd1_txt', 'd2_tag', 'd2_seg', 'd3_phr_occ', 'd3_phr_feats', 'd4_doc_feats',
     't0_annotate', 't1_train', 't2_classify', 't3_test',
     'o1_index', 'o2_matcher', 'o3_selector',
     'workspace' ]


def init(language, source_file, source_path, target_path, pipeline_config, shuffle_file):

    """Creates a directory named target_path/language and all subdirectories and files in
    there needed for further processing. See the module docstring for more details."""

    settings_strings = ["timestamp    =  %s\n" % time.strftime("%x %X"),
                        "language     =  %s\n" % language,
                        "source_file  =  %s\n" % source_file,
                        "source_path  =  %s\n" % source_path,
                        "target_path  =  %s\n" % target_path,
                        "shuffle      =  %s\n" % str(shuffle_file)]
    
    print "\n[--init] initializing %s/%s" % (target_path, language)
    print "\n   %s" % ("   ".join(settings_strings))
    
    lang_path = os.path.join(target_path, language)
    if os.path.exists(lang_path):
        sys.exit("[--init] ERROR: %s already exists" % lang_path)
    data_path = os.path.join(lang_path, 'data')
    conf_path = os.path.join(lang_path, 'config')
    state_path = os.path.join(lang_path, 'state')
    
    print "[--init] creating directory structure in %s" % (lang_path)
    ensure_path(conf_path)
    create_data_directories(data_path)

    print "[--init] creating %s/config-general.txt" % (conf_path)
    settings_file = open(os.path.join(conf_path, 'config-general.txt'), 'w')
    settings_file.write("".join(settings_strings))

    create_default_pipeline_config_file(pipeline_config, conf_path)
    create_filelist(source_file, source_path, conf_path, shuffle_file)
    #create_stages_file(conf_path)
    create_default_train_and_test_file_selections(conf_path)
    print ""
    

def ensure_path(path, verbose=False):
    """Make sure path exists."""
    try:
        os.makedirs(path)
        if verbose:
            print "[ensure_path] creating %s" % (path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        

def create_data_directories(target_path):
    """Create subdirectories in target_path for all processing areas."""
    for subdir in PROCESSING_AREAS:
        subdir_path = target_path + os.sep + subdir
        ensure_path(subdir_path)


def create_stages_file(conf_path):
    # NOTE: this may not be needed anymore with the new approach
    print "[--init] creating %s/stages.txt" % (conf_path)
    fh = open(os.path.join(conf_path, 'stages.txt'), 'w')
    fh.close()


def create_filelist(source_file, source_path, conf_path, shuffle_file):
    print "[--init] creating %s/files.txt" % (conf_path)
    file_list = os.path.join(conf_path, 'files.txt')
    if source_file is not None:
        shutil.copyfile(source_file, file_list)
    elif source_path is not None:
        filenames = []
        for (root, dirs, files) in os.walk(source_path):
            for file in files:
                filenames.append(os.path.join(root, file))
        if shuffle_file:
            random.shuffle(filenames)
        fh = open(file_list, 'w')
        for fname in filenames:
            fh.write(fname + "\n")
        fh.close()
    else:
        sys.exit("[--init] ERROR: need to define input with -f or -s option")


def create_default_train_and_test_file_selections(conf_path):
    """Take first 500 files of filelist and use those as the default for the test and
    training set."""
    file_list = os.path.join(conf_path, 'files.txt')
    train_file = open(os.path.join("%s" % conf_path, "training-files-000000-000500.txt"), 'w')
    test_file = open(os.path.join("%s" % conf_path, "testing-files-000000-000500.txt"), 'w')
    print "[--init] creating %s" % (train_file.name)
    print "[--init] creating %s" % (test_file.name)
    lines = get_lines(file_list, start=0, limit=500)
    train_file.write("\n".join(lines) + "\n")
    test_file.write("\n".join(lines) + "\n")


def create_default_pipeline_config_file(pipeline_config, conf_path):
    fh = open(os.path.join(conf_path, 'config-pipeline.txt'), 'w')
    print "[--init] creating %s" % (fh.name)
    fh.write(pipeline_config.lstrip())
    fh.close()


def get_lines(filename, start=0, limit=500):
    """Return a list with n=limit lines from filename, starting from line n=start.""" 
    current_count = start
    fh = open(filename)
    line_number = 0
    while line_number < current_count:
        fh.readline(),
        line_number += 1
    lines_read = 0
    lines = []
    while lines_read < limit:
        line = fh.readline().strip()
        if line == '':
            break
        lines.append(line)
        lines_read += 1
    fh.close()
    return lines

        


if __name__ == '__main__':

    (opts, args) = getopt.getopt(sys.argv[1:], 'l:s:f:t:', ['shuffle'])

    source_file = None
    source_path = None
    target_path = config_data.working_patent_path
    language = config_data.language
    pipeline_config = DEFAULT_PIPELINE
    shuffle_file = False
    
    for opt, val in opts:

        if opt == '-l': language = val
        if opt == '-f': source_file = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '--shuffle': shuffle_file = True
        
    init(language, source_file, source_path, target_path, pipeline_config, shuffle_file)
