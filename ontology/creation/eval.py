#!/usr/bin/python26
# -*- coding: utf-8 -*-

# eval.py
# PGA 11/9/12
# Evaluation module

# test files in
# /home/j/anick/patent-classifier/ontology/annotation/en
# doc_feats.eval
# phr_occ.lab (phrases labeled y, n, "" from a general ontology)
# phr_occ.eval.unlab (unlabeled phrases corresponding to doc_feats.eval, with associated sentences for each phrase)
# phr_occ.eval.lab (labeled phrases corresponding to doc_feats.eval in the format of phr_occ.lab)


# Assume we have 
# 1. a single file with a set of lines in doc_feats format
# 2. a corresponding manually labeled file for each phrase [gold dynamic labels: Gd]
# 4. a system labeled file for each phrase with thresholds [system labels: Sd@T]
# 3. an independent file of machine labled phrases (static ontology with thresholds) [gold static labels: Gs@T]

# We measure dynamic precision/recall @threshold as

# Precision@T = intersection(#Y(Sd@T), #Y(Gd))/#Y(Sd@T)  [true positives / all system positives]
# Recall@T = intersection(#Y(Sd@T), #Y(Gd))/#Y(Gd)  [true positives / gold positives]

# We measure static precision/recall (based on static ontology) @threshold as

# Precision@T = intersection(#Y(Ss@T), #Y(Gd))/#Y(Ss@T)  [true positives / all system positives]
# Recall@T = intersection(#Y(Ss@T), #Y(Gd))/#Y(Gs)  [true positives / gold positives]

# Note that the model used should be consistent across each set  of evaluations.
# However,  we should also run metrics on different models (built on different sized document sets)
    
"""
I named the doc_feats file sample1
bash-3.2$ cd /home/j/anick/patent-classifier/ontology/annotation/en/
bash-3.2$ ls
doc_feats.eval  phr_occ.cum  phr_occ.eval.unlab  phr_occ.lab  phr_occ.uct
bash-3.2$ cp doc_feats.eval sample1

To run tests, uyou can use one of the hard-coded versions:

    eval.ten(.8)  # run english test with threshold set to .9
    eval.tcn(.8)  # run Chinese test
    eval.tde(.8)  # run German test

To get the nubers with threshold set to 0, use 0.000000000001 (to avoid cofusion with no data)

"""

import train
import mallet
import os
import collections
import codecs

####################################################################################
### Testing static classification 
### 

# precision/recall/accuracy calculation
class PRA:

    def __init__(self, d_eval, d_system, threshold, s_log):
        self.d_eval = d_eval
        self.d_system = d_system

        self.true_pos = 0
        self.system_pos = 0
        self.false_pos = 0
        self.false_neg = 0
        self.true_neg = 0
        self.correct = 0
        self.l_false_pos = []
        self.l_false_neg = []
        self.l_true_pos = []
        #self.precision = 0.0
        #self.recall = 0.0
        #self.accuracy = 0.0
        self.total = 0
        self.eval_pos = 0
        self.eval_labeled = 0
        
        i = 0
        none_count = 0
        for phrase in self.d_eval.keys():

            i += 1
            #if i < 10:
            #    print "[PRA]phrase: %s" % phrase

            self.total += 1
            gold_label = self.d_eval.get(phrase)
            """
            if i < 10:
                if self.d_system.has_key(phrase):
                    print "[PRA]Found key: %s" % phrase
                else:
                    print "[PRA]key not found: %s" % phrase
            """
            system_score = self.d_system.get(phrase)
            #if i < 10:
            #    print "[PRA]system_score: %s" % system_score
            #    print "[PRA]%s,%s,%s\n" % (phrase, gold_label, system_score) 

            # Handle the case where the gold phrase doesn't appear in the scored subset (data sample) at all.
            # Default the score to 0.0
            if system_score == None:
                system_score = 0.0
                none_count += 1

            if system_score > threshold:
                system_label = "y"
            else:
                if system_score > 0.0:
                    system_label = "n"
                else:
                    # "u" for unknown, meaning the term does not show up in the system data.
                    system_label = "u"

            if gold_label == "y" and system_label == "y":
                self.true_pos += 1
                self.correct += 1
            elif gold_label == "y" and system_label == "n":
                self.false_neg += 1
            elif gold_label == "n" and system_label == "n":
                self.correct += 1
                self.true_neg += 1
            elif gold_label == "n" and system_label == 'y':
                self.false_pos += 1

            # log the gold and system labels for each phrase
            s_log.write("%s\t|%s|\t%s\t%f\n" % (gold_label, system_label, phrase, system_score))
        print "Counts. total phrases in eval: %i, non-matches: %i" % (i, none_count) 

        
    def precision(self):
        total_pos = self.true_pos + self.false_pos
        if total_pos >0:
            res = float(self.true_pos) / (self.true_pos + self.false_pos)
            return(res)
        else:
            print "[WARNING: precision]true_pos: %i, false_pos: %i" % (self.true_pos, self.false_pos) 
            return(-1)

    def recall(self):
        res = float(self.true_pos) / (self.true_pos + self.false_neg)
        return(res)

    def accuracy(self):
        res = float(self.correct) / self.total
        return(res)

# function used to initialize the label dictionaries to the label "n"
def default_n():
    return("n")

# class to take an evaluation (gold standard) file (terms labeled with "y", "n") and the output of the mallet classifier (in the form of 
# a scores file, and populate dictionaries to hold this information, keyed by term.
class EvalData:
    
    def __init__(self, eval_file, system_file):
        
        self.d_eval_phr2label = {}   # map from evaluation phrase to class
        self.d_system_phr2score = {} # map from phrase to score (between 0.0 and 1.0)
        s_eval = codecs.open(eval_file, "r", encoding='utf-8')
        s_system = codecs.open(system_file, "r", encoding='utf-8')

        # populate dictionaries

        # gold data: manually annotated file of random phrases
        for line in s_eval:

            # if line begins with tab, it has not been labeled, since y/n should appear in col 1 before the tab.
            if line.strip() == '': continue
            if line.lstrip()[0] == '#': continue

            if line[0] != "\t":
                # also omit any header lines that don't contain a tab in column two
                if line[1] == "\t":
                    line = line.strip()
                    (label, phrase) = line.split("\t")
                    
                    # normalize segmentation by removing all spaces from Chinese words
                    #phrase = phrase.replace(' ','')
                    # NOTE how the phrase and label are printed out.  First byte(s) of phrase seems lost or misplaced
                    #print "[EvalData]storing label/phrase: %s, %s" % (label, phrase)

                    self.d_eval_phr2label[phrase] = label

        # output from mallet maxent classifier ("yes" score, averaged over multiple document instances)
        n = 0
        x = 0
        for line in s_system:

            n += 1
            #print "line %i" % n
            line = line.rstrip()
            (phrase, score, count, min, max) = line.split("\t")
            
            #if count == '1': continue
            x += 1
            # normalize segmentation by removing all spaces from Chinese words
            #phrase = phrase.replace(' ','')

            self.d_system_phr2score[phrase] = float(score)
            """
            if n < 10:
                print "[ED]phrase: %s, score: %s" % (phrase, score)
                if self.d_system_phr2score.has_key(phrase):
                    print "[ED]Found key in d_system: %s" % phrase
                else:
                    print "[ED]key not found in d_system: %s" % phrase
                if self.d_eval_phr2label.has_key(phrase):
                    print "[ED]Found key in d_eval: %s" % phrase
                else:
                    print "[ED]key not found in d_eval: %s" % phrase
                print "[EvalData]Storing sys score, phrase: %s, score: %f, actual: %f"  % (phrase, float(score), self.d_system_phr2score.get(phrase))
            """

        #print x
        
        #print system_file
        #print len(self.d_system_phr2score)
        #print self.d_system_phr2score.keys()
        #for w in [u"camera", u"data", u"database"]:
        #    print w, self.d_eval_phr2label.get(w), self.d_system_phr2score.get(w)

        #sys.exit()

        s_eval.close()
        #s_training.close()
        s_system.close()

        
# tests over the 500 doc patent databases for each language
def tcn(threshold):
    eval_dir = "/home/j/anick/patent-classifier/ontology/eval/"
    eval_dir = "../eval/"
    eval_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/annotation/cn/phr_occ.eval.lab.txt"
    #eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/cn/phr_occ.eval.lab"
    #eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/cn/phr_occ.lab"

    system_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents-20121130/cn/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500"
    log_file_name = eval_dir + "tcn_c1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)

# use the annotation data for testing rather than the evaluation data
def tcna(threshold):
    eval_dir = "/home/j/anick/patent-classifier/ontology/eval/"
    eval_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/annotation/cn/phr_occ.lab"
    #eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/cn/phr_occ.eval.lab"
    #eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/cn/phr_occ.lab"

    system_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents-20121130/cn/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500"
    log_file_name = eval_dir + "tcna_c1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)


def tde(threshold):
    eval_dir = "/home/j/anick/patent-classifier/ontology/eval/"
    eval_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/annotation/de/phr_occ.eval.lab"
    system_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents-20121130/de/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500" 
    log_file_name = eval_dir + "tde_c1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)

def ten(threshold):
    eval_dir = "/home/j/anick/patent-classifier/ontology/eval/"
    eval_dir = "../eval/"
    # data labeled for phrases chunked by the original rules, which included conjunction and "of"
    eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.lab"
    # data labeled for more restrictive chunks"
    #eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.newchunk.lab"
    #system_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/utest.1.MaxEnt.out.avg_scores.nr"
    system_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents-20121111/en/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500"

    log_file_name = eval_dir + "ten_c1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)


def t4(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.newchunk.lab"
    system_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/utest.1.MaxEnt.out.avg_scores.nr"
    log_file_name = "t4_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)


def t3(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.lab"
    system_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/utest.1.MaxEnt.out.avg_scores.nr"
    log_file_name = "t3_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)


def t2(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.lab"
    system_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents-20121111/en/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500"
    log_file_name = "t2_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)


def t1(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.lab"
    system_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/utest.9.MaxEnt.out.scores.sum.nr"
    log_file_name = "t1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)


# use ctrl-q <tab> to put real tabs in file in emacs
def t0(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/t0.phr_occ.eval.lab" 
    system_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/t0.scores.sum.nr" 
    log_file_name = "t0_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)
       
def test(eval_test_file, system_test_file, threshold, log_file_name):
    edata = EvalData(eval_test_file, system_test_file)
    # open a log file to keep gold and system labels for each phrase
    s_log = codecs.open(log_file_name, "w", 'utf-8')

    pra = PRA(edata.d_eval_phr2label, edata.d_system_phr2score, threshold, s_log)

    precision = pra.precision()
    print "precision: %.2f" % precision
    recall = pra.recall()
    print "recall: %.2f" % recall
    accuracy = pra.accuracy()
    print "accuracy: %.2f" % accuracy
    total = pra.total
    print "total: %i" % total
    print "true pos: %i" % pra.true_pos
    print "false pos: %i" % pra.false_pos
    print "false neg: %i" % pra.false_neg
    print "true neg: %i" % pra.true_neg
    print "correct: %i" % pra.correct
    print "precision: %.2f, recall: %.2f, accuracy: %.2f, threshold: %.2f, total: %i" % (precision, recall, accuracy, threshold, total)

    s_log.close()


####################################################################################
### Testing dynamic classification (incomplete)

# input:doc_feats_file = doc_feats_path/file_name
# output: mallet_file = mallet_subdir/featname + "." + version + ".mallet" = test_dir...
def eval_sample(doc_feats_path, train_dir, test_dir, file_name, featname, version):
    train.make_unlabeled_mallet_file(doc_feats_path, test_dir, file_name, featname, version)

    #Mallet_test parameters: test_file_prefix, version, test_dir, train_file_prefix, train_output_dir

    # create an instance of Mallet_test class to do the rest
    # let's do the work in the test directory for now.
    mtest = mallet.Mallet_test(file_name, version , test_dir, "utrain", train_dir)
    # creates train_path = train_output_dir/train_file_prefix.version
    # Uses path to locate .vectors file for training

    # creates test_path = test_dir/test_file_prefix.version
    # Uses path to create test_mallet_file = test_path.mallet

    # create the mallet vectors file from the mallet file

    ### Not sure if the next line is necessary
    mtest.write_test_mallet_vectors_file()

    mtest.mallet_test_classifier("MaxEnt")

def test1():
    doc_feats_path = "/home/j/anick/patent-classifier/ontology/annotation/en"
    path_en = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en"
    train_dir = os.path.join(path_en, "train")
    test_dir = os.path.join(path_en, "test")
    file_name = "sample1"
    featname = "sample1"
    version = "1"
    eval_sample(doc_feats_path, train_dir, test_dir, file_name, featname, version)

    
##########################


# MV versions of test routines

def mten_all(test_file):
    for threshold in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        print "\nTHRESHOLD =", threshold
        mten(threshold, test_file)
    
def mten(threshold, system_test_file):
    log_dir = "../evaluation/logs/"
    # data labeled for phrases chunked by the original rules, which included conjunction and "of"
    eval_test_file = "../annotation/en/phr_occ.eval.lab"
    # data labeled for more restrictive chunks"
    #system_test_file = "data/patents/filter-off/en/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000009"
    log_file_name = log_dir + "ten_c1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)

def mtcn(threshold):
    eval_dir = "../eval/"
    # data labeled for phrases chunked by the original rules, which included conjunction and "of"
    eval_test_file = "../annotation/cn/phr_occ.eval.lab.txt"
    # data labeled for more restrictive chunks"
    system_test_file = "data/patents/cn/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500"
    log_file_name = eval_dir + "tcn_c1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)

def mtde(threshold):
    eval_dir = "../eval/"
    # data labeled for phrases chunked by the original rules, which included conjunction and "of"
    eval_test_file = "../annotation/de/phr_occ.eval.lab.txt"
    # data labeled for more restrictive chunks"
    system_test_file = "data/patents/de/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500"
    log_file_name = eval_dir + "tde_c1_" + str(threshold) + ".gs.log"
    test(eval_test_file, system_test_file, threshold, log_file_name)


# NOT USED
    
def mo():
    training_file = "../annotation/en/phr_occ.lab"
    fragment_file = "../annotation/en/ontology-evaluation-20121128.lab"
    get_overlap(training_file, fragment_file)
    
def get_overlap(training_set, ontology_fragment):
    training_y = {}
    for line in codecs.open(training_set, encoding='utf-8'):
        (boolean, term) = line.rstrip().split("\t")
        if boolean == 'y':
            training_y[term] = True
    terms = 0
    terms_in_training_set = 0
    for line in codecs.open(ontology_fragment, encoding='utf-8'):
        terms += 1
        (boolean, term) = line.rstrip().split("\t")
        if boolean == 'y':
            if training_y.has_key(term):
                terms_in_training_set += 1
    print "Terms in training set: %d/%d (%.0f%%)" % (terms_in_training_set, terms,
                                                     100*(terms_in_training_set/float(terms)))



if __name__ == '__main__':

    import sys

    test_file = "data/patents/yy/en/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000009"

    if len(sys.argv) == 2:
        test_file = sys.argv[1]
        mten_all(test_file)
    else:
        threshold = float(sys.argv[1])
        test_file = sys.argv[2]
        mten(threshold, test_file)
    
