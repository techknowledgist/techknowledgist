# role.py
# rewrite of term_verb_count focusing on role detection rather than mutual information

# directory structure
# /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/act
# <root>/<corpus>/data/tv
#   <year>.tf, terms, feats
#   <year>.<act|pn>.tfc, tc, tcs, fc, fc_uc, fc_prob, fc_cat_prob, fc_kl, 
#   <year>.<act|pn>.cat.w<cutoff>.a, c, t, p, n

# TODO: add codecs to all writes
# move corpus_root and code_root to a configuration parameter

code_root = "/home/j/anick/patent-classifier/ontology/roles"
corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents"

"""
Enclosed is documententation for preparing files to run role/polarity NB

Summary: The goal is to label NP's within a patent domain/year with one of the high level 
"ACT" roles: attribute, component, task.  Then to label the attributes with their polarity
(positive or negative).  Input is two generic feature seed sets and the feature data from
our chunker for the domain/year.
  
The generic feature seed set is used to generate a set of labeled NP's in each new domain. 
By default, we choose as training terms any NP's which occur with at least 2 labeled feature
occurrences and for which all labels are the same.

The resulting terms are then used to estimate parameters for NB classifier.  We could also
try using them as a maxent training set, perhaps using the terms which contain a mix of feature
types as "other".

Open issues:
As of 7/9/2014 PGA
1. For polarity, we need a way to distinguish neutral attributes
2. It would be useful to normalize attributes syntactically, so that attributes with a 
slot filler ("speed of the cpu") could be recognized as the same as NN compounds ("cpu speed").
Currently we lose the filler in the first case.  However, we may not currently keep enough 
info in the feature file to do this (as we only keep the head noun of phrases in a dependency
relationship).
3. Need to test on more domains
4. Need a larger evaluation, containing more examples of A and T, in order to compare alternative
variants, such as more/less restrictive cutoffs for the classifier categories.  e.g. if scores
are very close, is it better to count polarity as neutral or to assume ambiguity between T and C?

Seed features are in code_dir as
seed.act.en.dat : ACT seed features
seed.pn.en.dat : Polarity seed features

########
function tf2tfc(corpus_root, corpus, year, fcat_file, cat_list, cat_type, subset):
cat_type: act, pn
fcat_file: no longer used
cat_list [a, c, t] or [p, n]
subset "a" (for attribute in polarity classification or "" for none, in ACT classification)

Input: .tf term + feature cooccurrences for a domain and year

output
<cat_type>.tfc: term feature category count
<cat_type>.tc: term category term_category_pair_frequency term_frequency probability

########
function tc2tcs(corpus_root, corpus, year, min_prob, min_pair_freq, cat_type, subset)
min_prob : minimum class probability to select term as a seed for the class 
1.0 means all features for this term are of the same class
min_pair_freq : minimum frequency of co-occurrence of term + feature
(e.g. 2.  There must be 2 occurrences of the term and feature to use this feature as a diagnostic) 
cat_type : act or pn
subset : a or ""

Input: .tc
Output: 
<cat_type>.tcs : term category term_category_pair_count prob   - these are seed terms for Naive Bayes training

#########
function: tcs2fc(corpus_root, corpus, year, cat_type, subset)
Input: .tcs, .tf
Output:
<cat_type>.fc : feature category
This contains one line for each occurrence of a feature with a term categorized in the seed term file (.tcs) 
Thus the same feature can occur multiple times, possibly with different categories.

########
script: run_fc2fcuc.sh corpus_root corpus start_year end_year cat_type subset
Input: .fc
Output: .fc_uc   feature category count
The same feature may appear with multiple categories

#########
function: fcuc2fcprob(corpus_root, corpus, year, cat_list, cat_type, subset)
Input: .fc_uc, .tcs
Output: 
.fc_prob category term_cat_frequency cat_prob
.cat_prob feature category feature_category_pair_frequency feature_freq category_given_feature feature_given_category
.fc_kl feature, max_letter,  max_cat, next_cat, feature_freq, kld, lcgf_prob_string, lfgc_prob_string
where max_letter is the highest scoring category, max_cat, next_cat are the direction of the divergence for the most divergent categories (written as <cat><+|->

By sorting on divergence(kld), we can see the effect of features compared to expected values of the prob distribution.

At this point we have all the files we need to run naive bayes (functions in nbayes.py)

"""

import pdb
import re
import glob
import os
import sys
#import log
import math
import collections
from collections import defaultdict
import codecs
import utils
import pnames
import pickle

# pattern can contain alpha or blank, must be length >=2
re_alpha_phrase = re.compile('^[a-z ]{2,}$')

def alpha_phrase_p(term):
    mat = bool(re_alpha_phrase.search(term))
    return(mat)

# Given a set of terms, return a set of all pairs of terms, in which each pair is
# in alphabetical order. 
def set2pairs_alpha(term_set):
    l_pairs = []
    l_sorted_terms = sorted(term_set)
    while len(l_sorted_terms) > 1:
        term1 = l_sorted_terms.pop(0)
        for term2 in l_sorted_terms:
            l_pairs.append(term1 + "|" + term2)
    return(l_pairs)

# filename creator, based on naming conventions
"""
/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv
1997.act.cat.w0.2 => 1997.act.cat.w0.2
1997.act.cat.w0.3
1997.act.fc => 1997.f.act.fc
1997.act.fc.cat_prob => 1997.a.act.cat_prob
1997.act.fc.kl => 1997.a.act.fc_kl
1997.act.fc.prob => 1997.a.act.fc_prob
1997.act.fc.uc => 1997.a.act.fc_uc
1997.act.tc => 1997.a.act.tc
1997.act.tcs
1997.act.tfc
1997.feats => 1997.feats
1997.terms => 1997.terms
1997.tf = > 1997.tf
1997.tf.a => 1997.a.tf
1997.tf.t => 1997.t.tf
---
1997.act.fc => 1997.a.pn.fc  
"""

# for creating a cat file_type based on a given cutoff value (e.g. "0.1")
def cat_cutoff_file_type(cutoff):
    file_type = "cat.w" + str(cutoff)
    return file_type

# K-L Divergence of two probability distributions, passed
# in as lists of probabilities.
# plist1 and plist2 must be the same length.
# plist2 should never contain a 0 probability
# plist2 is the unconditional prob for each category, as stored in
# 1997.fc.cat_prob.
# plist1 can contain a 0
def kl_div(plist1, plist2):
    #pdb.set_trace()
    div = 0
    i = 0
    while i < len(plist1):
        if plist1[i] == 0:
            div = div + 0
        else:
            # math.log with one argument computes the natural log
            div = div + (math.log(plist1[i]/plist2[i])) * plist1[i]
        i += 1
    return(div)

def test_kl():
    # totals in 1997
    p2 = [0.020546, 0.885152, 0.020934, 0.073368]
    # "comprises" in 1997
    p_comprises = [0.000908, 0.988193, 0.000454, 0.010445]
    p_having = [0.035375, 0.906816, 0.024590, 0.033218]
    p_c = [0, 1, 0, 0]
    p_a = [1, 0, 0, 0]
    p_o = [0, 0, 1, 0]
    p_t = [0, 0, 0, 1]

    print "comprises: %f" % kl_div(p_comprises, p2)
    print "having: %f" % kl_div(p_having, p2)
    print "a,c,o,t: %f, %f, %f, %f" % (kl_div(p_a, p2), kl_div(p_c, p2), kl_div(p_o, p2), kl_div(p_t, p2))

# The list of files is taken 
# to be all the files in a given directory.
# Each line in a file contains a term, a verb, and a count.
# creates pair_counts (document frequency of each pair), mi in outroot/year
# We assume inroot/year and outroot have been checked to exist at this point
# outfilename will the be value of the year


# convert term feature (.tf) info to term category info (.tc)
# also create .tfc (term, feature, cat)
def tf2tfc(corpus_root, corpus, year, fcat_file, cat_list, cat_type, subset):
    yearfilename = str(year) 
    year_cat_name = yearfilename + "." + cat_type
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    d_term_freq = collections.defaultdict(int)
    d_feature_freq = collections.defaultdict(int)
    
    d_feature2cat = {}
    # the tc means "term-category" 
    #infile = inroot + "/" + yearfilename + ".tf"
    # note there is no cat_type in the file name for .tf file, so use ""
    infile = pnames.tv_filepath(corpus_root, corpus, year, "tf" , subset, "")
    """
    if subset != "":
        infile = infile + "." + subset
    """

    #tc_file = outroot + "/" + year_cat_name + ".tc"
    tc_file = pnames.tv_filepath(corpus_root, corpus, year, "tc" , subset, cat_type)
    #tfc_file = outroot + "/" + year_cat_name + ".tfc"
    tfc_file = pnames.tv_filepath(corpus_root, corpus, year, "tfc" , subset, cat_type)

    # load the feature categories for fcat_file
    s_fcat_file = open(fcat_file)
    for line in s_fcat_file:
        line = line.strip()
        #print "line: %s\n" % line
        (fcat, feature) = line.split("\t")
        # ignore categories that are not in cat_list
        if fcat in cat_list:
            d_feature2cat[feature] = fcat

    s_fcat_file.close()

    s_infile = codecs.open(infile, encoding='utf-8')
    s_tfc_file = codecs.open(tfc_file, "w", encoding='utf-8')

    for line in s_infile:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        feature = l_fields[1]
        count = int(l_fields[2])

        # process the term files
        # PGA, on reviewing this, I am not sure these sets are needed, since
        # we are in a loop for a single line, so we should never have more than one
        # instance of a term or feature per line.
        term_set = set()
        feature_set = set()
        pair_set = set()
        s_infile = codecs.open(infile, encoding='utf-8')
        # check if the feature has a category
        # and replace it with the category.
        # Otherwise ignore this pair.
        if d_feature2cat.has_key(feature):
            cat = d_feature2cat[feature]
            # .tfc file is similar to .tf but only contains lines for labeled features and adds the category label
            s_tfc_file.write("%s\t%s\t%s\t%i\n" % (term, feature, cat, count))
            # record occurrences of terms and features within this doc
            term_set.add(term)
            feature_set.add(feature)
            pair = term + "\t" + cat
            pair_set.add(pair)
            #print "[for .tfc]term_set len: %i, pair_set len: %i" % (len(term_set), len(pair_set))
                
        s_infile.close()

        # increment the doc_freq for terms and verbs in the doc
        # By making the list a set, we know we are only counting each term or verb once
        # per document
        # NOTE: This may be unnecessary, since we only have one line (term) at a time at this point.
        for term in term_set:
            d_term_freq[term] += count

        for feature in feature_set:
            d_feature_freq[feature] += count
            #print "d_verb_freq for %s: %i" % (verb, d_verb_freq[verb])

        for pair in pair_set:
            d_pair_freq[pair] += count

    s_tfc_file.close()
    s_tc_file = codecs.open(tc_file, "w", encoding='utf-8')
    
    for pair in d_pair_freq.keys():
        (term, cat) = pair.split("\t")
        prob = float(d_pair_freq[pair]) / float(d_term_freq[term])
        
        s_tc_file.write( "%s\t%s\t%i\t%i\t%f\n" % (term, cat,  d_pair_freq[pair], d_term_freq[term], prob))

    else:
        pass
        #print "omitting: %s, %s" % (term1, term2)
    s_tc_file.close()

# generate a set of term category "seeds" for learning new diagnostic features
# .tc is of the form:
# acoustic devices        c       2       2       1.000000
# As long as min_prob > .5, there will be one cat output for each term.  We are simply choosing the one
# with highest probability and ignoring cases where the freq of the term feature pair <= min_pair_freq
def tc2tcs(corpus_root, corpus, year, min_prob, min_pair_freq, cat_type, subset):
    # the tc means "term-category" 
    #infile = inroot + "/" + year_cat_name + ".tc"
    infile = pnames.tv_filepath(corpus_root, corpus, year, "tc", subset, cat_type)
    #outfile = outroot + "/" + year_cat_name + ".tcs"
    tcs_file = pnames.tv_filepath(corpus_root, corpus, year, "tcs", subset, cat_type)


    s_tcs_file = codecs.open(tcs_file, "w", encoding='utf-8')

    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[1]
        pair_count = int(l_fields[2])
        prob = float(l_fields[4])

        if pair_count >= min_pair_freq and prob >= min_prob:
            s_tcs_file.write("%s\t%s\t%i\t%f\n" % (term, cat, pair_count, prob))

    s_infile.close()
    s_tcs_file.close()

# labels features found in .tf file with the category
# associated with any known seed term (in .tcs file)
def tcs2fc(corpus_root, corpus, year, cat_type, subset): 
    
    #seed_file = inroot + "/" + year_cat_name + ".tcs"
    seed_file = pnames.tv_filepath(corpus_root, corpus, year, "tcs", subset, cat_type)
    #term_feature_file = inroot + "/" + str(year) + ".tf"
    # recall use "" for cat_type for .tf file
    term_feature_file = pnames.tv_filepath(corpus_root, corpus, year, "tf", subset, "")
    #outfile = outroot + "/" + year_cat_name + ".fc"
    fc_file = pnames.tv_filepath(corpus_root, corpus, year, "fc", subset, cat_type)
    d_seed = {}

    s_fc_file = codecs.open(fc_file, "w", encoding='utf-8')

    # read in all the seeds and their categories
    s_seed_file = codecs.open(seed_file, encoding='utf-8')
    for line in s_seed_file:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[1]
        d_seed[term] = cat

    s_seed_file.close()

    #pdb.set_trace()
    # create the output file of cat feature by substituting the 
    # category for any seed term encountered
    s_term_feature_file = codecs.open(term_feature_file, encoding='utf-8')
    for line in s_term_feature_file:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        feature = l_fields[1]
        count = l_fields[2]
        if d_seed.has_key(term):
            cat = d_seed[term]
            s_fc_file.write("%s\t%s\n" % (feature, cat))
            #s_fc_file.write("%s\t%s\t%s\t%s\n" % (feature, cat, term, count))
    s_term_feature_file.close()
    s_fc_file.close()

# convert feature category count (.fc_uc) info to feature category prob info (.fc_prob)
# cat_list is a list of category names (e.g., ["a", "c", "o", "t"]) used for computing 
# K-L divergence between probability distributions.  K-L div is computed between marginal probs for
# each class vs. conditional probs for each class given the feature.
# For applying Bayes rule, we also compute the log of prob of feature given a category, using +1 
# smoothing.
def fcuc2fcprob(corpus_root, corpus, year, cat_list, cat_type, subset):
    
    print "[fcuc2fcprob]cat_list: %s" % cat_list
    yearfilename = str(year)
    year_cat_name = yearfilename + "." + cat_type
    # count of number of docs a feature-category pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    # accumulate feature_cat instances for each category
    d_feature_cat_freq = collections.defaultdict(int)
    # accumulate term_cat instances for each category
    d_term_cat_freq = collections.defaultdict(int)
    # accumulate freq for each feature
    d_feature_freq = collections.defaultdict(int)
    # overall prob for each category
    d_cat_prob = collections.defaultdict(int)
    # we will need a list of overall probs for input into kl_div
    cat_prob_list = []
    # capture the number of labeled instances to compute prior prob for each category
    instance_freq = 0
    # count total number of terms (denominator in computing prior prob)
    term_count = 0
    smoothing_parameter = 1
    min_feature_freq = 10

    ##fc_uc_file = inroot + "/" + year_cat_name + ".fc_uc"
    fc_uc_file = pnames.tv_filepath(corpus_root, corpus, year, "fc_uc", subset, cat_type)
    # output file to store prob of category given the term
    ##prob_file = outroot + "/" + year_cat_name + ".fc.prob"
    prob_file = pnames.tv_filepath(corpus_root, corpus, year, "fc_prob", subset, cat_type)
    # output file to store prior probs of each category
    ##cat_prob_file = outroot + "/" + year_cat_name + ".fc.cat_prob"
    cat_prob_file = pnames.tv_filepath(corpus_root, corpus, year, "cat_prob", subset, cat_type)
    # tcs_file contains seed term and category
    tcs_file = pnames.tv_filepath(corpus_root, corpus, year, "tcs", subset, cat_type)

    s_cat_prob_file = codecs.open(cat_prob_file, "w", encoding='utf-8')

    #kl_file = outroot + "/" + year_cat_name + ".fc.kl"
    kl_file = pnames.tv_filepath(corpus_root, corpus, year, "fc_kl", subset, cat_type)
    s_kl_file = codecs.open(kl_file, "w", encoding='utf-8')

    # process the pairs
    cat_set = set()
    feature_set = set()
    pair_set = set()

    # compute prior probs (using the labeled seed terms)
    # (replaces older version that computed priors based on feature-cat counts)
    # tcs_file is .tcs
    # We treat each seed term as a "document" represented by a weighted feature vector,
    # where the weight is the doc freq of the feature across all instances of the seed term.
    # This is analogous to document classification, in which a doc is represented as a word vector,
    # weighted by the term freq of each word in the doc.
    # Thus the prior probabilities are the proportion of terms in each category relative to all terms.

    s_tcs_file = codecs.open(tcs_file, encoding='utf-8')
    # <term> <category> <doc frequency> <prob of ?>
    # graphical timelines     c       2       1.000000
    for line in s_tcs_file:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[1]
        count = int(l_fields[2])

        ### /// check this logic
        # increment the doc_freq for the cat, based on the cat for this term
        d_term_cat_freq[cat] += count
        term_count += count

    s_tcs_file.close()

    s_prob_file = codecs.open(prob_file, "w", encoding='utf-8')

    # Compute prior prob distribution of categories
    num_categories = len(cat_list)
    for cat in cat_list:
        #print "Compute prob distribution of categories"
        #pdb.set_trace()
        # compute the probability of the category
        cat_prob = float(d_term_cat_freq[cat]) / float(term_count)
        # add prob to a list for use in kl_div
        # This is our actual prob distribution of categories
        cat_prob_list.append(cat_prob)
        d_cat_prob[cat] = cat_prob
        s_cat_prob_file.write("%s\t%i\t%f\n" % (cat, d_term_cat_freq[cat],  cat_prob))

    # get feature data for use in kl-div
    # infile is .fc_uc
    s_fc_uc_file = codecs.open(fc_uc_file, encoding='utf-8')
    for line in s_fc_uc_file:
        line = line.strip()
        l_fields = line.split("\t")
        feature = l_fields[0]
        cat = l_fields[1]
        count = int(l_fields[2])

        # create a pair for dictionary key
        pair = cat + "\t" + feature
        pair_set.add(pair)

        ### /// check this logic
        # increment the doc_freq for cats and features in the doc
        # By making the pair list a set (above), we know we are only counting each cat or feature once
        # per document
        d_feature_cat_freq[cat] += count
        d_feature_freq[feature] += count
        d_pair_freq[pair] += count
        instance_freq += count

    s_fc_uc_file.close()
    
    """
    # old version that computed priors using feature freq
    s_prob_file = codecs.open(prob_file, "w", encoding='utf-8')

    # Compute prob distribution of categories
    num_categories = len(cat_list)
    for cat in cat_list:
        #print "Compute prob distribution of categories"
        #pdb.set_trace()
        # compute the probability of the category
        cat_prob = float(d_cat_freq[cat]) / float(instance_freq)
        # add prob to a list for use in kl_div
        # This is our actual prob distribution of categories
        cat_prob_list.append(cat_prob)
        d_cat_prob[cat] = cat_prob
        s_cat_prob_file.write("%s\t%i\t%f\n" % (cat, d_cat_freq[cat],  cat_prob))
    """

    """
    # old version that does not compute kl-divergence
    for pair in d_pair_freq.keys():
        l_pair = pair.split("\t")
        cat = l_pair[0]
        feature = l_pair[1]
        # prob of category given the feature
        cgf_prob = float(d_pair_freq[pair]) / float(d_feature_freq[feature])
        # prob of feature given the category
        fgc_prob = float(d_pair_freq[pair]) / float(d_cat_freq[cat])

    """
    # num_features is needed to compute smoothing in denominator of fgc probabilities
    num_features = len(d_feature_freq.keys())
    # track the total prob of fgc for each cat as a sanity check
    d_cum_fgc_prob = collections.defaultdict(float)

    for feature in d_feature_freq.keys():
        # accumulate probs for each cat
        cgf_prob_list = []
        fgc_prob_list = []
        cgf_prob_string = ""
        fgc_prob_string = ""

        # log of probs
        lcgf_prob_list = []
        lfgc_prob_list = []
        lcgf_prob_string = ""
        lfgc_prob_string = ""

        feature_freq = d_feature_freq[feature]
        # keep category and prob to sort to find max prob category and runner up
        fcat_prob_list = []

        for cat in cat_list:
            # create the key needed for d_pair_freq
            pair = cat + "\t" + feature
            # prob of category given the feature
            # We'll do +1 smoothing to avoid 0 probs.
            #pdb.set_trace()
            cgf_prob = float(d_pair_freq[pair] + smoothing_parameter) / float(feature_freq + (smoothing_parameter * num_categories))
            lcgf_prob = math.log(cgf_prob)
            fcat_prob_list.append([cat, cgf_prob])
            cgf_prob_list.append(cgf_prob)

            # smoothing denominator should include smoothing parameter (e.g. 1) times the number of observations.
            # Number of observations is the number of types in the numerator.

            # prob of feature given the category
            fgc_prob = float(d_pair_freq[pair] + smoothing_parameter) / float(d_feature_cat_freq[cat] + (smoothing_parameter * num_features))
            # accumulate the probs over all features to verify its total to 1.0
            d_cum_fgc_prob[cat] += fgc_prob
            lfgc_prob = math.log(fgc_prob)
            # prob_list aligns with cats in cat_list
            fgc_prob_list.append(fgc_prob)
            lfgc_prob_list.append(lfgc_prob)
            # write out each feature cat pair info separately 
            s_prob_file.write("%s\t%s\t%i\t%i\t%f\t%f\n" % (feature, cat,  d_pair_freq[pair], feature_freq, cgf_prob, fgc_prob))
            # also capture the conditional probs in a string for storage as a field in output file
            cgf_prob_string = cgf_prob_string + " " + str(cgf_prob)
            fgc_prob_string = fgc_prob_string + " " + str(fgc_prob)
            lcgf_prob_string = lcgf_prob_string + " " + str(lcgf_prob)
            lfgc_prob_string = lfgc_prob_string + " " + str(lfgc_prob)

        # also compute kl divergence and write a summary line for each feature
        #pdb.set_trace()
        # if there are not any instances of a category in the .fc file, then we'll get a 0 in
        #the cat_prob_list.  Since we cannot divide by 0, print a warning and exit.
        if 0 in cat_prob_list:
            print "[fcuc2fcprob]Some category does not appear in the .fc file. Exiting.  cat_prob_list: %s" % cat_prob_list
            exit
        kld = kl_div(cgf_prob_list, cat_prob_list)

        # compute max and runner up prob categories
        fcat_prob_list.sort(utils.list_element_2_sort)
        #print "fcat_prob_list: %s" % fcat_prob_list
        #pdb.set_trace()
        max_cat = fcat_prob_list[0][0]
        # keep the letter of the highest prob class for printing out.
        # Note that the max class prob could be lower than expected prob if there are more
        # than 2 classes.  That is, the class could have the highest prob for this feature,
        # but its probability could be lower than expected by chance.  Hence we add a + or -
        # symbol after max_cat to indicate this in the output
        max_letter = max_cat
        max_score = fcat_prob_list[0][1]
        if max_score > d_cat_prob[max_cat]:
            max_cat = max_cat + "+"
        else:
            max_cat = max_cat + "-"
        next_cat = fcat_prob_list[1][0]
        next_score = fcat_prob_list[1][1]
        if next_score > d_cat_prob[next_cat]:
            next_cat = next_cat + "+"
        else:
            next_cat = next_cat + "-"
        """
        # if the runner-up exceeds a threshold, print it as well
        if fcat_prob_list[1][1] >= .2:
            next_cat = fcat_prob_list[1][0]
        """
        if feature_freq >= min_feature_freq:
            #print "%s\t%i\t%f\t%s\t%s" % (feature, feature_freq, kld, cgf_prob_string, fgc_prob_string)
            s_kl_file.write("%s\t%s\t%s %s\t%i\t%f\t%s\t%s\n" % (feature, max_letter,  max_cat, next_cat, feature_freq, kld, lcgf_prob_string, lfgc_prob_string))

    for cat in d_cum_fgc_prob.keys():
        print "[fcuc2fcprob]category: %s, cum_fgc_prob (should total to 1.0): %f" % (cat, d_cum_fgc_prob[cat])


    s_prob_file.close()
    s_cat_prob_file.close()
    s_kl_file.close()


"""
# moved to tf.py
#---
# Create a single file of term feature count for each year (from the .xml extracts of phr_feats data)
# role.run_dir2features_count()
# modified 3/3/14 to take parameters from run_tf_steps
def run_dir2features_count(inroot, outroot, start_range, end_range):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb_tas"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"

    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k/data/tv"

    # cs
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    # chemical
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-12-chemical/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-12-chemical/data/tv"

    # health
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv"

    # test (4 files from health 1997)
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/test/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/test/data/tv"
    

    # Chinese cs
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-cn-all-600k/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-cn-all-600k/data/tv"

    print "Output dir: %s" % outroot

    # range should be start_year and end_year + 1
    #for int_year in range(1981, 2008):
    #for int_year in range(1995, 2008):
    #for int_year in range(1997, 1998):
    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        inroot_year = inroot + "/" + year
        print "Processing dir: %s" % inroot_year

        dir2features_count(inroot_year, outroot, year)
        print "Completed: %s" % year
"""

# term feature to term feature category for terms whose feature appears in our seed list
# role.run_tf2tfc()
def run_tf2tfc(corpus_root, corpus, start_range, end_range, fcat_file, cat_list, cat_type, subset):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    #fcat_file = "/home/j/anick/patent-classifier/ontology/creation/feature.cat.en.dat"
    #fcat_file = "/home/j/anick/patent-classifier/ontology/creation/seed.cat.en.dat"

    # category r and n are useful but overlap with other cats.  Better to work with them separately.
    #cat_list = ["a", "b", "c", "p", "t", "o"]

    #for int_year in range(1997, 1998):
    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_tf2tfc]Processing dir: %s" % year

        # cat_list allows discretion over the category set
        tf2tfc(corpus_root, corpus, year, fcat_file, cat_list, cat_type, subset)
        print "[run_tf2tfc]Completed: %s.tc" % (year)

# term category to seed terms
# role.run_tc2tcs()
def run_tc2tcs(corpus_root, corpus, start_range, end_range, cat_type, subset):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    #outroot = inroot

    # cutoffs
    # changed from .7 to 1 to avoid getting a lot of possibly ambiguous common terms into the seed  list for training
    min_prob = 1
    # changed from 1 to 2 on 3/8/14  PGA.  Files generated before this date will have used 1.
    # changed to 3 on 3/11/14
    # changed to 2 on 3/12 to boost output after raising min_prob to 1
    min_pair_freq = 2

    # note: To explore the actual term sets produced by different cutoffs, do e.g.
    # cat 1997.act.tc | python $CDIR/filtergt.py 5 1 | python $CDIR/filtergt.py 4 2 | more
    # the .tc file has lines of the form:
    # signal quality  a       3       3       1.000000
    # where field 3 is the # of term-feat pairs that match the category (a)
    # and field 4 is the # of term-feat pairs matching any category.
    # field 5 is the probability of the category(a) given the features associated with "signal quality"
    # In this case, since the prob is 1, fields 3 and 4 are equal.  

    #for int_year in range(1997, 1998):
    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_tc2tcs]Processing dir: %s" % year

        tc2tcs(corpus_root, corpus, year, min_prob, min_pair_freq, cat_type, subset)
        #print "[run_tc2tcs]Completed: %s.st in %s" % (year, outroot)

# use the seed terms to create a file of feature category pairs.  That is, for
# each line containing a seed term, replace it with the category.
# role.run_tcs2fc()
def run_tcs2fc(corpus_root, corpus, start_range, end_range, cat_type, subset):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    #outroot = inroot

    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_tcs2fc]Processing dir: %s" % year

        tcs2fc(corpus_root, corpus, year, cat_type, subset)
        #print "[run_tcs2fc]Completed: %s.fc in %s" % (year, outroot)


# Generate probability for each feature cat combination
# Input file is the result of a uc on the .fc file
# First run:
#      sh run_fc2fcuc.sh

# role.run_fcuc2fcprob()
def run_fcuc2fcprob(corpus_root, corpus, start_range, end_range, cat_list, cat_type, subset):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    #outroot = inroot

    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_fcuc2fcprob]Processing dir: %s" % year

        fcuc2fcprob(corpus_root, corpus, year, cat_list, cat_type, subset)
        #print "[run_fcuc2fcprob]Completed: %s.fc in %s" % (year, outroot)

def summary(term, d_term2act, d_term2pn):
    if d_term2act.has_key(term):
        (term, num_diagnostic_feats, num_doc_feature_instances, cat, doc_freq, score_a, score_c, score_t, feats) = d_term2act[term].split("\t")
        print "ACT: %s\t%s\%s\t%s" % (term, cat, doc_freq, feats)
    if d_term2pn.has_key(term):
        (term, num_diagnostic_feats, num_doc_feature_instances, cat, doc_freq, score_p, score_n, feats) = d_term2pn[term].split("\t")
        print "Polarity: %s\t%s\%s\t%s" % (term, cat, doc_freq, feats)
        
# return the cat files as dictionaries
# (d_act, d_pn) = role.get_dcats("ln-us-cs-500k", 2002)
def get_dcats(corpus, year):

    d_term2act = {}
    d_term2pn = {}

    file_type = "cat.w0.0"
    act_file = pnames.tv_filepath(corpus_root, corpus, year, file_type, "", cat_type="act")
    pn_file = pnames.tv_filepath(corpus_root, corpus, year, file_type, "a", cat_type="pn")

    s_act_file = codecs.open(act_file, encoding='utf-8')
    for line in s_act_file:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        d_term2act[term] = l_fields
    s_act_file.close()

    s_pn_file = codecs.open(pn_file, encoding='utf-8')
    for line in s_pn_file:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        d_term2pn[term] = l_fields
    s_pn_file.close()

    return(d_term2act, d_term2pn)

# in progress
def get_hword2label(corpus, year):

    d_term2act = {}
    d_term2pn = {}

    file_type = "cat.w0.0"
    act_file = pnames.tv_filepath(corpus_root, corpus, year, file_type, "", cat_type="act")

    s_act_file = codecs.open(act_file, encoding='utf-8')
    for line in s_act_file:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        d_term2act[term] = l_fields
    s_act_file.close()

# line to extract headwords
# fcpy (fuse code python) is "python /home/j/anick/patent-classifier/ontology/creation"
# fcpy="python /home/j/anick/patent-classifier/ontology/creation"
# cat 2002.terms | cut -f1 | sed 's/.* //' | sort | uniq -c | sort -nr | $fcpy/reformat_uc1.py 

# 3/19/14 temporal entropy idea
# Similar to Kanhabua and Norvig use of TE in Machine Learning and Knowledge Discovery in Databases: European Conference ...
# edited by Wray Buntine, Marko Grobelnik, Dunja Mladenic, John Shawe-Taylor
# http://books.google.com/books?id=5THWkRwjZywC&pg=PA739&lpg=PA739&dq=%22temporal+entropy%22+terms&source=bl&ots=0TptVioYXD&sig=pB0ZYlF63pZfYYcC0eZc_4uSg3I&hl=en&sa=X&ei=ikMqU9TYB9SEqQGmrYGYBw&ved=0CEMQ6AEwBQ#v=onepage&q=%22temporal%20entropy%22%20terms&f=false

# Get the feats with doc freq > 1000 in 2005
# cat 2005.feats | grep prev_V= | $pgt 2 1000 |cut -f1,2 > 2005.feats.gt1000
# Get the terms with freq > 10 in 2005 (from .terms)
#cat 2005.terms | $pgt 2 10 | wc -l
# 50670
# cat 2005.terms | $pgt 2 10 | cut -f1,2 > 2005.terms.gt10

# Todo later, compare TE for c, a, t terms

# To compute TE, we'll need for each year:

# d_year_term2freq where key is term|year  (from .terms)
# d_y_term_feat2freq where key is term|feat|year (from .tf)

# but just use the terms and feats filtered as above

# d_t2e  = role.get_te("ln-us-cs-500k")
#(d_term, d_feat, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq) = role.get_te_dicts("ln-us-cs-500k")
def get_te_dicts(corpus):

    # store the terms and feats we will consider after filtering
    d_feat = {}
    d_term = {}

    # store all the freq data needed for computing probs from TE
    #d_term_feat_year2freq = {}
    d_term_year2freq = {}
    # we also need to keep track of all the feats for a given term in a year
    d_term_year2feats = defaultdict(set)
    # Freq of a term_feat combinations in a given year
    d_term_feat_year2freq = {}

    file_type = "cat.w0.0"
    # use our reference file for terms
    ref_term_file = pnames.tv_filepath(corpus_root, corpus, 2005,  "terms.gt10", "", cat_type="")
    # mini file for testing
    #ref_term_file = pnames.tv_filepath(corpus_root, corpus, 2005,  "terms.gt10.10", "", cat_type="")
    ref_feat_file = pnames.tv_filepath(corpus_root, corpus, 2005, "feats.gt1000", "", cat_type="")

    # reference terms
    s_in_file = codecs.open(ref_term_file, encoding='utf-8')
    for line in s_in_file:
        line = line.strip("\n")
        (term, freq) = line.split("\t")
        d_term[term] = int(freq)
    s_in_file.close()

    # reference feats
    s_in_file = codecs.open(ref_feat_file, encoding='utf-8')
    for line in s_in_file:
        line = line.strip("\n")
        (feat, freq) = line.split("\t")
        d_feat[feat] = int(freq)
    s_in_file.close()

    #for year in range(1997, 2008):
    for year in range(1997, 2008):
        str_year = str(year)
        
        tf_file = pnames.tv_filepath(corpus_root, corpus, year,  "tf", "", "")
        terms_file = pnames.tv_filepath(corpus_root, corpus, year,  "terms", "", "")

        # terms_file contains the doc_freq for each term, so load it in!
        s_in_file = codecs.open(terms_file, encoding='utf-8')
        for line in s_in_file:
            line = line.strip("\n")
            (term, freq, instance_freq, prob) = line.split("\t")
            # only use filtered terms
            if d_term.has_key(term):
                key = "^".join([term, str_year])
                d_term_year2freq[key] = int(freq)
        s_in_file.close()

        s_in_file = codecs.open(tf_file, encoding='utf-8')
        for line in s_in_file:
            line = line.strip("\n")
            (term, feat, freq, xxx) = line.split("\t")
            # only use filtered terms and feats
            if d_feat.has_key(feat) and d_term.has_key(term):
                tfy_key = "^".join([term, feat, str_year])
                tf_key = "^".join([term, feat])
                ty_key = "^".join([term, str_year])
                # add the feat to the set of feats occurring with this term
                d_term_year2feats[ty_key].add(feat)
                d_term_feat_year2freq[tfy_key] = int(freq)
        s_in_file.close()


    l_dicts = [d_term, d_feat, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq]
    pickle_dicts = [d_term_year2freq, d_term_year2feats, d_term_feat_year2freq]
    # pickle the results
    te_data_file = pnames.tv_filepath(corpus_root, corpus, "te_data", "pickle" , "", "")
    #s_te_data_file = codecs.open(te_data_file, "w", encoding='utf-8')
    pickle.dump(pickle_dicts, open(te_data_file, "wb"))
    #s_te_data_file.close()

    return(l_dicts)

# (d_term_year2freq, d_term_year2feats, d_term_feat_year2freq) = role.get_te_pickled("ln-us-cs-500k", "patrick.10")
def get_te_pickled(corpus, terms_filename):

    # list of terms for which to compute feature entropy
    terms_file = pnames.tv_filepath(corpus_root, corpus, "te_in",  terms_filename, "", "")
    pickle_file = pnames.tv_filepath(corpus_root, corpus, "te_data",  "pickle", "", "")

    (d_term_year2freq, d_term_year2feats, d_term_feat_year2freq) = pickle.load( open( pickle_file, "rb" ) )
    print "[get_te_pickled]loaded pickle data"
    get_te(corpus, terms_filename, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq)
    # return the dicts so they can be reused in python environment without reloading from pickle
    return([d_term_year2freq, d_term_year2feats, d_term_feat_year2freq])

# compute temporal entropy for a set of terms in terms_file
# d_term2feat_entropy = role.get_te("ln-us-cs-500k", "patrick.10", d_term_year2freq, d_term_year2feats, d_term_feat_year2freq)
# This assumes that range data dictionaries have been put into te_data.pickle by get_te_dicts.
def get_te(corpus, terms_filename, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq):

    # list of terms for which to compute feature entropy
    terms_file = pnames.tv_filepath(corpus_root, corpus, "te_in",  terms_filename, "", "")

    print "[get_te]loaded pickle data through parameters"
    # Now we have all the term freq data loaded
    # we can compute the prob for each term_feat pair over the years
    d_term_feat2entropy = defaultdict(float)

    # compute entropy of term-feat count over the year range
    s_in_file = codecs.open(terms_file, encoding='utf-8')

    # track the terms we will be computing entropy for
    l_input_terms = []
    # IMPORTANT: The number of years must be consistent with the number of
    # years in the range, for the entropy computation
    NUM_YEARS = 11
    # inverse log of number of partitions (used in K&N temporal entropy definition)
    ILNY = 1 / math.log(NUM_YEARS, 2)

    for line in s_in_file:
        line = line.strip("\n")
        term = line
        l_input_terms.append(term)
        # get all features for the term 
        l_feats = d_term2feats[term]

        # accumulate the number of docs a term occurs in
        term_cum_freq = 0

        for year in range(1997, 2008):
            str_year = str(year)
            ty_key = "^".join([term, str_year])

            # accumulate total number of docs the term is in across all years
            if d_term_year2freq.has_key(ty_key):
                term_cum_freq += d_term_year2freq[ty_key]

        # for each feature of this term
        # compute its prob for each year
        # as doc-freq in the year / doc_freq in the entire range (all years)
        for feat in l_feats:
            tf_key = "^".join([term, feat])
            # accumulate the frequency of the feature across years
            feat_cum_freq = 0
            # accumulate normalized frequency for each year
            cum_norm_freq = 0
            # keep list of freq in each year
            l_feat_year_freq = []
            for year in range(1997, 2008):
                str_year = str(year)
                tfy_key = "^".join([term, feat, str_year])
                ty_key = "^".join([term, str_year])

                #pdb.set_trace()
                # prob is the term-feat doc frequency / term doc freq
                # Verify that this term occurs in this year before computing anything
                if d_term_feat_year2freq.has_key(tfy_key):
                    #pdb.set_trace()
                    # get the term freq for this year
                    freq = float(d_term_feat_year2freq[tfy_key])
                    # normalize by dividing freq by the # docs for the term for the year
                    norm_freq = freq / d_term_year2freq[ty_key]
                    # update the cumulative freq for the feature
                    feat_cum_freq += freq
                    cum_norm_freq += norm_freq
                    # update our year list of freqs
                    l_feat_year_freq.append(norm_freq)
                    print "[TE]tfy: %s, freq: %i, doc_freq: %i, norm_freq: %f, feat_cum_freq: %i, cum_norm_freq: %f" % (tfy_key, freq, d_term_year2freq[ty_key], norm_freq, feat_cum_freq, cum_norm_freq)

            # Now that we have the cumumlative freq, we can compute probs
            # Note that we have omitted 0 freqs.  However, if we wanted to track feature
            # freq by year, we should include them (and set probs to 0 also)
            #norm_cum_freq = float(feat_cum_freq) / term_cum_freq
            for norm_freq in l_feat_year_freq:
                prob = norm_freq / cum_norm_freq
                #pdb.set_trace()
                # By just walking through the tf file for the year, we are getting all the probs
                # for terms and feats that occur at least once.
                # we are skipping any 0 probs, since they do not contribute to the summation anyway
                # entropy assumes that prob(x)*log(prob(x) = 0 whenever prob(x) = 0.
                # Do the summation in d_term_feat2entropy
                # The result is the average log(prob(term-feat))
                d_term_feat2entropy[tf_key] += prob * math.log(prob, 2)
                print "[TE]feat: %s, norm_freq: %f, cum_norm_freq: %f, prob: %f, sum(ent): %f" % (feat, norm_freq, cum_norm_freq, prob, d_term_feat2entropy[tf_key]  )
            # Entropy is actually -1 * the sum.
            # Use the formula from
            # "Using temporal language models for document dating" (Kanhabua and Norvig)
            # commented out straight entropy:
            #d_term_feat2entropy[tf_key] = -1 * d_term_feat2entropy[tf_key]
            d_term_feat2entropy[tf_key] = 1 + ILNY * d_term_feat2entropy[tf_key]
            
            print "Finished feat for all years: tfy: %s, sum_entropy: %f" % (tfy_key, d_term_feat2entropy[tf_key]  )
    s_in_file.close()

    # Now for each term, sort the feats by entropy
    entropy_file = pnames.tv_filepath(corpus_root, corpus, "te_out",  terms_filename, "", "")
    s_entropy = codecs.open(entropy_file, "w", encoding='utf-8')

    d_term2feat_entropy = {}

    for term in l_input_terms:
        l_feats = d_term2feats[term]
        l_feat_entropy = []
        
        for feat in l_feats:
            tf_key = "^".join([term, feat])
            entropy = d_term_feat2entropy[tf_key]
            l_feat_entropy.append([feat, entropy])
        #pdb.set_trace()
        l_feat_entropy.sort(utils.list_element_2_sort)
        d_term2feat_entropy[term] = l_feat_entropy
        s_entropy.write("%s\t%s\n" % (term, d_term2feat_entropy[term]))

    s_entropy.close()
    return(d_term2feat_entropy)

# (d_feat_year2freq, d_feat_range2freq) = role.build_d_feat_year2freq("ln-us-cs-500k", 1997, 1998)
def build_d_feat_year2freq(corpus, start, end):

    # use the data in .feats for this (field 2 is freq)
    d_feat_year2freq = defaultdict(int)
    d_feat_range2freq = defaultdict(int)

    range_end = end + 1
    for year in range(start, range_end):
        str_year = str(year)
        feats_file = pnames.tv_filepath(corpus_root, corpus, str_year,  "feats", "", "")
        s_feats_file = codecs.open(feats_file, encoding='utf-8')

        for line in s_feats_file:
            line = line.strip()
            l_fields = line.split("\t")
            feat = l_fields[0]
            freq = l_fields[1]
            
            fy_key = "^".join([feat, str_year])
            # feat2freq given year
            d_feat_year2freq[fy_key] = int(freq)
            # feat2freq for range
            d_feat_range2freq[feat] += int(freq)
    
        s_feats_file.close()
    return([d_feat_year2freq, d_feat_range2freq])

# d_term_year2feats = role.build_d_term_year2feats("ln-us-cs-500k", 1997, 2007)
def build_d_term_year2feats(corpus, start, end):

    # use the data in .feats for this (field 2 is freq)
    d_term_year2feats = defaultdict(set)
    d_term_range2feats = defaultdict(set)

    range_end = end + 1
    for year in range(start, range_end):
        str_year = str(year)
        tf_file = pnames.tv_filepath(corpus_root, corpus, str_year,  "tf", "", "")
        s_tf_file = codecs.open(tf_file, encoding='utf-8')

        for line in s_tf_file:
            line = line.strip()
            l_fields = line.split("\t")
            term = l_fields[0]
            feat = l_fields[1]
            freq = l_fields[2]

            ty_key = "^".join([term, str_year])
            # term to feats given year
            d_term_year2feats[ty_key].add(feat)
            # feat2freq for range ?? needed??
            # d_term_range2feats[term].add(feat) 
    
        s_tf_file.close()
    return(d_term_year2feats)

        

# d_feats is a reference file limiting the set of feats to consider to some threshold
# feat prob by year
# (d_fgr, d_fgy) = role.get_fpgy("ln-us-cs-500k", "patrick.10", 1997, 1998, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq)
# (d_fgr, d_fgy) = role.get_fpgy("ln-us-cs-500k", "patrick.61", 1997, 2007, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq)
# feature probability given year
def get_fpgy(corpus, terms_filename, start, end, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq):

    # threshold for the number of feature occurrences in the range of years
    min_range_freq = 80

    # file of terms for which to compute fpy
    terms_file = pnames.tv_filepath(corpus_root, corpus, "te_in",  terms_filename, "", "")

    # use a constrained set of features only
    ref_feat_file = pnames.tv_filepath(corpus_root, corpus, 2005, "feats.gt1000", "", cat_type="")
    # reference feats
    d_feat = {}
    s_in_file = codecs.open(ref_feat_file, encoding='utf-8')
    for line in s_in_file:
        line = line.strip("\n")
        (feat, freq) = line.split("\t")
        d_feat[feat] = int(freq)
    s_in_file.close()

    print "[get_te]loaded pickle data through parameters"
    # Now we have all the term freq data loaded
    # we can compute the prob for each feat over the years
    # Count is number of doc_feature combinations in the year for our term set

    # add one to end for python range
    range_end = end + 1

    # we can sum over d_term_year2freq to populate term-doc counts
    d_td_year2freq = defaultdict(int)
    # feat-doc count given the year
    d_fd_year2freq = defaultdict(int)
    d_fd_range2freq = defaultdict(int)
    # total number term-doc entries for the terms in the term_list
    td_range_freq = 0

    s_in_file = codecs.open(terms_file, encoding='utf-8')

    # track the terms we will be computing feat probs for
    l_input_terms = []
    # list of all feats compiled
    l_all_feats = set()

    for line in s_in_file:
        line = line.strip("\n")
        term = line
        l_input_terms.append(term)
    
        # accumulate the term_doc counts for each year and total
        for year in range(start, range_end):
            str_year = str(year)
            ty_key = "^".join([term, str_year])
            # total term-doc per year
            if d_term_year2freq.has_key(ty_key):
                d_td_year2freq[year] += d_term_year2freq[ty_key]
                # total term-doc over the range
                td_range_freq += d_term_year2freq[ty_key]

                # get all features for the term for this year
                l_feats = d_term_year2feats[ty_key]

                for feat in l_feats:
                    # add it to the total set
                    l_all_feats.add(feat)
                    # Don't bother with real low frequency feats (which are omitted from d_feat)
                    if d_feat.has_key(feat):
                        tfy_key = "^".join([term, feat, str_year])
                        fy_key =  "^".join([feat, str_year])
                        d_fd_year2freq[fy_key] += d_term_feat_year2freq[tfy_key]
                        d_fd_range2freq[feat] += d_term_feat_year2freq[tfy_key]
                
    # Now we should be able to compute prob(feat|year) and prob(feat|range)
    # total term-doc per year
    # d_td_year2freq[year]
    # total term-doc over the range
    # td_range_freq
    # feature doc freq given year
    # d_fd_year2freq[fy_key]
    # feature doc freq total in range
    # d_fd_range2freq[feat]
    # all feats
    # l_all_feats
    d_fgy = {}  # fy_key
    d_fgr = {}  # feat

    for feat in l_all_feats:
        if d_feat.has_key(feat) and d_fd_range2freq[feat] > min_range_freq:
            # feature given entire range (marginal prob)
            d_fgr[feat] = float(d_fd_range2freq[feat]) / td_range_freq
            print "feat: %s, fgr: %i, tgr: %i, prob(fgr): %f" % (feat, d_fd_range2freq[feat], td_range_freq, d_fgr[feat])
            # feature given year 
            for year in range(start, range_end):
                str_year = str(year)
                fy_key = "^".join([feat, str_year])
                d_fgy[fy_key] = float(d_fd_year2freq[fy_key]) / d_td_year2freq[year]
                print "feat: %s, year: %s, fgy: %i, tgy: %i, prob(fgy): %f" % (feat, year, d_fd_year2freq[fy_key], d_td_year2freq[year], d_fgy[fy_key])

    return([d_fgr, d_fgy])

# prob of year given the feature
# (l_retained_feats, d_l_ygf_actual, d_l_ygf_expected) = role.get_ypgf("ln-us-cs-500k", "patrick.10", 1997, 2007, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq)
def get_ypgf(corpus, terms_filename, start, end, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq):

    min_range_freq = 80

    # list of terms for which to compute fpy
    terms_file = pnames.tv_filepath(corpus_root, corpus, "te_in",  terms_filename, "", "")

    # use a constrained set of features only
    ref_feat_file = pnames.tv_filepath(corpus_root, corpus, 2005, "feats.gt1000", "", cat_type="")
    # reference feats
    d_feat = {}
    s_in_file = codecs.open(ref_feat_file, encoding='utf-8')
    for line in s_in_file:
        line = line.strip("\n")
        (feat, freq) = line.split("\t")
        d_feat[feat] = int(freq)
    s_in_file.close()

    print "[get_ypgf]loaded pickle data through parameters"
    # Now we have all the term freq data loaded
    # we can compute the prob for each feat over the years
    # Count is number of doc_feature combinations in the year for our term set

    # add one to end for python range
    range_end = end + 1

    # sums needed for computations
    d_fy2sum_tfy_over_terms = defaultdict(int)
    d_f2sum_tfy_in_range_over_terms = defaultdict(int)

    d_y2sum_ty_over_terms = defaultdict(int)
    sum_ty_in_range_over_terms = 0

    # we can sum over d_term_year2freq to populate term-doc counts
    d_td_year2freq = defaultdict(int)
    # feat-doc count given the year
    d_fd_year2freq = defaultdict(int)
    d_fd_range2freq = defaultdict(int)
    # total number term-doc entries for the terms in the term_list
    td_range_freq = 0

    # Make a list of the terms we will be computing feat probs for
    l_input_terms = []
    # list of all feats compiled
    l_all_feats = set()

    #"""
    s_terms_file = codecs.open(terms_file, encoding='utf-8')

    for line in s_terms_file:
        # each line is a single term
        term = line.strip("\n")
        l_input_terms.append(term)
        
    s_terms_file.close()
    #"""

    # parameters for testing
    l_input_terms = ["firewalls", "interface"]
    #l_input_terms = ["firewalls"]
    #start = 2005
    #range_end = 2007
    min_range_freq = 0


    # term freq means the # occurrences of a doc containing the term
    for term in l_input_terms:
        #pdb.set_trace()
        # accumulate the term_doc counts for each year and total range
        for year in range(start, range_end):
            str_year = str(year)
            ty_key = "^".join([term, str_year])
            # total term-doc per year
            if d_term_year2freq.has_key(ty_key):
                d_y2sum_ty_over_terms[year] += d_term_year2freq[ty_key]
                #d_td_year2freq[year] += d_term_year2freq[ty_key]
                # total term-doc over the range
                #td_range_freq += d_term_year2freq[ty_key]
                sum_ty_in_range_over_terms += d_term_year2freq[ty_key]

                # get all features for the term for this year
                l_feats = d_term_year2feats[ty_key]

                for feat in l_feats:
                    # add it to the total set
                    l_all_feats.add(feat)
                    # Don't bother with real low frequency feats (which are omitted from d_feat)
                    if d_feat.has_key(feat):
                        tfy_key = "^".join([term, feat, str_year])
                        fy_key =  "^".join([feat, str_year])
                        #d_fd_year2freq[fy_key] += d_term_feat_year2freq[tfy_key]
                        #d_fd_range2freq[feat] += d_term_feat_year2freq[tfy_key]
                        d_fy2sum_tfy_over_terms[fy_key] += d_term_feat_year2freq[tfy_key]
                        d_f2sum_tfy_in_range_over_terms[feat] += d_term_feat_year2freq[tfy_key]
                        #pdb.set_trace()
                
    # Now we should be able to compute expected prob(year|feat) and actual(year|feat)
    # total term-doc per year
    # d_td_year2freq[year]
    # total term-doc over the range
    # td_range_freq
    # feature doc freq given year
    # d_fd_year2freq[fy_key]
    # feature doc freq total in range
    # d_fd_range2freq[feat]
    # all feats
    # l_all_feats
    d_ygf_actual = {}  # fy_key
    d_ygf_expected = {}  # feat
    d_tgy = {}

    d_l_ygf_expected = defaultdict(list)
    d_l_ygf_actual = defaultdict(list)

    for year in range(start, range_end):
        # compute proportion of terms (actually term-docs) in each year
        # needed for computation of expected year given feature
        if sum_ty_in_range_over_terms > 0: 
            d_tgy[year] = d_y2sum_ty_over_terms[year] / float(sum_ty_in_range_over_terms)
        else:
            d_tgy[year] = 0

    # compute probs for each feat
    # for testing, make our own feat list:
    #l_all_feats = ["prev_Npr=use_of"] # ["prev_V=include"]
    #l_all_feats = ["prev_V=including", "prev_V=include"]

    # minimum number of actual term feature occurrences over the range
    # to output the actual and expected probs.
    min_tfy_in_range = 20
    # keep a list of the feats we return probs for, given the threshold
    l_retained_feats = []

    for feat in l_all_feats:
        #if True: 
        if d_feat.has_key(feat): # and d_fd_range2freq[feat] > min_range_freq:
        #if d_feat.has_key(feat) and d_fd_range2freq[feat] > min_range_freq:
            # note that d_fd_range2freq[feat] doesn't seem to have any feats in it, so ignore it for now...
            # feature given entire range (marginal prob)
            l_retained_feats.append(feat)
            for year in range(start, range_end):
                str_year = str(year)
                fy_key = "^".join([feat, str_year])
                # actual prob for each feat
                if d_f2sum_tfy_in_range_over_terms[feat] > 0:
                    d_ygf_actual[fy_key] = d_fy2sum_tfy_over_terms[fy_key] / float(d_f2sum_tfy_in_range_over_terms[feat])
                else:
                    d_ygf_actual[fy_key] = 0
                if d_f2sum_tfy_in_range_over_terms[feat] > min_tfy_in_range:
                    print "actual prob of year: %i given feat %s: %f (sum_tfy-year: %i, sum_tfy-range: %i)" % (year, feat, d_ygf_actual[fy_key], d_fy2sum_tfy_over_terms[fy_key], d_f2sum_tfy_in_range_over_terms[feat]) 
                    # keep a list of actual probs sorted by year for the feature
                    d_l_ygf_actual[feat].append(d_ygf_actual[fy_key])

                    # for each feat, compute fraction of features in year / total # features in range
                    # multiply it by the proportion of terms in the year.
                    # d_ygf_expected[fy_key] = d_tgy[year] * (d_f2sum_tfy_in_range_over_terms[feat]) / float(sum_ty_in_range_over_terms)
                    # expectation is just based on the percentage of terms in each year
                    d_ygf_expected[fy_key] = d_tgy[year]
                    print "expected prob of year: %i given feat %s: %f (sum_ty-year: %i, sum_ty-range: %i)" % (year, feat, d_ygf_expected[fy_key], d_y2sum_ty_over_terms[year], sum_ty_in_range_over_terms) 
                    # keep a list of actual probs sorted by year for the feature
                    d_l_ygf_expected[feat].append(d_ygf_expected[fy_key])

                #pdb.set_trace()
    return([l_retained_feats, d_l_ygf_actual, d_l_ygf_expected])
        
# compute kl_div comparing actual and expected values
def feat_kl_div(l_retained_feats, d_l_ygf_actual, d_l_ygf_expected):

    # create a list of pairs: feature, kl_div, which we will later sort by kl_div
    l_kl = []
    l_diff = []
    diff_sign = ""

    for feat in l_retained_feats:
        l_feat_actual_probs = d_l_ygf_actual[feat]
        l_feat_expected_probs = d_l_ygf_expected[feat]
        kl_score = kl_div(l_feat_actual_probs, l_feat_expected_probs)
        # compute the difference in prob for each year
        l_diff = []
        diff_sign = ""
        for i in range(0, len(l_feat_actual_probs)):
            actual = l_feat_actual_probs[i]
            expected = l_feat_expected_probs[i]
            l_diff.append(actual - expected)
            if actual > expected:
                diff_sign += "+"
            else:
                diff_sign += "-"
        l_kl.append([feat, kl_score, l_diff, diff_sign])

    l_kl.sort(utils.list_element_2_sort)
    for (feat, kl_score, l_diff, diff_sign) in l_kl:

        if kl_score > 0:
            print "feat: %s, kl_div: %f, diff: %s" % (feat, kl_score, diff_sign)

# role.run_time_kl(d_term_year2freq, d_term_year2feats, d_term_feat_year2freq)
def run_time_kl(d_term_year2freq, d_term_year2feats, d_term_feat_year2freq):
    (l_retained_feats, d_l_ygf_actual, d_l_ygf_expected) = get_ypgf("ln-us-cs-500k", "patrick.61", 1997, 2007, d_term_year2freq, d_term_year2feats, d_term_feat_year2freq) 
    feat_kl_div(l_retained_feats, d_l_ygf_actual, d_l_ygf_expected)


############################################################
# To get a final set of features, we can filter the feature set based on raw freq and prob values:
# cat 1997.fc.prob.k6 | egrep -v '      1       ' | egrep -v '  2       '  | python /home/j/anick/patent-classifier/ontology/creation/fgt.py 5 .7 > 1997.fc.prob.fgt5_7
# cat 1997.fc.prob.fgt5_7| python /home/j/anick/patent-classifier/ontology/creation/fgt.py 6 .00001 > 1997.fc.prob.fgt5_7.fgt6_00001

# bash-4.1$ cat 1997.fc.prob.fgt5_7 | wc -l
#17993

# cat 1997.fc.prob.fgt5_7.fgt6_00001 | wc -l
#11324

# Before these steps, you need to run:
#sh run_term_features.sh which extracts the features of interest for each file in the source
# directories and puts them into a local directory (...corpus/term_root/<year>)

# tf => tfc, tc
# run several steps over a given range of years, starting with tf files
# role.run_tf_steps()


# NOTE:  there are different parameters for running pn vs act!!!
# cat_type: act, pn
# subset is either "" for processing act from .tf, or "a", or "t" for processing pn from a subset of
# .tf based on the output of act classification.

# role.run_tf_steps("ln-us-14-health", 1997, 1997, "pn", ["tc", "tcs", "fc", "uc", "prob"])
# role.run_tf_steps("ln-us-14-health", 1997, 1997, "act", ["tc", "tcs", "fc", "uc", "prob"])
# role.run_tf_steps("ln-us-cs-500k", 1997, 1997, "act", ["tf", "tc", "tcs", "fc", "uc", "prob"])
# role.run_tf_steps("ln-us-cs-500k", 1997, 1997, "act", ["tc", "tcs", "fc", "uc", "prob"])
# role.run_tf_steps("ln-us-cs-500k", 1997, 1997, "act", ["tcs", "fc", "uc", "prob"])
# role.run_tf_steps("ln-us-cs-500k", 1997, 1997, "act", ["uc",  "prob"])
# role.run_tf_steps("ln-us-cs-500k", 1997, 1997, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")
# role.run_tf_steps("ln-us-all-600k", 1997, 1997, "act", ["tc", "tcs", "fc", "uc", "prob"], "")
# role.run_tf_steps("ln-us-all-600k", 1997, 1997, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")

# role.run_tf_steps("ln-us-14-health", 1997, 1997, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")
# role.run_tf_steps("ln-us-14-health", 2002, 2002, "act", ["tf", "tc", "tcs", "fc", "uc", "prob"], "")
# role.run_tf_steps("ln-us-all-600k", 2002, 2002, "act", ["tf"], "")

# role.run_tf_steps("ln-us-14-health", 2002, 2002, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")

# role.run_tf_steps("ln-us-cs-500k", 1997, 1997, "act", ["tf"])
# role.run_tf_steps("ln-us-cs-500k", 2007, 2007, "act", ["tf"])
# role.run_tf_steps("ln-us-cs-500k", 2002, 2002, "pn", ["prob"], "a")

# role.run_tf_steps("ln-us-12-chemical", 1997, 1997, "act", ["tf", "tc", "tcs", "fc", "uc", "prob"], "")
# role.run_tf_steps("ln-us-14-health", 1997, 1997, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")

# role.run_tf_steps("wos-cs-520k", 1997, 1997, "act", ["tf", "tc", "tcs", "fc", "uc", "prob"], "")

# role.run_tf_steps("ln-us-cs-500k", 1999, 1999, "act", ["tf"], "")
# role.run_tf_steps("ln-us-cs-500k", 1998, 2007, "act", ["tc", "tcs", "fc", "uc", "prob"], "")
# role.run_tf_steps("ln-us-all-600k", 1998, 2007, "act", ["tf"], "")

# 2014 07/05
# rerunning with adjusted initial feature seed sets
# role.run_tf_steps("ln-us-cs-500k", 2002, 2002, "act", ["tc", "tcs", "fc", "uc", "prob"])
# role.run_tf_steps("ln-us-14-health", 2002, 2002, "act", ["tc", "tcs", "fc", "uc", "prob"])

# 2014 08/19 new domains added
# role.run_tf_steps("ln-us-A27-molecular-biology", 2002, 2002, "act", ["tc", "tcs", "fc", "uc", "prob"])

# note: tf removed from todo_list.  This should be done beforehand by tf.py to create the
# .tf, .terms, .feats, .cs files for a year range
def run_tf_steps(corpus, start, end, cat_type="act", todo_list=[ "tc", "tcs", "fc", "uc", "prob"], subset=""):

    # tv_subpath
    tv_subpath = "/data/tv"
    # term_subpath
    term_subpath = "/data/term_features"

    #tv_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #tv_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    #tv_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-12-chemical/data/tv"
    #tv_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv"
    # small test set
    #tv_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/test/data/tv"

    # category r and n are useful but overlap with other cats.  Better to work with them separately.
    #cat_list = ["a", "b", "c", "p", "t", "o"]
    # moved the abcopt results to tv_abcopt
    # There are few significant features that specifically select for p and b.  So let's remove them as well.
    #cat_list = ["a", "c", "t", "o"]

    # We only use term_root and tv_root for the .tf step, which uses two directories
    term_root = corpus_root + corpus + term_subpath
    tv_root = corpus_root + corpus + tv_subpath
    # the .tf file (and .tf.a subset)  will be the same for all classifiers
    tf_root = tv_root

    # use subdirectories for classifying into act categories
    # This is a bit of a hack.  We need a place to put data for different classification tasks, so we 
    # create directories of tv, where we put the default data for classification into acot classes.
    fcat_file = ""
    cat_list = []
    if cat_type == "act":
        fcat_file = code_root + "/seed." + cat_type + ".en.dat"
        cat_list = ["a", "c", "t"]
    elif cat_type == "pn":
        fcat_file = "/home/j/anick/patent-classifier/ontology/creation/seed." + cat_type + ".en.dat"
        cat_list = ["p", "n"]

    # Be safe, check if tv_root path exists, and create it if not
    if not os.path.exists(tv_root):
        os.makedirs(tv_root)
        print "Created outroot dir: %s" % tv_root

    print "[run_tf_steps]tv_root: %s, fcat_file: %s, cat_list: %s" % (tv_root, fcat_file, cat_list)
    outroot = tv_root    
    #start_year = 1997
    #end_year = 1997
    start_year = int(start)
    end_year = int(end)

    #end parameters section
    start_range = start_year
    end_range = end_year + 1

    # steps
    # from xml phr_feats files in /term_features/<year>, create <year>.tf in /tv

    #pnames.tv_filepath(corpus_root, corpus, year, file_type, subset, cat_type="")
    if "tf" in todo_list:    
        if cat_type == "pn":
            print "[run_tf_steps]ERROR: You shouldn't use the tf step if cat_type is pn. a.tf and .t.tf files should already exist."
            quit
        else: 
            print "[run_tf_steps]Creating .tf, .terms, .feats"
            run_dir2features_count(term_root, tv_root, start_range, end_range)
    if "tc" in todo_list:
        # from .tf, create .tc, .tfc
        # tc: term cat
        # tfc: term frequency category
        print "[run_tf_steps]Creating .tc, .tfc"
        run_tf2tfc(corpus_root, corpus, start_range, end_range, fcat_file, cat_list, cat_type, subset)
    if "tcs" in todo_list:
        # from .tc, create .tcs
        print "[run_tf_steps]Creating .tcs"
        run_tc2tcs(corpus_root, corpus, start_range, end_range, cat_type, subset)
    if "fc" in todo_list:
        # from .tcs and .tf, create .fc
        print "[run_tf_steps]Creating .fc"
        run_tcs2fc(corpus_root, corpus, start_range, end_range, cat_type, subset)
    if "uc" in todo_list:
        # from .fc, create .fc_uc
        print "[run_tf_steps]Creating .fc_uc"
        arglist = corpus_root + " " + corpus + " " + str(start_year) + " " + str(end_year) + " " + cat_type + " " + subset
        bashCommand = "sh run_fc2fcuc.sh " + arglist 
        os.system(bashCommand)
    
    if "prob" in todo_list:
        print "[run_tf_steps]Creating .fc_prob, fc_cat_prob and .fc_kl"
        run_fcuc2fcprob(corpus_root, corpus, start_range, end_range, cat_list, cat_type, subset)

    print "[run_tf_steps]Completed"
    
