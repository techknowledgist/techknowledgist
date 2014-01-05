# mi.py
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
                #print "term matches: %s" % term

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


