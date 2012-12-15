"""

Script to initialize a working directory for patent processing. It does the following
things: (1) initialize the directory structure for a language, (2) import or create a file
config/files.txt with all external files to process, (3) create two default files that
define the set of training and test files, (4) initialize a config/stages.txt file that
keeps track of how many files have been processed by each processing stage, and (5) create
a file config/creation_settings.txt with settings used by this script.

The default for the training and test set is to use the first 500 files in FILES.txt. This
was done because it made sense for the 500 sample patents that were often used. Normally,
having identical files for test and training sets is a no no, but due to the particular
nature of how we train and test it was okay.

The STAGES.txt file may be obsolete in a little while.

The directory tree created inside the language directory is as follows:

    |-- config
    |   |-- creation_settings.txt
    |   |-- files.txt
    |   |-- stages.txt
    |   |-- testing-files-000000-000500.txt
    |   `-- training-files-000000-000500.txt
    |-- data
    |   |-- annotate       'input for annotation effort'
    |   |-- classify       'classification results'
    |   |-- doc_feats      'results from merging phrase features intro doc features'
    |   |-- ds_fact        'intermediate results from document structure parser'
    |   |-- ds_sect        'intermediate results from document structure parser'
    |   |-- ds_tags        'intermediate results from document structure parser'
    |   |-- ds_text        'intermediate results from document structure parser'
    |   |-- idx            'term indexes'
    |   |-- phr_feats      'results from candidate selection'
    |   |-- phr_occ        'results from candidate selection'
    |   |-- seg            'segmenter results'
    |   |-- selector       'results of the selector'
    |   |-- tag            'tagger results '
    |   |-- test           'test and evlauation area'
    |   |-- train          'vectors for the classifier and classifier models'
    |   |-- txt            'results of document structure parser'
    |   |-- ws             'work space to save data that crosses years'
    |   `-- xml            'import of XML data'
    `-- state
    
No existing files or directories will be overwritten, except for the five files in the
config directory that are listed above (creation_settings.txt, files.txt, stages.txt,
testing-files-000000-000500.txt, and training-files-000000-000500.txt).


USAGE

   % python step1_initialize.py OPTIONS

OPTIONS

   -l en|de|cn   --  language
   -f FILE       --  input: use external FILE and copy it to ALL_FILES.txt
   -s DIRECTORY  --  input: generate ALL_FILES.txt from DIRECTORY
   -t DIRECTORY  --  output: target directory where the language directory is put
   --shuffle     --  performs a random sort of FILES.txt, used with the -s option

Typical invocations:

    % python step1_initialize.py -l en -t data/patents -f filelist.txt
    % python step1_initialize.py -l en -t data/patents -s ../external/US/Xml --shuffle

    Both commands create a directory en/ inside of data/patents/, with config/ and data/
    subdirectories and several files mentioned above in the config/ subdirectory. The
    first form copies filelist.txt to en/config/files.txt. The second form traverses the
    directory ../external/US/Xml/, takes all file paths, randomly shuffles them, and then
    saves the result to en/config/files.txt.

"""


import os, sys, shutil, getopt, errno, random, time
import config_data


def init(language, source_file, source_path, target_path, shuffle_file):

    """Creates a directory named target_path/language and all subdirectories and files in
    there needed for further processing. See the module docstring for more details."""

    settings_strings = ["timestamp    =  %s\n" % time.strftime("%x %X"),
                        "language     =  %s\n" % language,
                        "source_file  =  %s\n" % source_file,
                        "source_path  =  %s\n" % source_path,
                        "target_path  =  %s\n" % target_path,
                        "shuffle      =  %s\n" % str(shuffle_file)]
    
    print "[--init] initializing %s/%s" % (target_path, language)
    print "\n        %s" % "        ".join(settings_strings)
    
    lang_path = os.path.join(target_path, language)
    if os.path.exists(lang_path):
        sys.exit("[--init] ERROR: %s already exists" % lang_path)
    data_path = os.path.join(lang_path, 'data')
    conf_path = os.path.join(lang_path, 'config')
    state_path = os.path.join(lang_path, 'state')
    ensure_path(conf_path)
    ensure_path(state_path)
    create_data_directories(data_path)

    print "[--init] creating %s/creation_settings.txt" % (conf_path)
    settings_file = open(os.path.join(conf_path, 'creation_settings.txt'), 'w')
    settings_file.write("".join(settings_strings))

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
    elif os.path.exists(file_list):
        print "[--init] %s already exists" % file_list
    else:
        sys.exit("[--init] ERROR: need to define input with -f or -s option")

    # NOTE: this may not be needed anymore with the new approach
    print "[--init] creating %s/stages.txt" % (conf_path)
    fh = open(os.path.join(conf_path, 'stages.txt'), 'w')
    fh.close()

    create_default_train_and_test_file_selections(file_list, conf_path)
    

def ensure_path(path):
    """If path already exists, print a message and continue"""
    try:
        os.makedirs(path)
        print "[ensure_path] creating %s" % (path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        

def create_data_directories(target_path):
    """Create subdirectories in target_path for all processing stages."""
    l_subdir = ["xml", "txt", "tag", "seg", "ds_text", "ds_tags", "ds_sect", "ds_fact",
                "phr_occ", "phr_feats", "doc_feats", 'ws', 'annotate', 'idx', 'train',
                'test', 'classify', 'selector' ]
    for subdir in l_subdir:
        subdir_path = target_path + os.sep + subdir
        ensure_path(subdir_path)


def create_default_train_and_test_file_selections(file_list, conf_path):
    """Take first 500 files of filelist and use those as the default for the test and
    training set."""
    train_file = open(os.path.join("%s" % conf_path, "training-files-000000-000500.txt"), 'w')
    test_file = open(os.path.join("%s" % conf_path, "testing-files-000000-000500.txt"), 'w')
    print "[--init] creating %s" % (train_file.name)
    print "[--init] creating %s" % (test_file.name)
    lines = get_lines(file_list, start=0, limit=500)
    train_file.write("\n".join(lines) + "\n")
    test_file.write("\n".join(lines) + "\n")


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
    shuffle_file = False
    
    for opt, val in opts:

        if opt == '-l': language = val
        if opt == '-f': source_file = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '--shuffle': shuffle_file = True
        
    init(language, source_file, source_path, target_path, shuffle_file)
