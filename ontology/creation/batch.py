"""

Run al processing in batch. Very similar to patent_analyzer.py, but approaches the task
from a different angle

The script starts with lists of files pointing to all single files in the external
directory, with a list for each language. these lists have all files for a lnaguage in a
random order
   
Maintains a file for each lannguage which stores what what was done for each processing
stage. Lines in that file look as follows:

   --xml2txt 500
   --txt2tag 200
   --tag2chk 100

These lines indicate that the first 500 lines of the input have gone through the xml2txt
stage, 200 through the txt2tag stage and 100 through the tag2chk phase. Initially this
file is empty but when a value is first retrieved it is initialized to 0.
   
The input to the scipt is a stage and a number of documents to process. For example:

   % python batch.py --xml2txt -n 100

This sends 100 documents through the xml2txt phase (using a default data directory), after
which the lines in the progress file are updated to

   --xml2txt 600
   --txt2tag 200
   --tag2chk 100

Unlike patent_analyzer.opy, this script does not call directory level methods like
xml2txt.patents_xml2txt(...), but instead calls methods that process one file only, doing
all the housekeeping itself.


Usage:
    
    % python patent_analyzer.py [OPTIONS]

    -l LANG     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -s PATH     --  external source directory with XML files, see below for the default
    -t PATH     --  target directory, default is data/patents
    -n INTEGER  --  number of documents to process
    --init      --  initialize directory structure in target path (non-destructive)
    --populate  --  populate directory in target path with files from source path
    --xml2txt   --  document structure parsing
    --txt2tag   --  tagging
    --tag2chk   --  creating chunks in context
    --summary   --  create summary lists

    All long options require a target path and a language (via the -l and -t options or
    their defaults). The long options --init and --populate also require a source path
    (via -s or its default). The -n option is ignored if --init is used.
    
The final results of these steps are in:

    TARGET_PATH/LANGUAGE/phr_occ
    TARGET_PATH/LANGUAGE/phr_feat
    TARGET_PATH/LANGUAGE/ws

    
Examples for all stages:

Initialization of directories is purely defined by what is found in the source data,
initializing directories for all years. It also creates the file with all patents in
random order.

% setenv SOURCE_PATENTS /home/j/corpuswork/fuse/fuse-patents/500-patents/DATA/Lexis-Nexis
% python batch.py --init -l en -s $SOURCE_PATENTS/US/Xml/ -t data/patents

Population follows the paradigm above, taking elements from the list. With the following
you add 10 files to the data/patents/en/xml directory.

% python batch.py --populate -l en -n 10 -s $SOURCE_PATENTS/US/Xml/ -t data/patents

Running the document structure parser. From here on, you do not need the source directory
anymore. Just say what you want to do and how many files you want to do. Assumes that
previous processing stages on those files have been done.

% python batch.py --xml2txt -l en -n 10 -t data/patents
% python batch.py --txt2tag -l de -n 10 -t data/patents/

Note that the tagger may only work on machines like pasiphae. The invocation there is
slightly different:

% python2.6 batch.py --txt2tag -l de -n 10 -t data/patents/

"""

import os, sys, time, shutil, getopt, subprocess
from random import shuffle

import putils
import xml2txt
import txt2tag
import tag2chunk
import cn_txt2seg
import cn_seg2tag
import pf2dfeats

import config_data

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser


# will be overwritten by command line options
source_path = config_data.external_patent_path
target_path = config_data.working_patent_path
language = config_data.language


def initialize(source_path, target_path, language):
    """Creates a directory inside data/patents, using the language and the range of years as
    determined by the year range in the external sample's subdirectory. Also creates a
    file named ALL_FILES.tx with all file paths in the source directory and creates an
    empty file ALL_STAGES.txt with infomraiton on what files have been processed."""
    print "[--init] initializing %s/%s" % (target_path, language)
    print "[--init] using %s" % source_path
    lang_path = os.path.join(target_path, language)
    l_year = os.listdir(source_path)
    putils.make_patent_dir(language, target_path, l_year)
    filenames = []
    print "[--init] creating %s/%s/ALL_FILES.txt" % (target_path, language)
    for (root, dirs, files) in os.walk(source_path):
        for file in files:
            filenames.append(os.path.join(root, file))
    shuffle(filenames)
    fh = open(os.path.join(lang_path, 'ALL_FILES.txt'), 'w')
    for fname in filenames:
        fh.write(fname + "\n")
    fh.close()
    print "[--init] creating %s/%s/ALL_STAGES.txt" % (target_path, language)
    fh = open(os.path.join(lang_path, 'ALL_STAGES.txt'), 'w')
    fh.close()
    
def populate_xml_directory(source_path, target_path, language, limit):
    """Populate xml directory in the target directory with limit files from the source path."""
    print "[--populate] populating %s/%s/xml" % (target_path, language)
    print "[--populate] using %d files from %s" % (limit, source_path)
    stages = read_stages(target_path, language)
    fnames = files_to_process(stages, '--populate', limit)
    count = 0
    for (year, fname) in fnames:
        count += 1
        source_file = os.path.join(source_path, year, fname)
        target_file = os.path.join(target_path, language, 'xml', year, fname)
        print "[--populate] %04d adding %s" % (count, target_file)
        shutil.copyfile(source_file, target_file)
    stages['--populate'] += limit
    write_stages(target_path, language, stages)

def run_xml2txt(target_path, language, limit):
    """Takes xml files and runs the document structure parser in onto mode. Adds files
    to the language/txt directory and ds_* directories with intermediate document
    structure parser results."""
    print "[--xml2txt] on %s/%s/xml/" % (target_path, language)
    stages = read_stages(target_path, language)
    xml_parser = Parser()
    xml_parser.onto_mode = True
    mappings = {'en': 'ENGLISH', 'de': "GERMAN", 'cn': "CHINESE" }
    xml_parser.language = mappings[language]
    fnames = files_to_process(stages, '--xml2txt', limit)
    count = 0
    for year, fname in fnames:
        count += 1
        source_file = os.path.join(target_path, language, 'xml', year, fname)
        target_file = os.path.join(target_path, language, 'txt', year, fname)
        print "[--xml2txt] %04d creating %s" % (count, target_file)
        xml2txt.xml2txt(xml_parser, source_file, target_file)
    stages['--xml2txt'] += limit
    stages = write_stages(target_path, language, stages)

def run_txt2tag(target_path, language, limit):
    """Takes txt files and runs the tagger (and segmenter for Chinese) on them. Adds files to
    the language/tag and language/seg directories. Works on pasiphae but not on chalciope."""
    print "[--txt2tag] on %s/%s/txt/" % (target_path, language)
    stages = read_stages(target_path, language)
    tagger = txt2tag.get_tagger(language)
    fnames = files_to_process(stages, '--txt2tag', limit)
    count = 0
    for year, fname in fnames:
        count += 1
        source_file = os.path.join(target_path, language, 'txt', year, fname)
        target_file = os.path.join(target_path, language, 'tag', year, fname)
        if language == 'cn':
            # TODO: need the equivalent of the one below
            cn_txt2seg.patent_txt2seg_dir(target_path, language)
            cn_seg2tag.patent_txt2tag_dir(target_path, language)
        else:
            print "[--txt2tag] %04d creating %s" % (count, target_file)
            txt2tag.tag(source_file, target_file, tagger)
    stages['--txt2tag'] += limit
    stages = write_stages(target_path, language, stages)

    
def read_stages(target_path, language):
    stages = {}
    for line in open(os.path.join(target_path, language, 'ALL_STAGES.txt')):
        if not line.strip():
            continue
        (stage, count) = line.strip().split("\t")
        stages[stage] = int(count)
    return stages

def write_stages(target_path, language, stages):
    stages_file = os.path.join(target_path, language, 'ALL_STAGES.txt')
    backup_file = os.path.join(target_path, language,
                               "ALL_STAGES.%s.txt" % time.strftime("%Y%m%d-%H%M%S"))
    shutil.copyfile(stages_file, backup_file)
    fh = open(stages_file, 'w')
    for stage, count in stages.items():
        fh.write("%s\t%d\n" % (stage, count))
    fh.close()

def files_to_process(stages, stage, limit):
    current_count = stages.setdefault(stage, 0)
    files = open(os.path.join(target_path, language, 'ALL_FILES.txt'))
    line_number = 0
    while line_number < current_count:
        files.readline(),
        line_number += 1
    files_read = 0
    fnames = []
    while files_read < limit:
        fname = files.readline().strip()
        basename = os.path.basename(fname)
        dirname = os.path.dirname(fname)
        year = os.path.split(dirname)[1]
        fnames.append((year, basename))
        files_read += 1
    return fnames


    
if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:n:',
        ['init', 'populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 'summary'])

    init, populate = False, False
    limit = 0
    xml_to_txt, txt_to_seg, txt_to_tag, tag_to_chk = False, False, False, False
    pf_to_dfeats = False
    summary = False
    
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        if opt == '--init': init = True
        if opt == '--populate': populate = True
        if opt == '--xml2txt': xml_to_txt = True
        if opt == '--txt2tag': txt_to_tag = True
        if opt == '--tag2chk': tag_to_chk = True
        if opt == '--pf2dfeats': pf_to_dfeats = True
        if opt == '--summary': summary = True


    if init:
        initialize(source_path, target_path, language)
    elif populate:
        populate_xml_directory(source_path, target_path, language, limit)
    elif xml_to_txt:
        run_xml2txt(target_path, language, limit)
    elif txt_to_tag:
        run_txt2tag(target_path, language, limit)

    elif tag_to_chk:
        # populates language/phr_occ and language/phr_feat
        tag2chunk.patent_tag2chunk_dir(target_path, language)
    
    elif pf_to_dfeats:
        # creates a union of the features for each chunk in a doc (for training)
        pf2dfeats.patent_pf2dfeats_dir(target_path, language)

    elif summary:
        # create summary data phr_occ and phr_feats across dates, also phrase file suitable for 
        # annotation (phr_occ.unlab) in the ws subdirectory
        command = "sh ./cat_phr.sh %s %s" % (target_path, language)
        subprocess.call(command, shell=True)

    # Note: At this point, user must manually create an annotated file phr_occ.lab and
    # place it in <lang>/ws subdirectory.
        
    elif union_train:
        # creates a mallet training file for labeled data with features as union of all phrase
        # instances within a doc.
        # Creates a model: utrain.<version>.MaxEnt.model in train subdirectory
        train.patent_utraining_data(target_path, language, version, xval)

    elif union_test:
        train.patent_utraining_test_data(target_path, language, version)

    elif tech_scores:
        # use the mallet.out file from union_test to generate a sorted list of 
        # technology terms with their probabilities
        command = "sh ./patent_tech_scores.sh %s %s %s" % (target_path, version, language)
        subprocess.call(command, shell=True)

    elif all:
        print "[patent_analyzer]source_path: %s, target_path: %s, language: %s" % (source_path, target_path, language)
        l_year = os.listdir(source_path)
        putils.make_patent_dir(language, target_path, l_year)
        putils.populate_patent_xml_dir(language, source_path, target_path, l_year)
        xml2txt.patents_xml2txt(target_path, language)
        if language == 'cn':
            cn_txt2seg.patent_txt2seg_dir(target_path, language)
            cn_seg2tag.patent_txt2tag_dir(target_path, language)
        else:
            txt2tag.patent_txt2tag_dir(target_path, language)
        tag2chunk.patent_tag2chunk_dir(target_path, language)
        pf2dfeats.patent_pf2dfeats_dir(target_path, language)
        command = "sh ./cat_phr.sh %s %s" % (target_path, language)
        subprocess.call(command, shell=True)
