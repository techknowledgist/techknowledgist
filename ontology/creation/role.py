# role.py
# rewrite of term_verb_count focusing on role detection rather than mutual information

# directory structure
# /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/act
# <root>/<corpus>/data/tv
#   <year>.tf, terms, feats
#   <year>.<act|pn>.tfc, tc, tcs, fc, fc_uc, fc_prob, fc_cat_prob, fc_kl, 
#   <year>.<act|pn>.cat.w<cutoff>.a, c, t, p, n

# TODO: add codecs to all writes

import pdb
import re
import glob
import os
import sys
import log
import math
import collections
from collections import defaultdict
import codecs
import utils

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
def tv_filepath(corpus_root, corpus, year, file_type, subset, cat_type=""):
    # check for illegal parameter values
    # note: for file_type, we allow values of the form "cat.<cutoff>"
    if file_type not in ["tf", "cat", "cat_prob", "fc", "fc_kl", "fc_prob", "fc_uc", "tc", "tcs", "tfc", "feats", "terms"] and not file_type[0:5] == "cat.w":
        print "[tv_filepath]ERROR: unknown file type: %s" % file_type
        quit
    if subset not in ["", "a", "t", "c"]:
        # note: subset can be empty string
        print "[tv_filepath]ERROR: unknown subset: %s" % subset
        quit
    if cat_type not in ["", "pn", "act"]:
        print "[tv_filepath]ERROR: unknown cat_type: %s" % cat_type
        quit
    tv_subpath = "/data/tv/"
    # make sure we don't create double slashes in the name
    if corpus_root[-1] != "/":
        corpus_root += "/"
    if cat_type != "":
        cat_type = "." + cat_type
    if subset != "":
        subset = "." + subset
    full_filename = corpus_root + corpus + tv_subpath + str(year) + subset + cat_type + "." + file_type
    print "[tv_filepath]file: %s" % full_filename
    return(full_filename)

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


#----
# from individual term features files, create a summary file per year
# with the freq of the term feature combination  (.tf)
# NOTE: alpha filter does not apply to Chinese.  Removed for now.

# 2/27/14 PGA added code to count terms and feats and write out their counts 
# in separate files (.terms, .feats)

def dir2features_count(inroot, outroot, year):
    outfilename = str(year)
    # term-feature output file
    outfile = outroot + "/" + outfilename + ".tf"
    terms_file = outroot + "/" + outfilename + ".terms"
    feats_file = outroot + "/" + outfilename + ".feats"

    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    # count of number of docs a term occurs in
    d_term_freq = collections.defaultdict(int)
    # count of number of instances of a term
    d_term_instance_freq = collections.defaultdict(int)
    # count of number of instances of a feature
    d_feat_instance_freq = collections.defaultdict(int)
    # count of number of docs a feature occurs in
    d_feat_freq = collections.defaultdict(int)

    # Be safe, check if outroot path exists, and create it if not
    if not os.path.exists(outroot):
        os.makedirs(outroot)
        print "Created outroot dir: %s" % outroot

    # doc_count needed for computing probs
    doc_count = 0

    # make a list of all the files in the inroot directory
    filelist = glob.glob(inroot + "/*")
    #print "inroot: %s, filelist: %s" % (inroot, filelist)
    
    for infile in filelist:

        # process the term files
        # for each file, create a set of all term-feature pairs in the file
        pair_set = set()
        term_set = set()
        feature_set = set()
        s_infile = codecs.open(infile, encoding='utf-8')
        for term_line in s_infile:
            term_line = term_line.strip("\n")
            l_fields = term_line.split("\t")
            term = l_fields[0]
            feature = l_fields[1]
            term_feature_within_doc_count = int(l_fields[2])
            #print "term: %s, feature: %s" % (term, feature)

            """
            # filter out non alphabetic phrases, noise terms
            if alpha_phrase_p(term):
                pair = term + "\t" + feature
                print "term matches: %s, pair is: %s" % (term, pair)
                pair_set.add(pair)
            """

            # if the feature field is "", then we use this line to count term
            # instances
            if feature == "":
                d_term_instance_freq[term] += term_feature_within_doc_count
                # add term to set for this document to accumulate term-doc count
                term_set.add(term)
                # note:  In ln-us-cs-500k 1997.tf, it appears that one term (e.g. u'y \u2033')
                # does not get added to the set.  Perhaps the special char is treated as the same
                # as another term and therefore is excluded from the set add.  As a result
                # the set of terms in d_term_freq may be missing some odd terms that occur in .tf.
                # Later will will use terms from .tf as keys into d_term_freq, so we have to allow for
                # an occasional missing key at that point (in nbayes.py)
            else:
                # the line is a term_feature pair
                # alpha filter removed to handle chinese
                pair = term + "\t" + feature
                ##print "term matches: %s, pair is: %s" % (term, pair)
                pair_set.add(pair)
                feature_set.add(feature)
                d_feat_instance_freq[feature] += term_feature_within_doc_count
                
        s_infile.close()

        # increment the doc_freq for term-feature pairs in the doc
        # By making the list a set, we know we are only counting each term-feature combo once
        # per document
        for pair in pair_set:
            d_pair_freq[pair] += 1
            
        # also increment doc_freq for features and terms
        
        for term in term_set:
            d_term_freq[term] +=1

        for feature in feature_set:
            d_feat_freq[feature] += 1

        # track total number of docs
        doc_count += 1

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    s_terms_file = codecs.open(terms_file, "w", encoding='utf-8')
    s_feats_file = codecs.open(feats_file, "w", encoding='utf-8')
    print "Writing to %s" % outfile

    # compute prob
    print "Processed %i files" % doc_count

    for pair in d_pair_freq.keys():
        pair_prob = float(d_pair_freq[pair])/doc_count
        l_pair = pair.split("\t")
        term = l_pair[0]
        #print "term after split: %s, pair is: %s" % (term, pair)
        feature = l_pair[1]
        s_outfile.write( "%s\t%s\t%i\t%f\n" % (term, feature, d_pair_freq[pair], pair_prob))

    for term in d_term_freq.keys():
        term_prob = float(d_term_freq[term])/doc_count
        s_terms_file.write( "%s\t%i\t%i\t%f\n" % (term, d_term_freq[term], d_term_instance_freq[term], term_prob))

    for feat in d_feat_freq.keys():
        feat_prob = float(d_feat_freq[feat])/doc_count
        s_feats_file.write( "%s\t%i\t%i\t%f\n" % (feat, d_feat_freq[feat], d_feat_instance_freq[feat], feat_prob))

    s_outfile.close()
    s_terms_file.close()
    s_feats_file.close()


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
    infile = tv_filepath(corpus_root, corpus, year, "tf" , subset, "")
    """
    if subset != "":
        infile = infile + "." + subset
    """

    #tc_file = outroot + "/" + year_cat_name + ".tc"
    tc_file = tv_filepath(corpus_root, corpus, year, "tc" , subset, cat_type)
    #tfc_file = outroot + "/" + year_cat_name + ".tfc"
    tfc_file = tv_filepath(corpus_root, corpus, year, "tfc" , subset, cat_type)

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
# with highest probability and ignoring cases where the freq of the term feature pair >= min_pair_freq
def tc2tcs(corpus_root, corpus, year, min_prob, min_pair_freq, cat_type, subset):
    # the tc means "term-category" 
    #infile = inroot + "/" + year_cat_name + ".tc"
    infile = tv_filepath(corpus_root, corpus, year, "tc", subset, cat_type)
    #outfile = outroot + "/" + year_cat_name + ".tcs"
    tcs_file = tv_filepath(corpus_root, corpus, year, "tcs", subset, cat_type)


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
    seed_file = tv_filepath(corpus_root, corpus, year, "tcs", subset, cat_type)
    #term_feature_file = inroot + "/" + str(year) + ".tf"
    # recall use "" for cat_type for .tf file
    term_feature_file = tv_filepath(corpus_root, corpus, year, "tf", subset, "")
    #outfile = outroot + "/" + year_cat_name + ".fc"
    fc_file = tv_filepath(corpus_root, corpus, year, "fc", subset, cat_type)
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
    # accumulate freq for each category
    d_cat_freq = collections.defaultdict(int)
    # accumulate freq for each feature
    d_feature_freq = collections.defaultdict(int)
    # overall prob for each category
    d_cat_prob = collections.defaultdict(int)
    # we will need a list of overall probs for input into kl_div
    cat_prob_list = []
    # capture the number of labeled instances to compute prior prob for each category
    instance_freq = 0
    smoothing_parameter = 1
    min_feature_freq = 10

    ##infile = inroot + "/" + year_cat_name + ".fc_uc"
    infile = tv_filepath(corpus_root, corpus, year, "fc_uc", subset, cat_type)
    # output file to store prob of category given the term
    ##prob_file = outroot + "/" + year_cat_name + ".fc.prob"
    prob_file = tv_filepath(corpus_root, corpus, year, "fc_prob", subset, cat_type)
    # output file to store prior probs of each category
    ##cat_prob_file = outroot + "/" + year_cat_name + ".fc.cat_prob"
    cat_prob_file = tv_filepath(corpus_root, corpus, year, "cat_prob", subset, cat_type)

    s_cat_prob_file = codecs.open(cat_prob_file, "w", encoding='utf-8')

    #kl_file = outroot + "/" + year_cat_name + ".fc.kl"
    kl_file = tv_filepath(corpus_root, corpus, year, "fc_kl", subset, cat_type)
    s_kl_file = codecs.open(kl_file, "w", encoding='utf-8')

    # process the pairs
    cat_set = set()
    feature_set = set()
    pair_set = set()

    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
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
        d_cat_freq[cat] += count
        d_feature_freq[feature] += count
        d_pair_freq[pair] += count
        instance_freq += count

    s_infile.close()

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
            fgc_prob = float(d_pair_freq[pair] + smoothing_parameter) / float(d_cat_freq[cat] + (smoothing_parameter * num_features))
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
def run_tf_steps(corpus, start, end, cat_type="act", todo_list=["tf", "tc", "tcs", "fc", "uc", "prob"], subset=""):
    #parameters
    code_root = "/home/j/anick/patent-classifier/ontology/creation/"
    # path to corpus
    corpus_root = code_root + "data/patents/"
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

    #tv_filepath(corpus_root, corpus, year, file_type, subset, cat_type="")
    if "tf" in todo_list:    
        if cat_type == "pn":
            print "[run_tf_steps]ERROR: You shouldn't use the tf step if cat_type is pn. a.tf and .t.tf files should already exist."
            quit
        else: 
            print "[run_tf_steps]Creating .tf, .terms, .feats"
            run_dir2features_count(term_root, tv_root, start_range, end_range)
    if "tc" in todo_list:
        # from .tf, create .tc, .tfc
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
        print "[run_tf_steps]Creating .fc.prob and .fc.kl"
        run_fcuc2fcprob(corpus_root, corpus, start_range, end_range, cat_list, cat_type, subset)

    print "[run_tf_steps]Completed"
    
