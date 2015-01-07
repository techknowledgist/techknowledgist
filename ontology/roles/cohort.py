# cohort.py

# functions based on a cohort of terms which
# appear for the first time in a given year
# show evidence of growth over time.
# We use these to determine features which might be used to 
# identify promising terms automatically.

import pdb
import sys
import collections
import os
import glob
import codecs
import roles_config
import pnames

# location of data files
corpus_root = roles_config.CORPUS_ROOT

# input:
# <cohort_year>.cohort.filt.gold: gold growth terms
# <prob_year>.tf: terms and prob(f|t)
# <feature_year>.feats.1000:  1000 top features for the domain (in feature_year)
# output:
# <cohort_year>.cohort.<year_offset>.probs: year_offset is the # years since the cohort_year
# feature average_gold_term_prob(f|t) average_prob(f|t) diff

# feature_year is an arbitrary year chosen to extract the top features for the domain, which
# will then be assumed to be the same for every year.
feature_year = 2002

# cohort.feat_probs("ln-us-A28-mechanical-engineering", 1998, 2002, 2002)

# years should be passed in as integers (unquoted)
def feat_probs(corpus, cohort_year, prob_year, feature_year):
    # create file names
    cohort_file = pnames.tv_filepath(corpus_root, corpus, cohort_year, "cohort.filt.gold", "", "")
    tf_file = pnames.tv_filepath(corpus_root, corpus, prob_year, "tf", "", "")
    feats_file = pnames.tv_filepath(corpus_root, corpus, feature_year, "feats.1000", "", "")
    
    year_offset = prob_year - cohort_year
    offset_probs_str = str(year_offset) + ".probs"
    fgt_file = pnames.tv_filepath(corpus_root, corpus, cohort_year, offset_probs_str, "", "")
    print "[cohort.py feat_probs]]Writing to: %s" % fgt_file 

    s_cohort_file = codecs.open(cohort_file, encoding='utf-8')
    s_tf_file = codecs.open(tf_file, encoding='utf-8')
    s_feats_file = codecs.open(feats_file, encoding='utf-8')
    s_fgt_file = codecs.open(fgt_file, "w", encoding='utf-8')

    #dictionaries
    # sum of probs for feature given cohort term
    d_feat2sum_prob_fgct = collections.defaultdict(int)
    # sum of probs for feature given any term
    d_feat2sum_prob_fgt = collections.defaultdict(int)

    # count of number terms contributing to the sum of probs, so
    # that we can divide by the count to calculate the average.
    d_feat2_count_fgct = collections.defaultdict(int)
    d_feat2_count_fgt = collections.defaultdict(int)

    # Boolean dictionaries to keep track of sets of items
    # features of interest
    d_feats = {}
    # terms in gold cohort
    d_cohort = {}

    # terms in corpus
    d_all_terms = {}

    # import features
    for line in s_feats_file:
        line = line.strip()
        l_fields = line.split("\t")
        feat = l_fields[0]
        d_feats[feat] = True

    # import gold_cohort
    for line in s_cohort_file:
        line = line.strip()
        # first line is info about the thresholds for the cohort growth
        if line[0] != "#":
            l_fields = line.split("\t")
            term = l_fields[0]
            d_cohort[term] = True

    #pdb.set_trace()

    # import f|t probs
    for line in s_tf_file:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        feat = l_fields[1]

        # keep track of all terms seen to count them later
        d_all_terms[term] = True

        if d_feats.has_key(feat):
            # if this is a feature we are interested in
            prob = float(l_fields[4])
            # add its prob to the total for this feature,
            # given any term
            d_feat2sum_prob_fgt[feat] = prob + d_feat2sum_prob_fgt[feat]
            #d_feat2_count_fgt[feat] += 1

            # if the term is a cohort term, also add the prob
            # to the total for feature given cohort term
            if d_cohort.has_key(term):
                d_feat2sum_prob_fgct[feat] = prob + d_feat2sum_prob_fgct[feat]
                #d_feat2_count_fgct[feat] += 1


    #pdb.set_trace()
    # output probs
    count_all_terms = len(d_all_terms.keys())
    count_gold_terms = len(d_cohort.keys())

    print "[cohort.py] total terms in corpus: %i, in gold set: %i" % (count_all_terms, count_gold_terms)
    for feat in d_feats.keys():
        average_prob_fgt = float(d_feat2sum_prob_fgt[feat]) / count_all_terms
        average_prob_fgct = float(d_feat2sum_prob_fgct[feat]) / count_gold_terms

        diff = average_prob_fgct - average_prob_fgt
        ratio = average_prob_fgct / average_prob_fgt
        s_fgt_file.write("%s\t%f\t%f\t%f\t%f\n" % (feat, average_prob_fgct, average_prob_fgt, diff, ratio))

    s_cohort_file.close()
    s_tf_file.close()
    s_feats_file.close()
    s_fgt_file.close()


    
