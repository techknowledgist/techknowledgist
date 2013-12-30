# mi.py
# compute mutual information for a set of files of the form
# <term>\t<count>
# as created by m1_term_counts.sh

import re
import glob
import os
import sys
import log
import math
import collections
from collections import defaultdict
import codecs


# need to generalize the noise file to other languages
# The noise file is a list of terms that are not technical terms or too general
# to be of interest as a member of a term pair.  We save time and space by skipping
# them.  For now, it is created manually by looking at the most frequently occurring 
# terms in the term_counts files, as follows:
# cat *.xml | cut -f1 | sort | uniq -c |sort -nr | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc2.py | cut -f1 > /home/j/anick/patent-classifier/ontology/creation/mi_noise.en
# Then edit the mi_noise.en file by removing non-noise terms.
mi_noise_file = "/home/j/anick/patent-classifier/ontology/creation/mi_noise.en"
d_mi_noise = {}

# This is the threshold for filtering out terms from pairs
# to be retained.  A term which appears in > than this percent 
# of docs will not be included in pairs.  It is useful in reducing the
# size of the data but eliminating pairs that are not likely to be of interest.
# For now, we leave it as 1.0, since we may not need it.
prob_threshold = 1.0

# given a noise file, populate a dictionary
s_mi_noise = codecs.open(mi_noise_file, encoding='utf-8')
for term in s_mi_noise:
    term = term.strip("\n")
    #print "noise: %s" % term
    d_mi_noise[term] = True
s_mi_noise.close()

# return True id term is a noise term
def mi_noise_p(term):
    #print "testing noise: %s" % term
    if d_mi_noise.has_key(term):
        #print "noise is True"
        return(True)
    else:
        return(False)

# given two phrases, return True if they share a word in common
def share_word_p(term1, term2):
    if len(set(term1.split(" ")) & set(term2.split(" "))) > 0:
        return(True)
    else:
        return(False)

# For English morphological suffix based variants,
# test whether term2 is a variant of term1.
def variant_p(term1, term2):
    try:
        if (term1[0:len(term1) - 2] == term2[0:len(term1) - 2]):
            return(True)
        else:
            return(False)
        
    except:
        return(False)

# pattern can contain alpha or blank, must be length >=2
re_alpha_phrase = re.compile('^[a-z ]{2,}$')

def alpha_phrase_p(term):
    mat = bool(re_alpha_phrase.search(term))
    return(mat)

def set2pairs_alpha(term_set):
    l_pairs = []
    l_sorted_terms = sorted(term_set)
    while len(l_sorted_terms) > 1:
        term1 = l_sorted_terms.pop(0)
        for term2 in l_sorted_terms:
            l_pairs.append(term1 + "|" + term2)
    return(l_pairs)

"""
# reads filelist and processes files in inroot/year
# creates term_counts, pair_counts, mi in outroot/year
# We assume inroot/year and outroot have been checked to exist at this point
# outfilename by convention should be a year, e.g. "2002"
def filelist2mi(filelist_file, inroot, outroot, outfilename):
    # count of number of docs a term appears in
    d_doc_freq = collections.defaultdict(int)
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)

    outfile = outroot + "/" + outfilename + ".mi"

    # doc_count needed for computing probs
    doc_count = 0

    s_filelist = open(filelist_file)
    for line in s_filelist:
        line = line.strip("\n")
        l_line = line.split("\t")
        year = int(l_line[0])
        filename = l_line[2]
        infile = inroot + "/" + filename
        # process the term files
        term_set = set()
        s_infile = codecs.open(infile, encoding='utf-8')
        for term_line in s_infile:
            term_line = term_line.strip("\n")
            l_term_line = term_line.split("\t")
            term_set.add(l_term_line[0])
            
        s_infile.close()

        # increment the doc_freq for terms in the doc
        for term in term_set:
            d_doc_freq[term] += 1
            #print "d_doc_freq for %s: %i" % (term, d_doc_freq[term])

        # increment the doc_freq for cooccurring pairs of terms
        l_pairs = set2pairs_alpha(term_set)
        for pair in l_pairs:
            d_pair_freq[pair] += 1

        doc_count += 1
    s_filelist.close()

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    
    # compute probs and mi
    print "Processed %i files" % doc_count
    d_mi = defaultdict(int)
    for pair in d_pair_freq.keys():
        l_pair = pair.split("|")
        term1 = l_pair[0]
        term2 = l_pair[1]
        term1_prob = float(d_doc_freq[term1])/doc_count
        term2_prob = float(d_doc_freq[term2])/doc_count

        # check against a prob threshold to filter terms that are too common
        if term1_prob <= prob_threshold and term2_prob <= prob_threshold:
            pair_prob = float(d_pair_freq[pair])/doc_count
            # compute normalized pmi
            pmi = math.log(pair_prob/(term1_prob * term2_prob),2)
            norm_pmi = pmi / (-1 * math.log(pair_prob, 2))
            d_mi[pair] = norm_pmi
            #print "npmi for %s: %f, freq: %i, %i, %i" % (pair, norm_pmi, d_pair_freq[pair], d_doc_freq[term1], d_doc_freq[term2])
            s_outfile.write( "%s\t%s\t%f\t%i\t%i\t%i\n" % (term1, term2, norm_pmi, d_pair_freq[pair], d_doc_freq[term1], d_doc_freq[term2]))

    s_outfile.close()
"""

# Same as filelist2mi except that the list of files is taken 
# to be all the files in a given directory.
# creates term_counts, pair_counts, mi in outroot/year
# We assume inroot/year and outroot have been checked to exist at this point
# outfilename will the be value of the year
def dir2mi(inroot, outroot, year, d_mi_noise):
    outfilename = str(year)
    # count of number of docs a term appears in
    d_doc_freq = collections.defaultdict(int)
    # count of number of docs a term pair cooccurs in
    d_pair_freq = collections.defaultdict(int)

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
        s_infile = codecs.open(infile, encoding='utf-8')
        for term_line in s_infile:
            term_line = term_line.strip("\n")
            term = term_line.split("\t")[0]
            #print "term: %s" % term
            # filter out non alphabetic phrases, noise terms
            if alpha_phrase_p(term) and not mi_noise_p(term):
                #print "term matches: %s" % term
                term_set.add(term)
            
        s_infile.close()

        # increment the doc_freq for terms in the doc
        for term in term_set:
            d_doc_freq[term] += 1
            #print "d_doc_freq for %s: %i" % (term, d_doc_freq[term])

        # increment the doc_freq for cooccurring pairs of terms
        l_pairs = set2pairs_alpha(term_set)
        for pair in l_pairs:
            d_pair_freq[pair] += 1

        doc_count += 1

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    
    # compute probs and mi
    print "Processed %i files" % doc_count
    d_mi = defaultdict(int)
    for pair in d_pair_freq.keys():
        l_pair = pair.split("|")
        term1 = l_pair[0]
        term2 = l_pair[1]
        
        # Do not include terms that share a word in common or are morphological variants
        if not share_word_p(term1, term2) and not variant_p(term1, term2):

            term1_prob = float(d_doc_freq[term1])/doc_count
            term2_prob = float(d_doc_freq[term2])/doc_count

            # check against a prob threshold to filter terms that are too common
            if term1_prob <= prob_threshold and term2_prob <= prob_threshold:
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
                    #print "npmi for %s: %f, freq: %i, %i, %i" % (pair, norm_pmi, d_pair_freq[pair], d_doc_freq[term1], d_doc_freq[term2])
                    s_outfile.write( "%s\t%s\t%f\t%f\t%i\t%i\t%i\n" % (term1, term2, fpmi, norm_pmi, d_pair_freq[pair], d_doc_freq[term1], d_doc_freq[term2]))

        else:
            pass
            #print "omitting: %s, %s" % (term1, term2)
    s_outfile.close()

def test_mi_mini():
    filelist_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_counts"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m2_mi"
    year = "2002"
    
    filelist2mi(filelist_file, inroot, outroot, year)

# TBD
def test_mi():
    filelist_file = "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/config/files.txt"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_284k/data/m1_term_counts"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_284k/data/m2_mi"
    year = "2002"
    
    filelist2mi(filelist_file, inroot, outroot, year)

# version that works against files in a directory rather than a list of files
def test_dir2mi():
    year = "2002"
    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m1_term_counts"
    inroot_year = inroot + "/" + year
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/m2_mi"

    dir2mi(inroot_year, outroot, year)

#mi.test_cs_500k()
def test_cs_500k():

    inroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m1_term_counts"
    outroot = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_mi"
    print "Output dir: %s" % outroot

    # range should be start_year and end_year + 1
    #for int_year in range(1981, 2008):
    for int_year in range(1995, 2008):
    
        year = str(int_year)
        inroot_year = inroot + "/" + year

        print "Processing dir: %s" % inroot_year

        dir2mi(inroot_year, outroot, year, d_mi_noise)
        print "Completed: %s" % year
