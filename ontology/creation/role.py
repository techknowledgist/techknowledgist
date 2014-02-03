# role.py
# rewrite of term_verb_count focusing on role detection rather than mutual information

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

def dir2features_count(inroot, outroot, year):
    outfilename = str(year)
    # term-feature output file
    outfile = outroot + "/" + outfilename + ".tf"

    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)

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
        s_infile = codecs.open(infile, encoding='utf-8')
        for term_line in s_infile:
            term_line = term_line.strip("\n")
            l_fields = term_line.split("\t")
            term = l_fields[0]
            feature = l_fields[1]
            #print "term: %s, feature: %s" % (term, feature)

            """
            # filter out non alphabetic phrases, noise terms
            if alpha_phrase_p(term):
                pair = term + "|" + feature
                print "term matches: %s, pair is: %s" % (term, pair)
                pair_set.add(pair)
            """

            # alpha filter removed to handle chinese
            pair = term + "|" + feature
            ##print "term matches: %s, pair is: %s" % (term, pair)
            pair_set.add(pair)

                
        s_infile.close()

        # increment the doc_freq for term-feature pairs in the doc
        # By making the list a set, we know we are only counting each term-feature combo once
        # per document
        for pair in pair_set:
            d_pair_freq[pair] += 1
            
        # track total number of docs
        doc_count += 1

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    print "Writing to %s" % outfile

    # compute prob
    print "Processed %i files" % doc_count
    d_mi = defaultdict(int)
    for pair in d_pair_freq.keys():
        pair_prob = float(d_pair_freq[pair])/doc_count
        l_pair = pair.split("|")
        term = l_pair[0]
        #print "term after split: %s, pair is: %s" % (term, pair)
        feature = l_pair[1]

        s_outfile.write( "%s\t%s\t%i\t%f\n" % (term, feature, d_pair_freq[pair], pair_prob))

    s_outfile.close()

# convert term feature (.tv) info to term category info (.tc)
# also create .tfc (term, feature, cat)
def tf2tfc(inroot, outroot, year, fcat_file, cat_list):
    yearfilename = str(year)
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    d_term_freq = collections.defaultdict(int)
    d_feature_freq = collections.defaultdict(int)
    
    d_feature2cat = {}
    # the tc means "term-category" 
    infile = inroot + "/" + yearfilename + ".tf"
    outfile = outroot + "/" + yearfilename + ".tc"
    tfc_file = outroot + "/" + yearfilename + ".tfc"

    # Be safe, check if outroot path exists, and create it if not
    if not os.path.exists(outroot):
        os.makedirs(outroot)
        print "Created outroot dir: %s" % outroot

    # load the feature categories for fcat_file
    s_fcat_file = open(fcat_file)
    for line in s_fcat_file:
        line = line.strip()
        #print "line: %s\n" % line
        l_fields = line.split("\t")
        fcat = l_fields[0]
        feature = l_fields[1]
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
        term_set = set()
        feature_set = set()
        pair_set = set()
        s_infile = codecs.open(infile, encoding='utf-8')
        # check if the feature has a category
        # and replace it with the category.
        # Otherwise ignore this pair.
        if d_feature2cat.has_key(feature):
            cat = d_feature2cat[feature]
            s_tfc_file.write("%s\t%s\t%s\t%i\n" % (term, feature, cat, count))
            term_set.add(term)
            feature_set.add(feature)
            pair = term + "|" + cat
            pair_set.add(pair)
                
        s_infile.close()

        # increment the doc_freq for terms and verbs in the doc
        # By making the list a set, we know we are only counting each term or verb once
        # per document
        for term in term_set:
            d_term_freq[term] += count

        for feature in feature_set:
            d_feature_freq[feature] += count
            #print "d_verb_freq for %s: %i" % (verb, d_verb_freq[verb])

        for pair in pair_set:
            d_pair_freq[pair] += count

    s_tfc_file.close()
    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    
    for pair in d_pair_freq.keys():
        l_pair = pair.split("|")
        term = l_pair[0]
        cat = l_pair[1]
        prob = float(d_pair_freq[pair]) / float(d_term_freq[term])
        
        s_outfile.write( "%s\t%s\t%i\t%i\t%f\n" % (term, cat,  d_pair_freq[pair], d_term_freq[term], prob))

    else:
        pass
        #print "omitting: %s, %s" % (term1, term2)
    s_outfile.close()

# generate a set of term category "seeds" for learning new diagnostic features
# .tc is of the form:
# acoustic devices        c       2       2       1.000000
# As long as min_prob > .5, there will be one cat output for each term.  We are simply choosing the one
# with highest probability and ignoring cases where the freq of the term feature pair >= min_pair_freq
def tc2tcs(inroot, outroot, year, min_prob, min_pair_freq):
    # the tc means "term-category" 
    infile = inroot + "/" + year + ".tc"
    outfile = outroot + "/" + year + ".tcs"

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')

    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[1]
        pair_count = int(l_fields[2])
        prob = float(l_fields[4])

        if pair_count >= min_pair_freq and prob >= min_prob:
            s_outfile.write("%s\t%s\t%i\t%f\n" % (term, cat, pair_count, prob))

    s_infile.close()
    s_outfile.close()

# labels features found in .tf file with the category
# associated with any known seed term (in .tcs file)
def tcs2fc(inroot, outroot, year):
    seed_file = inroot + "/" + year + ".tcs"
    term_feature_file = inroot + "/" + year + ".tf"
    outfile = outroot + "/" + year + ".fc"
    d_seed = {}

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')

    # read in all the seeds and their categories
    s_seed_file = codecs.open(seed_file, encoding='utf-8')
    for line in s_seed_file:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[1]
        d_seed[term] = cat

    s_seed_file.close()

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
            s_outfile.write("%s\t%s\n" % (feature, cat))
            #s_outfile.write("%s\t%s\t%s\t%s\n" % (feature, cat, term, count))

    s_outfile.close()

# convert feature category count (.fcuc) info to feature category prob info (.fcprob)
def fcuc2fcprob(inroot, outroot, year):
    yearfilename = str(year)
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    d_cat_freq = collections.defaultdict(int)
    d_feature_freq = collections.defaultdict(int)
    # capture the number of labeled instances to compute prior prob for each category
    instance_freq = 0

    infile = inroot + "/" + yearfilename + ".fc.uc"
    outfile = outroot + "/" + yearfilename + ".fc.prob"
    # output file to store prior probs of each category
    cat_prob_file = outroot + "/" + yearfilename + ".fc.cat_prob"
    s_cat_prob_file = codecs.open(cat_prob_file, "w", encoding='utf-8')

    # Be safe, check if outroot path exists, and create it if not
    if not os.path.exists(outroot):
        os.makedirs(outroot)
        print "Created outroot dir: %s" % outroot

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
        pair = cat + "|" + feature
        pair_set.add(pair)

        # increment the doc_freq for cats and features in the doc
        # By making the pair list a set (above), we know we are only counting each cat or feature once
        # per document
        d_cat_freq[cat] += count
        d_feature_freq[feature] += count
        d_pair_freq[pair] += count
        instance_freq += count

    s_infile.close()

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')

    for pair in d_pair_freq.keys():
        l_pair = pair.split("|")
        cat = l_pair[0]
        feature = l_pair[1]
        # prob of category given the feature
        cgf_prob = float(d_pair_freq[pair]) / float(d_feature_freq[feature])
        # prob of feature given the category
        fgc_prob = float(d_pair_freq[pair]) / float(d_cat_freq[cat])

        s_outfile.write("%s\t%s\t%i\t%i\t%f\t%f\n" % (feature, cat,  d_pair_freq[pair], d_feature_freq[feature], cgf_prob, fgc_prob))

    else:
        pass
        #print "omitting: %s, %s" % (term1, term2)
    
    for cat in d_cat_freq.keys():
        cat_prob = float(d_cat_freq[cat]) / float(instance_freq)
        s_cat_prob_file.write("%s\t%i\t%f\n" % (cat, d_cat_freq[cat],  cat_prob))

    s_outfile.close()
    s_cat_prob_file.close()

# This doesn't work for Chinese because it filters out term wutg non-alphabest characters
# using an ascii fitler
def dir2tfc(term_uc_year_file, term_cat_year_file, out_year_file):
    d_term2cat = {}
    s_uc = codecs.open(term_uc_year_file, encoding='utf-8')
    s_vc = codecs.open(term_cat_year_file, encoding='utf-8')
    s_tfc = codecs.open(out_year_file, "w", encoding='utf-8')
        
    # for each term with a cat, store its primary cat and cat_freq in a dictionary
    for line in s_vc:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[1]
        cat_freq = l_fields[2]
        d_term2cat[term] = [cat, cat_freq]

    for line in s_uc:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        uc = l_fields[1]

        #if the term is in the uc dictionary, output a line
        # note that terms in .uc have to exceed a threshold of within doc freq,
        # whereas the terms in .vc do not.  The latter occur in verbal contexts.
        # If there is no entry for the term in d_term2cat, we give it the category "u" for unknown.
        # Also, pre-filter any terms with non-alpha characters to weed out a lot of noise.
        if alpha_phrase_p(term):
            if d_term2cat.has_key(term):
                (cat, cat_freq) = d_term2cat[term]
            else:
                cat = "u"
                cat_freq = "0"

            output_line = "\t".join([term, cat, uc, cat_freq])
            s_tfc.write("%s\n" % output_line)

    s_uc.close()
    s_vc.close()
    s_tfc.close()
# create .tfc from .uc and .vc data
# role.run_dir2tfc()
def run_dir2tfc():

    term_cat_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"
    term_uc_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_mi_tas"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"
    print "Output dir: %s" % outroot

    # range should be start_year and end_year + 1
    #for int_year in range(1981, 2008):
    for int_year in range(1995, 2008):
    #for int_year in range(1995, 1996):
    
        year = str(int_year)
        term_uc_year_file = term_uc_root + "/" + year + ".uc"
        term_cat_year_file = term_cat_root + "/" + year + ".vc"
        out_year_file = outroot  + "/" + year + ".tfc"

        print "Processing input: %s, %s.  Output: %s" % (term_uc_year_file, term_cat_year_file, out_year_file)

        dir2tfc(term_uc_year_file, term_cat_year_file, out_year_file)
        print "Completed: %s" % out_year_file

#---
# Create a single file of term feature count for each year (from the .xml extracts of phr_feats data)
# role.run_dir2features_count()
def run_dir2features_count():
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb_tas"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"

    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k/data/tv"

    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/term_features"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-cn-all-600k/data/term_features"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-cn-all-600k/data/tv"

    print "Output dir: %s" % outroot

    # range should be start_year and end_year + 1
    #for int_year in range(1981, 2008):
    #for int_year in range(1995, 2008):
    #for int_year in range(1997, 1998):
    for int_year in range(1997, 1998):
    
        year = str(int_year)
        inroot_year = inroot + "/" + year
        print "Processing dir: %s" % inroot_year

        dir2features_count(inroot_year, outroot, year)
        print "Completed: %s" % year

# term feature to term feature category for terms whose feature appears in our seed list
# role.run_tf2tfc()
def run_tf2tfc(inroot, outroot, start_range, end_range, fcat_file, cat_list):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"

    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    #outroot = inroot

    #fcat_file = "/home/j/anick/patent-classifier/ontology/creation/feature.cat.en.dat"
    #fcat_file = "/home/j/anick/patent-classifier/ontology/creation/seed.cat.en.dat"

    # category r and n are useful but overlap with other cats.  Better to work with them separately.
    #cat_list = ["a", "b", "c", "p", "t", "o"]

    #for int_year in range(1997, 1998):
    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_tf2tfc]Processing dir: %s" % year

        # cat_list allows discretion over the category set
        tf2tfc(inroot, outroot, year, fcat_file, cat_list)
        print "[run_tf2tfc]Completed: %s.tc in %s" % (year, outroot)

"""
# term category to seed terms
# role.run_tc2tcs()
def run_tc2tcs(inroot, outroot, start_range, end_range):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"

    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"

    min_prob = .6
    min_pair_freq = 2

    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_tc2st]Processing dir: %s" % year

        tc2tcs(inroot, outroot, year, min_prob, min_pair_freq)
        print "[run_tc2st]Completed: %s.st in %s" % (year, outroot)

"""

# term category to seed terms
# role.run_tc2tcs()
def run_tc2tcs(inroot, outroot, start_range, end_range):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    #outroot = inroot

    min_prob = .7
    min_pair_freq = 2

    #for int_year in range(1997, 1998):
    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_tc2tcs]Processing dir: %s" % year

        tc2tcs(inroot, outroot, year, min_prob, min_pair_freq)
        print "[run_tc2tcs]Completed: %s.st in %s" % (year, outroot)

# use the seed terms to create a file of feature category pairs.  That is, for
# each line containing a seed term, replace it with the category.
# role.run_tcs2fc()
def run_tcs2fc(inroot, outroot, start_range, end_range):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    #outroot = inroot

    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_tcs2fc]Processing dir: %s" % year

        tcs2fc(inroot, outroot, year)
        print "[run_tcs2fc]Completed: %s.fc in %s" % (year, outroot)


# Generate probability for each feature cat combination
# Input file is the result of a uc on the .fc file
# First run:
#      sh run_fc2fcuc.sh

# role.run_fcuc2fcprob()
def run_fcuc2fcprob(inroot, outroot, start_range, end_range):
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    #outroot = inroot

    for int_year in range(start_range, end_range):
    
        year = str(int_year)
        print "[run_fcuc2fcprob]Processing dir: %s" % year

        fcuc2fcprob(inroot, outroot, year)
        print "[run_fcuc2fcprob]Completed: %s.fc in %s" % (year, outroot)

# To get a final set of features, we can filter the feature set based on raw freq and prob values:
# cat 1997.fc.prob.k6 | egrep -v '      1       ' | egrep -v '  2       '  | python /home/j/anick/patent-classifier/ontology/creation/fgt.py 5 .7 > 1997.fc.prob.fgt5_7
# cat 1997.fc.prob.fgt5_7| python /home/j/anick/patent-classifier/ontology/creation/fgt.py 6 .00001 > 1997.fc.prob.fgt5_7.fgt6_00001

# bash-4.1$ cat 1997.fc.prob.fgt5_7 | wc -l
#17993

# cat 1997.fc.prob.fgt5_7.fgt6_00001 | wc -l
#11324

# tf => tfc, tc
# run several steps over a given range of years, starting with tf files
# role.run_tf_steps()
def run_tf_steps():
    #parameters
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    outroot = inroot    
    start_year = 1997
    end_year = 2007

    fcat_file = "/home/j/anick/patent-classifier/ontology/creation/seed.cat.en.dat"

    # category r and n are useful but overlap with other cats.  Better to work with them separately.
    #cat_list = ["a", "b", "c", "p", "t", "o"]
    # moved the abcopt results to tv_abcopt
    # There are few significant features that specifically select for p and b.  So let's remove them as well.
    cat_list = ["a", "c", "t", "o"]

    #end parameters section
    start_range = start_year
    end_range = end_year + 1

    run_tf2tfc(inroot, outroot, start_range, end_range, fcat_file, cat_list)
    # next line no longer needed
    ###run_tc2st(inroot, outroot, start_range, end_range)
    run_tc2tcs(inroot, outroot, start_range, end_range)

    run_tcs2fc(inroot, outroot, start_range, end_range)

    arglist = inroot + " " + str(start_year) + " " + str(end_year)
    bashCommand = "sh run_fc2fcuc.sh " + arglist 
    os.system(bashCommand)
    print "[run_fc2fcuc.sh]Completed"

    run_fcuc2fcprob(inroot, outroot, start_range, end_range)
