"""

Scripts that lets you run the trainer and classifier on specified datasets.

OPTIONS

    -l LANG     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -t PATH     --  target directory, default is data/patents
     
    --train     --  create model for classifier
    --classify  --  run classifier
    --test      --  evaluate classifier

    --version STRING  --  identifier for the model
    --xval INTEGER    --  cross-validation setting for classifier (--utrain only), default is 0
    --model STRING    --  the identifier of a model (--classify only)

    --config FILENAME           --  file with pipeline configuration
    --files FILENAME            --  contains files to process, either for training or testing
    --annotation-file FILENAME  --  specify file with labeled terms (--utrain only)
    --annotation-count INTEGER  --  number of lines to take (--utrain only)

    --verbose         --  set verbose printing to stdout
    --show-data       --  print available datasets, then exits
    --show-pipelines  --  print defined pipelines, then exits

Example for --utrain:

$ python step4_classify.py --train -t data/patents -l en --config pipeline-default.txt --filelist training-files-v1.txt --annotation-file ../annotation/en/phr_occ.lab --annotation-count 2000 --version standard --xval 0

$ python step4_classify.py --classify -t data/patents -l en --config pipeline-default.txt --filelist testing-files-v1.txt --model standard --version standard.batch1

"""

import os, sys, time, shutil, getopt, subprocess, codecs

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser
from ontology.utils.batch import GlobalConfig, DataSet, get_datasets
from ontology.utils.file import ensure_path, get_lines, create_file
from step1_initialize import DOCUMENT_PROCESSING_IO
from step2_document_processing import show_datasets, show_pipelines, find_input_dataset

import train
import mallet
import find_mallet_field_value_column
import sum_scores

from ontology.utils.batch import read_stages, update_stages, write_stages
from ontology.utils.batch import files_to_process
from ontology.utils.file import filename_generator
from ontology.utils.git import get_git_commit


# note that --scores is now folded in with classify (and perhaps test)
ALL_STAGES = ['--train', '--classify', '--test']


def run_utrain(config, file_list, annotation_file, annotation_count, version, xval):

    """Creates a MaxEnt statistical model for the classifier as well as a series of
    intermediate files and files that log the state of the system at processing time. Uses
    labeled data with features as union of all phrase instances within a doc."""

    train_dir = os.path.join(config.target_path, config.language, 'data', 't1_train')
    intitialize_utrain(config, file_list, annotation_file, annotation_count,
                       train_dir, version, xval)

    # select data sets and check whether all files are available
    file_list = os.path.join(config.config_dir, file_list)
    input_dataset1 = find_utrain_input_dataset1(config)
    input_dataset2 = find_utrain_input_dataset2(config)
    check_file_availability(input_dataset1, file_list)
    check_file_availability(input_dataset2, file_list)

    # this step is not needed for model building but can be consumed by later stages
    create_summary_files(input_dataset1, input_dataset2, file_list, train_dir, version)
    
    ## build the model using the doc features dataset
    fnames = filename_generator(input_dataset2.path, file_list)
    mallet_file = os.path.join(train_dir, "utrain-%s.mallet" % version)
    train.patent_utraining_data3(mallet_file, annotation_file, annotation_count, 
                                 fnames, version, xval)


def intitialize_utrain(config, file_list, annotation_file, annotation_count,
                       train_dir, version, xval):

    info_file_general = os.path.join(train_dir, "utrain-%s-info-general.txt" % version)
    info_file_annotation = os.path.join(train_dir, "utrain-%s-info-annotation.txt" % version)
    info_file_config = os.path.join(train_dir, "utrain-%s-info-config.txt" % version)
    info_file_filelist = os.path.join(train_dir, "utrain-%s-info-filelist.txt" % version)
    
    if os.path.exists(info_file_general):
        sys.exit("WARNING: model for setting utrain-%s already exists" % version)

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
    shutil.copyfile(os.path.join(config.config_dir, file_list), info_file_filelist)

    
def create_summary_files(input_dataset1, input_dataset2, file_list, train_dir, version, prefix='utrain'):
    """Concatenate files from the datasets that occur in file_list. For now only does the
    doc_feats and phr_feats files, not the phr_occ files."""
    
    file_generator1 = filename_generator(input_dataset1.path, file_list)
    file_generator2 = filename_generator(input_dataset2.path, file_list)
    doc_feats_file = os.path.join(train_dir, "%s-%s-features-doc_feats.txt" % (prefix, version))
    phr_feats_file = os.path.join(train_dir, "%s-%s-features-phr_feats.txt" % (prefix, version))
    fh_doc_feats = codecs.open(doc_feats_file, 'w', encoding='utf-8')
    fh_phr_feats = codecs.open(phr_feats_file, 'w', encoding='utf-8')
    for fname1 in file_generator1:
        fh_phr_feats.write(codecs.open(fname1, encoding='utf-8').read())
    for fname2 in file_generator2:
        fh_doc_feats.write(codecs.open(fname2, encoding='utf-8').read())

        
def find_utrain_input_dataset1(config):
    # TODO: unlike, step2_document_processing.find_input_dataset(), this one has the input
    # hard-coded rather than referring to DOCUMENT_PROCESSING_IO
    datasets = []
    for ds in get_datasets(config, '--utrain', 'd3_phr_feats'):
        full_config = ds.pipeline_trace
        full_config.append(ds.pipeline_head)
        # for d3_phr_feats we do not need to apply the entire pipeline, therefore matching
        # should not be on the entire pipeline either
        if full_config == config.pipeline[:-1]:
            datasets.append(ds)
    return check_result(datasets)


def find_utrain_input_dataset2(config):
    # TODO: see remark under find_utrain_input_dataset1
    datasets = []
    for ds in get_datasets(config, '--utrain', 'd4_doc_feats'):
        full_config = ds.pipeline_trace
        full_config.append(ds.pipeline_head)
        if full_config == config.pipeline:
            datasets.append(ds)
    return check_result(datasets)



def check_result(datasets):
    """Return the dataset if there is only one in the list, otherwise write a warning and
    exit."""
    if len(datasets) == 1:
        return datasets[0]
    elif len(datasets) > 1:
        print "WARNING, more than one approriate training set:"
        for ds in datasets:
            print '  ', ds
        sys.exit("Exiting...")
    elif len(datasets) == 0:
        print "WARNING: no datasets available to meet input requirements"
        sys.exit("Exiting...")


def check_file_availability(dataset, filelist):
    """Check whether all files in filelist have been processed and are available in
    dataset. If not, print a warning and exit."""
    file_generator = filename_generator(dataset.path, filelist)
    total = 0
    not_in_dataset = 0
    for fname in file_generator:
        total += 1
        if not os.path.exists(fname):
            not_in_dataset += 1
    if not_in_dataset > 0:
        sys.exit("WARNING: %d out %d files in %s have not been processed yet\n         %s" % 
                 (not_in_dataset, total, os.path.basename(filelist), dataset))

        
    
#def run_utest(target_path, language, version, limit, classifier='MaxEnt',
#              use_all_chunks_p=True):

def run_utest(config, file_list, model, version, use_all_chunks_p=True):

    """Run the classifier on n=limit documents. Batch version of the function
    train.patent_utraining_test_data(). Appends results to test/utest.1.MaxEnt.out and
    keeps intermediate results for this invocation in test/utest.1.mallet.START-END (raw
    feature vectors) and test/utest.1.MaxEnt.out.BEGIN_END, where begin and end are taken
    from ALL_STAGES.txt and the limit parameter."""

    train_dir = os.path.join(config.target_path, config.language, 'data', 't1_train')
    classify_dir = os.path.join(config.target_path, config.language, 'data', 't2_classify')
    intitialize_utest(config, file_list, classify_dir, model, version)

    # select data sets and check whether all files are available
    file_list = os.path.join(config.config_dir, file_list)
    input_dataset1 = find_utrain_input_dataset1(config)
    input_dataset2 = find_utrain_input_dataset2(config)
    check_file_availability(input_dataset1, file_list)
    check_file_availability(input_dataset2, file_list)

    # not sure whether this is needed
    create_summary_files(input_dataset1, input_dataset2, file_list, classify_dir, version, 'utest')


    # ???
    fnames = filename_generator(input_dataset2.path, file_list)
    for f in fnames: print os.path.basename(f)

    mallet_file = os.path.join(train_dir, "utrain-%s.mallet" % version)
    print mallet_file

    
    # get dictionary of annotations and keep label stats (total_count == unlabeled_count
    # if use_all_chunks_p is False, otherwisetal_count == unlabeled_count + labeled_counts
    d_phr2label = train.load_phrase_labels(target_path, language)
    stats = { 'labeled_count': 0, 'unlabeled_count': 0, 'total_count': 0 }

    #(train_dir, test_dir, mallet_file, results_file, all_results_file) = \
    #    _classifier_io(target_path, language, version, classifier, stages)
    #print "[--utest] vector file - %s" %  mallet_file
    #print "[--utest] results file - %s" %  results_file

    exit()

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
    




def intitialize_utest(config, file_list, classify_dir, model, version):

    info_file_general = os.path.join(classify_dir, "utest-%s-info-general.txt" % version)
    info_file_config = os.path.join(classify_dir, "utest-%s-info-config.txt" % version)
    info_file_filelist = os.path.join(classify_dir, "utest-%s-info-filelist.txt" % version)
    if os.path.exists(info_file_general):
        sys.exit("WARNING: already ran classifer for version %s" % version)

    with open(info_file_general, 'w') as fh:
        fh.write("version \t %s\n" % version)
        fh.write("file_list \t %s\n" % file_list)
        fh.write("model \t %s\n" % model)
        fh.write("config_file \t %s\n" % os.path.basename(config.pipeline_config_file))
        fh.write("git_commit \t %s" % get_git_commit())

    shutil.copyfile(config.pipeline_config_file, info_file_config)
    shutil.copyfile(os.path.join(config.config_dir, file_list), info_file_filelist)











    
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
    longopts = ['config=', 'filelist=', 'annotation-file=', 'annotation-count=',
                'train', 'classify', 'test',
                'version=', 'xval=', 'model=', 'eval-on-unseen-terms',
                'verbose', 'show-data', 'show-pipelines']
    try:
        return getopt.getopt(sys.argv[1:], 'l:t:n:', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))



if __name__ == '__main__':

    # default values of options
    target_path, language, stage = 'data/patents', 'en', None
    file_list = 'training-files-000000-000500.txt'
    pipeline_config = 'pipeline-default.txt'
    verbose, show_data_p, show_pipelines_p = False, False, False
    annotation_count = 9999999999999
    version, xval, = None, "0"
    model, use_all_chunks = None, True
    
    (opts, args) = read_opts()

    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        if opt == '--version': version = val
        if opt == '--xval': xval = val
        if opt == '--model': model = val
        if opt == '--filelist': file_list = val
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
    if verbose:
        config.pp()

    if show_data_p:
        show_datasets(target_path, language, config)
    elif show_pipelines_p:
        show_pipelines(target_path, language)

    elif stage == '--train':
        run_utrain(config, file_list, annotation_file, annotation_count, version, xval)
    #elif stage == '--utest':
    #    run_utest(target_path, language, version, limit, use_all_chunks_p=use_all_chunks)
    elif stage == '--classify':
        run_utest(config, file_list, model, version, use_all_chunks_p=use_all_chunks)
    elif stage == '--scores':
        run_scores(target_path, version, language, range)
