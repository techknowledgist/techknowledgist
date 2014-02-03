# term_verb_count.py
# compute mutual information for a set of files of the form
# <term>\t<count>
# as created by m1_term_counts.sh

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

"""
# This is the original version without code to handle vcat
def dir2mi(inroot, outroot, year):
    outfilename = str(year)
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    d_term_freq = collections.defaultdict(int)
    d_verb_freq = collections.defaultdict(int)
    outfile = outroot + "/" + outfilename + ".mi"

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
        term_set = set()
        verb_set = set()
        pair_set = set()
        s_infile = codecs.open(infile, encoding='utf-8')
        for term_line in s_infile:
            term_line = term_line.strip("\n")
            l_fields = term_line.split("\t")
            term = l_fields[0]
            verb = l_fields[1]
            #print "term: %s, verb: %s" % (term, verb)
            # filter out non alphabetic phrases, noise terms
            if alpha_phrase_p(term):
                #print "term matches: %s" % term
                term_set.add(term)
                verb_set.add(verb)
                pair = term + "|" + verb
                # increment the doc freq for the pair
                # Note the pairs are already unique within the file,
                # so we don't need to worry about removing duplicates.
                d_pair_freq[pair] += 1

                
        s_infile.close()

        # increment the doc_freq for terms and verbs in the doc
        # By making the list a set, we know we are only counting each term or verb once
        # per document
        for term in term_set:
            d_term_freq[term] += 1

        for verb in verb_set:
            d_verb_freq[verb] += 1
            #print "d_verb_freq for %s: %i" % (verb, d_verb_freq[verb])

        # track total number of docs
        doc_count += 1

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    
    # compute probs and mi
    print "Processed %i files" % doc_count
    d_mi = defaultdict(int)
    for pair in d_pair_freq.keys():
        l_pair = pair.split("|")
        term1 = l_pair[0]
        term2 = l_pair[1]
        
        term1_prob = float(d_term_freq[term1])/doc_count
        term2_prob = float(d_verb_freq[term2])/doc_count

        pair_prob = float(d_pair_freq[pair])/doc_count
        # compute normalized pmi
        # Check for odd cases where a term prob of 0 arises
        # It shouldn't happen but it does
        denom = term1_prob * term2_prob
        if denom == 0:
            #print "0 probability for term1: [%s, %f] or term2: [%s, %s]" % (term1, term1_prob, term2, term2_prob)
            pass
        else:
            pmi = math.log(pair_prob/(term1_prob * term2_prob),2)
            norm_pmi = pmi / (-1 * math.log(pair_prob, 2))
            d_mi[pair] = norm_pmi

            # compute npmi * log(freq)
            fpmi = norm_pmi * math.log(d_pair_freq[pair], 2)
            #print "npmi for %s: %f, freq: %i, %i, %i" % (pair, norm_pmi, d_pair_freq[pair], d_term_freq[term1], d_verb_freq[term2])
            s_outfile.write( "%s\t%s\t%f\t%f\t%i\t%i\t%i\n" % (term1, term2, fpmi, norm_pmi, d_pair_freq[pair], d_term_freq[term1], d_verb_freq[term2]))

    else:
        pass
        #print "omitting: %s, %s" % (term1, term2)
    s_outfile.close()
"""

# We use the same function to compute mi for term-verb pairs
# as for term-category pairs.  To do the latter, vcat_p should 
# be True and a vcat_file supplied.
# NOTE: The alpha filter does not work for Chinese!

def dir2mi(inroot, outroot, year, vcat_p=False, vcat_file=""):
    outfilename = str(year)
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    d_term_freq = collections.defaultdict(int)
    d_verb_freq = collections.defaultdict(int)
    # if vcat_p == True, map verbs to categories using this dict
    d_verb2cat = {}
    if vcat_p:
        # the tc means "term-category" mutual information
        outfile = outroot + "/" + outfilename + ".tcmi"
    else:
        # term-verb output file
        outfile = outroot + "/" + outfilename + ".mi"

    # Be safe, check if outroot path exists, and create it if not
    if not os.path.exists(outroot):
        os.makedirs(outroot)
        print "Created outroot dir: %s" % outroot

    if vcat_p:
        # load the verb categories for vcat_file
        s_vcat_file = open(vcat_file)
        for line in s_vcat_file:
            line = line.strip()
            #print "line: %s\n" % line
            l_fields = line.split("\t")
            vcat = l_fields[0]
            verb = l_fields[1]
            d_verb2cat[verb] = vcat

        s_vcat_file.close()

    # doc_count needed for computing probs
    doc_count = 0

    # make a list of all the files in the inroot directory
    filelist = glob.glob(inroot + "/*")
    #print "inroot: %s, filelist: %s" % (inroot, filelist)
    
    for infile in filelist:

        # process the term files
        term_set = set()
        verb_set = set()
        pair_set = set()
        s_infile = codecs.open(infile, encoding='utf-8')
        for term_line in s_infile:
            term_line = term_line.strip("\n")
            l_fields = term_line.split("\t")
            term = l_fields[0]
            verb = l_fields[1]
            #print "term: %s, verb: %s" % (term, verb)

            # if we are 

            # filter out non alphabetic phrases, noise terms
            if alpha_phrase_p(term):
                #print "term matches: %s" % (term)

                if vcat_p:
                    # check if the verb has a category
                    # and replace it with the category.
                    # Otherwise ignore this pair.
                    if d_verb2cat.has_key(verb):
                        verb = d_verb2cat[verb]
                        term_set.add(term)
                        verb_set.add(verb)
                        pair = term + "|" + verb
                        pair_set.add(pair)
                else:
                    # keep all terms, verbs, and pairs
                    term_set.add(term)
                    verb_set.add(verb)
                    pair = term + "|" + verb
                    pair_set.add(pair)
                
        s_infile.close()

        # increment the doc_freq for terms and verbs in the doc
        # By making the list a set, we know we are only counting each term or verb once
        # per document
        for term in term_set:
            d_term_freq[term] += 1

        for verb in verb_set:
            d_verb_freq[verb] += 1
            #print "d_verb_freq for %s: %i" % (verb, d_verb_freq[verb])

        for pair in pair_set:
            d_pair_freq[pair] += 1

        # track total number of docs
        doc_count += 1

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    
    # compute probs and mi
    print "Processed %i files" % doc_count
    d_mi = defaultdict(int)
    for pair in d_pair_freq.keys():
        l_pair = pair.split("|")
        term1 = l_pair[0]
        term2 = l_pair[1]
        
        term1_prob = float(d_term_freq[term1])/doc_count
        term2_prob = float(d_verb_freq[term2])/doc_count

        pair_prob = float(d_pair_freq[pair])/doc_count
        # compute normalized pmi
        # Check for odd cases where a term prob of 0 arises
        # It shouldn't happen but it does
        denom = term1_prob * term2_prob
        if denom == 0:
            #print "0 probability for term1: [%s, %f] or term2: [%s, %s]" % (term1, term1_prob, term2, term2_prob)
            pass
        else:
            pmi = math.log(pair_prob/(term1_prob * term2_prob),2)
            norm_pmi = pmi / (-1 * math.log(pair_prob, 2))
            d_mi[pair] = norm_pmi

            # compute npmi * log(freq)
            fpmi = norm_pmi * math.log(d_pair_freq[pair], 2)
            #print "npmi for %s: %f, freq: %i, %i, %i" % (pair, norm_pmi, d_pair_freq[pair], d_term_freq[term1], d_verb_freq[term2])
            s_outfile.write( "%s\t%s\t%f\t%f\t%i\t%i\t%i\n" % (term1, term2, fpmi, norm_pmi, d_pair_freq[pair], d_term_freq[term1], d_verb_freq[term2]))

    else:
        pass
        #print "omitting: %s, %s" % (term1, term2)
    s_outfile.close()


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

#---

# convert term verb (.tv) info to term category info (.tc)
# also create .tvc with term, verb and category info
def tv2tc(inroot, outroot, year, vcat_file=""):
    yearfilename = str(year)
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)
    d_term_freq = collections.defaultdict(int)
    d_verb_freq = collections.defaultdict(int)
    # if vcat_p == True, map verbs to categories using this dict
    d_verb2cat = {}
    # the tc means "term-category" 
    infile = inroot + "/" + yearfilename + ".tv"
    outfile = outroot + "/" + yearfilename + ".tc"
    tvc_file = outroot + "/" + yearfilename + ".tvc"


    # Be safe, check if outroot path exists, and create it if not
    if not os.path.exists(outroot):
        os.makedirs(outroot)
        print "Created outroot dir: %s" % outroot

    # load the verb categories for vcat_file
    s_vcat_file = open(vcat_file)
    for line in s_vcat_file:
        line = line.strip()
        #print "line: %s\n" % line
        l_fields = line.split("\t")
        vcat = l_fields[0]
        verb = l_fields[1]
        d_verb2cat[verb] = vcat

    s_vcat_file.close()

    s_infile = codecs.open(infile, encoding='utf-8')
    s_tvc_file = codecs.open(infile, "w", encoding='utf-8')

    for line in s_infile:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        verb = l_fields[1]
        count = int(l_fields[2])

        # process the term files
        term_set = set()
        verb_set = set()
        pair_set = set()
        s_infile = codecs.open(infile, encoding='utf-8')
        # check if the verb has a category
        # and replace it with the category.
        # Otherwise ignore this pair.
        if d_verb2cat.has_key(verb):

            cat = d_verb2cat[verb]
            s_tvc_file.write("%s\t%s\t%s\t%i\n" % (term, verb, cat, count))

            # for compatibility with some old code, we replace verb with cat
            verb = cat
            term_set.add(term)
            verb_set.add(verb)
            pair = term + "|" + verb
            pair_set.add(pair)
                
        s_infile.close()
        s_tvc_file.close()

        # increment the doc_freq for terms and verbs in the doc
        # By making the list a set, we know we are only counting each term or verb once
        # per document
        for term in term_set:
            d_term_freq[term] += count

        for verb in verb_set:
            d_verb_freq[verb] += count
            #print "d_verb_freq for %s: %i" % (verb, d_verb_freq[verb])

        for pair in pair_set:
            d_pair_freq[pair] += count

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    
    # We cannot compute probs and mi since we no longer have the doc count

    for pair in d_pair_freq.keys():
        l_pair = pair.split("|")
        term = l_pair[0]
        verb = l_pair[1]
        prob = float(d_pair_freq[pair]) / float(d_term_freq[term])
        
        s_outfile.write( "%s\t%s\t%i\t%i\t%f\n" % (term, verb,  d_pair_freq[pair], d_term_freq[term], prob))

    else:
        pass
        #print "omitting: %s, %s" % (term1, term2)
    s_outfile.close()

# Incomplete - tvc/tfc file not handled correctly yet
# convert term feature (.tv) info to term category info (.tc)
# also create .tfc (term, feature, cat)
def tf2tfc(inroot, outroot, year, fcat_file=""):
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
    
    # We cannot compute probs and mi since we no longer have the doc count

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


# given a term_cat file (.tc), create a seed_term file (.st)
# with pairs of category and term which exceed the thresholds for min_prob and min_pair_freq
# These will be used for detecting new features.
# .tc file is of the form: iron oxide      o       2       2       1.000000
# term cat pair_count term_count prob
def tc2st(inroot, outroot, year, min_prob, min_pair_freq):
    # the tc means "term-category" 
    infile = inroot + "/" + year + ".tc"
    outfile = outroot + "/" + year + ".st"

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


# was st2fc => st2fctc                
def st2fc(inroot, outroot, year):
    seed_file = inroot + "/" + year + ".st"
    term_feature_file = inroot + "/" + year + ".tf"
    #outfile = outroot + "/" + year + ".fc"
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

    # Note: We cannot compute mi since we no longer have the doc count

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

def mi2vcat(inroot, year, vcat_file):
    d_verb2cat = {}
    # keep track of terms that are associated with some category verb
    d_term = {}
    d_termcat2freq = {}
    # list of category labels
    # component
    # product
    # name
    # goal/beneficiary
    # affected
    # obstacle
    # cat codes updated 12/27/13 PGA
    # added obstacle, result, replaced goal with beneficiary
    l_cat_codes = ["a", "b", "c", "n", "o", "p", "r", "t"]

    # generate input and output file names
    inyear = inroot + "/" + year
    infile = inyear + ".mi"
    outfile = inyear + ".vc"

    # load the verb categories for vcat_file
    s_vcat_file = open(vcat_file)
    for line in s_vcat_file:
        line = line.strip()
        #print "line: %s\n" % line
        l_fields = line.split("\t")
        vcat = l_fields[0]
        verb = l_fields[1]
        d_verb2cat[verb] = vcat

    s_vcat_file.close()

    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        verb = l_fields[1]
        doc_freq = int(l_fields[4])
        if d_verb2cat.has_key(verb):
            cat = d_verb2cat[verb]
            # To simplify the dictionary, make term and cat into a single key
            term_cat = term + "|" + cat
            # add the doc_freq to the total doc freq for this term and category.
            if d_termcat2freq.has_key(term_cat):
                d_termcat2freq[term_cat] += doc_freq
            else:
                d_termcat2freq[term_cat] = doc_freq
            d_term[term] = True
            #pdb.set_trace()
            #print "verb: %s, cat: %s, term_cat: %s, doc_freq: %i, total: %i" % (verb, cat, term_cat, doc_freq, d_termcat2freq[term_cat])

    # write out the categories and frequencies per term
    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    # keep track of the category with the highest freq

    for term in d_term.keys():
        max_freq = 0
        max_cat = ""
        # make a list of doc_freqs for each category for this term
        l_term_cat_freqs = []
        # make a list of codes that occur for this term
        l_term_cat_codes = []
        # construct the term_cat key for each cat
        for cat in l_cat_codes:
            freq = 0
            term_cat = term + "|" + cat
            if d_termcat2freq.has_key(term_cat):
                freq = d_termcat2freq[term_cat]
                l_term_cat_codes.append(cat)

            l_term_cat_freqs.append(freq)
            # update the max frequency and category found so far
            if freq >= max_freq:
                max_freq = freq
                max_cat = cat

        codes_str = "".join(l_term_cat_codes)
        freqs_str = "	".join(str(freq) for freq in l_term_cat_freqs)
        # write out the .vc file
        s_outfile.write("%s\t%s\t%s\t%s\t%s\n" % (term, max_cat, str(max_freq), codes_str, freqs_str))
        
    s_outfile.close()


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

def test_mi_mini():
    filelist_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_counts"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m2_mi"
    year = "2002"
    
    filelist2mi(filelist_file, inroot, outroot, year)

# version that works against files in a directory rather than a list of files
# term_verb_count.test_dir2mi()

def test_dir2mi():
    year = "2002"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_verb"
    inroot_year = inroot + "/" + year
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m2_tv"

    dir2mi(inroot_year, outroot, year)

# term_verb_count.test_cs_500k()
def test_cs_500k():

    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb_tas"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"
    print "Output dir: %s" % outroot

    # range should be start_year and end_year + 1
    #for int_year in range(1981, 2008):
    for int_year in range(1995, 2008):
    
        year = str(int_year)
        inroot_year = inroot + "/" + year

        print "Processing dir: %s" % inroot_year

        dir2mi(inroot_year, outroot, year)
        print "Completed: %s" % year

# generate term category output for a range of years
# term_verb_count.run_dir2mi_tc_cs_500k()
def run_dir2mi_tc_cs_500k():

    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_verb_tas"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"
    print "Output dir: %s" % outroot

    # range should be start_year and end_year + 1
    #for int_year in range(1981, 2008):
    for int_year in range(1995, 2008):
    #for int_year in range(1995, 1996):
    
        year = str(int_year)
        inroot_year = inroot + "/" + year
        vcat_file = "/home/j/anick/patent-classifier/ontology/creation/verb.cat.en.dat"

        print "Processing dir: %s" % inroot_year

        dir2mi(inroot_year, outroot, year, vcat_p=True, vcat_file=vcat_file)
        print "Completed: %s" % year


# term_verb_count.run_mi2vcat()
def run_mi2vcat():
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"
    year = "1995"
    vcat_file = "/home/j/anick/patent-classifier/ontology/creation/verb.cat.en.dat"
    for int_year in range(1995, 2008):
        year = str(int_year)
        print "[run_mi2vcat] processing year: %s" % year
        mi2vcat(inroot, year, vcat_file)

# create .tfc from .uc and .vc data
# term_verb_count.run_dir2tfc()
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
# term_verb_count.run_dir2features_count()
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

# term verb to term category
# term_verb_count.run_tv2tc()
def run_tv2tc():
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"

    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    outroot = inroot

    vcat_file = "/home/j/anick/patent-classifier/ontology/creation/verb.cat.en.dat"

    #for int_year in range(1997, 1998):
    for int_year in range(1997, 2008):
    
        year = str(int_year)
        print "Processing dir: %s" % year

        tv2tc(inroot, outroot, year, vcat_file)
        print "Completed: %s.tc in %s" % (year, outroot)


# term feature to term feature category for terms whose feature appears in our seed list
# term_verb_count.run_tf2tfc()
def run_tf2tfc():
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"

    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    outroot = inroot

    #fcat_file = "/home/j/anick/patent-classifier/ontology/creation/feature.cat.en.dat"
    fcat_file = "/home/j/anick/patent-classifier/ontology/creation/seed.cat.en.dat"

    #for int_year in range(1997, 1998):
    for int_year in range(1997, 2008):
    
        year = str(int_year)
        print "Processing dir: %s" % year

        tf2tfc(inroot, outroot, year, fcat_file)
        print "Completed: %s.tc in %s" % (year, outroot)



# term category to seed terms
# term_verb_count.run_tc2st()
def run_tc2st():
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"

    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"


    min_prob = .6
    min_pair_freq = 2

    #for int_year in range(1997, 1998):
    for int_year in range(2007, 2008):
    
        year = str(int_year)
        print "Processing dir: %s" % year

        tc2st(inroot, outroot, year, min_prob, min_pair_freq)
        print "Completed: %s.st in %s" % (year, outroot)


# term category to seed terms
# term_verb_count.run_tc2tcs()
def run_tc2tcs():
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k_old/data/tv"
    
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"
    outroot = inroot

    min_prob = .7
    min_pair_freq = 2

    #for int_year in range(1997, 1998):
    for int_year in range(1997, 2008):
    
        year = str(int_year)
        print "Processing dir: %s" % year

        tc2tcs(inroot, outroot, year, min_prob, min_pair_freq)
        print "Completed: %s.st in %s" % (year, outroot)


# use the seed terms to create a file of feature category pairs.  That is, for
# each line containing a seed term, replace it with the category.
# term_verb_count.run_st2fc()
def run_st2fc():
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"

    for int_year in range(1997, 1998):
    
        year = str(int_year)
        print "Processing dir: %s" % year

        st2fc(inroot, outroot, year)
        print "Completed: %s.fc in %s" % (year, outroot)


# use the seed terms to create a file of feature category pairs.  That is, for
# each line containing a seed term, replace it with the category.
# term_verb_count.run_tcs2fc()
def run_tcs2fc():
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    outroot = inroot

    for int_year in range(1997, 2008):
    
        year = str(int_year)
        print "Processing dir: %s" % year

        tcs2fc(inroot, outroot, year)
        print "Completed: %s.fc in %s" % (year, outroot)


# Generate probability for each feature cat combination
# Input file is the result of a uc on the .fc file
# First run:
#      sh run_fc2fcuc.sh

# term_verb_count.run_fcuc2fcprob()
def run_fcuc2fcprob():
    #inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-all-600k/data/tv"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv"

    outroot = inroot

    for int_year in range(1997, 2008):
    
        year = str(int_year)
        print "Processing dir: %s" % year

        fcuc2fcprob(inroot, outroot, year)
        print "Completed: %s.fc in %s" % (year, outroot)

# To get a final set of features, we can filter the feature set based on raw freq and prob values:
# cat 1997.fc.prob.k6 | egrep -v '      1       ' | egrep -v '  2       '  | python /home/j/anick/patent-classifier/ontology/creation/fgt.py 5 .7 > 1997.fc.prob.fgt5_7
# cat 1997.fc.prob.fgt5_7| python /home/j/anick/patent-classifier/ontology/creation/fgt.py 6 .00001 > 1997.fc.prob.fgt5_7.fgt6_00001

# bash-4.1$ cat 1997.fc.prob.fgt5_7 | wc -l
#17993

# cat 1997.fc.prob.fgt5_7.fgt6_00001 | wc -l
#11324
