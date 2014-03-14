# nbayes.py
# Perform naive Bayes classification
# 
# probability data:
# feature\tweight\tlfgc0 lfgc1 lfgc2 ...
# where a feature is of the form prev_V=manage
# weight is used as a threshold, e.g. kl-divergence
# lfgc(n) is the log of the conditional prob of a feature given a category
# We assume the number of categories is the same for all records and in a predetermined order
# e.g., a c o t (for affected, constituent, obstacle, task)

import pdb
import codecs
import sys
import math
from collections import defaultdict
#from role import tv_filepath
import role

# populate the conditional probability table
# lfcg[feature] -> [prefix, wt, [<lfgc>+]]

# input file line example (1997.fc_kl):
# prev_V=improving        a      a+ c-   275     2.514945                -0.249762837589 -1.90682879901  -4.01096295328  -2.73002910782              -4.90099344745  -10.2646354049  -8.91492178304  -8.46281913295

# d_lfgc = nbayes.populate_lfgc("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.fc_kl")
def populate_lfgc(infile):
    print "[populate_lfgc]infile: %s" % infile
    # dict of weight, log(feature given category)
    d_lfgc = {}
    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        l_fields = line.split("\t")
        feature = l_fields[0]
        prefix = feature.split("=")[0]
        # weight is the kl-divergence score for this feature
        weight = float(l_fields[4])
        # list of conditional probs for each category
        #l_lfgc_strings = l_fields[6].split(" ")
        #pdb.set_trace()
        # get the log probs for feature given category 
        l_lfgc = [float(i) for i in l_fields[6].strip().split(" ")]
        d_lfgc[feature] = [prefix, weight, l_lfgc]

    s_infile.close()
    return(d_lfgc)

# populate prior prob table
# This is an ordered list, with the same order of cats as the lfgc list
# priors = [<prior>+]
# example of line (1997.fc.cat_prob): cat freq prob
# a       28900   0.021762

# returns a list of 2 lists:
# ordered names of categories
# ordered priors for each category
# (l_cats, l_priors) = nbayes.populate_priors("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.fc.cat_prob")
def populate_priors(infile):
    l_cats = []
    l_priors = []
    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        l_fields = line.split("\t")
        cat = l_fields[0]
        l_cats.append(cat)
        prob = l_fields[2]
        l_priors.append(float(prob))

    s_infile.close()
    return([l_cats, l_priors])


# thresholds = [<threshold>+]

# populate term/feature dictionary
# restricted to certain prefixes (e.g. prev_VNP=)
# feature_prefixes = []
# d_term2feats[term] => [<feature>+]

# input file example (1997.tf):
# protected amidino group prev_V=represents       1       0.000050
# d_term2feats = nbayes.populate_terms("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.tf")
# create a dict with key = term and value = [feature, doc_frequency (for the term-feature pair)]
def populate_terms(infile):
    d_term2feats = defaultdict(list)

    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        feature = l_fields[1]
        freq = int(l_fields[2])
        d_term2feats[term].append([feature, freq])

    s_infile.close()
    return(d_term2feats)

# return a dict with key term and value its document frequency
def populate_term2freq(term2freq_file):
    d_term2freq = {}

    s_infile = codecs.open(term2freq_file, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        (term, doc_freq, corpus_freq, prob ) = line.split("\t")
        d_term2freq[term] = doc_freq

    s_infile.close()
    return(d_term2freq)

    
# create .tf.a and .tf.t by filtering out any terms not labeled as a or t in
# <year>.act.cat.w0.2

"""
def old filter_tf_file(tv_root, year, act_file):
    tf_file = tv_root + str(year) + ".tf"
    tfa_file = tf_file + ".a"
    tft_file = tf_file + ".t"

    s_tfa = codecs.open(tfa_file, "w", encoding='utf-8')
    s_tft = codecs.open(tft_file, "w", encoding='utf-8')

    d_term2cat = defaultdict(str)

    # store the category of each term labeled a and t 
    s_act_file = codecs.open(act_file, encoding='utf-8')
    for line in s_act_file:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[3]
        d_term2cat[term] = cat
        #print "term: %s, cat: %s" % (term, cat)
    s_act_file.close()

    # create subset files of .tf for the a and t terms
    s_tf_file = codecs.open(tf_file, encoding='utf-8')
    for line in s_tf_file:
        # don't bother to strip off newline
        # just grab the term
        term = line.split("\t")[0]
        cat = d_term2cat[term]
        if cat == "a":
            s_tfa.write(line)
        elif cat == "t":
            s_tft.write(line)

    s_tf_file.close()
    s_tfa.close()
    s_tft.close()
"""

def filter_tf_file(corpus_root, corpus, year, act_file_type):
    #tf_file = tv_root + str(year) + ".tf"
    tfa_subset = "a"
    tft_subset = "t"

    tf_file = role.tv_filepath(corpus_root, corpus, year, "tf", "", cat_type="")
    tfa_file = role.tv_filepath(corpus_root, corpus, year, "tf", tfa_subset, cat_type="")
    tft_file = role.tv_filepath(corpus_root, corpus, year, "tf", tft_subset, cat_type="")
    print "[filter_tf_file]Creating tfa_file: %s" % tfa_file
    print "[filter_tf_file]Creating tft_file: %s" % tft_file

    act_file = role.tv_filepath(corpus_root, corpus, year, act_file_type, "", "act")
    print "[filter_tf_file]Reading from act_file: %s" % act_file
    
    s_tfa = codecs.open(tfa_file, "w", encoding='utf-8')
    s_tft = codecs.open(tft_file, "w", encoding='utf-8')

    d_term2cat = defaultdict(str)

    # store the category of each term labeled a and t 
    s_act_file = codecs.open(act_file, encoding='utf-8')
    for line in s_act_file:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[3]
        d_term2cat[term] = cat
        #print "term: %s, cat: %s" % (term, cat)
    s_act_file.close()

    # create subset files of .tf for the a and t terms
    s_tf_file = codecs.open(tf_file, encoding='utf-8')
    for line in s_tf_file:
        # don't bother to strip off newline
        # just grab the term
        term = line.split("\t")[0]
        cat = d_term2cat[term]
        if cat == "a":
            s_tfa.write(line)
        elif cat == "t":
            s_tft.write(line)

    s_tf_file.close()
    s_tfa.close()
    s_tft.close()

# For each term in d_term2features,
# for each cat
# compute priors[cat_idx] + sum of lfgc[feature][cat_idx] for all features with wt over threshold 
# Choose category as cat with highest score.
# max_cat

# nbayes.classify(l_cats, l_priors, d_lfgc, d_term2feats, 0.7, "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.cat.0.7")
# nbayes.classify(l_cats, l_priors, d_lfgc, d_term2feats, 0.7, "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.cat.0.7")

# output is: term #diagnostic-features #term-feature-instances class doc_freq scores features
def classify(l_cats, l_priors, d_lfgc, d_term2feats, d_term2freq, min_weight, outfile):
    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    unlabeled_count = 0
    for term in d_term2feats.keys():
        #print "term: %s" % term
        # initialize small dictionary to accumulate scores per category for the term
        d_cat_scores = dict(zip(l_cats, l_priors))
        # iterate over the features for the term, accumulating the score for each 
        # category from the feature's log conditional prob.
        #pdb.set_trace()
        num_diagnostic_feats = 0
        num_doc_feature_instances = 0
        # accumulate all features into a list to create a string of feats for output
        feat_list = []
        for (feat, freq) in d_term2feats[term]:
            if d_lfgc.has_key(feat) and (d_lfgc[feat][1] > min_weight):
                #pdb.set_trace()
                num_diagnostic_feats += 1
                num_doc_feature_instances += freq
                feat_list.append(feat + "^" + str(freq))
                cat_idx = 0
                #pdb.set_trace()
                # for each category, add the score for this feature to the accumulating score
                # for the category.  The score multiplies the freq by the log(feature given category prob)
                # Example: d_lfgc["prev_V=make"]   is  [u'prev_V', 0.210119, [-0.21130909366699999, -1.6582280765999999]]
                for cat in l_cats:
                    #score = d_lfgc[feat][1] * freq
                    #print "feat: %s, weight: %f" % (feat, score)
                    if d_lfgc[feat][2][cat_idx] > 0:
                        pdb.set_trace()
                    d_cat_scores[cat] += (d_lfgc[feat][2][cat_idx]) * freq
                    cat_idx += 1
        # find the category with the highest (i.e. max cat) score
        # default the category output to "u" for unknown if there are no diagnostic features
        max_cat = "u"
        score_string = ""
        # Remember how many diagnostic features were used and number of (doc)instances of this term with a diagnostic feature
        # That is, we only count a term-feature pair once per doc.
        output_string = term + "\t" + str(num_diagnostic_feats) + "\t" + str(num_doc_feature_instances)
        if num_diagnostic_feats > 0:
            max_cat_score = -1000000000
            max_cat = ""
            #print "%s:" % (term)
            score_string = ""
            for cat in l_cats:
                score = d_cat_scores[cat]
                score_string = score_string + "\t" + str(score)
                #print "%s: %s" % (cat, score)
                if score > max_cat_score:
                    max_cat = cat
                    max_cat_score = score
        else:
            unlabeled_count += 1
        if d_term2freq.has_key(term):
            # note: we have found some cases where a term in .tf does not have a corresponding entry in d_term2freq
            # (see comments in role.py)  To prevent a key error we check that key exists first, even though all terms
            # should be keys in d_term2freq

            # get the term's document frequency
            doc_freq = str(d_term2freq[term])

            output_string = output_string + "\t" + max_cat + "\t" + doc_freq +  "\t" + score_string + "\t" + ' '.join(feat_list)
            #print "output: %s" % output_string

            # save space by not outputting the unknown lines (lines that were not categorized)
            if max_cat != "u":
                s_outfile.write("%s\n" % output_string)

    print "unlabeled terms (no category assigned): %i" % unlabeled_count

    s_outfile.close()


# NOTE:
# For running "act" classifications, use the .tf file (terms_subset = "")
# For running "pn" classification, use a subset of .tf filtered by type (subset="a" or "t")
# This way we are classifying only terms already known to be aspects or tasks

# nbayes.classify(l_cats, l_priors, d_lfgc, d_term2feats, .5)
# nbayes.run_classify("ln-us-14-health", 1997, "act", "")
# nbayes.run_classify("ln-us-14-health", 2002, "act")
# nbayes.run_classify("ln-us-14-health", 1997, "pn")
# nbayes.run_classify("ln-us-cs-500k", 1997, "act", "")
# nbayes.run_classify("ln-us-cs-500k", 1997, "pn")
# nbayes.run_classify("ln-us-cs-500k", 1997, "pn", "a")
# nbayes.run_classify("ln-us-all-600k", 1997, "act", "")  
# nbayes.run_classify("ln-us-cs-500k", 1997, "pn")
# nbayes.run_classify("ln-us-all-600k", 1997, "pn", "a")
# nbayes.run_classify("ln-us-14-health", 1997, "pn", "a")

def run_classify(corpus, year, cat_type, subset=""):

    corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    #tv_loc = "/data/tv/"
    outfile_qualifier = "cat"
    priors_qualifier = "cat_prob"
    terms_qualifier = "tf"
    term2freq_qualifier = "terms"
    lfgc_qualifier = "fc_kl"

    ################ variable parts of path
    outfile_year = str(year)
    year_cat_name = outfile_year + "." + cat_type
    #corpus = "ln-us-cs-500k"
    #corpus = "ln-us-12-chemical"
    ################

    #print "[run_classify]Output dir: %s" % tv_loc

    #path_to_terms_file = outroot + corpus + tv_loc + outfile_year + "."
    #path_to_terms_file = role.tv_filepath(corpus_root, corpus, year, "tf", subset, "")
    #path_to_file = outroot + corpus + tv_loc + year_cat_name + "."
    #priors_file = path_to_file + priors_qualifier
    priors_file = role.tv_filepath(corpus_root, corpus, year, priors_qualifier, subset, cat_type)
    #terms_file = path_to_terms_file + terms_qualifier
    terms_file = role.tv_filepath(corpus_root, corpus, year, terms_qualifier, subset, "")

    #lfgc_file = path_to_file + lfgc_qualifier
    lfgc_file = role.tv_filepath(corpus_root, corpus, year, lfgc_qualifier, subset, cat_type)

    #term2freq_file = path_to_terms_file + term2freq_qualifier
    term2freq_file = role.tv_filepath(corpus_root, corpus, year, term2freq_qualifier, "", "")
    

    # compute l_cats, l_priors, d_lfgc, d_term2feats once and use them to run several thresholds
    print "[nbayes.py]priors_file: %s" % priors_file 
    (l_cats, l_priors) = populate_priors(priors_file)

    print "[nbayes.py]lfgc_file: %s" % lfgc_file 
    d_lfgc = populate_lfgc(lfgc_file)

    print "[nbayes.py]terms_file: %s" % terms_file 
    d_term2feats = populate_terms(terms_file)

    print "[nbayes.py]term2freq_file: %s" % term2freq_file 
    d_term2freq = populate_term2freq(term2freq_file)
    
    # min_weight = .2
    #for min_weight in [.1, .2]:
    for cutoff in [ .1, .05, .0]:
        cutoff_qualifier = role.cat_cutoff_file_type(cutoff)
        #outfile = path_to_file + outfile_qualifier + ".w" + cutoff_qualifier
        outfile = role.tv_filepath(corpus_root, corpus, year, cutoff_qualifier, subset, cat_type)
        print "[nbayes.py]classifying into outfile: %s" % outfile 
        classify(l_cats, l_priors, d_lfgc, d_term2feats, d_term2freq, cutoff, outfile)


        
# nbayes.run_filter_tf_file("ln-us-all-600k", 1997, "0.1")        
# nbayes.run_filter_tf_file("ln-us-cs-500k", 1997, "0.1")        
# nbayes.run_filter_tf_file("ln-us-14-health", 1997, "0.1")        
def run_filter_tf_file(corpus, year, cutoff="0.1"):
    corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    #tv_loc = "/data/tv/"
    #tv_root = outroot + corpus + tv_loc 
    #year = str(year)
    # e.g., act file: 1997.act.cat.w0.2
    
    #act_file = tv_root + year + ".act.cat.w" + cutoff
    #act_file = role.tv_filepath(corpus_root, corpus, year, file_type, subset, cat_type=""):
    #print "[run_filter_tf_file]Creating .tf.a and .tf.t from %s" % act_file
    #filter_tf_file(tv_root, year, act_file)
    act_file_type = role.cat_cutoff_file_type(cutoff)
    filter_tf_file(corpus_root, corpus, year, act_file_type)
