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

import os, sys, time, shutil, getopt, subprocess, codecs, textwrap
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
import mallet

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser
from ontology.utils.batch import read_stages, update_stages, write_stages
from ontology.utils.batch import files_to_process

# defaults that can be overwritten by command line options
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
    fnames = files_to_process(target_path, language, stages, '--populate', limit)
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
    fnames = files_to_process(target_path, language, stages, '--xml2txt', limit)
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
    fnames = files_to_process(target_path, language, stages, '--txt2tag', limit)
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
    fnames = files_to_process(target_path, language, stages, '--tag2chk', limit)
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
    fnames = files_to_process(target_path, language, stages, '--pf2dfeats', limit)
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
    fnames = files_to_process(target_path, language, stages, '--summary', limit)
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

    
def run_annotate1(target_path, language, limit):

    """Create input for annotation effort fro creating a prior. This function is different
    in the sense that it does not keep track of how far it got into the corpus. Rather,
    you tell it how many files you want to use and it takes those files off the top of the
    ws/phr_occ.all file and generates the input for annotation from there. And unlike
    --summary, this does not append to the output files but overwrites older versions. The
    limit is used just to determine how many files are taken to create the list for
    annotation, it is not used to increment any number in the ALL_STAGES.txt file."""
    
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

    
def run_annotate2(target_path, language, limit):

    """Prepare two files that can be used for evaluation. One file named
    phr_occ.eval.unlab that lists a term-file pairs from n=limit files where all contexts
    are listed following the pair. This file is input for manual annotation. And one file
    named doc_feats.eval which is a subset of doc_feats.all, but it contains only those
    term-file pairs that occur in phr_occ.eval.unlab."""
    
    eval1 = os.path.join(target_path, language, 'ws', 'phr_occ.eval.unlab')
    eval2 = os.path.join(target_path, language, 'ws', 'doc_feats.eval')
    fh_eval1 = codecs.open(eval1, 'w', encoding='utf-8')
    fh_eval2 = codecs.open(eval2, 'w', encoding='utf-8')
    
    phr_occ_array = _read_phr_occ(target_path, language, limit)
    doc_feats_array = _read_doc_feats(target_path, language, limit)

    # sort phrases on how many contexts we have for each
    phrases = phr_occ_array.keys()
    sort_fun = lambda x: sum([len(x) for x in phr_occ_array[x].values()])
    phrases = reversed(sorted(phrases, key=sort_fun))

    for phrase in phrases:
        if not (phr_occ_array.has_key(phrase) and doc_feats_array.has_key(phrase)):
            continue
        for doc in phr_occ_array[phrase].keys():
            fh_eval1.write("\n?\t%s\t%s\n\n" % (phrase, doc))
            for sentence in phr_occ_array[phrase][doc]:
                lines = textwrap.wrap(sentence, 100)
                fh_eval1.write("\t- %s\n" %  lines[0])
                for line in lines[1:]:
                    fh_eval1.write("\t  %s\n" % line)
        for doc in doc_feats_array[phrase].keys():
            for sentence in doc_feats_array[phrase][doc]:
                fh_eval2.write(sentence)
            

def _read_phr_occ(target_path, language, limit):
    """Return the contents of ws/phr_occ.all in a dictionary."""
    def get_stuff(line):
        """Returns the file name, the phrase and the context, here the context is the
        sentence listed with the phrase."""
        (fname, year, phrase, sentence) = line.strip("\n").split("\t")
        fname = fname.split('.xml_')[0]
        return (fname, phrase, sentence)
    return _read_phrocc_or_docfeats('phr_occ.all', get_stuff)

def _read_doc_feats(target_path, language, limit):
    """Return the contents of ws/doc_feats.all in a dictionary."""
    def get_stuff(line):
        """Returns the file name, the phrase and the context, here the context is the
        entire line."""
        (phrase, id, feats) = line.strip("\n").split("\t",2)
        (year, fname, phrase2) = id.split('|')
        return (fname, phrase, line)
    return _read_phrocc_or_docfeats('doc_feats.all', get_stuff)

def _read_phrocc_or_docfeats(fname, get_stuff_fun):
    phr_occ_file = os.path.join(target_path, language, 'ws', fname)
    fh_phr_occ = codecs.open(phr_occ_file, encoding='utf-8')
    phr_occ_array = {}
    current_fname = None
    count = 0
    for line in fh_phr_occ:
        fname, phrase, context = get_stuff_fun(line)
        if count >= limit:
            break
        if fname != current_fname:
            current_fname = fname
            count += 1
        phr_occ_array.setdefault(phrase, {})
        phr_occ_array[phrase].setdefault(fname, []).append(context)
    return phr_occ_array

                                                   
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

    
def run_utest(target_path, language, version, limit, classifier='MaxEnt'):

    """Run the classifier on n=limit documents. Batch version of the function
    train.patent_utraining_test_data(). Appends results to test/utest.1.MaxEnt.out and
    keeps intermediate results for this invocation in test/utest.1.mallet.START-END (raw
    feature vectors) and test/utest.1.MaxEnt.out.BEGIN_END, where begin and end are taken
    from ALL_STAGES.txt and the limit parameter."""
    
    # get dictionary of annotations and keep label stats (total_count == unlabeled_count
    # if use_all_chunks_p is False, otherwisetal_count == unlabeled_count + labeled_counts
    d_phr2label = train.load_phrase_labels(target_path, language)
    stats = { 'labeled_count': 0, 'unlabeled_count': 0, 'total_count': 0 }

    stages = read_stages(target_path, language)
    fnames = files_to_process(target_path, language, stages, '--utest', limit)
    (train_dir, test_dir, mallet_file, results_file, all_results_file) = \
        _classifier_io(target_path, language, version, classifier, stages)
    print "[--utest] vector file - %s" %  mallet_file
    print "[--utest] results file - %s" %  results_file

    count = 0
    fh = codecs.open(mallet_file, "a", encoding='utf-8')
    for (year, fname) in fnames:
        count += 1
        doc_feats_file = os.path.join(target_path, language, 'doc_feats', year, fname)
        if verbose:
            print "%05d %s" % (count, doc_feats_file)
        train.add_file_to_utraining_test_file(doc_feats_file, fh, d_phr2label, stats)
    fh.close()
    
    _run_classifier(train_dir, test_dir, version, classifier, mallet_file, results_file)
    _append_classifier_results(results_file, all_results_file)
    update_stages(target_path, language, '--utest', limit)
    
    
def _classifier_io(target_path, language, version, classifier, stages):
    start = stages.get('--utest', 0)
    file_range = "%06d-%06d" % (start, start + limit)
    test_dir = os.path.join(target_path, language, "test")
    train_dir = os.path.join(target_path, language, "train")
    mallet_file = os.path.join(test_dir, "utest.%s.mallet.%s" % (version, file_range))
    results_file = os.path.join(test_dir, "utest.%s.%s.out.%s" % (version, classifier, file_range))
    all_results_file = os.path.join(test_dir, "utest.%s.%s.out" % (version, classifier))
    fh = codecs.open(mallet_file, "a", encoding='utf-8')
    return (train_dir, test_dir, mallet_file, results_file, all_results_file)

def _run_classifier(train_dir, test_dir, version, classifier, mallet_file, results_file):
    """Create an instance of the classifier and run it."""
    mtest = mallet.Mallet_test("utest", version , test_dir, "utrain", train_dir)
    mtest.mallet_test_classifier(classifier, mallet_file, results_file)

def _append_classifier_results(results_file, all_results_file):
    """Append the results file to test/utest.1.MaxEnt.out"""
    command = "cat %s >> %s" % (results_file, all_results_file)
    print '[--utest]', command
    subprocess.call(command, shell=True)


if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:n:',
        ['init', 'populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 'summary',
         'annotate1', 'annotate2', 'utrain', 'utest', 'scores', 'verbose'])

    init, populate = False, False
    limit = 0
    xml_to_txt, txt_to_seg, txt_to_tag, tag_to_chk = False, False, False, False
    pf_to_dfeats = False
    summary, annotate1, annotate2 = False, False, False
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
        if opt == '--annotate1': annotate1 = True
        if opt == '--annotate2': annotate2 = True
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
    elif annotate1:
        run_annotate1(target_path, language, limit)
    elif annotate2:
        run_annotate2(target_path, language, limit)
        
    # Note: At this point, user must manually create an annotated file phr_occ.lab, it is
    # expected that this file lives in ../annotation/<language>. It is automatically
    # copied to the <language>/ws subdirectory in the next step.
        
    elif union_train:
        run_utrain(target_path, language, version, xval, limit)

    elif union_test:
        run_utest(target_path, language, version, limit)

    elif tech_scores:
        # use the mallet.out file from union_test to generate a sorted list of 
        # technology terms with their probabilities
        command = "sh ./patent_tech_scores.sh %s %s %s" % (target_path, version, language)
        subprocess.call(command, shell=True)
