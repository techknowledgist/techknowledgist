# experiments.py

import tag2chunk
import pf2dfeats
import subprocess
import os
import putils
import train
import mallet2
import config_mallet


# experiments with mallet training and testing
# attribute pruning

# experiment uses 500 English patents.  For chunking, we set chunk_filter to False (ie.
# all chunks are included in training/testing.  )
# ts1 directory contains the files for 1980 - 1999 
# ts2 contains files from 2000 on
# This allows us to train and test on two separate sets
# It also allows us to see how well the past (pre-2000) can predict the future


ts1_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1"
ts2_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts2"
ts490_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490"


language = "en"
chunk_filter_p = False

# to create annotations which cover phrases of different lengths:
# cat  phr_occ.unlab | grep -v " " > phr_occ.unlab.0s
# cat  phr_occ.unlab | grep " " | grep -v " .* " > phr_occ.unlab.1s
# cat  phr_occ.unlab | grep " .* " >  phr_occ.unlab.2s

# experiments
# create .mallet training file
#     experiments.train_data_ts1()
# create a classifier from .mallet file 
#     experiments.train_ts1()

# create .mallet test file
# This file contains all instances in test data files, regardless of whether or not
# the term is annotated.  The test data files should be different from the training data files.
#     experiments.test_data_ts2()

# create vector file for test data
# experiments.test_vectors_ts2()

# set up the directory structure needed for both ts1 and ts2
def init_from_tag(source_path, target_path, language):
    l_year = os.listdir(source_path)
    putils.make_patent_dir(language, target_path, l_year)

def init1():
    source_path = os.path.join(ts1_path, language, "tag")
    init_from_tag(source_path, ts1_path, language)
    source_path = os.path.join(ts2_path, language, "tag")
    init_from_tag(source_path, ts2_path, language)

# create feature sets for tagged data for 1980-1999 (training) and 2000+ (test)
# train model
def features_ts1():
    
    # create chunks from tag files
    tag2chunk.patent_tag2chunk_dir(ts1_path, language, chunk_filter_p)
    pf2dfeats.patent_pf2dfeats_dir(ts1_path, language)
    # create a summary file with all training data (across all docs)
    command = "sh ./cat_phr.sh %s %s" % (ts1_path, language)
    subprocess.call(command, shell=True)
    

def features_ts2():    
    # now process the test data
    
    # create chunks from tag files
    tag2chunk.patent_tag2chunk_dir(ts2_path, language, chunk_filter_p)
    pf2dfeats.patent_pf2dfeats_dir(ts2_path, language)
    # create a summary file with all training data (across all docs)
    command = "sh ./cat_phr.sh %s %s" % (ts2_path, language)
    subprocess.call(command, shell=True)

# create features for the 490-10 split
# train model
# experiments.features_ts490()
def features_ts490():
    
    # create chunks from tag files
    tag2chunk.patent_tag2chunk_dir(ts490_path, language, chunk_filter_p)
    pf2dfeats.patent_pf2dfeats_dir(ts490_path, language)
    # create a summary file with all training data (across all docs)
    command = "sh ./cat_phr.sh %s %s" % (ts490_path, language)
    subprocess.call(command, shell=True)



# copy the annotations into each directory
#bash-3.2$ cat phr_occ.lab | egrep '^[yn]' > /home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/ws/phr_occ.lab
#bash-3.2$ cat phr_occ.lab | egrep '^[yn]' > /home/j/anick/patent-classifier/ontology/creation/data/patents/ts2/en/ws/phr_occ.lab

# **Create .mallet file in ts1/train
# versions: 1, ext, int, loc
# experiments.train_data_ts1("ext")
# experiments.test_data_ts2("ext")
def train_data_ts1(version):
    # create .mallet file
    #train.patent_utraining_data(ts1_path, language, version="1", xval=0, limit=0, classifier="MaxEnt")
    d_phr2label = train.load_phrase_labels(ts1_path, language)
    train.make_utraining_file(ts1_path, language, version, d_phr2label, limit=0)

def test_data_ts2(version):
    # create .mallet file 
    # make_utraining_test_file(patent_dir, lang, version, d_phr2label, use_all_chunks_p=True)
    # labeled data is empty for testing
    d_phr2label = train.load_phrase_labels(ts1_path, language)
    train.make_utraining_test_file(ts2_path, language, version, d_phr2label, use_all_chunks_p=True)

#---

# make the mallet file
# experiments.train_data_ts490("ext")
def train_data_ts490(version):
    # create .mallet file
    #train.patent_utraining_data(ts1_path, language, version="1", xval=0, limit=0, classifier="MaxEnt")
    d_phr2label = train.load_phrase_labels(ts490_path, language)
    train.make_utraining_file(ts490_path, language, version, d_phr2label, limit=0)

# experiments.test_data_ts10("ext")
def test_data_ts10(version):
    # create .mallet file 
    # make_utraining_test_file(patent_dir, lang, version, d_phr2label, use_all_chunks_p=True)
    # labeled data is empty for testing
    d_phr2label = train.load_phrase_labels(ts10_path, language)
    train.make_utraining_test_file(ts10_path, language, version, d_phr2label, use_all_chunks_p=True)

    

# train classifier
# experiments.mc_ts1("ext")
def mc_ts1(version):
    mallet_dir = config_mallet.mallet_dir
    train_file_prefix = "utrain"
    test_file_prefix = "utrain"
    #version = "1"
    train_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/train"
    test_dir ="/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/test"
    classifier_type = "MaxEnt"
    number_xval = 0 
    training_portion = 0

    #mallet_config = mallet2.MalletConfig(mallet_dir, train_file_prefix, test_file_prefix, version, train_dir, test_dir, classifier_type="MaxEnt", number_xval=0, training_portion=0, prune_p=True, infogain_pruning="10000", count_pruning="2")
    mallet_config = mallet2.MalletConfig(mallet_dir, train_file_prefix, test_file_prefix, version, train_dir, test_dir, classifier_type="MaxEnt", number_xval=0, training_portion=0, prune_p=False, infogain_pruning="2000", count_pruning="5")

    return(mallet_config)

# experiments.mc_ts2("ext")
def mc_ts2(version):
    mallet_dir = config_mallet.mallet_dir
    train_file_prefix = "utrain"
    test_file_prefix = "utest"
    #version = "1"
    # model and training vectors are in train_dir
    train_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts1/en/train"
    # new mallet data for testing/classification is in test_dir
    test_dir ="/home/j/anick/patent-classifier/ontology/creation/data/patents/ts2/en/test"
    classifier_type = "MaxEnt"
    number_xval = 0 
    training_portion = 0

    mallet_config = mallet2.MalletConfig(mallet_dir, train_file_prefix, test_file_prefix, version, train_dir, test_dir, classifier_type="MaxEnt", number_xval=0, training_portion=0, prune_p=False)

    return(mallet_config)


#-----
def mc_ts10(version):
    mallet_dir = config_mallet.mallet_dir
    train_file_prefix = "utrain"
    test_file_prefix = "utest"
    #version = "1"
    # model and training vectors are in train_dir
    #train_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/train"
    train_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/train"
    # new mallet data for testing/classification is in test_dir
    test_dir ="/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/test"
    classifier_type = "MaxEnt"
    number_xval = 0 
    training_portion = 0

    mallet_config = mallet2.MalletConfig(mallet_dir, train_file_prefix, test_file_prefix, version, train_dir, test_dir, classifier_type="MaxEnt", number_xval=0, training_portion=0, prune_p=False)

    return(mallet_config)

# called by train_ts490
def mc_ts490(version):
    mallet_dir = config_mallet.mallet_dir
    train_file_prefix = "utrain"
    test_file_prefix = "utest"
    #version = "1"
    # model and training vectors are in train_dir
    train_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/train"
    # new mallet data for testing/classification is in test_dir
    test_dir ="/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/test"
    classifier_type = "MaxEnt"
    number_xval = 0 
    training_portion = 0

    mallet_config = mallet2.MalletConfig(mallet_dir, train_file_prefix, test_file_prefix, version, train_dir, test_dir, classifier_type="MaxEnt", number_xval=0, training_portion=0, prune_p=False)

    return(mallet_config)




# train classifier for ts1 data
# experiments.train_ts1("ext")
def train_ts1(version):
    mallet_config = mc_ts1(version)
    mallet_training = mallet2.MalletTraining(mallet_config)
    mallet_training.mallet_train_classifier()
    print "[train1]After training classifier"
    return(mallet_config)

# prepare data to be classified
# experiments.test_vectors_ts2("ext")
def test_vectors_ts2(version):
    mallet_config = mc_ts2(version)
    mallet_classifier = mallet2.MalletClassifier(mallet_config)
    mallet_classifier.mallet_csv2vectors_test()
    return(mallet_config)

# experiments.test_ts2_class("ext")
def test_ts2_class(version):
    mallet_config = mc_ts2(version)
    #mallet_training = mallet2.MalletTraining(mallet_config)
    mallet_classifier = mallet2.MalletClassifier(mallet_config)
    #mallet_classifier.write_mallet_vectors_file()
    mallet_classifier.mallet_test_classifier()
    print "[test_ts2]After applying classifier"
    return(mallet_config)

#---
#  build & test classifier

# first we make sure the proper annotation file (named phr_occ.lab) is in ws directory:
#  cp annot.20130212.ts490.no_ts10.ac.lo.lab phr_occ.lab 

# experiments.train_ts490("ext")
# Note: this depends on the existence of a mallet file with the same version name,
# created in train_data_ts490(version).
def train_ts490(version):
    mallet_config = mc_ts490(version)
    mallet_training = mallet2.MalletTraining(mallet_config)
    mallet_training.mallet_train_classifier()
    print "[train ts490]After training classifier"
    return(mallet_config)

# experiments.test_ts10_class("ext")
def test_ts10_class(version):
    mallet_config = mc_ts10(version)
    #mallet_training = mallet2.MalletTraining(mallet_config)
    mallet_classifier = mallet2.MalletClassifier(mallet_config)
    #mallet_classifier.write_mallet_vectors_file()
    mallet_classifier.mallet_test_classifier()
    print "[test_ts10]After applying classifier"
    return(mallet_config)



#------------------------------------------------------------------------------------

# experiments on 490/10 split
ts490_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts490"
ts10_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ts10"

# create feature sets for 490/10 split with ts490 as training and ts10 as testing data
# train model
# experiments.features_ts490() 
def features_ts490():
    
    # create chunks from tag files
    tag2chunk.patent_tag2chunk_dir(ts490_path, language, chunk_filter_p)
    pf2dfeats.patent_pf2dfeats_dir(ts490_path, language)
    # create a summary file with all training data (across all docs)
    command = "sh ./cat_phr.sh %s %s" % (ts490_path, language)
    subprocess.call(command, shell=True)
    
# experiments.features_ts10()
def features_ts10():    
    # now process the test data
    
    # create chunks from tag files
    tag2chunk.patent_tag2chunk_dir(ts10_path, language, chunk_filter_p)
    pf2dfeats.patent_pf2dfeats_dir(ts10_path, language)
    # create a summary file with all training data (across all docs)
    command = "sh ./cat_phr.sh %s %s" % (ts10_path, language)
    subprocess.call(command, shell=True)


# generate scores
def gen_scores(target_path, version, language, classifier):
    command = "sh ./patent_tech_scores.sh %s %s %s %s" % (target_path, version, language, classifier)

    print "[gen_scores]command: %s" % command
    subprocess.call(command, shell=True)

def gen_scores_ts10(version):
    gen_scores(ts10_path, version, "en", "MaxEnt")


### sample run
# Create the features by running tag2chunks and pf2dfeats

#  experiments.features_ts490()
# experiments.features_ts10()

# put the correct annotation files in ws for ts490 and ts10.
# Currently annotation file must be named phr_occ.lab
# Use annot_utils.py to make sure that training annotations and evaluation annotations do not overlap

# create the .mallet file for a given version (each version filters the feature set)
# note the current difference between train and test, which is due to default locations where the files go
# This distinction should be unnecessary.
# note also that filtering of features in the mallet file is done for training but not for testing, since any
# features not in the classifier will be ignored anyway.  In theory, we could use the same mallet file to test 
# all versions of a classifier built with subsets of the same feature superset.  On the other hand, we could also
# decide to do filtering on the test mallet data as well to mirror the training data process.

# note: for these to work, the following files must exist:
# the training file should contain annotations and should be diffed with test file so that 
# no terms from the test are included in training. (use annot_utils.py functions)
# ie. start with phr_occ.unlab, merge with annotation file and remove test annotations.
# /home/j/anick/patent-classifier/ontology/creation/data/patents/ts490/en/ws/phr_occ.lab

# the test file can be a copy of the phr_occ.unlab file produced automatically.
# /home/j/anick/patent-classifier/ontology/creation/data/patents/ts10/en/ws/phr_occ.lab

# experiments.train_data_ts490("ext")
# experiments.test_data_ts10("ext")


# build and test classifier
# experiments.train_ts490("ext") 
# experiments.test_ts10_class("ext") 

# generate scores
# experiments.gen_scores_ts10("ext")

# run separate versions entirely
def run_version(version):

    train_data_ts490(version)
    test_data_ts10(version)
    # build and test classifier
    train_ts490(version) 
    test_ts10_class(version) 

    # generate scores
    gen_scores_ts10(version)

# experiments.run_version("int")
#  experiments.run_version("all")

