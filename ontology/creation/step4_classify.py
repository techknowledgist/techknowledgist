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

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser
from ontology.utils.batch import GlobalConfig, DataSet
from ontology.utils.file import ensure_path, get_lines, create_file
from step1_initialize import DOCUMENT_PROCESSING_IO
from step2_document_processing import show_datasets, show_pipelines, find_input_dataset

import train
import mallet
import find_mallet_field_value_column
import sum_scores

from ontology.utils.batch import read_stages, update_stages, write_stages
from ontology.utils.batch import files_to_process
from ontology.utils.git import get_git_commit


ALL_STAGES = ['--summary', '--utrain', '--utest', '--scores']


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

    
    
def run_utrain(config, file_list, annotation_file, annotation_count, version, xval):
    """Creates a mallet training file for labeled data with features as union of all
    phrase instances within a doc. Also creates a model utrain.<version>.MaxEnt.model in
    the train subdirectory. Limit is used to determine the size of the training set, as
    with run_annotate, it is not used for incrementing values in ALL_STAGES.txt. """

    train_dir = os.path.join(config.target_path, config.language, 'data', 't1_train')
    config_dir = os.path.join(config.target_path, config.language, 'config')
    train_id = "%s.%s" % (version, xval)
    info_file_general = os.path.join(train_dir, "utrain-%s-info-general.txt" % train_id)
    info_file_annotation = os.path.join(train_dir, "utrain-%s-info-annotation.txt" % train_id)
    info_file_config = os.path.join(train_dir, "utrain-%s-info-config.txt" % train_id)
    info_file_filelist = os.path.join(train_dir, "utrain-%s-info-filelist.txt" % train_id)
    
    #if os.path.exists(info_file_general):
    #    sys.exit("WARNING: model for setting utrain-%s already exists" % train_id)

    with open(info_file_general, 'w') as fh:
        fh.write("version \t %s\n" % version)
        fh.write("xval \t %s\n" % xval)
        fh.write("file_list \t %s\n" % file_list)
        fh.write("annotation_file \t %s\n" % annotation_file)
        fh.write("annotation_count \t %s\n" % annotation_count)
        fh.write("config_file \t %s\n" % os.path.basename(config.pipeline_config_file))
        fh.write("git_commit \t %s" % get_git_commit())

    with codecs.open(annotation_file) as fh1:
        with codecs.open(info_file_annotation, 'w') as fh2:
            count = 0
            for line in fh1:
                count += 1
                if count > annotation_count:
                    break
                fh2.write(line)
    
    shutil.copyfile(config.pipeline_config_file, info_file_config)
    shutil.copyfile(os.path.join(config_dir, file_list), info_file_filelist)


    ## select data set

    #should really use the function below and merge in the stuff needed
    #print find_input_dataset('--utrain', config)
    
    # Use the stage-to-data mapping to find the input name
    input_name = DOCUMENT_PROCESSING_IO['--utrain']['in']
    # Get all data sets D for input name
    dirname = os.path.join(config.target_path, config.language, 'data', input_name)
    datasets1 = [ds for ds in os.listdir(dirname) if ds.isdigit()]
    datasets2 = [DataSet(stage, input_name, config, ds) for ds in datasets1]
    for ds in datasets2:
        ds.pp()
    # Filer the datasets making sure that d.trace + d.head matches
    # config.pipeline(txt).trace

    """
    datasets3 = [ds for ds in datasets2 if ds.input_matches_global_config()]
    config.pp()
    print datasets2
    print datasets3
    # If there is one result, return it, otherwise write a warning and exit
    if len(datasets3) == 1:
        return datasets3[0]
    elif len(datasets3) > 1:
        print "WARNING, more than one approriate training set:"
        for ds in datasets3:
            print '  ', ds
        sys.exit("Exiting...")
    elif len(datasets3) == 0:
        print "WARNING: no datasets available to meet input requirements"
        sys.exit("Exiting...")
    """

    ## gather all data into summary files

    ## build the model (adjust train.patent_utraining_data2 so that it takes full
    ## pathnames)

    
    
    """
    fnames = files_to_process(target_path, language, stages, '--utrain', limit)
    annot_path = config_data.annotation_directory
    source_annot_lang_file = os.path.join(annot_path, language, 'phr_occ.lab')
    target_annot_lang_file = os.path.join(target_path, language, 'ws', 'phr_occ.lab')
    shutil.copyfile(source_annot_lang_file, target_annot_lang_file)
    #train.patent_utraining_data(target_path, language, version, xval, limit)
    train.patent_utraining_data2(target_path, language, fnames, version, xval)
    """
    
    
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



def read_opts():
    longopts = ['config=', 'files=', 'annotation-file=', 'annotation-count=', 
                'summary', 'utrain', 'utest', 'scores',
                'version=', 'xval=',
                'verbose', 'show-data', 'show-pipelines', 'eval-on-unseen-terms']
    try:
        return getopt.getopt(sys.argv[1:], 'l:t:n:', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))

        
        
if __name__ == '__main__':

    # default values of options
    target_path, language, stage = 'data/patents', 'en', None
    pipeline_config = 'pipeline-default.txt'
    verbose, show_data_p, show_pipelines_p = False, False, False
    annotation_count = 9999999999999
    version, xval = "1", "0"
    use_all_chunks = True
    
    (opts, args) = read_opts()

    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        if opt == '--version': version = val
        if opt == '--xval': xval = val
        if opt == '--files': file_list = val
        if opt == '--annotation-file': annotation_file = val
        if opt == '--annotation-count': annotation_count = int(val)
        if opt == '--verbose': verbose = True
        if opt == '--config': pipeline_config = val
        if opt == '--show-data': show_data_p = True
        if opt == '--show-pipelines': show_pipelines_p = True
        if opt in ALL_STAGES:
            stage = opt
        if opt == '--verbose': verbose = True
        if opt == '--eval-on-unseen-terms': use_all_chunks = False

        
    config = GlobalConfig(target_path, language, pipeline_config)
    config.pp()

    if show_data_p:
        show_datasets(target_path, language, config)
    elif show_pipelines_p:
        show_pipelines(target_path, language)

    elif stage == '--summary':
        run_summary(target_path, language, limit)
    elif stage == '--utrain':
        run_utrain(config, file_list, annotation_file, annotation_count, version, xval)
    elif stage == '--utest':
        run_utest(target_path, language, version, limit, use_all_chunks_p=use_all_chunks)
    elif stage == '--scores':
        run_scores(target_path, version, language, range)
