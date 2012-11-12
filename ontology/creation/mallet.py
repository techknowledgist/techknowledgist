# library for dealing with mallet feature production
# PGA 10/72012
#
# python 2.6 or higher required

# We assume that training data files will all be in placed in a single directory $train_dir
# file names for use with mallet are constructed using
# a user supplied file_prefix (e.g. test_data)
# a user supplied trainer (which must be a case sensitive Mallet trainer keyword (e.g. MaxEnt)
# system supplied qualifiers (such as .out, .mallet, .vectors, .vectors.out)
#
# import test_flib to test the flib methods with a small example.

# For mallet command line documentation, see
# http://www.cs.cmu.edu/afs/cs.cmu.edu/project/cmt-40/Nice/Urdu-MT/code/Tools/POS/postagger/mallet_0.4/doc/command-line-classification.html


import os
import re
import pickle
from collections import defaultdict


# mallet_dir may be different depending on machine
from config_mallet import *


############################################################################
# Mallet_instance class encapsulates data and methods to capture one line of a mallet instance input file
# Each line consists of: name, label, data
# data (features) are in the form fname=fvalue (e.g. next_pos=NN)
class Mallet_instance:

    # leave id as "" to generate numeric ids for instance names
    # or pass in an id (e.g., tlink.ds_id)
    # meta is optional string of information to be stored with the instance that will
    # not affect mallet processing (ie. for storing notes about the instance).
    def __init__(self, id, label, meta):
        self.id = str(id)
        self. label = label
        self.l_feat = []
        # meta data string used to capture info for future debugging
        # e.g., the sentence, event strings, etc.
        self.meta = meta

    # add a feature to the mallet instance.
    # Each feature is composed of a name and value
    # This way we can post-filter features by name to test different feature sets

    def add_feat(self, fname, fvalue):
        # If fvalue is not a string, we need to convert it to string
        str_value = str(fvalue)
        #feat = fname + "=" + str_value
        feat = fname + "=" + str_value
        self.l_feat.append(feat)

###################################################################
# Mallet_training class encapsulates data and methods for adding instances and running mallet.
# Note: Need to allow an instance list to be reused with a filter for ablation testing
# test sets require different parameters, maybe have a separate class?

class Mallet_training:

    def __init__(self, file_prefix, version, train_output_dir):

        self.train_output_dir = train_output_dir
        self.file_prefix = file_prefix
        # id's are 0 based
        self.next_instance_id = 0
        path_wo_version = os.path.join(train_output_dir, file_prefix)
        self.train_path_prefix = path_wo_version + "." + version

        self.train_mallet_file = self.train_path_prefix + ".mallet"
        self.train_vectors_file = ""
        self.train_vectors_out_file = ""
        self.train_out_file = ""
        self.train_meta_file = ""

        self.l_instance = []

        # table of instances indexed by predicted and actual labels
        self.d_labels2uid = defaultdict(list)
        self.d_uid2labels = {}
        
    # NOTE: The next two functions are used to build a .mallet file.  If this is built
    # externally, they can be ignored.  However, the mallet file must consist of 
    # <uid> <label> <f1> <f2> ....
    # and be named <file_prefix>.mallet

    # add an instance object to the list of instances in the Mallet_training object
    def add_instance(self, mallet_instance):
        # each mallet instance contains <id> <label> <feature>+
        # check if id is needed
        # if id parameter is "", we will default to ordered integer ids
        if mallet_instance.id == "":
            mallet_instance.id = str(self.next_instance_id)
            self.next_instance_id += 1
        self.l_instance.append(mallet_instance)

    # write out training instances file to file $file_prefix.mallet
    def write_train_mallet_file(self):

        mallet_stream = open(self.train_mallet_file, "w")
        print "writing to: %s (with feature uniqueness enforced)" %  self.train_mallet_file
        for instance in self.l_instance:
            mallet_stream.write("%s %s " % (instance.id, instance.label))
            # use (list(set(...))) to insure that each feature is only included once.
            # Some features, like prev_J, tend to occur multiple times.  Mallet will 
            # create a vector with value for the feature > 1.0 if it appears multiple times.
            # However, we are currently treating all features as binary (present/absent)
            mallet_stream.write(" ".join(list(set(instance.l_feat))))
            mallet_stream.write("\n")
        mallet_stream.close()

    # convert mallet instance file to mallet vectors format in file $file_prefix.vectors
    # This is required to run the classifier on the data.
    # command format: sh $mallet_dir/csv2vectors --input $train_dir/features.mallet --output $train_dir/features.vectors --print-output TRUE > $train_dir/features.vectors.out
    def write_train_mallet_vectors_file(self):

        self.train_vectors_file = self.train_path_prefix + ".vectors"
        self.train_vectors_out_file = self.train_vectors_file + ".out" 
        cmd = "sh " + mallet_dir + "/csv2vectors --token-regex '[^ ]+' --input " + self.train_mallet_file + " --output " + self.train_vectors_file + " --print-output TRUE > " + self.train_vectors_out_file
        print "[write_train_mallet_vectors_file]cmd: %s" % cmd
        os.system(cmd)

    # set vectors file name attribute directly (useful if testing on vectors data created elsewhere)
    # arg is full path for .vectors file
    def set_mallet_vectors_file(self, full_vectors_path):
        self.train_vectors_file = full_vectors_path
        self.train_vectors_out_file = full_vectors_path + ".out" 

    # train a mallet classifier
    # trainer is the case-sensitive name for a mallet classifier (e.g., "MaxEnt", "NaiveBayes")
    # To divide training data into a training and evaluation set, set training_portion to a value
    # between 0 and 1, (e.g., .7)
    # To do cross validation, set number_cross_val to some number >= 2 (e.g., 10)
    # To use all instances to train a classifier, leave both parameters empty (i.e., = 0)
    # Model will be in $train_path_prefix.<trainer>.model
    # Output (accuracy, confusion matrix, label predicted/actual) is in $train_path_prefix.<trainer>.out
    # Command line format: vectors2train --training-file train.vectors --trainer  MaxEnt --output-classifier foo_model --report train:accuracy train:confusion> foo.stdout 2>foo.stderr
    def mallet_train_classifier(self, trainer, number_cross_val = 0, training_portion = 0):
        print "[mallet_train_classifier] number_cross_val(string) is: %s" % number_cross_val
        print "[mallet_train_classifier] number_cross_val is: %i" % number_cross_val
        print "[mallet_train_classifier] trainer is %s" % trainer
        self.classifier_file = self.train_path_prefix + "." + trainer + ".model"
        self.classifier_out_file = self.train_path_prefix + "." + trainer + ".out"
        self.classifier_stderr_file = self.train_path_prefix + "." + trainer + ".stderr"

        # --report test:raw option provides <id> <actual> <predicted> labels, e.g.
        # 2 OUT OUT:0.6415563874015857 IN:0.3584436125984143 
        

        # using training-portion
        if training_portion > 0.0:
            print "[mallet_train_classifier]Using mallet command with portions"
            cmd = "sh " + mallet_dir + "/mallet train-classifier --input " + self.train_vectors_file + " --trainer " + trainer + " --output-classifier " + self.classifier_file + " --training-portion " + str(training_portion) + " --report test:accuracy test:confusion train:raw > " + self.classifier_out_file + " 2> " + self.classifier_stderr_file

        elif number_cross_val < 2: 
            print "[mallet_train_classifier]Using mallet command without cross validation or portions"
            cmd = "sh " + mallet_dir + "/mallet train-classifier --input " + self.train_vectors_file + " --trainer " + trainer + " --output-classifier " + self.classifier_file + " --report test:accuracy test:confusion test:raw > " + self.classifier_out_file + " 2> " + self.classifier_stderr_file

        else:
            # using cross-validation
            print "[mallet_train_classifier]Using mallet command with cross validation"
            cmd = "sh " + mallet_dir + "/mallet train-classifier --input " + self.train_vectors_file + " --trainer " + trainer + " --output-classifier " + self.classifier_file + " --cross-validation " + str(number_cross_val) + " --report test:accuracy test:confusion test:raw > " + self.classifier_out_file + " 2> " + self.classifier_stderr_file

        print "[mallet_train_classifier]cmd: %s" % cmd
        os.system(cmd)

##################
# PGA 
# class for creating a test data set using the same features as a pre-existing classifier
# Test data contains <id> <feature>+

class Mallet_test:

    def __init__(self, test_file_prefix, version, test_dir, train_file_prefix, train_output_dir):

        self.test_dir = test_dir
        self.test_file_prefix = test_file_prefix
        self.train_file_prefix = train_file_prefix
        
        # id's are 0 based
        self.next_instance_id = 0
        train_path_wo_version = os.path.join(train_output_dir, train_file_prefix)
        test_path_wo_version = os.path.join(test_dir, test_file_prefix)
        self.train_path_prefix = train_path_wo_version + "." + version
        self.train_vectors_file = self.train_path_prefix + ".vectors"
        # check on path ///
        self.test_path_prefix =  test_path_wo_version + "." + version
        self.test_mallet_file = self.test_path_prefix + ".mallet"

        #print "[mallet_test init]train_path_prefix: %s" % self.train_path_prefix
        self.test_vectors_file = ""
        self.test_vectors_out_file = ""
        self.test_out_file = ""
        self.test_meta_file = ""

        self.l_instance = []

    # skip next two functions if .mallet file is created elsewhere
    def add_instance(self, mallet_instance):
        # each mallet instance contains <id> <label> <feature>+
        # check if id is needed
        # if id parameter is "", we will default to ordered integer ids
        if mallet_instance.id == "":
            mallet_instance.id = str(self.next_instance_id)
            self.next_instance_id += 1
        self.l_instance.append(mallet_instance)

    # write out test instances file to test_dir
    def write_test_mallet_file(self):

        mallet_stream = open(self.test_mallet_file, "w")
        print "writing to: %s" %  self.test_mallet_file
        for instance in self.l_instance:
            # note the label is not included as a field in test data for mallet
            mallet_stream.write("%s %s " % (instance.id))
            # Make sure l_feat list is unique before creating the mallet output line.
            # We are treating each feature as binary(present/absent) and some features can
            # occur more than once in phr_feats file.
            mallet_stream.write(" ".join(list(set(instance.l_feat))))
            mallet_stream.write("\n")
        mallet_stream.close()

    # sh $mallet_dir/csv2vectors --input $test_dir/features.mallet --output $test_dir/features.vectors --print-output TRUE > $test_dir/features.vectors.out



    # create test vectors file compatible with training vectors file (using use-pipe-from option)
    def write_test_mallet_vectors_file(self):
        
        self.test_vectors_file = self.test_path_prefix + ".vectors"
        self.test_vectors_out_file = self.test_vectors_file + ".out"

        # sh $mallet_dir/csv2vectors --token-regex "[^ ]+" --name 1 --label 2 --data 3  --input $test_dir/$type.$version.mallet --output $test_dir/$type.$version.test.vectors --print-output TRUE --line-regex "^([^ ]+) ([^ ]+) ([^|]*)(\|.*)$" --use-pipe-from $train_dir/$type.$version.train.vectors > $test_dir/$type.$version.test.vectors.out

        # added  --token-regex "[^ ]+" to use blank as token separator
        #cmd = "sh " + mallet_dir + "/csv2vectors  --token-regex \"[^ ]+\" --line-regex \"^([^ ]+) (.+)\" --name 1 --data 2 --input " + self.test_mallet_file + " --output " + self.test_vectors_file + " --print-output TRUE --use-pipe-from " + self.train_vectors_file  + "  > " + self.test_vectors_out_file

        #cmd = "sh " + mallet_dir + "/csv2vectors --input " + self.test_mallet_file + " --output " + self.test_vectors_file + " --print-output TRUE --use-pipe-from " + self.train_vectors_file  + "  > " + self.test_vectors_out_file

        cmd = "sh " + mallet_dir + "/csv2vectors --input " + self.test_mallet_file + " --output " + self.test_vectors_file + " --print-output TRUE --use-pipe-from " + self.train_vectors_file  + "  > " + self.test_vectors_out_file
        print "[write_test_mallet_vectors_file]cmd: %s" % cmd
        os.system(cmd)

    # trainer is parameter to the method to allow for multiple classifiers over the same data
    # However, models built with the trainer must already exist in the training directory

    # Note also that training with xvalidation on will create multiple models, one per trial.
    # You need to train with no xvalidation to generate a model file name that will work with the tester here.
    
    def mallet_test_classifier(self, trainer, mallet_file=None, results_file=None):

        print "[mallet_test_classifier] trainer is %s" % trainer
        self.classifier_file = self.train_path_prefix + "." + trainer + ".model"
        self.classifier_out_file = self.test_path_prefix + "." + trainer + ".out"
        self.classifier_stderr_file = self.test_path_prefix + "." + trainer + ".stderr"
        # override defaults above with filenames handed in by the caller (MV)
        if mallet_file is not None:
            self.test_mallet_file = mallet_file
        if results_file is not None:
            self.classifier_out_file = results_file

        #sh /home/j/anick/mallet/mallet-2.0.7/bin/mallet classify-file --input $test_dir/$type.$version.features.vectors  --classifier $train_dir/$type.$version.classifier.mallet  --output -  >  $test_dir/$type.$version.res.stdout

        cmd = "sh " + mallet_dir + "/mallet classify-file --line-regex \"^(\S*)[\s,]*(\S*)[\s]*(.*)$\" --name 1 --data 3 --input " + self.test_mallet_file + " --classifier " + self.classifier_file + " --output -  > " + self.classifier_out_file + " 2> " + self.classifier_stderr_file

        cmd = "sh " + mallet_dir + "/mallet classify-file " + \
              "--line-regex \"^(\S*)[\s,]*(\S*)[\s]*(.*)$\" --name 1 --data 3 --input " + \
              self.test_mallet_file + " --classifier " + self.classifier_file + \
              " --output -  > " + self.classifier_out_file + " 2> " + self.classifier_stderr_file

        print "[mallet_test_classifier]cmd: %s" % cmd
        os.system(cmd)

        
    #def write_test_meta_file(self):

#######################################################################
# analyze mallet results different ways
class ResultInspector():

    def __init__(self, ds, name, version, trainer, train_output_dir):
        self.ds = ds
        self.name = name
        self.version = version
        self.trainer = trainer
        self.train_output_dir = train_output_dir
        
        # files
        self.train_path_prefix = train_output_dir + name + "." + version
        self.classifier_out_file = self.train_path_prefix + "." + trainer + ".out"
        self.train_mallet_file = self.train_path_prefix + ".mallet"


        # dictionaries for tlink data
        self.d_uid2features = {}
        self.d_uid2labels = {}
        self.d_labels2uid = defaultdict(list)
        # maps actual label and feature to list of so labeled tlinks containing the feature
        self.d_afeat2uid = defaultdict(list)
        
        self.load_raw_data()

    def load_raw_data(self):

        # extract the raw data section from the .out file
        in_raw_data = False

        # process the .out file for label information (output of report test:raw option)
        # NOTE: in the case of cross validation folds, this will only capture the test results of
        # all folds
        
        out_stream = open(self.classifier_out_file)
        for line in out_stream:
            if in_raw_data and re.match("^[^ ]+ [^ ]+ [^ ]+:", line):
                m = re.match("^(?P<id>[^ ]+) (?P<actual>[^ ]+) (?P<pred>[^ ]+):", line)
                uid = m.group("id")
                actual = m.group("actual")
                pred = m.group("pred")
                # index the line
                
                self.d_uid2labels[uid] = [actual, pred]
                #print "Indexed %s => [%s %s]" % (uid, actual, pred)
            else:
                # No more raw data
                in_raw_data = False
                
            if " Raw Testing Data" in line:
                in_raw_data = True

        out_stream.close()

        # now create a reverse index from label pairs to id lists
        for uid in self.d_uid2labels.keys():
            [actual, pred] = self.d_uid2labels.get(uid)
            labels_key = actual + "_" + pred
            self.d_labels2uid[labels_key].append(uid)

        # .mallet file example line: 61 AFTER c2_path__to c1_vrel__PRD c1_etype__PROBLEM c2_etype__TEST
        mallet_stream = open(self.train_mallet_file, "r")
        for line in mallet_stream:
            line = line.strip()
            line_fields = line.split(" ")
            uid = line_fields[0]
            actual = line_fields[1]
            feature_list = line_fields[2:]
            self.d_uid2features[uid] = feature_list

            # also index tlinks by actual label and feature (LABEL_feat)
            for feat in feature_list:
                key = actual + "_" + feat
                self.d_afeat2uid[key].append(uid)
                

        mallet_stream.close()

    # print a list of ids for a given label pair (for inspection of misclassified instances)
    def print_res(self, actual, pred):
        labels_key = actual + "_" + pred
        l_uid = self.d_labels2uid[labels_key]
        print "%s %s:" % (actual, pred)
        for uid in l_uid:
            print "%s" % uid
            # output more diagnostic info here
            # by linking id with actual i2b2 concept data
            
    def print_uid_res(self, uid):
        print self.d_uid2features[uid]
        print self.d_uid2labels[uid]

    # debug a feature, given actual label and feature, range within list of uids to display.
    def db_feat(self, actual, feat, start=0, end=4):
        key = actual + "_" + feat
        l_uid = self.d_afeat2uid[key][start:end]
        for uid in l_uid:
            print "\nTLINK: %s" % uid
            self.db_tlink(uid)
            
    # debug tlink with useful info on sentence, tlink, and mallet results
    def db_tlink(self, uid):
        # uid is composed of doc_id, "tl", and tlink id
        [doc_id, tlstr, tlink_id] = uid.split("_")
        [actual_label, pred_label] = self.d_uid2labels[uid] 
        print "Actual: %s. pred: %s" % (actual_label, pred_label)
        print "Features: %s" % self.d_uid2features[uid]

        # There is a bug that some keys are missing, so we include a workaround for now ///
        if self.ds.id2tlinks.has_key(uid):
            self.ds.id2docs[doc_id].display_tlink(self.ds.id2tlinks[uid])
            print "Path: %s" % self.ds.id2tlinks[uid].dep_path
        else:
            print "Missing key %s in ds.id2.tlinks" % uid
        
####################################################################
# small utility functions for creating features

def startswith_one(str, l_prefix):
    for p in l_prefix:
        #print "matching %s with %s" % (p, str)
        if str.startswith(p):
            return True
        
    return False

def verb_p(dep_node):
    if dep_node.pos == None:
        return False
    if dep_node.pos.startswith("VB"):
        return True
    else:
        return False

# if head is a verb, return the dep_node's deprel (e.g., SBJ)
def verb_rel(dep_node):
    if dep_node.pos == None:
        return False
    if verb_p(dep_node.head):
        return(dep_node.deprel)
    else:
        return None

#returns a list of lemmas for dep_nodes found in the path matching one of the
# parts of speech in pos_list.  The pos tags are matched as prefixes, such that
# VB will match all verb pos.
# verb = VB, prep = IN, conj = CC
# Path is a list of DependencyNode instances
def feat_path_contains_pos(path, pos_list):
    l_lemmas = []
    for dep_node in path:
        #print "Trying to match dep_node pos: %s, pos_list: %s" % (dep_node.pos, pos_list)
        if startswith_one(dep_node.pos, pos_list):
            #print "matched %s,  lemma is %s" % (dep_node.pos, dep_node.lemma)
            l_lemmas.append(dep_node.lemma)
    return(l_lemmas)

def tok_seq_contains_pos(seq, pos_list, append_pos_p=True):
    l_lemmas = []
    for tok in seq:
        #print "Trying to match dep_node pos: %s, pos_list: %s" % (tok.dep_node.pos, pos_list)
        if startswith_one(tok.dep_node.pos, pos_list):
            #print "matched %s,  lemma is %s" % (tok.dep_node.pos, tok.dep_node.lemma)
            lemma = tok.dep_node.lemma
            if append_pos_p:
                lemma = tok.dep_node.pos + "_" + tok.dep_node.lemma
            l_lemmas.append(lemma)
    return(l_lemmas)

# return True if string contains any part in l_parts
def string_contains(string, l_parts):
    for part in l_parts:
        if part in string:
            return(True)
    return(False)

# returns a sting version of a sequence of tokens (separated by "_")
def l_tok2string(l_tok):
    l_tok_str = []
    joined_string = ""
    for tok in l_tok:
        l_tok_str.append(tok.form)
    joined_string =  "_".join(l_tok_str)
    return(joined_string)
