"""

Scripts that lets you run the trainer and classifier on specified datasets. It
runs in three major modes: training, classification and evaluation. These modes
are selected with the following three options:

    --train      create model for classifier
    --classify   run classifier
    --evaluate   run evaluation on test corpus
    
The are two options that are relevant for all three modes

    --corpus PATH          corpus directory, default is data/patents
    --verbose              switched on verbose mode

Note that unlike with the document processing step there is no language option,
this reflects the mostly language independent nature of this step. Of course,
the corpus itself has the lanuage in its configuration file. Also, as we will
see below, language-specific information can be handed in to the process
(annotated terms for example).

    
SHOWING INFO

There are two options that are there purely to print information about the
corpus:

    --show-data        print available datasets, then exit
    --show-pipelines   print defined pipelines, then exit

Both these options require the --corpus option but nothing else. The following
shows how to use the three main modes.

    
TRAINING

For training, you typically want to pick the best pipeline settings as it became
apparent from all previous testing and create a model for a sufficiently large
training set. Below is an example invocation:

   $ python step4_classify.py \
       --train \
       --corpus data/patents/201305-en \
       --language en \
       --pipeline pipeline-default.txt \
       --filelist files-testing.txt \
       --annotation-file ../annotation/en/technology/phr_occ.lab \
       --annotation-count 2000 \
       --model standard \
       --features extint \
       --xval 0 \
       --verbose

This creates a set of files in data/t1_train/standard in the corpus directory,
where the last part of the directory name is given by the --model option (which
basically gives a name to the model created). Additional options:

  --pipeline FILENAME - file with pipeline configuration; this is used to select
      the data set, picking out the data set created with that pipeline, the
      default is 'pipeline-default.txt'.

  --filelist FILENAME - contains files to process, that is, the elements from
      the data set used to create the model

  --annotation-file FILENAME - this specifies file with labeled terms, these
      terms are used to created positive and negative instances in the
      --filelist file

  --annotation-count INTEGER - number of lines to take from the annotation file,
      the default is to use all labeled terms

  --features FILENAME - file with features to use for the model, the name refers
      to the basename of a file in the features directory, the default is to use
      all features

  --xval INTEGER - cross-validation setting for classifier, if set to 0 (which
      is the default) then no cross-validation will be performed


CLASSIFICATION

For running the classifier, you just pick your model with the --model option,
picking out a model created by the trainer, and run it on a set of files defined
by a pipeline and a file list. Here is a typical invocation:

  $ python step4_classify.py \
      --classify \
      --corpus data/patents/201305-en \
      --pipeline pipeline-default.txt \
      --filelist files-testing.txt \
      --model standard \
      --batch standard.batch1 \
      --create-summary \
      --verbose

Other options:

  --pipeline FILENAME - file with pipeline configuration (see above)

  --filelist FILENAME - contains files to classify

  --model STRING - selects the model used for classification

  --batch STRING - name of the current batch

  --create-summary - use this to create summary files for features

You have to run the classifier many times when you have a large dataset, hence
the --batch options which allows you to number all these batches. It is a good
idea to reflect the model used this in the names. For example, if you use the
standard model and you run three batches, you should name them (using --batch)
something like standard-batch1, standard-batch2, standard-batch3 and
standard-batch4.

You should use --create-summary in case you want to do some indexing or
matching, which happens on the summary files (this may be changed later so we
never need the summaries).


EVALUATION


"""

import os, sys, shutil, getopt, subprocess, codecs

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

import train
import mallet2
import config
import find_mallet_field_value_column
import sum_scores

from ontology.utils.batch import RuntimeConfig, get_datasets, show_datasets, show_pipelines
from ontology.utils.file import filename_generator, ensure_path
from ontology.utils.git import get_git_commit

# note that the old--scores option is now folded in with --classify
ALL_MODES = ['--train', '--classify', '--evaluate']

VERBOSE = False


class TrainerClassifier(object):

    """Abstract class with some common methods for the trainer and the
    classifier."""
    
    def _find_datasets(self):
        """Select data sets and check whether all files are available."""
        self.input_dataset1 = find_input_dataset1(self.rconfig)
        self.input_dataset2 = find_input_dataset2(self.rconfig)
        check_file_availability(self.input_dataset1, self.file_list)
        check_file_availability(self.input_dataset2, self.file_list)



class Trainer(TrainerClassifier):

    """Class that takes care of all the housekeeping around a call to the train
    module. Its purpose is to create a mallet mmodel while keeping track of
    processing configurations and writing statistics."""

    def __init__(self, rconfig, file_list, features,
                 annotation_file, annotation_count, model, xval=0):
        """Store parameters and initialize file names."""
        self.rconfig = rconfig
        self.features = features
        self.file_list = os.path.join(rconfig.config_dir, file_list)
        self.annotation_file = annotation_file
        self.annotation_count = annotation_count
        self.model = model
        self.xval = xval
        self.data_dir = os.path.join(rconfig.target_path, 'data')
        self.train_dir = os.path.join(self.data_dir, 't1_train', model)
        self.info_file_general = os.path.join(self.train_dir, "train.info.general.txt")
        self.info_file_annotation = os.path.join(self.train_dir, "train.info.annotation.txt")
        self.info_file_config = os.path.join(self.train_dir, "train.info.config.txt")
        self.info_file_filelist = os.path.join(self.train_dir, "train.info.filelist.txt")
        self.info_file_features = os.path.join(self.train_dir, "train.info.features.txt")
        self.info_file_stats = os.path.join(self.train_dir, "train.info.stats.txt")
        self.doc_feats_file = os.path.join(self.train_dir, "train.features.doc_feats.txt")
        self.phr_feats_file = os.path.join(self.train_dir, "train.features.phr_feats.txt")
        self.mallet_file = os.path.join(self.train_dir, "train.mallet")

    def run(self):
        """Run the trainer by finding the input data and building a model from it. Also
        writes files with information on configuration settings, features, gold standard
        term annotations and other things required to reproduce the model."""
        if os.path.exists(self.train_dir):
            exit("WARNING: Classifier model %s already exists" % self.train_dir)
        ensure_path(self.train_dir)
        self._find_datasets()
        self._create_info_files()
        self._build_model()
        
    def _create_info_files(self):
        """Create the info files that together give a complete picture of the
        configuration of the classifier as it ran. This is partially done by copying
        external files into the local directory."""
        self._create_info_general_file()
        self._create_info_annotation_file()
        self._create_info_features_file()
        shutil.copyfile(self.rconfig.pipeline_config_file, self.info_file_config)
        shutil.copyfile(self.file_list, self.info_file_filelist)

    def _create_info_general_file(self):
        with open(self.info_file_general, 'w') as fh:
            fh.write("$ python %s\n\n" % ' '.join(sys.argv))
            fh.write("model             =  %s\n" % self.model)
            fh.write("xval              =  %s\n" % self.xval)
            fh.write("file_list         =  %s\n" % self.file_list)
            fh.write("annotation_file   =  %s\n" % self.annotation_file)
            fh.write("annotation_count  =  %s\n" % self.annotation_count)
            fh.write("config_file       =  %s\n" % \
                     os.path.basename(rconfig.pipeline_config_file))
            fh.write("features          =  %s\n" % self.features)
            fh.write("git_commit        =  %s" % get_git_commit())

    def _create_info_annotation_file(self):
        with codecs.open(self.annotation_file) as fh1:
            with codecs.open(self.info_file_annotation, 'w') as fh2:
                written = 0
                for line in fh1:
                    if line.startswith('y') or line.startswith('n'):
                        written += 1
                        if written > self.annotation_count:
                            break
                        fh2.write(line)

    def _create_info_features_file(self):
        if self.features is not None:
            if os.path.isfile(self.features):
                shutil.copyfile(self.features, self.info_file_features)
            else:
                features_file = os.path.join('features', features + '.features')
                if os.path.isfile(features_file):
                    shutil.copyfile(features_file, self.info_file_features)
                else:
                    print "[initialize_train] WARNING: no file", features_file

    def _build_model(self):
        """Build the classifier model using the doc features files."""
        fnames = filename_generator(self.input_dataset2.path, self.file_list)
        train.patent_utraining_data3(
            self.mallet_file, self.annotation_file, self.annotation_count, fnames,
            self.features, self.model, self.xval, VERBOSE, self.info_file_stats)



class Classifier(TrainerClassifier):

    def __init__(self, rconfig, file_list, model, batch,
                 classifier='MaxEnt', create_summary=False, use_all_chunks_p=True):

        """Run the classifier on the files in file_list. Uses config to find the
        input dataset. The batch variable contains a user-specified identifier
        of the run and model refers to a previously created training model."""

        self.rconfig = rconfig
        self.file_list = os.path.join(rconfig.config_dir, file_list)
        self.model = model
        self.batch = batch
        self.classifier = classifier
        self.create_summary = create_summary
        self.use_all_chunks_p = use_all_chunks_p
        
        self.data_dir = os.path.join(self.rconfig.target_path, 'data')
        self.train_dir = os.path.join(self.data_dir, 't1_train', model)
        self.classify_dir = os.path.join(self.data_dir, 't2_classify', batch)
        self.label_file = os.path.join(self.train_dir, "train.info.annotation.txt")
        self.mallet_file = os.path.join(self.classify_dir, "classify.mallet")
        self.results_file = os.path.join(self.classify_dir, "classify.%s.out" % (classifier))
        self.stderr_file = os.path.join(self.classify_dir, "classify.%s.stderr" % (classifier))
        self.info_file_general = os.path.join(self.classify_dir, "classify.info.general.txt")
        self.info_file_config = os.path.join(self.classify_dir, "classify.info.config.txt")
        self.info_file_filelist = os.path.join(self.classify_dir, "classify.info.filelist.txt")
        self.doc_feats_file = os.path.join(self.classify_dir, "classify.features.doc_feats.txt")
        self.phr_feats_file = os.path.join(self.classify_dir, "classify.features.phr_feats.txt")

        base = os.path.join(self.classify_dir, "classify.%s.out" % (classifier))
        self.classifier_output = base
        self.scores_s1 = base + ".s1.all_scores"
        self.scores_s2 = base + ".s2.y.nr"
        self.scores_s3 = base + ".s3.scores"
        self.scores_s4 = base + ".s4.scores.sum"
        self.scores_s5 = base + ".s5.scores.sum.nr"


    def run(self):
        """Run the classifier on the data set defined by the configuration."""
        self._find_datasets()
        self._create_info_files()
        self._create_summary_files()
        self._create_mallet_file()
        print "[--classify] creating results file - %s" % \
              os.path.basename(self.results_file)
        mconfig = mallet2.MalletConfig(
            config.MALLET_DIR, 'train', 'classify', self.batch,
            self.train_dir, self.classify_dir,
            # TODO: probably need to replace xval with 0
            classifier_type=self.classifier, number_xval=xval, training_portion=0,
            prune_p=False, infogain_pruning="5000", count_pruning="3")
        mtest = mallet2.MalletClassifier(mconfig)
        mtest.mallet_test_classifier()
        self._calculate_scores()


    def _create_info_files(self):
        if os.path.exists(self.info_file_general):
            sys.exit("WARNING: already ran classifer for batch %s" % self.batch)
        print "[--classify] initializing %s directory" %  self.batch
        ensure_path(self.classify_dir)
        with open(self.info_file_general, 'w') as fh:
            fh.write("$ python %s\n\n" % ' '.join(sys.argv))
            fh.write("batch        =  %s\n" % self.batch)
            fh.write("file_list    =  %s\n" % self.file_list)
            fh.write("model        =  %s\n" % self.model)
            fh.write("config_file  =  %s\n" % os.path.basename(rconfig.pipeline_config_file))
            fh.write("git_commit   =  %s" % get_git_commit())
        shutil.copyfile(self.rconfig.pipeline_config_file, self.info_file_config)
        shutil.copyfile(self.file_list, self.info_file_filelist)

    def _create_mallet_file(self):
        print "[--classify] creating vector file - %s" %  os.path.basename(self.mallet_file)
        count = 0
        d_phr2label = train.load_phrase_labels3(self.label_file)
        fh = codecs.open(self.mallet_file, "a", encoding='utf-8')
        stats = { 'labeled_count': 0, 'unlabeled_count': 0, 'total_count': 0 }
        fnames = filename_generator(self.input_dataset2.path, self.file_list)
        for doc_feats_file in fnames:
            count += 1
            if VERBOSE:
                print "[--classify] %05d %s" % (count, doc_feats_file)
            train.add_file_to_utraining_test_file(doc_feats_file, fh, d_phr2label, stats,
                                                  use_all_chunks_p=self.use_all_chunks_p)
        fh.close()
        print "[--classify]", stats


    def _create_summary_files(self):
        """Concatenate files from the datasets that occur in file_list. For now
        only does the doc_feats and phr_feats files, not the phr_occ files. This
        step is not needed for model building but can be consumed by later
        stages or be used for analysis. The default for the trainer is to not
        use it."""
        if create_summary:
            generator1 = filename_generator(self.input_dataset1.path, self.file_list)
            generator2 = filename_generator(self.input_dataset2.path, self.file_list)
            fh_doc_feats = codecs.open(self.doc_feats_file, 'w', encoding='utf-8')
            fh_phr_feats = codecs.open(self.phr_feats_file, 'w', encoding='utf-8')
            for fname1 in generator1:
                fh_phr_feats.write(codecs.open(fname1, encoding='utf-8').read())
                for fname2 in generator2:
                    fh_doc_feats.write(codecs.open(fname2, encoding='utf-8').read())


    def _calculate_scores(self):
        """Use the clasifier output files to generate a sorted list of technology terms
        with their probabilities. This is an alternative way of using the commands in
        patent_tech_scores.sh."""
        self._scores_s1_select_score_lines()
        self._scores_s2_select_scores()
        self._scores_s3_remove_tiny_scores()
        self._scores_s4_summing_scores()
        self._scores_s5_sort_scores()

    def run_score_command(self, command, message):
        if VERBOSE:
            prefix = os.path.join(self.rconfig.target_path, 
                                  'data', 't2_classify', self.batch)
            print "[--scores]", message
            print "[--scores]", command.replace(prefix + os.sep, '')
        subprocess.call(command, shell=True)

    def _scores_s1_select_score_lines(self):
        message = "select the line from the classifier output that contains the scores"
        command = "cat %s | egrep '^[0-9]' > %s" % (self.classifier_output, self.scores_s1)
        self.run_score_command(command, message)

    def _scores_s2_select_scores(self):
        if VERBOSE:
            print "[--scores] select 'y' scores and sort"
        column = find_mallet_field_value_column.find_column(self.scores_s1, 'y')
        message = "'y' score is in column %s of %s" % \
                  (column, os.path.basename(self.scores_s1))
        command = "cat %s | cut -f1,%s | sort -k2 -nr > %s" % \
                  (self.scores_s1, column, self.scores_s2)
        self.run_score_command(command,message)

    def _scores_s3_remove_tiny_scores(self):
        message = "remove tiny scores (that is, scores like 8.833699651282083E-6)"
        command = "cat %s | grep -v \"E-\" > %s" % (self.scores_s2, self.scores_s3)
        self.run_score_command(command, message)

    def _scores_s4_summing_scores(self):
        if VERBOSE:
            print "[--scores] summing scores into", os.path.basename(self.scores_s4)
        sum_scores.sum_scores(self.scores_s3, self.scores_s4)

    def _scores_s5_sort_scores(self):
        message = "sort on average scores"
        command = "cat %s | sort -k2,2 -nr -t\"\t\" > %s" % (self.scores_s4, self.scores_s5)
        self.run_score_command(command, message)


def find_input_dataset1(rconfig):
    """Find the dataset that is input for training. Unlike the code in
    step2_document_processing.find_input_dataset(), this function hard-codes the input
    data type rather than referring to DOCUMENT_PROCESSING_IO. Note that this particular
    one was only used for generating the summary files, it is currently not used as input
    to training."""
    datasets = []
    for ds in get_datasets(rconfig, '--train', 'd3_phr_feats'):
        full_config = ds.pipeline_trace
        full_config.append(ds.pipeline_head)
        # for d3_phr_feats we do not need to apply the entire pipeline, therefore matching
        # should not be on the entire pipeline either
        if full_config == rconfig.pipeline[:-1]:
            datasets.append(ds)
    return check_result(datasets)

def find_input_dataset2(rconfig):
    # TODO: see remark under find_input_dataset1
    datasets = []
    for ds in get_datasets(rconfig, '--train', 'd4_doc_feats'):
        full_config = ds.pipeline_trace
        full_config.append(ds.pipeline_head)
        if full_config == rconfig.pipeline:
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
        sys.exit("WARNING: %d/%d files in %s have not been processed yet\n         %s" %
                 (not_in_dataset, total, os.path.basename(filelist), dataset))


def read_opts():
    longopts = ['corpus=', 'language=',
                'train', 'classify', 'evaluate', 'create-summary',
                'pipeline=', 'filelist=', 'annotation-file=', 'annotation-count=',
                'batch=', 'features=', 'xval=', 'model=', 'eval-on-unseen-terms',
                'verbose', 'show-data', 'show-pipelines']
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))



if __name__ == '__main__':

    # default values of options
    target_path = config.WORKING_PATENT_PATH
    stage = None
    file_list = 'files.txt'
    pipeline_config = 'pipeline-default.txt'
    show_data_p, show_pipelines_p = False, False
    annotation_count = 9999999999999
    batch, features, xval, = None, None, "0"
    model, use_all_chunks = None, True
    create_summary = False

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': target_path = val
        if opt == '--model': model = val
        if opt == '--batch': batch = val
        if opt == '--filelist': file_list = val
        if opt == '--create-summary': create_summary = True
        if opt == '--annotation-file': annotation_file = val
        if opt == '--annotation-count': annotation_count = int(val)
        if opt == '--pipeline': pipeline_config = val
        if opt == '--features': features = val
        if opt == '--xval': xval = val
        if opt == '--show-data': show_data_p = True
        if opt == '--show-pipelines': show_pipelines_p = True
        if opt in ALL_MODES:
            mode = opt
        if opt == '--verbose': VERBOSE = True
        if opt == '--eval-on-unseen-terms': use_all_chunks = False

    # there is no language to hand in to the runtime config, will be plucked
    # from the general configuration
    rconfig = RuntimeConfig(target_path, None, pipeline_config)
    if VERBOSE:
        rconfig.pp()

    if show_data_p:
        show_datasets(rconfig, config.DATA_TYPES)
    elif show_pipelines_p:
        show_pipelines(rconfig)

    elif mode == '--train':
        Trainer(rconfig, file_list, features,
                annotation_file, annotation_count, model, xval).run()
    elif mode == '--classify':
        Classifier(rconfig, file_list, model, batch,
                   create_summary=create_summary,
                   use_all_chunks_p=use_all_chunks).run()

    elif mode == '--evaluate':
        pass
