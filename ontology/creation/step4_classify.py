"""

OPTIONS

    -l LANG      --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -t PATH      --  target directory, default is data/patents
    -n INTEGER   --  number of documents to process
    -r STRING    --  range of documents to take, that is, the postfix of classifier output
     
    --summary    --  create summary lists
    --annotate1  --  prepare files for annotation of the prior
    --annotate2  --  prepare files for annotation for evaluation
    --utrain     --  create model for classifier
    --utest      --  run classifier
    --scores     --  generate scores from classifier results

    All the above long options require a target path and a language (via the -l and -t
    options or their defaults). The long options --init and --populate also require a
    source path (via -s or its default). The -n option is ignored if --init is used.

    --verbose   --  print name of each processed file to stdout

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
import find_mallet_field_value_column
import sum_scores

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


def run_summary(target_path, language, limit):
    """Collect data from directories into workspace area: ws/doc_feats.all,
    ws/phr_feats.all and ws/phr_occ.all. All downstream processing should rely on these
    data and nothing else."""
    print "[--summary] appending to files in ws"
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

    
    
def run_utrain(target_path, language, version, xval, limit):
    """Creates a mallet training file for labeled data with features as union of all
    phrase instances within a doc. Also creates a model utrain.<version>.MaxEnt.model in
    the train subdirectory. Limit is used to determine the size of the training set, as
    with run_annotate, it is not used for incrementing values in ALL_STAGES.txt. """

    stages = read_stages(target_path, language)
    fnames = files_to_process(target_path, language, stages, '--utrain', limit)
    annot_path = config_data.annotation_directory
    source_annot_lang_file = os.path.join(annot_path, language, 'phr_occ.lab')
    target_annot_lang_file = os.path.join(target_path, language, 'ws', 'phr_occ.lab')
    shutil.copyfile(source_annot_lang_file, target_annot_lang_file)
    #train.patent_utraining_data(target_path, language, version, xval, limit)
    train.patent_utraining_data2(target_path, language, fnames, version, xval)
    update_stages(target_path, language, '--utrain', limit)

    
def run_utest(target_path, language, version, limit, classifier='MaxEnt',
              use_all_chunks_p=True):

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
        train.add_file_to_utraining_test_file(doc_feats_file, fh, d_phr2label, stats,
                                              use_all_chunks_p=use_all_chunks_p)
    fh.close()
    
    _run_classifier(train_dir, test_dir, version, classifier, mallet_file, results_file)
    #_append_classifier_results(results_file, all_results_file)
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


def run_scores(target_path, version, language, range, classifier='MaxEnt'):
    
    """Use the clasifier output files from --utest to generate a sorted list of technology
    terms with their probabilities. This is an alternative way of using the commands in
    patent_tech_scores.sh."""

    def run_command(command):
        print "[--scores]", command.replace('data/patents/en/test/','')
        subprocess.call(command, shell=True)

    dir = os.path.join(target_path, language, 'test')
    base = os.path.join(dir, "utest.%s.%s.out" % (version, classifier))
    fin = base + ".%s" % range
    fout1 = base + ".s1.all_scores.%s" % range
    fout2 = base + ".s2.y.nr.%s" % range
    fout3 = base + ".s3.scores.%s" % range
    fout4 = base + ".s4.scores.sum.%s" % range
    fout5 = base + ".s5.scores.sum.nr.%s" % range
    
    print "[--scores] select the line from the classifier output that contains the scores"
    command = "cat %s | egrep '^[0-9]' > %s" % (fin, fout1)
    run_command(command)

    print "[--scores] select 'y' scores and sort"
    column = find_mallet_field_value_column.find_column(fout1, 'y')
    print "[--scores] 'y' score is in column %s of %s" % (column, os.path.basename(fout1))
    command = "cat %s | cut -f1,%s | sort -k2 -nr > %s" % (fout1, column, fout2)
    run_command(command)

    print "[--scores] remove tiny scores (that is, scores like 8.833699651282083E-6)"
    command = "cat %s | grep -v \"E-\" > %s" % (fout2, fout3)
    run_command(command)

    print "[--scores] summing scores into", fout4
    sum_scores.sum_scores(fout3, fout4)

    print "[--scores] sort on average scores"
    command = "cat %s | sort -k2,2 -nr -t\"\t\" > %s" % (fout4, fout5)
    run_command(command)
    

if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:n:r:',
        ['summary', 'annotate1', 'annotate2', 'utrain', 'utest', 'scores',
         'verbose', 'eval-on-unseen-terms'])

    use_all_chunks = True
    summary, annotate1, annotate2 = False, False, False
    union_train, union_test, tech_scores = False, False, False
    limit, range = 0, None
    version, xval = "1", "0"

    # default values of options
    language = 'en'
    target_path = 'data/patents'
    pipeline_config = 'pipeline-default.txt'
    verbose = False
    limit = 1
    stage = None
    
    for opt, val in opts:

        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        if opt == '-r': range = val
        
        if opt == '--summary': summary = True
        if opt == '--annotate1': annotate1 = True
        if opt == '--annotate2': annotate2 = True
        if opt == '--utrain': union_train = True
        if opt == '--utest': union_test = True
        if opt == '--scores': tech_scores = True

        if opt == '--verbose': verbose = True
        if opt == '--eval-on-unseen-terms': use_all_chunks = False

        
    config = GlobalConfig(target_path, language, pipeline_config)
        
    if summary:
        run_summary(target_path, language, limit)
    elif union_train:
        run_utrain(target_path, language, version, xval, limit)
    elif union_test:
        run_utest(target_path, language, version, limit, use_all_chunks_p=use_all_chunks)
    elif tech_scores:
        run_scores(target_path, version, language, range)
