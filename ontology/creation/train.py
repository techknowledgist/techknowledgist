# create a training set for fuse technology classification

# This file contains functions for training a classifier using a file of phrases annotated
# with "y" for "is a technology term", "n", and "?", not sure.
# Format of the labeled file is 
# <label><tab><phrase>
# label can be left out.
# Labeled data is used for training
# For testing/classification, the annotation file's labels can be used to limit test data to 
# instances of unlabeled chunks only or all chunks.  

# labeled data is in 
# /home/j/anick/fuse/data/patents/en/ws/phr_occ.lab
# /home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents/cn/ws

import os
import sys
import mallet
import putils
import codecs


def load_phrase_labels(patent_dir, lang):

    """Populate dictionary of labeled phrases with their labels assume label file is in
    the workspace (ws) directory We will treat the "?" as a special label which for the
    purposes of this function is equivalent to no label."""

    d_phr2label = {}
    label_file = os.path.join(patent_dir, lang, "ws", "phr_occ.lab")

    s_label_file = open(label_file)
    for line in s_label_file:
        line = line.strip("\n")
        (label, phrase) = line.split("\t")
        # store the label if the line has one and is not "?"
        if label != "" and label != "?":
            d_phr2label[phrase] = label

    s_label_file.close()
    return(d_phr2label)


def make_utraining_file_by_dir(patent_dir, lang, version, d_phr2label):

    """Create a .mallet training file using features unioned over all chunk occurrences
    within a doc."""
    
    doc_feats_dir = os.path.join(patent_dir, lang, "doc_feats")
    train_dir = os.path.join(patent_dir, lang, "train")
    train_file_prefix = "utrain." + str(version)
    train_file_name = train_file_prefix + ".mallet"
    train_file = os.path.join(train_dir, train_file_name)
    #print "[make_training_file]doc_feats_dir: %s, train_file: %s" \
    #      % (doc_feats_dir, train_file)

    s_train = open(train_file, "w")

    labeled_count = 0
    unlabeled_count = 0
    for year in os.listdir(doc_feats_dir):
        year_path = os.path.join(doc_feats_dir, year)
        for file in os.listdir(year_path):
            year_file = os.path.join(year_path, file)
            #print "year_path: %s, file: %s" % (year_path, file)
            
            s_doc_feats_input = open(year_file)
            # extract key, uid, and features
            for line in s_doc_feats_input:
                line = line.strip("\n")
                fields = line.split("\t")
                phrase = fields[0]
                uid = fields[1]
                feats = fields[2:]
                # check if the phrase has a known label
                if d_phr2label.has_key(phrase):
                    label = d_phr2label.get(phrase)
                    if label == "":
                        print "[make_training_file]Error: found phrase with null label: %s" % phrase
                        sys.exit()
                    else:
                        mallet_list = [uid, label]
                        mallet_list.extend(feats)
                        # create a whitespace separated line with format
                        # uid label f1 f2 f3 ...
                        mallet_line = " ".join(mallet_list) + "\n"
                        s_train.write(mallet_line)
                        labeled_count += 1
                else:
                    unlabeled_count += 1

            s_doc_feats_input.close()
    s_train.close()
    print "labeled instances: %i, unlabeled: %i" % (labeled_count, unlabeled_count)
    print "[make_training_file]Created training data in: %s" % train_file


def make_utraining_file(patent_dir, lang, version, d_phr2label, limit=0):

    """ Create a file with training instances for Mallet. It uses the precomputed summary
    of all doc_feats for multiple directories in <lang>/ws/doc_feats.all and is a more
    efficient version of make_utraining_file_by_dir. The limit parameter gives the maximum
    number of files from the input that should be used for the model, if it is zero, than
    all files will be taken."""

    s_train, s_doc_feats_input = _get_training_io(patent_dir, lang, version)
    labeled_count = 0
    unlabeled_count = 0
    current_fname = None
    file_count = 0

    for line in s_doc_feats_input:
        # extract key, uid, and features
        fields = line.strip("\n").split("\t")
        phrase = fields[0]
        uid = fields[1]
        if limit > 0:
            # do not do this check if no limit was given, partially so that code from
            # patent_analyzer.py does not need to be changed
            (year, fname, rest) = uid.split('|',2)
            if fname != current_fname:
                current_fname = fname
                file_count += 1
            if file_count == limit:
                break
        feats = fields[2:]
        # check if the phrase has a known label
        if d_phr2label.has_key(phrase):
            label = d_phr2label.get(phrase)
            if label == "":
                print "[make_training_file]Error: found phrase with null label: %s" % phrase
                sys.exit()
            else:
                mallet_list = [uid, label]
                mallet_list.extend(feats)
                # create a whitespace separated line with format
                # uid label f1 f2 f3 ...
                mallet_line = " ".join(mallet_list) + "\n"
                s_train.write(mallet_line)
                labeled_count += 1
        else:
            unlabeled_count += 1

    s_doc_feats_input.close()
    s_train.close()
    print "labeled instances: %i, unlabeled: %i" % (labeled_count, unlabeled_count)
    print "[make_training_file]Created training data in: %s" % s_train.name
    

def _get_training_io(patent_dir, lang, version):
    """Open an input file with document features and a mallet output file."""
    doc_feats_file = os.path.join(patent_dir, lang, "ws", "doc_feats.all")
    train_dir = os.path.join(patent_dir, lang, "train")
    train_file = os.path.join(train_dir, "utrain.%s.mallet" % str(version))
    s_doc_feats_input = codecs.open(doc_feats_file, encoding='utf-8')
    s_train = codecs.open(train_file, "w", encoding='utf-8')
    return (s_train, s_doc_feats_input)



def patent_utraining_data(patent_dir, lang, version="1", xval=0, limit=0):
    # get dictionary of annotations
    d_phr2label = load_phrase_labels(patent_dir, lang)
    # create .mallet file
    make_utraining_file(patent_dir, lang, version, d_phr2label, limit)
    # create an instance of Mallet_training class to do the rest
    # let's do the work in the train directory for now.
    train_output_dir = os.path.join(patent_dir, lang, "train")
    mtr = mallet.Mallet_training("utrain", version , train_output_dir)
    # create the mallet vectors file from the mallet file
    mtr.write_train_mallet_vectors_file()
    # make sure xval is an int (since it can be passed in by command line args)
    xval = int(xval)
    # create the model (utrain.<version>.MaxEnt.model)
    mtr.mallet_train_classifier("MaxEnt", xval)



def make_utraining_test_file(patent_dir, lang, version, d_phr2label, use_all_chunks_p=True):

    """Testing using features unioned over all chunk occurrences within a doc. We only
    include chunks which are unlabeled in our testing data file for testing if
    use_all_chunks_p is set to False.  Otherwise we include all chunk instances, whether
    they have been manually annotated or not."""

    # We include a default label ("n") for the 2nd column in the .mallet output file but
    # it will be ignored for classification.
    default_label = "n"

    # total count should equal unlabeled count if use_all_chunks_p is False
    # If True, it should be the sum of labeled and unlabeled counts
    stats = { 'labeled_count': 0, 'unlabeled_count': 0, 'total_count': 0 }

    doc_feats_dir, s_test = _get_testing_io(patent_dir, lang, version)
    for year in os.listdir(doc_feats_dir):
        year_path = os.path.join(doc_feats_dir, year)
        for file in os.listdir(year_path):
            year_file = os.path.join(year_path, file)
            add_file_to_utraining_test_file(year_file, s_test, d_phr2label, stats,
                                            use_all_chunks_p, default_label)
    s_test.close()

    print "labeled instances: %i, unlabeled: %i, total: %i" % \
          (stats['labeled_count'], stats['unlabeled_count'], stats['total_count'])
    print "[make_utraining_test_file]Created testing data in: %s" % s_test.name


def _get_testing_io(patent_dir, lang, version):
    """Return the directory with document features and a mallet output file."""
    doc_feats_dir = os.path.join(patent_dir, lang, "doc_feats")
    test_dir = os.path.join(patent_dir, lang, "test")
    test_file = os.path.join(test_dir, "utest.%s.mallet" % str(version))
    s_test = codecs.open(test_file, "w", encoding='utf-8')
    return (doc_feats_dir, s_test)


def add_file_to_utraining_test_file(fname, s_test, d_phr2label, stats,
                                    use_all_chunks_p=True, default_label='n'):

    """Add document features from fname as vectors to s_test. This was factored out from
    make_utraining_test_file() so that I could call it from batch.py (MV)."""
    
    def incr(x): stats[x] += 1
    s_doc_feats_input = codecs.open(fname, encoding='utf-8')
    for line in s_doc_feats_input:
        fields = line.strip("\n").split("\t")
        phrase = fields[0]
        uid = fields[1]
        feats = fields[2:]
        # keep count of labeled and unlabeled instances
        incr('labeled_count') if d_phr2label.has_key(phrase) else incr('unlabeled_count')
        # include the instance if all chunks are used or if it doesn't have a label.
        if use_all_chunks_p == True or not d_phr2label.has_key(phrase):
            mallet_list = [uid, default_label]
            mallet_list.extend(feats)
            # create a whitespace separated line with format "uid f1 f2 f3 ..."
            mallet_line = u" ".join(mallet_list) + u"\n"
            s_test.write(mallet_line)
            incr('total_count')
    s_doc_feats_input.close()
    


def patent_utraining_test_data(patent_dir, lang, version="1"):
    # get dictionary of annotations
    d_phr2label = load_phrase_labels(patent_dir, lang)
    # create .mallet file
    make_utraining_test_file(patent_dir, lang, version, d_phr2label)
    return
    # create an instance of Mallet_test class to do the rest
    # let's do the work in the test directory for now.
    test_output_dir = os.path.join(patent_dir, lang, "test")
    train_output_dir = os.path.join(patent_dir, lang, "train")
    mtest = mallet.Mallet_test("utest", version , test_output_dir, "utrain", train_output_dir)
    # create the mallet vectors file from the mallet file
    #mtest.write_test_mallet_vectors_file()
    mtest.mallet_test_classifier("MaxEnt")

    
# filename is without the path
# featname is an id for the type of features used (e.g. "un" for union of all features for a chunk in a doc)
# version is an id for the version, usually indicating a specific feature set used (e.g. "1")
def make_unlabeled_mallet_file(doc_feats_path, mallet_subdir, file_name, featname, version):
    # We include a default label ("n") for the 2nd column in the .mallet output file but it will be ignored for classification.
    default_label = "n"

    mallet_file_name = featname + "." + version + ".mallet"
    doc_feats_file = os.path.join(doc_feats_path, file_name)
    mallet_file = os.path.join(mallet_subdir, mallet_file_name)
    s_doc_feats_input = open(doc_feats_file)
    s_mallet_output = open(mallet_file, "w")
    # extract key, uid, and features
    count = 0
    for line in s_doc_feats_input:
        count += 1
        line = line.strip("\n")
        fields = line.split("\t")
        phrase = fields[0]
        uid = fields[1]
        feats = fields[2:]
        mallet_list = [uid, default_label]
        #mallet_list = [uid]
        mallet_list.extend(feats)
        # create a whitespace separated line with format
        # uid f1 f2 f3 ...
        mallet_line = " ".join(mallet_list) + "\n"
        s_mallet_output.write(mallet_line)

    s_doc_feats_input.close()
    s_mallet_output.close()
    print "[make_unlabeled_mallet_file]Created %s, lines: %i" % (mallet_file, count)

# create mallet classifications for each doc
# use a model in patents/<lan>/train/utrain.<version>.MaxEnt.model
# The mallet file must be created using the same mallet features (train_vectors_file version)
# as the training data.
def pipeline_utraining_test_data(root, lang, patent_dir, version="1"):
    print "[pipeline_utraining_test_data]root %s, lang %s, patent_dir %s, version |%s|" % (root, lang, patent_dir, version)
    doc_feats_path = os.path.join(root, "doc_feats")

    # location of the corresponding training vectors and model file
    train_output_dir = os.path.join(patent_dir, lang, "train")
    test_output_dir = os.path.join(root, "test")

    #make_unlabeled_mallet_file(doc_feats_path, mallet_subdir, file_name, "utest", version)
    pipeline_make_utraining_test_file(root, lang, version)
    #sys.exit()

    # create an instance of Mallet_test class to do the rest
    # let's do the work in the test directory for now.
    mtest = mallet.Mallet_test("utest", version , test_output_dir, "utrain", train_output_dir)
    # create the mallet vectors file from the mallet file
    mtest.write_test_mallet_vectors_file()
    mtest.mallet_test_classifier("MaxEnt")


def pipeline_make_utraining_test_file(root, lang, version):
    
    # We include a default label ("n") for the 2nd column in the .mallet output file but
    # it will be ignored for classification.
    default_label = "n"

    doc_feats_dir = os.path.join(root, "doc_feats")
    test_dir = os.path.join(root, "test")
    test_file_prefix = "utest." + str(version)
    test_file_name = test_file_prefix + ".mallet"
    test_file = os.path.join(test_dir, test_file_name)
    print "[pipeline_make_utraining_test_file]doc_feats_dir: %s, version: %s, test_file: %s" \
          % (doc_feats_dir, version, test_file)

    s_test = open(test_file, "w")

    for file_name in os.listdir(doc_feats_dir):
        #print "year_path: %s, file: %s" % (year_path, file)
        file = os.path.join(doc_feats_dir, file_name)
        s_doc_feats_input = open(file)
        # extract key, uid, and features
        for line in s_doc_feats_input:
            line = line.strip("\n")
            fields = line.split("\t")
            phrase = fields[0]
            uid = fields[1]
            feats = fields[2:]
            # check if the phrase has a known label
            mallet_list = [uid, default_label]
            #mallet_list = [uid]
            mallet_list.extend(feats)
            # create a whitespace separated line with format
            # uid f1 f2 f3 ...
            mallet_line = " ".join(mallet_list) + "\n"
            s_test.write(mallet_line)
        s_doc_feats_input.close()
    s_test.close()
    #print "labeled instances: %i, unlabeled: %i" % (labeled_count, unlabeled_count)
    print "[make_utraining_test_file]Created testing data in: %s" % test_file
