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
"""

import train
import mallet
import os
import collections

####################################################################################
### Testing static classification 
### 




class PRA:
    def __init__(self, d_eval, d_system, threshold):
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
        
        for phrase in self.d_eval.keys():
            self.total += 1
            gold_label = self.d_eval.get(phrase)
            system_score = self.d_system.get(phrase)
            system_label = "n"
            if system_score > threshold:
                system_label = "y"

            if gold_label == "y":
                if system_label == "y":
                    self.true_pos += 1
                    self.correct += 1
                else:
                    self.false_neg += 1
            else:
                if gold_label == "n":
                    if system_label == "n":
                        self.correct += 1
                        self.true_neg += 1
                    else:
                        self.false_pos += 1

    def precision(self):
        res = float(self.true_pos) / (self.true_pos + self.false_pos)
        return(res)

    def recall(self):
        res = float(self.true_pos) / (self.true_pos + self.false_neg)
        return(res)

    def accuracy(self):
        res = float(self.correct) / self.total
        return(res)

def default_n():
    return("n")

class EvalData:
    
    def __init__(self, eval_file, system_file):
        
        self.d_eval_phr2label = collections.defaultdict(default_n)   # map from evaluation phrase to class
        #self.d_training_phr2label = collections.defaultdict(default_n)   # map from training phrase to class
        self.d_system_phr2score = collections.defaultdict(float)   # map from phrase to score (between 0.0 and 1.0)
        s_eval = open(eval_file)
        #s_training = open(training_file)
        s_system = open(system_file)
        
        # populate dictionaries

        # manually annotated file of random phrases
        for line in s_eval:
            # if line begins with tab, it has not been labeled
            if line[0] != "\t":
                line = line.strip("\n")
                (label, phrase) = line.split("\t")
                self.d_eval_phr2label[phrase] = label

        """
        # manually annotated file used for training a mallet maxent classifier
        for line in s_training:
            # if line begins with tab, it has not been labeled
            if line[0] != "\t":
                line = line.strip("\n")
                (label, phrase) = line.split("\t")
                self.d_gold_phr2label[phrase] = label
        """

        # output from mallet maxent classifier ("yes" score, averaged over multiple document instances)
        n = 0
        for line in s_system:
            n += 1
            #print "line %i" % n
            line = line.strip("\n")
            (phrase, score, count, min, max) = line.split("\t")
            self.d_system_phr2score[phrase] = float(score)

        s_eval.close()
        #s_training.close()
        s_system.close()

def t2(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.lab"
    system_test_file = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents-20121111/en/test/utest.1.MaxEnt.out.s5.scores.sum.nr.000000-000500"
    test(eval_test_file, system_test_file, threshold)


def t1(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/annotation/en/phr_occ.eval.lab"
    system_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/utest.9.MaxEnt.out.scores.sum.nr"
    test(eval_test_file, system_test_file, threshold)

# use ctrl-q <tab> to put real tabs in file in emacs
def t0(threshold):
    eval_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/t0.phr_occ.eval.lab" 
    system_test_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/test/t0.scores.sum.nr" 
    test(eval_test_file, system_test_file, threshold)
       
def test(eval_test_file, system_test_file, threshold):
    edata = EvalData(eval_test_file, system_test_file)
    pra = PRA(edata.d_eval_phr2label, edata.d_system_phr2score, threshold)
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
