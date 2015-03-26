# -*- coding: utf-8 -*-
# dealing with noun compounds

# TODO: 
# generate docs and compounds for annotation
# capture doc_freq and sort compounds in a doc by df

from elasticsearch import Elasticsearch
es = Elasticsearch()

import roles_config
import pnames
import os
import sys
import re
import codecs
import pdb
import math
import copy
from collections import defaultdict
# log is our own log routines for timing runs
import log
from ontology.utils.file import get_year_and_docid, open_input_file

import logging
logging.basicConfig()
# from http://excid3.com/blog/no-handlers-could-be-found-for-logger/
# What this does is imports the same logging module as the library does and it sets up a configuration application wide that the s logging import can use to write messages properly.plugin

# control messages output 
verbose_p = False

fuse_corpus_root = roles_config.FUSE_CORPUS_ROOT
corpus_root = roles_config.CORPUS_ROOT

from elasticsearch import Elasticsearch
es = Elasticsearch()

from es_np_query import *

# inflection package used for canonicalizing words in phrases
# https://pypi.python.org/pypi/inflect
import inflect
ie = inflect.engine()


# noise detection

re_noise_phrase = re.compile('[\,\+\=\.\:\\\\′\®\±\%\═\≅\>\>\<\≡\≡\″\≡\→]')

# bibliography names, e.g. "nestle f o"
re_bib_name = re.compile('[a-z]+ [a-z] [a-z]')

# if these words appear in a phrase, we reject the phrase as
# incomplete or inappropriate for bracketing analysis
# u'\u2212' is a type of dash found in doc US20040248097A1  (year 2000 biomed patents)
illegal_words = set([u'\u2212', u'\u2032', u'\u2550', "−", "-", "'s", "'", "′", "co", "et", "much", "millimeter", "milliliter", "mm", "ml", "example"])

max_legal_word_len = 30
def illegal_word_len_p(phr, max_len=max_legal_word_len):

    for word in phr.split(" "):
        if len(word) > max_len:
            return(True)
    return(False)

# return True if phr contains illegal punc or a word
# matching an illegal word
def illegal_phrase_p(phr):
    # use debugging here to catch illegal words/characters
    #if phr.find("nestle") >= 0:
    #    pdb.set_trace()
    # first character of phrase should be alpha
    if not phr[0].isalpha():
        return(True)
    if illegal_word_len_p(phr):
        return(True)

    illegal_punc_p = bool(re_noise_phrase.search(phr)) or bool(re_bib_name.search(phr))
    if illegal_punc_p:
        return(True)
    l_words = phr.split(" ")

    if list(illegal_words & set(l_words)) == []:
        return(False)
    else:
        return(True)
        
# remove illegal phrases from a .inst file (phrase\tdoc)
# es_np_nc.filter_phr_doc_file("bio.2000.3.inst")
def filter_phr_doc_file(phr_doc_file):
    filt_file = phr_doc_file + ".filt"
    s_phr_doc = codecs.open(phr_doc_file, encoding='utf-8')
    s_filt = codecs.open(filt_file, "w", encoding='utf-8')

    for line in s_phr_doc:
        phrase = line.split("\t")[0]
        if not(illegal_phrase_p(phrase)):
            s_filt.write("%s" % (line)) 

    s_phr_doc.close()
    s_filt.close()


#############################

# es_np_nc.canonical_np("cats monkeys")
# reduce all words in a noun phrase to singular form
def canonical_np(phr):
    l_words = phr.split(" ")
    # put canonical forms in a list, then join them to make a canonical phrase
    l_cwords = []
    for word in l_words:
        l_cwords.append(canonical_noun(word))
    return ' '.join(l_cwords)

# reduce a noun to its singular
def canonical_noun(word):
    #print "word: %s" % word
    cword = ie.singular_noun(word)
    if cword:
        return(cword)
    else:
        return(word)

###################################################################
#corpus statistics
"""
using the triple and bigram lists for a year of patents
bio.2003.2.inst.filt.su.f1.uc1.nr is list of bigrams and their doc freq
bio.2003.3.inst.filt.su.f1.uc1.nr is list of trigrams and their doc freq

"""
# map from canonical phrases to corpus stats
d_ctrigram2info = {}
d_cbigram2info = {}

# Until we index es with canonical phrases, we will have to handle it after the fact
# Starting with the list of raw phrase occurrences in docs, we create a canonicalized version
# in which each occurrence is replaced by its canonical form.  

# create 2 files: c_phr_doc_file, c_phr2surface_file

# es_np_nc.can_phr_doc_file("bio.2003.3.inst.filt2.h200") a test
# es_np_nc.can_phr_doc_file("bio.2003.3.inst.filt2")
# canonicalize the phr_doc file
# This replaces the phrase in (phrase doc_id pair) with the canonicalized phrase (.c)
# It also creates a file mapping canonicalized phrases to all surface forms (.c2s)
def can_phr_doc_file(phr_doc_file):
    # create the output file names given the input file name
    c_phr_doc_file = phr_doc_file + ".c"
    c_phr2surface_file = phr_doc_file + ".c2s"

    s_phr_doc = codecs.open(phr_doc_file, encoding='utf-8')
    s_c_phr_doc = codecs.open(c_phr_doc_file, "w", encoding='utf-8')
    s_c_phr2surface = codecs.open(c_phr2surface_file, "w", encoding='utf-8')
    
    # keep a set of all the surface forms for a canonical form
    # This will be written out to c_phr2surface_file
    d_cphr2surface = defaultdict(set)

    # phr is a surface phrase
    # cphr is a canonical phrase
    for line in s_phr_doc:
        line = line.strip()
        #pdb.set_trace()
        (phr, doc_id) = line.split("\t")
        cphr = canonical_np(phr)
        s_c_phr_doc.write("%s\t%s\n" % (cphr, doc_id)) 
        # update the set of surface forms for this canonical phrase
        d_cphr2surface[cphr].add(phr)
        
    # now outpt the d_cphr2surface sets
    for cphr in d_cphr2surface.keys():
        s_c_phr2surface.write("%s\t%s\n" % (cphr, "|".join(d_cphr2surface[cphr])) )

    s_phr_doc.close()
    s_c_phr_doc.close()
    s_c_phr2surface.close()

# map canonical bigram to its document frequency within some corpus
d_bigram2df = defaultdict(int) 

# Given files with bigram and trigram doc frequencies,
# create a file with a set of statistics for trigrams (.df)
# es_np_nc.trigram2info("bio.2003.3.inst.filt.c.su.f1.uc1.nr" , "bio.2003.2.inst.filt.c.su.f1.uc1.nr")
# es_np_nc.trigram2info("bio.2003.3.inst.filt.c.su.f1.uc1.nr.1k", "bio.2003.2.inst.filt.c.su.f1.uc1.nr.5k")
def trigram2info(trigram_file, bigram_file):
    stats_file = trigram_file + ".stats"
    s_bigram = codecs.open(bigram_file, encoding='utf-8')
    s_trigram = codecs.open(trigram_file, encoding='utf-8')
    s_stats = codecs.open(stats_file, "w", encoding='utf-8')

    # read the bigram df into a dictionary (d_bigram2df)
    # line is of the form: 2938    gene expression
    for line in s_bigram:
        line = line.strip()
        #pdb.set_trace()
        (df, phr) = line.split("\t")
        d_bigram2df[phr] = int(df)
        
    for line in s_trigram:
        line = line.strip()
        #pdb.set_trace()
        (df3gram, phr) = line.split("\t")
        # look up the df for subphrases AB, BC, AC
        l_words = phr.split(" ")
        df3gram = int(df3gram)
        ab = " ".join(l_words[0:2])
        bc = " ".join(l_words[1:3])
        ac = l_words[0] + " " + l_words[2]

        dfab = d_bigram2df[ab]
        dfbc = d_bigram2df[bc]
        dfac = d_bigram2df[ac]
        
        # compute stats
        # raw freq difference
        # ab-bc
        # ratio of |ab - bc| / (ab + bc)

        raw_diff = dfab - dfbc
        # note: frequencies can be 0 if the phrase doesn't exist in the text as a bigram
        ratio = round( (abs(raw_diff) / (dfab + dfbc + .00001)), 2)
        
        bracketing = "U"
        if raw_diff > 0:
            bracketing = "L"
        elif raw_diff < 0:
            bracketing = "R"
            
        # If the bigram scores are relatively balanced, mark trigram as possible bi-branching.
        if ratio < .5 and ratio > 0:
            bracketing += "B"

        # top_gram indicates whether the trigram or one of the bigrams has the highest frequency
        top_gram = "B"
        if (df3gram > dfab) and (df3gram > dfbc):
            top_gram = "T"


        
        #pdb.set_trace()
        s_stats.write("%s\t%i\t%i\t%i\t%i\t%i\t%.2f\t%s\t%s\n" % (phr, df3gram, dfab, dfbc, dfac, raw_diff, ratio, bracketing, top_gram))
        

    s_bigram.close()
    s_trigram.close()
    s_stats.close()

class bigramInfo():
    def __init__(self, cphr, df):
        l_words = cphr.split(" ")
        self.df = df
        self.ab = " ".join(l_words[0:2])
        self.bc = " ".join(l_words[1:3])
        self.ac = l_words[0] + " " + l_words[2]
        pass


###################################################################
# MUTUAL INFORMATION computation
# pmi is standard pmi
# norm_pmi is standard pmi normalized by the log of the pair_prob
# fpmi multiplies by the log of the joint frequency to boost scores of
# more frequent combinations.
def pmi(term1, freq1, term2, freq2, joint_freq, n, pmi_type="pmi"):

    # default value in case the pmi cannot be computed due to 0 freq somewhere
    pmi = -1000
    mi = -1000
    norm_pmi = -1000  
    fpmi = -1000

    term1_prob = float(freq1)/n
    term2_prob = float(freq2)/n

    pair_prob = float(joint_freq)/n
    # compute normalized pmi
    # Check for odd cases where a term prob of 0 arises
    # It shouldn't happen but it does
    denom = term1_prob * term2_prob
    
    if denom == 0:
        if verbose_p:
            print "0 probability for term1: [%s, %f] or term2: [%s, %s]" % (term1, term1_prob, term2, term2_prob)
        pass
    elif pair_prob == 0:
        if verbose_p:
            print "0 probability for pair: %s, %s" % (term1, term2)
        pass
    else:
        pmi = math.log(pair_prob/(term1_prob * term2_prob),2)
        mi = pair_prob * pmi
        norm_pmi = pmi / (-1 * math.log(pair_prob, 2))

        # compute npmi * log(freq)
        fpmi = norm_pmi * math.log(joint_freq, 2)
        if verbose_p:
            print "[pmi]npmi/fpmi for %s %s: %f, %f  freq/probs: %i/%f, %i/%f, %i/%f" % (term1, term2, norm_pmi, fpmi, freq1, term1_prob, freq2, term2_prob, joint_freq, pair_prob)
    #s_outfile.write( "%st%st%ft%ft%it%it%i\n" % (term1, term2, fpmi, norm_pmi, d_pair_freq[pair], d_term_freq[term1], d_verb_freq[term2]))
    if pmi_type == "pmi":
        result = pmi
    elif pmi_type == "mi":
        result = mi
    elif pmi_type == "norm_pmi":
        result = norm_pmi
    elif pmi_type == "fpmi":
        result = fpmi
    return(result)

# TBD add in morphology on head term (pluralization)
# TBD handle 0 prob and negative probs better.
# es_np.trigram_pmi("abnormal cell proliferation")
def trigram_pmi(phr, n=39392738, index_name="i_np_bio", pmi_type="pmi"):
    l_phr = phr.split(" ")
    term_0 = l_phr[0]
    term_1 = l_phr[1]
    term_2 = l_phr[2]

    sp1 = "[ " + l_phr[0] + " | " + l_phr[1] + " ]"
    sp2 = "[ " + l_phr[1] + " | " + l_phr[2] + " ]"
    sp3 = "[ " + l_phr[0] + " | " + l_phr[2] + " ]"
    
    joint_freq_0_1 = qmaf("sp", sp1, l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    joint_freq_1_2 = qmaf("sp", sp2, l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    joint_freq_0_2 = qmaf("sp", sp3, l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    freq_0 = qmaf("sp", l_phr[0], l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    freq_1 = qmaf("sp", l_phr[1], l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]
    freq_2 = qmaf("sp", l_phr[2], l_must=[], doc_type="np", index_name=index_name, query_type="count")["count"]

    pmi_ab = pmi(term_0, freq_0, term_1, freq_1, joint_freq_0_1, n, pmi_type=pmi_type)
    pmi_bc = pmi(term_1, freq_1, term_2, freq_2, joint_freq_1_2, n, pmi_type=pmi_type)
    pmi_ac = pmi(term_0, freq_0, term_2, freq_2, joint_freq_0_2, n, pmi_type=pmi_type)

    # adjacency measure
    score1 = pmi_bc - pmi_ab
    # dependency measure of first term to potential head terms
    score2 = pmi_ac - pmi_ab

    # simple combination score (with equal weighting)
    score3 = score1 + score2

    brackets = []
    if score1 > 0:
        brackets.append("r")
    else:
        brackets.append("l")

    if score2 > 0:
        brackets.append("r")
    else:
        brackets.append("l")

    if score3 > 0:
        brackets.append("r")
    else:
        brackets.append("l")

    return(brackets)


def vote_max(label_list):
    return max(set(label_list), key=label_list.count)


def bracket_trigram(trigram, label):
    l_words = trigram.split(" ")
    if label == "l":
        br = [ [ l_words[0], l_words[1] ], l_words[2] ]
    else:
        br = [ l_words[0], [l_words[1], l_words[2] ] ]
    return(br)

# evaluate trigram gold data using the bracketing output from bracket() as well as pmi values
# filter="all" to include all phrases in eval
# filter="corpus" to include only phrases that appear as a whole in the corpus
# es_np.eval_bio_br("bio_trigrams.dat", "bio_trigrams_br.eval", pmi_type="pmi", filter="all", score_method="full_adj")  
def eval_bio_br(gold_file, eval_file, pmi_type="pmi", filter="all", score_method="full_adj"):
    s_infile = codecs.open(gold_file, encoding='utf-8')
    s_eval_file = codecs.open(eval_file, "w", encoding='utf-8')

    phrase_count = 0
    # phrases that occur at least once in corpus 
    phrase_corpus_count = 0
    match1_count = 0
    match2_count = 0
    match3_count = 0
    match4_count = 0
    match5_count = 0

    label_letters = ["l", "r"]

    line_count = 0
    for line in s_infile:
        line_count += 1
        """
        # for debugging, stop after a few lines
        if line_count > 3:
            break
        """

        line = line.strip()
        [gold_label, phrase] = line.split("\t")
        # replace the letter label with the equivalent l or r bracketed phrase
        gold_label_br = bracket_trigram(phrase, gold_label)
        # let system_label_br be the top ranked bracketing for the phrase
        # NOTE: need to deal with ties.  Right now we simply take the first in the list. ///
        #system_label_br = bracket(phrase)[0][2]

        # use the br methods rather than bracket()
        br1 = br(phrase, es)
        #br1.tree_counts()

        l_score_info = br1.d_method2sorted_scores[score_method]
        # get the bracketing of the top ranked score
        system_label_br = l_score_info[0][2]
        if verbose_p:
            print "system_label_br: %s " % (system_label_br)

        phrase_count += 1

        #print "%s" % phrase
        label_list = trigram_pmi(phrase, n=39392738, index_name="i_nps_bio", pmi_type="pmi")
        [l1, l2, l3] = label_list
        
        # set l5 to be the label (l,r) the system chooses, based on comparing the bracketed formats
        # ie. we are translating from bracketings to (l,r) assuming that since there are only two choices,
        # then if system and gold agree, use the gold label, if not, use the complementary label.
        ###pdb.set_trace()
        if gold_label_br == system_label_br:
            l5 = gold_label
        else:
            # l5 gets the opposite label

            label_letters_copy = list(label_letters)
            label_letters_copy.remove(gold_label)
            
            l5 = label_letters_copy[0]
            #/// bug - the match always fails.
            print "setting l5 to %s, opposite of gold_label: %s" % (l5, gold_label)
            #pdb.set_trace()
        # vote for the highest freq label from the 3 MI metrics
        vote_label = vote_max(label_list)

        print "gold: %s %s (vl,l1,l2,l3,l5:) %s %s %s %s %s\t%s" % (gold_label_br, gold_label, vote_label, l1, l2, l3, l5, phrase)
        #pdb.set_trace()
        
        # check if the phrase occurs in the corpus
        corpus_count = qmaf("phr", phrase, index_name="i_nps_bio", query_type="count")["count"]

        if filter == "corpus":
            if corpus_count > 0:
                if gold_label == l1:
                    match1_count += 1

                if gold_label == l2:
                    match2_count += 1

                if gold_label == l3:
                    match3_count += 1

                if gold_label == vote_label:
                    match4_count += 1

                if gold_label_br == system_label_br:
                    match5_count += 1

                phrase_corpus_count += 1

        elif filter == "all":
            if gold_label == l1:
                match1_count += 1

            if gold_label == l2:
                match2_count += 1

            if gold_label == l3:
                match3_count += 1

            if gold_label == vote_label:
                match4_count += 1

            if gold_label_br == system_label_br:
                match5_count += 1

            phrase_corpus_count += 1

    print "matches: %i, %f, %i, %f, %i, %f, %i, %f, %i, %f out of %i (total: %i)" % (match1_count, float(match1_count)/phrase_corpus_count, match2_count, float(match2_count)/phrase_corpus_count, match3_count, float(match3_count)/phrase_corpus_count, match4_count, float(match4_count)/phrase_corpus_count, match5_count, float(match5_count)/phrase_corpus_count, phrase_corpus_count, phrase_count)

# Given a phrase, find the counts for each term to appear as the head of an Npr with the other 
# term as the object.
# eg. for stem cell research
# prev_N = research, sp = cell
# es_np.head_mod_pairs("stem cell research")
# [['research', 'cell', 2, 1], ['research', 'stem', 2, 0], ['cell', 'stem', 1, 0]]

def head_mod_pairs(phrase):
    l_words = phrase.split(" ")
    l_hm_pairs = []
    last_head_index = len(l_words) - 1
  
    # descend from last head term to first 
    # note that range does not include the last value, so the second
    # parameter is 1 index lower.
    for h in range(last_head_index, 0, -1):
        for m in range(h - 1, -1, -1):
            l_hm_pairs.append([l_words[h], l_words[m], h, m])

    return(l_hm_pairs)

def head2spn(word):
    spn_first_word_pattern = "[ " + word
    return(["spn", spn_first_word_pattern])

def mod2sp(word):
    sp_last_word_pattern = word + " ]"
    return(["sp", sp_last_word_pattern])

# not used
# es_np.count_hm_pairs("human stem cells")
def count_hm_pairs(phrase):
    l_hm_pairs = head_mod_pairs(phrase)
    l_hm_w_counts = []
    for hm_pair in l_hm_pairs:
        head = hm_pair[0]
        mod = hm_pair[1]
        # e.g. for the phrase "human skin", human is mod and skin is head
        #
        # qc_mult([["spn", "[ skin" ], ["sp", "human ]"]])
        count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=True)
        # add count value to end of hm_pair vector
        hm_pair.append(count)
        l_hm_w_counts.append(hm_pair)
        print "hm_pair: %s" % hm_pair
    return(l_hm_w_counts)


##############################
# analyzing trees and scoring

class treeInfo():
    def __init__(self, num_tree, phrase, l_pairInfo):
        self.num_tree = num_tree
        self.word_tree = ntree2words(num_tree, phrase)
        self.l_pairInfo = l_pairInfo

# methods for bracketing and scoring
# b = es_np.br("human cell line", es_np.es)
class br():
    def __init__(self, phrase, es):
        self.phrase = phrase
        l_words = phrase.split(" ")
        self.d_idx2word = {}
        # elasticsearch object
        self.es = es
        # map from pair of phrase indices (e.g. (0, 2) to the counts object
        # for the mod and head at those phrase positions.  This is 
        # essentially a cache of elasticsearch count query results, since 
        # many trees will contain the same pairs
        self.d_numpair2counts = {}
        self.d_method2sorted_scores = {}
        self.l_treeInfo = []

        # map word position in phrase to word
        for idx in range(0, len(l_words)):
            self.d_idx2word[idx] = l_words[idx]

        self.tree_counts()
        self.d_method2sorted_scores["Npr"] = self.sort_scores("Npr")
        self.d_method2sorted_scores["full_adj"] = self.sort_scores("full_adj")
        self.d_method2sorted_scores["partial_adj"] = self.sort_scores("partial_adj")

        #pdb.set_trace()

    def tree_counts(self):
        phrase = self.phrase
        trees = make_br_trees_num(phrase)
        cinfo = None
        for num_tree in trees:
            # accumulate count info for all pairs in the tree

            # score the tree using es counts
            # First generate all the pairs (of mod and head terms)
            l_pairs = tree2pairs(num_tree)
            l_pairInfo = []

            for pair in l_pairs:
                loc1 = pair[0]
                loc2 = pair[1]
                w1 = self.d_idx2word[loc1]
                w2 = self.d_idx2word[loc2]
                pair_key = tuple(pair)
                if self.d_numpair2counts.has_key(pair_key):
                    # use cached data
                    pinfo = self.d_numpair2counts[pair_key]
                    #pdb.set_trace()
                else:
                    # compute counts using es and update cache
                    pinfo = pairInfo(w1, w2, loc1, loc2, self.es)
                    self.d_numpair2counts[pair_key] = pinfo
                # add the pair info for the pair to our list
                l_pairInfo.append(pinfo)
            # dump the data into a tree_info object
            ti = treeInfo(num_tree, phrase, l_pairInfo)
            self.l_treeInfo.append(ti)


        """
        for ti in self.l_treeInfo:
            self.score_pairs(ti, self.d_numpair2counts, "Npr")
            self.score_pairs(ti, self.d_numpair2counts, "full_adj")
            self.score_pairs(ti, self.d_numpair2counts, "partial_adj")

        """

    def score_pairs(self, ti, d_numpair2counts, score_method):
        #pdb.set_trace()
        # note that score_method and count_method could be different!
        # keep cumulative scores indexed by method
        # for multi, we do +1 smoothing to avoid multiplying by 0
        d_add_method2score = defaultdict(lambda:0)
        d_mult_method2score = defaultdict(lambda:1)
        l_mh_info = []
        for pi in ti.l_pairInfo:

            #print "pi: %s, ti.l_pairInfo: %s" % (pi, ti.l_pairInfo)
            #pdb.set_trace()
            # keep track of mod head and count info
            mh_info = [pi.pair]

            if score_method == "Npr":
                # Given a mod and head in the NP order ("stem cells"), we compute the number of docs
                # spn is stemmed prev_Npr  "[ cells of "  as in "cells of human stem"
                # sp is stemmed NP "stem ]"  as last word in the phrase
                # we need to compute the count using elasticsearch query qc_mult
                
                # if mod and head are adjacent, include the Npr paraphrase counts in calculation
                count = pi.d_method2count["partial_adj"]
                mh_info.append(count)
                if pi.loc2 - pi.loc1 == 1:
                    mh_info.append(pi.d_method2count["Npr"])
                    count = count + pi.d_method2count["Npr"]
                    
                d_add_method2score[score_method] = d_add_method2score[score_method] + count
                # use +1 smoothing on the multiplication scoring to avoid multiplying by 0
                d_mult_method2score[score_method] = d_mult_method2score[score_method] * (count + 1) 
                ###pdb.set_trace()
            elif score_method == "full_adj":
                
                # full adjacent (stemmed) phrase made up of the two terms
                count = pi.d_method2count["full_adj"]
                mh_info.append(count)
                d_add_method2score[score_method] = d_add_method2score[score_method] + pi.d_method2count["full_adj"] 
                d_mult_method2score[score_method] = d_mult_method2score[score_method] * (pi.d_method2count["full_adj"] + 1 ) 

            elif score_method == "partial_adj":
                # partial adjacent (stemmed) phrase made up of the two terms
                count = pi.d_method2count["partial_adj"]
                mh_info.append(count)
                d_add_method2score[score_method] = d_add_method2score[score_method] + pi.d_method2count["partial_adj"] 
                d_mult_method2score[score_method] = d_mult_method2score[score_method] * (pi.d_method2count["partial_adj"] + 1)
            l_mh_info.append(mh_info)
        #print "bracketing: %s, %s, scores(mult, add): %i\t%i" % (ti.word_tree, l_mh_info, d_mult_method2score[score_method], d_add_method2score[score_method]) 
        #print "Returning from score_pairs!"
        return([d_mult_method2score[score_method], d_add_method2score[score_method], ti.word_tree, l_mh_info])
    
    def sort_scores(self, method, debug_p=False):
        #pdb.set_trace()
        l_scores = []
        sorted_scores = []
        #pdb.set_trace()
        #print "bracketing sorted by method: %s" % method
        #pdb.set_trace()
        for ti in self.l_treeInfo:

            l_scores.append(self.score_pairs(ti, self.d_numpair2counts, method))
        sorted_scores = reversed(sorted(l_scores))
        """
        l_scores = []
        for score in sorted_scores:
            (score_mult, score_add, tree, mh_path) = score
            if debug_p:
                print "bracketing: %s %i %i %s" % (tree, score_mult, score_add, mh_path)
            l_scores.append(score)
        """
        return(l_scores)

# generate all bracketed trees for a given phrase
# use numeric indices for each word (0 - len(phrase)-1 )
# uses merge_level()
def make_br_trees_num(phrase):

    l_words = phrase.split(" ")
    # create initial list of numeric indices into the phrase (first word index = 0)
    # generate all integers from 0 to length of phrase -1 
    # create a list of leaf nodes with these numeric values
    l_leaves = range(0, len(phrase.split(" ")))
    # list of final trees
    l_final_trees = []
    partial_tree_queue = [l_leaves]
    new_partial_tree_queue = []

    # if a list in the queue has length 1, we move it to l_trees
    while len(partial_tree_queue) > 0:
        for partial_tree in partial_tree_queue:
            pt_len = len(partial_tree)
            for idx in range(0, pt_len - 1):
                merged_tree = merge_level(partial_tree, idx)
                #print "[make_trees]idx: %i, partial_tree: %s, merged_tree: %s" % (idx, partial_tree, merged_tree)
                if len(merged_tree) > 1:
                    new_partial_tree_queue.append(merged_tree)
                else:
                    # we are at root of full tree.  Place it into list of final trees.
                    # unless it is a duplicate tree
                    #pdb.set_trace()
                    if merged_tree[0] not in l_final_trees:
                        l_final_trees.append(merged_tree[0])
                #print "[make_br_trees]new_partial_tree_queue: %s" % new_partial_tree_queue
        partial_tree_queue = new_partial_tree_queue
        new_partial_tree_queue = []

    #print "[make_br_trees]l_final_trees: %s" % l_final_trees

    return(l_final_trees)


def merge_level(partial_tree, idx):
    l_new_ptree = []
    mod = idx
    head = idx + 1
    l_new_ptree = []
    #print "[Entered merge_level] partial_tree: %s len: %i" % (partial_tree, len(partial_tree))
    if len(partial_tree) == 1:
        #print "[merge_level] len(partial_tree): %i" % len(partial_tree)
        l_new_ptree = partial_tree[0]
    else:
        for npt_idx in range(0, len(partial_tree)):
            if (npt_idx < mod ) or (npt_idx > head):
                l_new_ptree.append(partial_tree[npt_idx])
            elif npt_idx == mod:
                mh = [partial_tree[mod], partial_tree[head]]
                l_new_ptree.append(mh)
    #print "[merge_level]npt_idx: %i, l_new_ptree: %s" % (npt_idx, l_new_ptree)
    return(l_new_ptree)


# generate all bracketed trees for a given phrase
# creates trees as lists of lists rather than nodes
def make_br_trees_words(phrase):
    l_words = phrase.split(" ")
    # create initial list of numeric indices into the phrase (first word index = 0)
    # generate all integers from 0 to length of phrase -1 
    l_leaves = l_words
    # list of final trees
    l_final_trees = []
    partial_tree_queue = [l_leaves]
    new_partial_tree_queue = []

    # if a list in the queue has length 1, we move it to l_trees
    while len(partial_tree_queue) > 0:
        for partial_tree in partial_tree_queue:
            pt_len = len(partial_tree)
            for idx in range(0, pt_len - 1):
                merged_tree = merge_level(partial_tree, idx)
                #print "[make_trees]idx: %i, partial_tree: %s, merged_tree: %s" % (idx, partial_tree, merged_tree)
                if len(merged_tree) > 1:
                    new_partial_tree_queue.append(merged_tree)
                else:
                    # we are at root of full tree.  Place it into list of final trees.
                    # unless it is a duplicate tree
                    if merged_tree not in l_final_trees:
                        l_final_trees.append(merged_tree[0])
                #print "[make_br_trees]new_partial_tree_queue: %s" % new_partial_tree_queue
        partial_tree_queue = new_partial_tree_queue
        new_partial_tree_queue = []

    #print "[make_br_trees]l_final_trees: %s" % l_final_trees
    return(l_final_trees)

# convert a tree to pairs of [mod, head] 
# es_np.tree2pairs(['one', ['two', 'three']])
def tree2pairs(tree):
    l_pairs = []
    def tree2pairs(tree):
        left = tree[0]
        right = tree[1]

        if isinstance(left, list):
            (lhead) = tree2pairs(left)
        else:
            lhead = left
        if isinstance(right, list):
            (rhead) = tree2pairs(right)
        else:
            rhead = right
        l_pairs.append([lhead, rhead])
        return(rhead)

    tree2pairs(tree)
    return(l_pairs)

# convert a numeric tree (containing index ordinals) to a tree containing words from the phrase
def ntree2words(tree, phrase):
    l_words = phrase.split(" ")
    key = 0
    d_num2word = {}
    # map ordinal index to word in phrase
    for word in l_words:
        d_num2word[key] = word
        key += 1

    def tree2words(tree):
        left = tree[0]
        right = tree[1]

        if isinstance(left, list):
            left = tree2words(left)
        else:
            left = d_num2word[left]
        if isinstance(right, list):
            right = tree2words(right)
        else:
            right = d_num2word[right]
        return([left, right])

    return(tree2words(tree))

# bracket a 3-word phrase using a specific relation-type as count data.
# es_np.bracket("cell membrane research paper")
def bracket(phrase, relation_type="Npr"):
    d_mh = {}
    l_scores = []
    l_trees = make_br_trees(phrase)

    for tree in l_trees:
        l_pairs = tree2pairs(tree)
        l_scores.append(score_word_pairs(l_pairs, d_mh, tree, relation_type))
    sorted_scores = reversed(sorted(l_scores))
    l_scores = []
    for score in sorted_scores:
        (score_mult, score_add, tree, mh_path) = score
        l_scores.append(score)
        print "bracketing: %s %i %i %s" % (tree, score_mult, score_add, mh_path)
    return(l_scores)

def brackets(phrase):
    for relation_type in ["Npr", "fadj"]:
        print "Relation_type: %s" % relation_type
        bracket(phrase, relation_type)

# c = es_np.pairInfo("cell", "line", 0, 1, es_np.es)
class pairInfo():
    def __init__(self, w1, w2, loc1, loc2, es):
        self.w1 = w1
        self.w2 = w2
        # to use pair as a key, make it a tuple (immutable)
        self.pair = tuple([w1, w2])
        self.loc1 = loc1
        self.loc2 = loc2
        self.Npr = 0  # w2 prep w1
        self.full_adj = 0 # [ w1 | w2 ]
        self.partial_adj = 0  # w1 | w2
        self.d_method2count = defaultdict(int)

        self.d_method2count["Npr"] = self.count_Npr(w1, w2)
        self.d_method2count["full_adj"] = self.count_full_adj(w1, w2)
        self.d_method2count["partial_adj"] = self.count_partial_adj(w1, w2)
        
    def count_Npr(self, mod, head): 
        # Given a mod and head in the NP order ("stem cells"), we compute the number of docs
        # spn is stemmed prev_Npr  "[ cells of "  as in "cells of human stem"
        # sp is stemmed NP "stem ]"  as last word in the phrase
        # we need to compute the count using elasticsearch query qc_mult
        count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=False)
        return(count)

    def count_full_adj(self, mod, head):
        # full adjacent (stemmed) phrase made up entirely of the two terms
        count = qc_mult([["sp",  "[ " + mod + " | " + head + "  ]"]])
        return(count)

    def count_partial_adj(self, mod, head):
        # partial adjacent (stemmed) phrase made up of the two terms,
        # possibly within a longer phrase
        count = qc_mult([["sp",  mod + " | " + head ]])
        return(count)


# ie. based on count of spn, sp cooccurrence
def score_word_pairs(l_pairs, d_mh2counts, tree, relation_type="Npr"):
    score_add = 0
    score_mult = 1
    mh_path = []

    for pair in l_pairs:
        # make pair into a tuple so it can be used as a dict key
        pair = tuple(pair)

        [mod, head] = pair

        if d_mh.has_key(pair):
            # count has already been computed and cached in dict d_mh
            count = d_mh2counts[pair]
        else:
            if relation_type == "Npr":
                # Given a mod and head in the NP order ("stem cells"), we compute the number of docs
                # spn is stemmed prev_Npr  "[ cells of "  as in "cells of human stem"
                # sp is stemmed NP "stem ]"  as last word in the phrase
                # we need to compute the count using elasticsearch query qc_mult
                count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=False)
                d_mh[pair] = count
            elif relation_type == "fadj":
                # full adjacent (stemmed) phrase made up of the two terms
                count = qc_mult([["sp",  "[ " + mod + " | " + head + "  ]"]])
        mh_path.append([mod, head, count])    
        score_add += count
        # do laplace smoothing (+1 smoothing to avoid multiplying by 0)
        score_mult = score_mult * (count + 1)
    #print "bracketing: %s, %s, scores(add, mult): %i\t%i" % (tree, mh_path, score_add, score_mult)
    return([score_mult, score_add, tree, mh_path])

# path is a list of pairs of mod_index and head_index corresponding words
# l_words is list of words in a phrase
# d_mh is a dictionary with key = tuple[mod, head], value = count based on qc_mult result
# ie. based on count of spn, sp cooccurrence
def score_path(path, l_words, d_mh, ):
    score_add = 0
    score_mult = 1
    mh_path = []
    for pair in path:
        # make pair into a tuple so it can be used as a dict key
        pair = tuple(pair)

        [mod_index, head_index] = pair
        mod = l_words[mod_index]
        head = l_words[head_index]
        mh_path.append([mod, head])

        if d_mh.has_key(pair):
            # count has already been computed and cached in dict d_mh
            count = d_mh[pair]
        else:
            # we need to compute the count using elasticsearch query qc_mult
            count = qc_mult([head2spn(head), mod2sp(mod)], debug_p=False)
            d_mh[pair] = count
    
        score_add += count
        # do laplace smoothing (+1 smoothing to avoid multiplying by 0)
        score_mult = score_mult * (count + 1)
    print "path: %s, scores(add, mult): %i\t%i" % (mh_path, score_add, score_mult)

##########################################################################################
# for nc in document context study

"""
To use these functions:

cd /home/j/anick/patent-classifier/ontology/roles/
python2.7
import es_np_nc
import es_np_query

#To find doc_ids which contain a phrase
es_np_query.docs_matching("human cell line")
d = es_np_nc.test_docNc("US20070082860A1") 
# print info for all phrase of length 3
d.print_pinfo_len(3)

or use
es_np_nc.doc_compounds("US20070082860A1", 3) 

To dump many before_after vectors to a file
This function computes all docs containing the phrase (human cell line), computes
vectors and outputs to ba_vectors.hcl.txt
es_np_nc.dump_phr_vectors("human cell line", "ba_vectors.hcl.txt") 
"""        
##########################################################################################
# Computing local noun compound diagnostics

# get corpus frequency for a full (stemmed) phrase (using "sp" field)
# filters can be used to narrow to corpus to a specific year and/or domain
def get_corpus_freq(phr, l_filter_must=[]):
    sp_pattern = phr2sp(phr, phr_subset="f")
    r = qmamf(l_query_must=[["sp", sp_pattern]], l_filter_must=[], l_fields=[], doc_type="np", index_name="i_nps_bio", query_type="count")
    return(r["count"])

# get first location of a partial phrase pattern within a given doc
# es_np_nc.get_loc1("US7189536B2", "human cell", phr_subset="l")
def get_loc1_tf(doc_id, phr, phr_subset="f"):
    sp_pattern = phr2sp(phr, phr_subset=phr_subset)
    print "sp_pattern: %s" % sp_pattern
    r = qmamf(l_query_must=[["sp", sp_pattern]], l_filter_must=[["doc_id", doc_id]], l_fields=["phr", "loc"], doc_type="np", index_name="i_nps_bio", query_type="search")
    l_locs = []
    l_hits = r["hits"]["hits"]
    if l_hits == []:
        return([-1, 0])
    for hit in l_hits:
        loc = hit["fields"]["loc"][0]
        l_locs.append(int(loc))
    return([sorted(l_locs)[0], len(l_locs)])


# TODO: recreate index with locs as integers, remove conversion from str to int! ///

# sp is NP with | separating words and start and end brackets ([])  
#"spn":{"type":"string","analyzer":"analyzer_eng_n","index_options":"offsets"},
# based on prev_Npr feature (head_noun prep NP)


def doc_compounds(doc_id, phr_len):
    d = test_docNc(doc_id) 
    # print info for all phrase of length phr_len
    d.print_pinfo_len(phr_len)
    
# es_np_nc.dump_phr_vectors("human cell line", "ba_vectors.hcl.txt")
def dump_phr_vectors(phr, output_file):
    s_output = codecs.open(output_file, "w", encoding='utf-8')
    # get list of doc_ids matching the phrase
    l_docs = docs_matching(phr)
    i = 0
    for doc_id in l_docs:
        dnc = docNc(doc_id)
        dnc.print_pinfo_len(s_output, phr_len=3, verbose_p=False)
        i += 1
    print "[dump_phr_vectors]%i file vectors written to %s" % (i, output_file)
    s_output.close

# TBD: add fields for year and damain
class docNc():
    """
    Given a doc_id, a docNc (document noun compound) object maintains 2 dictionaries for the document:
    d_length2phr: given phrase length, returns list of compounds with that length
    d_phr2info: given a phrase, returns phrInfo instances which store data about the
    occurrences of the phrase within the doc.
    Note that the key for d_phr2info is a canonical phrase, in which all words are reduced to 
    singular noun form using the python inflect.py module.
    TODO: add a canonical form field to the es mapping.  Currently we rely on es minimal_english stemmer
    for canonicalizing phrases added to the es index.
    """
    def __init__(self, doc_id):
        self.doc_id = doc_id
        # lists of noun compounds within the doc, indexed by token length
        self.d_length2phr = defaultdict(list)
        # map nc (as a canonical phrase string, cphr) to a phrInfo object
        self.d_phr2info = {}

        self.populate_d_length2phr()
        # make sure l_locs is sorted within each phrInfo instance for this doc
        self.sort_pinfo()

    # TODO: use canonical phrase for phrase but keep surface phrase
    def populate_d_length2phr(self):
        # for each phrase length, retrieve all phrases in current doc
        # with that length and store the sorted list of sentence locations
        # in d_length2phr
        for phr_len in range(1,5):
            # retrieve all phrases of each length
            result = qs_mult([["length", phr_len ], ["doc_id", self.doc_id ]], l_fields=["phr", "term", "loc"]) 
            # result is a list of dictionaries of the form:
            # {u'_score': 1.0, u'_type': u'np', u'_id': u'US20070082860A1.xml_93', u'fields': {u'loc': [u'18'], u'phr': [u'amino acid residues']}, u'_index': u'i_nps_bio'}
            # for each phrase occurrence, extract the phrase and loc.
            for phr_occ in result:
                phr_info = phr_occ["fields"]
                # extract and store the phrase
                
                phr = phr_info["phr"][0]
                # we will index on the canonical phrase to collapse all variants together
                cphr = canonical_np(phr)

                term = phr_info["term"][0]
                # TODO: remove the int call after reindexing to fix bug where loc was stored as a string
                loc = int(phr_info["loc"][0])

                # extract and store the loc in a phrInfo instance
                # create one if one does not already exist for this doc and phrase
                # Note that d_phr2info uses the canonical phrase (cphr) as its key,
                # even though phrInfo objects take the surface phrase as its argument.
                # For speed, we might want to add the already computed cphr to the arguments
                # passed into phrInfo, so cphr doesn't need to be recomputed.
                if self.d_phr2info.has_key(cphr):
                    pinfo = self.d_phr2info[cphr]

                else:
                    pinfo = phrInfo(self.doc_id, cphr)
                    self.d_phr2info[cphr] = pinfo
                    # add the phrase to the dict of phrases accessed by length
                    self.d_length2phr[phr_len].append(cphr)
                #pdb.set_trace()
                pinfo.l_locs.append(loc)
                # keep a list of different surface forms for the canonical phrase
                pinfo.surface_forms.add(phr)
                #print "[populate_d_length2phr]len: %i, phr: %s, loc: %i" % (phr_len, phr, loc)

    # sort any fields within phrInfo instances that should be in sorted order
    # e.g. l_locs (the locations of occurrences of a canonical phrase).  Locations are sentence
    # numbers starting with 0.  The 0 line is the title.
    def sort_pinfo(self):
        for key in self.d_phr2info.keys():
            pinfo = self.d_phr2info[key]
            pinfo.l_locs.sort()
            pinfo.loc1 = pinfo.l_locs[0]
            pinfo.freq = len(pinfo.l_locs)
                
    # return phrases consisting of adjacent or separated (by 1) pairs of words in the phrase
    def get_phr_pairs(self, phr):
        l_words = phr.split(" ")
        l_pairs = []
        length = len(l_words)
        # go only to index length-1, since we are dealing with pairs of words.
        for i in range(0, length - 1):
            pair = l_words[i] + " " + l_words[i+1]
            pinfo = self.get_pinfo(pair)
            if pinfo != None:
                # save the key (a tuple of term indices) and the pinfo
                l_pairs.append([ (i, i+1), pinfo ])
            # also check for phrase made up of pairs separated by a term
            if (i+2) < length:
                sep_pair = l_words[i] + " " + l_words[i+2]
                #print "phr: %s, sep_pair: %s" % (phr, sep_pair)
                pinfo = self.get_pinfo(sep_pair)
                if pinfo != None:
                    l_pairs.append([ (i, i+2), pinfo ])

        return(l_pairs)

    def get_phr_triples(self, phr):
        #pdb.set_trace()
        l_words = phr.split(" ")
        l_triples = []
        length = len(l_words)
        # go only to index length-2, since we are dealing with triples of words.
        for i in range(0, length - 2):
            triple = l_words[i] + " " + l_words[i+1] + " " + l_words[i+2]
            pinfo = self.get_pinfo(triple)
            if pinfo != None:
                # save the key (a tuple of term indices) and the pinfo
                l_triples.append([ (i, i+1, i+2),   pinfo ])
        return(l_triples)

    def get_phr_fourples(self, phr):
        #pdb.set_trace()
        l_words = phr.split(" ")
        l_fourples = []
        length = len(l_words)
        # go only to index length-2, since we are dealing with triples of words.
        for i in range(0, length - 3):
            fourple = l_words[i] + " " + l_words[i+1] + " " + l_words[i+2] + " " + l_words[i+3]
            pinfo = self.get_pinfo(triple)
            if pinfo != None:
                # save the key (a tuple of term indices) and the pinfo
                l_fourples.append([ (i, i+1, i+2, i+3), pinfo ])
        return(l_fourples)

    def get_phr_words(self, phr):
        l_words = phr.split(" ")
        length = len(l_words)
        l_singles = []
        i = 0
        for word in l_words:
            pinfo = self.get_pinfo(word)
            if pinfo != None:
                # save the key (a tuple of term indices) and the pinfo
                l_singles.append([ (i), pinfo ])
            i += 1
        return(l_singles)

    def get_pinfo(self, phr):
        if self.d_phr2info.has_key(phr):
            pinfo = self.d_phr2info[phr]
        else:
            pinfo = None
        return(pinfo)

    # TBD
    # given a multiword phrase, return the set of key, head, mod combinations
    # for transformations of the phrase into a Noun prep Mod-NP combination.
    # ABC => 
    # C prep B ]
    # B prep A ]
    # C prep A ]
    # where "]" indicates the end of the modifier phrase
    def get_phr_npr_components(self, phr):
        l_words = phr.split(" ")
        l_nprtriples = []
        length = len(l_words)
        # go only to index length-2, since we are dealing with triples of words.
        for i in range(0, length - 2):
            triple = l_words[i] + " " + l_words[i+1] + " " + l_words[i+2]
            pinfo = self.get_pinfo(triple)
            if pinfo != None:
                # save the key (a tuple of term indices) and the pinfo
                l_triples.append([ (i, i+1, i+2),   pinfo ])
        return(l_triples)

        #///in progress.
            

    def get_phr_npr_components(self, phr):
        l_words = phr.split(" ")
        pass

    # d.print_pinfo_len(None, 3, True) to get all phrases with length 3 and their subphrase info
    # We pass in an output stream as first parameter and set verbose_p to False to send
    # output to a stream instead of stdout.
    def print_pinfo_len(self, s_output, phr_len=3, verbose_p=False):
        #s_output = codecs.open(output_file, "w", encoding='utf-8')
        # For each phrase in the document with a given length (e.g. 3)

        if verbose_p:
            print "KEY:"
            print "fp: phrase, tf, loc1"
            print 'ba: (0), (1), (2), (0,1), (1,2), (0,2)'
            print 'pp: (0, "l"), (0, "r"), (1, "l"), (1, "r"), (2, "l"), (2, "r")'
            print ""


        for cphr in self.d_length2phr[phr_len]:
            # l_components is a list of [key_tuple, pinfo] pairs
            # The key identifies the component terms using word indices starting at 0.
            # e.g. key (1,2) indicates an adjacent pair consisting of the second and third words of the 
            # full top level phrase.  pinfo contains a list of all locations for the phrase, as well as the first
            # location in the document.  This can be used to determine whether the component phrases occur before, after,
            # or not at all, compared to the full phrase.

            l_components = []
            # create a dictionary mapping subphrase types to relative locations: b(efore), a(fter), depending
            # on whether the subphrase occurs first in the document before or after the full phrase (cphr)
            d_subphrase2rel_loc = {}

            full_phrase_key = None

            #self.print_pinfo(phr)
            #pdb.set_trace()
            # construct all the subphrases and test whether they appear in the doc
            # Get the loc1 for the full phrase to use for testing relative locations
            # of subphrases
            if phr_len >= 4:
                if full_phrase_key == None:
                    full_phrase_key = (0,1,2,3)
                else:
                    l_components.extend(self.get_phr_fourples(cphr))
            if phr_len >= 3:
                if full_phrase_key == None:
                    full_phrase_key = (0,1,2)
                else:
                    l_components.extend(self.get_phr_triples(cphr))
            if phr_len >= 2:
                if full_phrase_key == None:
                    full_phrase_key = (0,1)
                else:
                    l_components.extend(self.get_phr_pairs(cphr))
            if phr_len >= 1:
                if full_phrase_key == None:
                    full_phrase_key = (0)
                else:
                    l_components.extend( self.get_phr_words(cphr))                    

            # surface form is used so that es stemming will apply
            full_phrase_surface = list(self.d_phr2info[cphr].surface_forms)[0]
            # term freq is the number of locations the phrase appears in the doc
            full_phrase_tf = len(self.d_phr2info[cphr].l_locs)
            # loc1 is the first sentence in which the term appears in the doc as
            # a full np.
            full_phrase_loc1 = self.d_phr2info[cphr].loc1

            # sort based on loc1
            l_components = sorted(l_components, key=lambda x: x[1].loc1)
            if verbose_p:
                print "%s:" % cphr

            for (key, pinfo) in l_components:
                if pinfo.loc1 <= full_phrase_loc1:
                    rel_loc = "b"
                else: 
                    rel_loc = "a"
                d_subphrase2rel_loc[key] = rel_loc
                
                #pdb.set_trace()
                if verbose_p:
                    print("key: %s, rel_loc: %s " % (str(key), rel_loc)),
                    self.print_pinfo(pinfo)

            full_phrase_vector = "\t".join([full_phrase_surface, str(full_phrase_tf), str(full_phrase_loc1)])
            ba_vector = self.make_ba_vector(d_subphrase2rel_loc)

            # create the d_pp_key2info dictionary here ///
            d_pp_key2info = get_head_mod_loc1_tf(full_phrase_surface, self.doc_id)
            #partial phrase vector 
            pp_vector = make_pp_vector(full_phrase_loc1, d_pp_key2info)

            entire_vector = "\t".join([full_phrase_vector, ba_vector, pp_vector])

            if verbose_p:
                print "fp:%s" % full_phrase_vector
                print "ba:%s" % ba_vector
                print "pp:%s" % pp_vector
                print ""
            else: 
                # output to file
                s_output.write("%s\n" % entire_vector)

        #s_output.close()

    # return a tab separated string with before-after labels for each
    # subphrase component in subphrase dictionary for the phrase.  Values are b,a,n(one)
    def make_ba_vector(self, d_subphrase2rel_loc):
        vector_fields = []
        for key in [(0), (1), (2), (0,1), (1,2), (0,2)]:
            try:
                rel_loc = d_subphrase2rel_loc[key]
            except:
                rel_loc = "n"
            vector_fields.append(rel_loc)
        vector = "\t".join(vector_fields)
        return(vector)

    def print_phr_pinfo(self, phr, verbose_p=False):
        if self.d_phr2info.has_key(phr):
            pinfo = self.d_phr2info[phr]
            if verbose_p == True:
                print "[print_pinfo]cphr: %s, phr: %s, freq: %i, l_locs: %s" % (pinfo.pchr, pinfo.phr, pinfo.freq, pinfo.l_locs)
            else:
                print "%i %s\t(%s)\t%i" % (pinfo.l_locs[0], pinfo.cphr, pinfo.phr, pinfo.freq)

    def print_pinfo(self, pinfo, verbose_p=False):
        if verbose_p == True:
            print "[print_pinfo]cphr: %s, phr: %s, freq: %i, l_locs: %s" % (pinfo.pchr, pinfo.phr, pinfo.freq, pinfo.l_locs)
        else:
            print "loc1: %i %s\t(%s)\tfreq:%i" % (pinfo.l_locs[0], pinfo.cphr, pinfo.phr, pinfo.freq)

    # /// TBD
    # given the head and modifier phr of an Npr relationship,
    # find all occurrences in the current doc and return the first location.
    def spn_sp2loc1(head, phr):
        pass
"""
    def get_loc1_components(self, phr):
        # keep track of the first occurrence sentence for phrase and its components
        l_loc1_component = []
"""

# compare loc1 for a partial phrase(pp) and the full phrase(phr)
# and return n(one), b(efore), a(fter)
def pp_rel_loc(phr_loc1, pp_loc1):
    if pp_loc1 == -1:
        return("n")
    if pp_loc1 <= phr_loc1:
        return("b")
    else:
        return("a")

# partial phrase vector for a 3-word compound
def make_pp_vector(phr_loc1, d_key2info):
    vector_fields = []
    for key in [(0, "l"), (0, "r"), (1, "l"), (1, "r"), (2, "l"), (2, "r")]:
        (pp_loc1, pp_tf) = d_key2info[key]
        rel_loc = pp_rel_loc(phr_loc1, pp_loc1)
        vector_fields.append(rel_loc)
        vector_fields.append(str(pp_tf))
    pp_vector = "\t".join(vector_fields)
    return(pp_vector)


def get_head_mod_loc1_tf(phr, doc_id):
    l_words = phr.split(" ")
    # key is tuple of (word_index, position) 
    # e.g. (2,"l") means for the 3rd word in phr serving as a left start of compounds in the doc
    # where pos is either l(eft) or r(ight) position in a compound
    # and word_index is the integer index n the current phrase
    # Each key maps to [loc1, pattern_freq]
    d_pp_key2info = {}
    i = 0
    for word in l_words:
        pos = "l"
        d_pp_key2info[(i, pos)] = get_loc1_tf(doc_id, word, phr_subset=pos)
        pos = "r"
        d_pp_key2info[(i, pos)] = get_loc1_tf(doc_id, word, phr_subset=pos)
        i += 1
    return(d_pp_key2info)

        


# Given a list of doc_ids and a phrase length (e.g. 3), find all
# phrases appearing in those docs and output an annotation file 
# consisting of those phrases.
# >>> ds = es_np_query.docs_matching("cell")       
# >>> len(ds)
# 97465
# remove dup doc_ids
# dss = set(ds)
# >>> ds100 = ds[0:100]
# es_np_nc.print_annotation_file(ds[0:10], l_phr_length=[3], output_file_prefix="cell_0-10")

def print_annotation_file(doc_list, l_phr_length=[3], output_file_prefix="sample"):
    # words that really shouldn't be included in noun compounds
    # % perchloric acid, patient 's organ, karnell et al

    # we create two output files: the set of phrases and the set of docs from which the phrases
    # came. The filenames are the output_file_prefix + .<phr_length>.annot and + <phr_length>.docs
    
    len_qualifier = "-".join(map(str, l_phr_length))
    
    full_output_file_prefix = output_file_prefix + "." + len_qualifier
    s_output_annot = codecs.open(full_output_file_prefix + ".annot", "w", encoding='utf-8')
    s_output_docs = codecs.open(full_output_file_prefix + ".docs", "w", encoding='utf-8')

    # set of surface_forms (for a canonical form)
    surface_set = set()
    for doc_id in doc_list:
        s_output_docs.write("%s\n" % doc_id)

        # collect all canonical forms (cphr) for phrases of length phr_length in the document
        cphr_set = set()
        dnc = docNc(doc_id)

        for phr_len in l_phr_length:
            cphr_set.update( dnc.d_length2phr[phr_len] )

        for cphr in cphr_set:
            # if cphr == 'human immunodeficiency viru':
            #    pdb.set_trace()
            # use the first surface variant, instead of the canonical form
            # since for some words the canonical form is not a word ("viru")
            surface_form  = list(dnc.d_phr2info[cphr].surface_forms)[0]
            surface_set.add(surface_form)

    #pdb.set_trace()        
    for surface_variant in surface_set:
        # filter out phrases with illegal words or punc

        '''
        # first test for illegal punc
        if illegal_phrase_p(surface_variant):
           break 
        # now test for illegal words
        surface_words = surface_variant.split(" ")
        #pdb.set_trace()
        if list(illegal_words & set(surface_words)) == []:
            s_output.write(" | %s | \n" % surface_variant)
        '''


        if not illegal_phrase_p(surface_variant):
            #print(" | %s | \n" % surface_variant)
            s_output_annot.write(" | %s | \n" % surface_variant)

    s_output_annot.close()
    s_output_docs.close()

            

class phrInfo():
    """
    phr should be canonical (i.e. result of canonical_np())
    A phrInfo instance contains data relating to all occurrences of a canonical phrase in a document, not
    just a single occurrence.
    """
    def __init__(self, doc_id, phr):
        self.doc_id = doc_id
        self.phr = phr
        # canonical np reduces all component words to singular form
        self.cphr = canonical_np(phr)
        self.term = phr.replace(" ", "_")
        self.l_words = phr.split(" ")
        # location of first occurrence of the phrase (initialized to None)
        self.loc1 = None
        # freq is number of occurrences of the phrase in the document
        self.freq = 0
        # l_locs lists sentence numbers in which the phrase occurs, sorted in ascending order, so that
        # l_locs[0] will be the first location in the document.
        self.l_locs = []
        # set of the surface variants for this canonical phrase
        self.surface_forms = set()
        # different types of subcomponents of the phrase
        # for now, index by offset tuples: e.g. (1), (0,1) where the numbers refer to the
        # indices of words in the phrase as a whole.
        # rel_loc is a location relative to the top level (full) phr: b(efore) or a(fter)
        # referring to where the first location of the subphrase appears relative to the full phrase.
        self.d_subphrase2rel_loc = {}

    def add_surface_form(self, surface_form):
        self.surface_forms.add(surface_form)

# extract all noun compounds and their subpart locations within a given doc
# d = es_np_nc.test_docNc("US20070082860A1")
def test_docNc(doc_id):
    dnc = docNc(doc_id)    
    return(dnc)


"""
ISSUES
Are unknown words treated correctly?

>>> es_np.bracket("zip stem cell research")     
bracketing: ['zip', [['stem', 'cell'], 'research']] 96 18 [['stem', 'cell', 11], ['cell', 'research', 7], ['zip', 'research', 0]]
bracketing: [['zip', ['stem', 'cell']], 'research'] 96 18 [['stem', 'cell', 11], ['zip', 'cell', 0], ['cell', 'research', 7]]
bracketing: [[['zip', 'stem'], 'cell'], 'research'] 96 18 [['zip', 'stem', 0], ['stem', 'cell', 11], ['cell', 'research', 7]]

We should incorporate prob of two word phrases where first word is beginning of phrase

Using the Npr allows us to catch cases where the NP is a short form of a relationship between between two nouns.  However,
this does not cover names or modifier relationship, as in
bracketing: [u'creatine', [u'kinase', u'activity']] 4295 862 [[u'kinase', u'activity', 858], [u'creatine', u'activity', 4]]
bracketing: [[u'creatine', u'kinase'], u'activity'] 859 858 [[u'creatine', u'kinase', 0], [u'kinase', u'activity', 858]]

or

bracketing: [u't', [u'cell', u'proliferation']] 20314 2907 [[u'cell', u'proliferation', 2901], [u't', u'proliferation', 6]]
bracketing: [[u't', u'cell'], u'proliferation'] 11608 2904 [[u't', u'cell', 3], [u'cell', u'proliferation', 2901]]

Thus, we need to integrate evidence from different types of np formation.

relational NP prep NP
verbal V NP
dispersion of head term in complete NP bigrams
prob mod given dom
prob dom given mod

want to score each mod head pair in dominance tree using multiple indicators

using chi square (from Nakov paper)

A #(w1,w2) cooccurences in mod-dom relationship
B #(w1, !w2) occurrences of w1 as mod without w2 as head
C #(!w1, w2) occurrences of w2 as head without w1 as mod
D N - A - B - C
N A+B+C+D total number of bigrams (head-mod relations) = Npr + ((length of all phrases) - # phrases)
each phrase can have n - 1 dom/mod relations in it.

estimate based on (1) % of phrases that have an Npr relation
(2) the average length of a phrase

length of all phrases = average length * number of phrases
#Npr = number of phrases * % phrases containing Npr 

Types of compounds
relational (verbal)
subtype (a isa b)
adjectival
proper-name
name subtype (ab isa b)

Another possible indicator: # times terms appear in same sentence or nearby sentence.  This would help with contextually
based NC's such as malaria mosquitos

BUGS:

Some phrases must have extra ws in them, resulting in such phrases in our index:
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'| | | | | | | | | |']}
{u'phr': [u'ctgcctgtcccaatgctc-agcc | | | | | | | | | | | | | | | | | | | | ctgcctgtccc']}

idea: local compound resolution.  Work from beginning of doc.  Track binary compounds and Npr relations.  For each 
compound with length > 2, can it be resolved using previously seen compounds?  If not, put it on TBD list.  
At end of doc, retry all TBD compounds.  Those that cannot be solved locally go on NLC list (nonlocal compound list), to be
solved using global means.  Perhaps they can be partially solved locally.

output: number of compounds solvable by prior context.  
number solvable by local context
number solvable by global context
compare to solving them all by global context.

"""
