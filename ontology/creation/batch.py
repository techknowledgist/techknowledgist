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
    --annotate  --  prepare files for annotation
    --utrain    --  create model for classifier
    --utest     --  run classifier
    --scores    --  generate scores from classifier results

    --verbose   --  print name of each processed file to stdout
    
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

import os, sys, time, shutil, getopt, subprocess, codecs
from random import shuffle

import config_data
import putils
import xml2txt
import txt2tag
import sdp
import tag2chunk
import cn_txt2seg
import cn_seg2tag
import pf2dfeats
import train

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
verbose = False

def run_init(source_path, target_path, language):
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
    
def run_populate(source_path, target_path, language, limit):
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
        if verbose:
            print "[--populate] %04d adding %s" % (count, target_file)
        shutil.copyfile(source_file, target_file)
    update_stages(target_path, language, '--populate', limit)

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
        if verbose:
            print "[--xml2txt] %04d creating %s" % (count, target_file)
        try:
            xml2txt.xml2txt(xml_parser, source_file, target_file)
        except Exception:
            fh = codecs.open(target_file, 'w')
            fh.close()
            print "[--xml2txt]      WARNING: error on", source_file
    update_stages(target_path, language, '--xml2txt', limit)

def run_txt2tag(target_path, language, limit):
    """Takes txt files and runs the tagger (and segmenter for Chinese) on them. Adds files to
    the language/tag and language/seg directories. Works on pasiphae but not on chalciope."""
    print "[--txt2tag] on %s/%s/txt/" % (target_path, language)
    stages = read_stages(target_path, language)
    tagger = txt2tag.get_tagger(language)
    segmenter = sdp.Segmenter()
    fnames = files_to_process(stages, '--txt2tag', limit)
    count = 0
    for year, fname in fnames:
        count += 1
        txt_file = os.path.join(target_path, language, 'txt', year, fname)
        seg_file = os.path.join(target_path, language, 'seg', year, fname)
        tag_file = os.path.join(target_path, language, 'tag', year, fname)
        if language == 'cn':
            if verbose:
                print "[--txt2tag] %04d creating %s" % (count, seg_file)
            cn_txt2seg.seg(txt_file, seg_file, segmenter)
            if verbose:
                print "[--txt2tag] %04d creating %s" % (count, tag_file)
            cn_seg2tag.tag(seg_file, tag_file, tagger)
        else:
            if verbose:
                print "[--txt2tag] %04d creating %s" % (count, tag_file)
            txt2tag.tag(txt_file, tag_file, tagger)
    update_stages(target_path, language, '--txt2tag', limit)

def run_tag2chk(target_path, language, limit):
    """Runs the np-in-context code on tagged input. Populates language/phr_occ and
    language/phr_feat."""
    print "[--tag2chk] on %s/%s/tag/" % (target_path, language)
    stages = read_stages(target_path, language)
    fnames = files_to_process(stages, '--tag2chk', limit)
    count = 0
    for (year, fname) in fnames:
        count += 1
        tag_file = os.path.join(target_path, language, 'tag', year, fname)
        occ_file = os.path.join(target_path, language, 'phr_occ', year, fname)
        fea_file = os.path.join(target_path, language, 'phr_feats', year, fname)
        if verbose:
            print "[--tag2chk] %04d adding %s" % (count, occ_file)
        tag2chunk.Doc(tag_file, occ_file, fea_file, year, language)
    update_stages(target_path, language, '--tag2chk', limit)

def run_pf2dfeats(target_path, language, limit):
    """Creates a union of the features for each chunk in a doc (for training)."""
    print "[--pf2dfeats] on %s/%s/phr_feats/" % (target_path, language)
    stages = read_stages(target_path, language)
    fnames = files_to_process(stages, '--pf2dfeats', limit)
    count = 0
    for (year, fname) in fnames:
        count += 1
        doc_id = os.path.splitext(os.path.basename(fname))[0]
        phr_file = os.path.join(target_path, language, 'phr_feats', year, fname)
        doc_file = os.path.join(target_path, language, 'doc_feats', year, fname)
        if verbose:
            print "[--pf2dfeats] %04d adding %s" % (count, doc_file)
        pf2dfeats.make_doc_feats(phr_file, doc_file, doc_id, year)
    update_stages(target_path, language, '--pf2dfeats', limit)

def run_summary(target_path, language, limit):
    """Collect data from directories into workspace area: ws/doc_feats.all,
    ws/phr_feats.all and ws/phr_occ.all. Al downstream processing should rely on these
    data and nothing else."""
    #subprocess.call("sh ./cat_phr.sh %s %s" % (target_path, language), shell=True)
    stages = read_stages(target_path, language)
    fnames = files_to_process(stages, '--summary', limit)
    doc_feats_file = os.path.join(target_path, language, 'ws', 'doc_feats.all')
    phr_feats_file = os.path.join(target_path, language, 'ws', 'phr_feats.all')
    phr_occ_file = os.path.join(target_path, language, 'ws', 'phr_occ.all')
    fh_doc_feats = codecs.open(doc_feats_file, 'a', encoding='utf-8')
    fh_phr_feats = codecs.open(phr_feats_file, 'a', encoding='utf-8')
    fh_phr_occ = codecs.open(phr_occ_file, 'a', encoding='utf-8')
    for (year, fname) in fnames:
        doc_feats_file = os.path.join(target_path, language, 'doc_feats', year, fname)
        phr_feats_file = os.path.join(target_path, language, 'phr_feats', year, fname)
        phr_occ_file = os.path.join(target_path, language, 'phr_occ', year, fname)
        fh_doc_feats.write(codecs.open(doc_feats_file, encoding='utf-8').read())
        fh_phr_feats.write(codecs.open(phr_feats_file, encoding='utf-8').read())
        fh_phr_occ.write(codecs.open(phr_occ_file, encoding='utf-8').read())
    update_stages(target_path, language, '--summary', limit)

    
def run_annotate(target_path, language, limit):

    """Create input for annotation effort. This function is different in the sense that it
    does not keep track of how far it got into the corpus. Rather, you tell it how many
    files you want to use and it takes those files off the top of the ws/phr_occ.all file
    and generates the input for annotation from there. And unlike --summary, this does not
    append to the output files but overwrites older versions. The limit is used just to
    determine how many files are taken to create the list for annotation, it is not used
    to increment any number in the ALL_STAGES.txt file."""
    
    phr_occ_all_file = os.path.join(target_path, language, 'ws', 'phr_occ.all')
    phr_occ_phr_file = os.path.join(target_path, language, 'ws', 'phr_occ.phr')
    fh_phr_occ_all = codecs.open(phr_occ_all_file, 'r', encoding='utf-8')
    fh_phr_occ_phr = codecs.open(phr_occ_phr_file, 'w', encoding='utf-8')

    # first collect all phrases
    print "Creating", phr_occ_phr_file 
    current_fname = None
    count = 0
    for line in fh_phr_occ_all:
        (fname, year, phrase, sentence) = line.strip("\n").split("\t")
        fname = fname.split('.xml_')[0] + '.xml'
        if fname != current_fname:
            current_fname = fname
            count += 1
        if count > limit:
            break
        fh_phr_occ_phr.write(phrase+"\n")

    # now create phr_occ.uct and phr_occ.unlab
    phr_occ_uct_file = os.path.join(target_path, language, 'ws', 'phr_occ.uct')
    phr_occ_unlab_file = os.path.join(target_path, language, 'ws', 'phr_occ.unlab')
    print "Creating", phr_occ_uct_file 
    command = "cat %s | sort | uniq -c | sort -nr | python reformat_uc.py > %s" \
              % (phr_occ_phr_file, phr_occ_uct_file)
    print '%', command
    subprocess.call(command, shell=True)    
    print "Creating", phr_occ_unlab_file 
    command = "cat %s | sed -e 's/^[0-9]*\t/\t/' > %s" \
              % (phr_occ_uct_file, phr_occ_unlab_file)
    print '%', command
    subprocess.call(command, shell=True)    

def run_utrain(target_path, language, version, xval, limit):
    """Creates a mallet training file for labeled data with features as union of all
    phrase instances within a doc. Also creates a model utrain.<version>.MaxEnt.model in
    the train subdirectory. Limit is used to determine the size of the training set, as
    with run_annotate, it is not used for incrementing values in ALL_STAGES.txt. """
    annot_path = os.path.join(config_data.annotation_directory, language)
    source_annot_lang_file = os.path.join(annot_path, 'phr_occ.lab')
    target_annot_lang_file = os.path.join(target_path, language, 'ws', 'phr_occ.lab')
    shutil.copyfile(source_annot_lang_file, target_annot_lang_file)
    train.patent_utraining_data(target_path, language, version, xval, limit)

        
def read_stages(target_path, language):
    stages = {}
    for line in open(os.path.join(target_path, language, 'ALL_STAGES.txt')):
        if not line.strip():
            continue
        (stage, count) = line.strip().split("\t")
        stages[stage] = int(count)
    return stages

def update_stages(target_path, language, stage, limit):
    """Updates the counts in ALL_STAGES.txt. This includes rereading the file because
    during processing on one machine another machine could have done some other processing
    and have updated the fiel, we do not want to lose those updates. This could
    potentially go wrong when to separate processes terminate at the same time, a rather
    unlikely occurrence."""
    stages = read_stages(target_path, language)
    stages[stage] += limit
    write_stages(target_path, language, stages)
    
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
        ['init', 'populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 
         'summary', 'annotate', 'utrain', 'utest', 'scores'])

    init, populate = False, False
    limit = 0
    xml_to_txt, txt_to_seg, txt_to_tag, tag_to_chk = False, False, False, False
    pf_to_dfeats = False
    summary, annotate = False, False
    union_train, union_test, tech_scores = False, False, False
    version = "1"
    xval = "0"

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
        if opt == '--annotate': annotate = True
        if opt == '--utrain': union_train = True
        if opt == '--utest': union_test = True
        if opt == '--scores': tech_scores = True
        if opt == '--verbose': verbose = True

    if init:
        run_init(source_path, target_path, language)
    elif populate:
        run_populate(source_path, target_path, language, limit)
    elif xml_to_txt:
        run_xml2txt(target_path, language, limit)
    elif txt_to_tag:
        run_txt2tag(target_path, language, limit)
    elif tag_to_chk:
        run_tag2chk(target_path, language, limit)
    elif pf_to_dfeats:
        run_pf2dfeats(target_path, language, limit)
    elif summary:
        run_summary(target_path, language, limit)
    elif annotate:
        run_annotate(target_path, language, limit)
        
    # Note: At this point, user must manually create an annotated file phr_occ.lab, it is
    # expected that this file lives in ../annotation/<language>. It is automatically
    # copied to the <language>/ws subdirectory in the next step.
        
    elif union_train:
        run_utrain(target_path, language, version, xval, limit)

    elif union_test:
        train.patent_utraining_test_data(target_path, language, version)

    elif tech_scores:
        # use the mallet.out file from union_test to generate a sorted list of 
        # technology terms with their probabilities
        command = "sh ./patent_tech_scores.sh %s %s %s" % (target_path, version, language)
        subprocess.call(command, shell=True)
