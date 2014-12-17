# fan.py
# feature analysis over time
# based on phran.py
# phrasal analysis of heads and mods
# This is done independent of ACT role analysis 

# given a list of terms in a file
# return an instance of a phr_info object
# dict d_term2heads with key = term, value a list of heads occurring with the term
# dict d_term2mods with key = term, value a list of mods occurring with the term
# dict d_head2count with key = a term used as a head, value = count of terms it occurs with
# dict d_mod2count with key = a term used as a mod, value = count of terms it occurs with
# headed_term_count = # terms that appear with a head
# modified_term_count = # terms that appear with a modifier

# To use:
# Load data
# rfcs = fan.RFreq("ln-us-cs-500k", 1997, 2006)
# Create a cohort of terms with specified growth in time span
# l_cohort_cs = rfcs.filter(1998, 1998, 2006, 1, 2000, 30, 10000)
# Output a file with features sorted by conditional prob ratio
# fan.cohort_features("ln-us-cs-500k", 2003, l_cohort_cs, "c98-06_30")
# To see top features:
# cat 2003.c98-06_30.fscores | sortnr -k3 | grep prev | head -100 | sortnr -k1 | more

# mechanical engineering corpus
# rfcs = fan.RFreq("ln-us-A28-mechanical-engineering", 1997, 2006)
# l_cohort_me = rfcs.filter(1998, 1998, 2006, 1, 2000, 10, 10000)
# fan.cohort_features("ln-us-A28-mechanical-engineering", 2003, l_cohort_me, "c98-06_30")

# TODO: compute cumulative feature scores

import pdb
import utils
from collections import defaultdict
from operator import itemgetter
import math
import codecs
import os

import pnames
import roles_config

from operator import itemgetter

# for WoS
# sources are in, e.g. /home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k/subcorpora/2000/data/d0_xml/01/files/WoS.out.2000000024

# 9/30/14 NOTE: tf.f file no longer needed.  The doc freq for terms can be gotten from .terms file
# Before running this, the corpus tv dir should contain all yearly tf.f files, which are
# created by running
# sh make_tf_f.sh ln-us-cs-500k
# sh make_tf_f.sh wos-cs-520k 

# term file should be a year file of the form: term category freq
# 

# rewrite to use .tf file instead of gt1 (which comes from w0.0).  
# The w0.0 file might not be able to classify some terms in a year, which
# will result in their freq looking like 0.  So it is better to 
# generate the frequency info first and then add the category data from the gt1 file.
# DONE


#corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents"
#CORPUS_ROOT = "/home/j/anick/patent-classifier/ontology/roles/data/patents"
corpus_root = roles_config.CORPUS_ROOT

# return a sorted (by descending numeric value) list of key-value pairs for a dict. 
def sort_dict_num_values(dict):
    l_key_values = []
    for key in dict.keys():
        l_key_values.append([key, dict[key]])

    l_key_values.sort(utils.list_element_2_sort)
    return(l_key_values)


# return a string with 2 decimal points of precision for the result of the division
def prob2str(count, total):
    fval = count / float(total)
    return("%.2f" % fval)


# pi98 = fan.phrInfo("ln-us-A21-computers", 1998)
# pi99 = fan.phrInfo("ln-us-A21-computers", 1999)
# pi00 = fan.phrInfo("ln-us-A21-computers", 2000)
# modified from phran.py to be independent of ACT role labels
class phrInfo():
    def __init__(self, corpus, year):
        year = str(year)
        # term file is used for extracting the doc frequency of terms for the year
        #term_file = corpus_root + "/" + corpus + "/data/tv/" + year + ".tf.f"
        #term_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "tf.f")
        #term_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "terms")
        term_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "terms.2")

        self.d_term2heads = defaultdict(list)
        self.d_term2mods =  defaultdict(list)
        self.d_head2terms = defaultdict(list)
        self.d_mod2terms =  defaultdict(list)
        self.d_head2count = defaultdict(int)
        self.d_head2count_2 = defaultdict(int)
        self.d_mod2count = defaultdict(int)
        self.d_mod2count_2 = defaultdict(int)
        self.term_count = 0
        self.headed_term_count = 0
        self.headed_term_count_2 = 0
        self.modified_term_count = 0
        self.modified_term_count_2 = 0
        self.d_term2freq = defaultdict(int)
        self.l_singletons = []
        self.l_head_counts = []
        self.l_mod_counts = []

        # sum of the frequencies for all terms containing the mod or head
        # use this to capture the average spread
        self.d_mod2sum_freq = defaultdict(int)
        self.d_head2sum_freq = defaultdict(int)
        self.d_mod2average_spread = defaultdict(int)
        self.d_head2average_spread = defaultdict(int)

        # list sorted by freq [[term, freq],...]
        self.l_tf = []

        # open the file and import list of terms
        s_term_file = codecs.open(term_file, encoding='utf-8')
        for term_line in s_term_file:
            term_line = term_line.strip("\n")
            term_fields = term_line.split("\t")
            term = term_fields[0]
            # freq is the number of docs the term occurred in (this year)
            freq = term_fields[1]
            freq = int(freq)
            self.d_term2freq[term] = freq
            self.term_count += 1
            self.l_tf.append([term, freq])
        s_term_file.close()

        # sort the term list by doc frequency
        self.l_tf.sort(utils.list_element_2_sort)

        self.compute_heads_mods()
       
    # revised version 10/5/14
    # term_no_mod is actually the head word only, so mod is phrase before last word
    # term_no_head is actually the mod
    # note that we have to be consistent between the conditions of mod2count and mod2terms in terms of 
    # the frequency criteria (>=2)
    def compute_heads_mods(self):
        for term in self.d_term2freq.keys():

            l_words = term.split(" ")
            if len(l_words) > 1:
                # term is a phrase.  Check for head and mod.
                term_no_mod = " ".join(l_words[1:])
                #if self.d_term2freq[term_no_mod] >= 2:
                #if self.d_term2freq.has_key(term_no_mod):
                # Then subterm exists on its own as a term in the corpus (appears at least twice)
                # extract the first word as the mod(ifier) and the remainder as the term_no_mod
                mod = l_words[0]
                #self.d_term2mods[term_no_mod].append(mod)
                #self.d_mod2terms[mod].append([term_no_mod, self.d_term2freq[term]])
                # collect all the modifiers of the head (term_no_mod) and their frequencies

                self.d_head2terms[term_no_mod].append([mod, self.d_term2freq[term]])
                self.d_head2sum_freq[term_no_mod] += self.d_term2freq[term]
                #self.modified_term_count += 1
                #self.d_mod2count[mod] += 1
                # leave out the disp at doc freq 1 for now, for efficiency
                # self.d_head2count[term_no_mod] += 1
                # Record counts with a document freq threshold of 2
                # where doc freq is the count for the full term
                if self.d_term2freq[term] >= 2:                        
                    self.d_head2count_2[term_no_mod] += 1

                self.d_head2average_spread[term_no_mod] = float(self.d_head2sum_freq[term_no_mod]) / self.d_head2count_2[term_no_mod]

                term_no_head = " ".join(l_words[0:len(l_words) - 1])

                # if self.d_term2freq.has_key(term_no_head):
                # Then subterm exists on its own
                head = l_words[-1]
                #self.d_term2heads[term_no_head].append(head)
                self.d_mod2terms[term_no_head].append([head, self.d_term2freq[term]])
                self.d_mod2sum_freq[term_no_head] += self.d_term2freq[term]
                #self.headed_term_count += 1
                # leave out the disp at doc freq 1 for now, for efficiency
                #self.d_mod2count[head] += 1
                # Record counts with a document freq threshold of 2
                if self.d_term2freq[term] >= 2:
                    self.d_mod2count_2[term_no_head] += 1

                self.d_mod2average_spread[term_no_head] = float(self.d_head2sum_freq[term_no_head]) / self.d_head2count_2[term_no_head]

            else:
                # we have a single word term
                self.l_singletons.append(term)
                
        # sort heads and mods
        for key in self.d_mod2terms.keys():
            self.d_mod2terms[key].sort(utils.list_element_2_sort)
        for key in self.d_head2terms.keys():
            self.d_head2terms[key].sort(utils.list_element_2_sort)


    def sort_heads(self):
        for head in self.d_head2count.keys():
            self.l_head_counts.append([head, self.d_head2count[head]])
        self.l_head_counts.sort(utils.list_element_2_sort)
        return(self.l_head_counts)

    def sort_mods(self):
        for mod in self.d_mod2count.keys():
            self.l_mod_counts.append([mod, self.d_mod2count[mod]])
        self.l_mod_counts.sort(utils.list_element_2_sort)
        return(self.l_mod_counts)


# difference in head and mod ratios between terms in
# corpus 2 (pi2) and corpus 1 (pi1), normalized by 
# term counts in the corpora
def hm_diff(pi2, pi1):
    normalization_factor = pi1.term_count / float(pi2.term_count)
    print "[hm_diff]pi1.term_count: %s, pi2.term_count: %s" % (pi1.term_count, pi2.term_count)
    l_mod_diff = []
    l_head_diff = []
    for term in pi2.d_head2count_2.keys():
        # Before computing ratios of dispersion,
        # do +1 smoothing, in case term has no instances in corpus 1
        # to avoid division by zero
        #pi2_count = pi2.d_head2count[term] + 1
        #pi1_count = pi1.d_head2count[term] + 1
        pi2_count_2 = pi2.d_head2count_2[term] + 1
        pi1_count_2 = pi1.d_head2count_2[term] + 1
        #score = (pi2_count / float(pi1_count)) * math.log(abs(pi2_count - pi1_count) + 1, 2) * normalization_factor
        #score = math.log((pi2_count / float(pi1_count)), 2) * math.log(abs(pi2_count - pi1_count) + 1, 2) * normalization_factor
        score2 = math.log((pi2_count_2 / float(pi1_count_2)), 2) * math.log(abs(pi2_count_2 - pi1_count_2) + 1, 2) * normalization_factor
        #score = (pi2_count / float(pi1_count)) * abs(pi2_count - pi1_count) * normalization_factor
        #score = (pi2_count / float(pi1_count)) * math.log(abs(pi2_count - pi1_count) + 1, 10) * normalization_factor
        #l_head_diff.append([term, score, pi2_count, pi1_count, score2, pi2_count_2, pi1_count_2])
        l_head_diff.append([term, score2, pi2_count_2, pi1_count_2])

    for term in pi2.d_mod2count_2.keys():
        # do +1 smoothing, in case term has no instances in corpus 1
        # to avoid division by zero
        #pi2_count = pi2.d_mod2count[term] + 1
        #pi1_count = pi1.d_mod2count[term] + 1
        pi2_count_2 = pi2.d_mod2count_2[term] + 1
        pi1_count_2 = pi1.d_mod2count_2[term] + 1

        #score = (pi2_count / float(pi1_count)) * math.log(abs(pi2_count - pi1_count) + 1, 2) * normalization_factor
        #score = math.log((pi2_count / float(pi1_count)), 2) * math.log(abs(pi2_count - pi1_count) + 1, 2) * normalization_factor
        score2 = math.log((pi2_count_2 / float(pi1_count_2)), 2) * math.log(abs(pi2_count_2 - pi1_count_2) + 1, 2) * normalization_factor
        #score = (pi2_count / float(pi1_count)) * abs(pi2_count - pi1_count) * normalization_factor
        #score = (pi2_count / float(pi1_count)) * math.log(abs(pi2_count - pi1_count) + 1, 10) * normalization_factor
        l_mod_diff.append([term, score2, pi2_count_2, pi1_count_2])

    l_head_diff.sort(utils.list_element_2_sort)
    l_mod_diff.sort(utils.list_element_2_sort)
    # note we only keep score2 now.

    return([l_head_diff, l_mod_diff])


# given a corpus and a range of years, generate phrase info and compute diffs

# prcs = fan.PiRange("ln-us-A21-computers", 1997, 2000)
# prme = fan.PiRange("ln-us-A28-mechanical-engineering", 1997, 2000)

# prmb3 = fan.PiRange("ln-us-A27-molecular-biology", 1997, 1998)
class PiRange():
    def __init__(self, corpus, start_year, end_year): 
        end_range = end_year + 1
        # dictionary to map year to phrInfo objects
        self.d_year2pi = {}
        self.d_1year2mod_diff = {}
        self.d_1year2head_diff = {}
        self.d_2year2mod_diff = {}
        self.d_2year2head_diff = {}
        for year in range(start_year, end_range):
            self.d_year2pi[year] = phrInfo(corpus, year)
            print "[pi_range]Created phrInfo for year: %i" % year
        # compute the dispersion diff scores

        start_range = start_year + 2
        for year in range(start_range, end_range):

            prev_year1 = year - 1
            prev_year2 = year - 2

            (self.d_1year2head_diff[year], self.d_1year2mod_diff[year]) = hm_diff(self.d_year2pi[year], self.d_year2pi[prev_year1])
            print "[pi_range]Created diff data for 1 year span ending: %i" % year
            """
            (self.d_2year2head_diff[year], self.d_2year2mod_diff[year]) = hm_diff(self.d_year2pi[year], self.d_year2pi[prev_year2])
            print "[pi_range]Created diff data for 2 year span ending: %i" % year
            """

# start_year should be 2 years ahead of the earliest year for which we have data
# e.g. 1999        
def print_pi_range(corpus, pi_range, start_year, end_year):
    end_range = end_year + 1
    for year in range(start_year, end_range):
        # We'll use the threshold of 2 docs per term, which requires resorting our term lists
        #top_mods1 = sorted(pi_range.d_1year2mod_diff[year], key=lambda x: (x[4],x[4]), reverse=True)[0:50]
        top_mods1 = pi_range.d_1year2mod_diff[year][0:50]
        print "%s" % top_mods1
        #top_heads1 = sorted(pi_range.d_1year2head_diff[year], key=lambda x: (x[4],x[4]), reverse=True)[0:50]
        #top_mods2 = sorted(pi_range.d_2year2mod_diff[year], key=lambda x: (x[4],x[4]), reverse=True)[0:50]
        #top_heads2 = sorted(pi_range.d_2year2head_diff[year], key=lambda x: (x[4],x[4]), reverse=True)[0:50]

# to get term freq of a term in a year from pi_range: <pi_range>.d_year2pi[2006].d_term2freq["gene"]
# to get the terms for a mod: <pi_range>.d_year2pi[1999].d_mod2terms["r1is"]        
#/// in progress


# fan.trend("ln-us-A27-molecular-biology", prmb5, 1999, 50, 1997, 2000)
# fan.trend("ln-us-A27-molecular-biology", prmb5, 1999, 50, 1997, 1999)
def trend(corpus, pi_range, disp_year, max_terms, start_year=1997, end_year=2007):
    trend_file = pnames.tv_dir(corpus_root, corpus) + "/trend." + str(disp_year)
    s_trend_file = codecs.open(trend_file, "w", encoding='utf-8')

    end_range = end_year + 1
    # get the top dispersion terms for a given year and print out the trend from start_year to end_year
    #top_mods1  = sorted(pi_range.d_1year2mod_diff[disp_year], key=lambda x: (x[4],x[4]), reverse=True)[0:50]
    # Use the difference between 1 year ago and present (d_1year2mod_diff)
    top_mods1  = pi_range.d_1year2mod_diff[disp_year][0:50]
    top_heads1 = pi_range.d_1year2head_diff[disp_year][0:50]

    l_mods_disp = []
    l_mods_freq = []
    l_heads_disp = []
    l_heads_freq = []
    l_mods_df_ratio = []
    l_heads_df_ratio = []

    #print "mods"
    rank = 1
    for item in top_mods1[0:max_terms]:
        freqs_str = ""
        term = item[0]

        # output dispersion for the term in range
        disp_str = "dm" + "\t" + str(rank) + "\t" + repr(term)
        for year in range(start_year, end_range):
            l_mods_disp.append(pi_range.d_year2pi[year].d_mod2count_2[term])
            single_disp_str = "\t" + str(pi_range.d_year2pi[year].d_mod2count_2[term])
            disp_str += single_disp_str

        print "%s" % disp_str
        s_trend_file.write("%s\n" % disp_str)

        #print "%s from %i to %i" % (item, start_year, end_year)
        freqs_str = "fm" + "\t" + str(rank) + "\t" + repr(term)
        for year in range(start_year, end_range):
            l_mods_freq.append(pi_range.d_year2pi[year].d_term2freq[term])
            # get the doc freq for the term in this year
            freq_str = "\t" + str(pi_range.d_year2pi[year].d_term2freq[term])
            freqs_str += freq_str
        print "%s" % freqs_str
        s_trend_file.write("%s\n" % freqs_str)

        # ratio line
        ratios_str = "rm" + "\t" + str(rank) + "\t" + repr(term)
        offset = 0
        for year in range(start_year, end_range):
            ratio = (float(l_mods_disp[offset]) + 1) / (l_mods_freq[offset] + 1)
            ratios_str == "\t" + format(ratio, ".2f")
            offset += 1
        s_trend_file.write("%s\n" % ratios_str)

        rank += 1

    #print "heads"
    rank = 1
    for item in top_heads1[0:max_terms]:
        freqs_str = ""
        term = item[0]
        
        # output dispersion for the term in range
        disp_str = "dh" + "\t" + str(rank) + "\t" + repr(term)
        for year in range(start_year, end_range):
            l_heads_disp.append(pi_range.d_year2pi[year].d_head2count_2[term])
            single_disp_str = "\t" + str(pi_range.d_year2pi[year].d_head2count_2[term])
            disp_str += single_disp_str
        print "%s" % disp_str
        s_trend_file.write("%s\n" % disp_str)

        #print "%s from %i to %i" % (item, start_year, end_year)
        freqs_str = "fh\t" +  str(rank) + "\t" + repr(term)
        for year in range(start_year, end_range):
            l_heads_freq.append(pi_range.d_year2pi[year].d_term2freq[term])
            # get the doc freq for the term in this year
            freq_str = "\t" + str(pi_range.d_year2pi[year].d_term2freq[term])
            freqs_str += freq_str
        print "%s" % freqs_str
        s_trend_file.write("%s\n" % freqs_str)

        # ratio line
        ratios_str = "rh" + "\t" + str(rank) + "\t" + repr(term)
        offset = 0
        for year in range(start_year, end_range):
            ratio = (float(l_heads_disp[offset]) + 1) / (l_heads_freq[offset] + 1)
            ratios_str == "\t" + format(ratio, ".2f")
            offset += 1
        s_trend_file.write("%s\n" % ratios_str)

        rank += 1

# store a range of term,year=>freq dictionaries
# rfcs = fan.RFreq("ln-us-cs-500k", 1997, 2006)
# rf = fan.RFreq("ln-us-all-600k", 1997, 2006)
# rfw = fan.RFreq("wos-cs-520k", 1997, 2006)
# Range frequencies
# Depends on: <year>.terms files must exist for all years in range

# rftcs = fan.RFreq("ln-us-A21-computers", 1997, 2007, "2005.act.cat.w0.0.t")


# rfa22 = fan.RFreq("ln-us-A22-communications", 1997, 2007, "")
class RFreq():

    def __init__(self, corpus, start_year, end_year, term_subset_file=""):
        root = corpus_root
        # frequency for a term-year combination
        self.d_ty2freq = defaultdict(int)
        # number of terms in this year
        self.d_y2tcount = defaultdict(int)
        # number of new terms in this year
        self.d_y2ncount = defaultdict(int)
        # has the term been seen in any year so far
        self.d_term2seen = defaultdict(bool)
        # is term new in this range (i.e., appear after the first year)
        self.d_term2new = defaultdict(bool)
        # appearance year for term
        self.d_term2y1 = defaultdict(int)
        # all new terms in a year
        self.d_y2l_cohort = defaultdict(list)
        # list of freq for the term starting with first appearance year
        self.d_term2l_history = defaultdict(list)
        self.corpus = corpus
        self.term_subset_p = False
        if term_subset_file != "":
            self.term_subset_p = True
        
        self.d_term_subset = {}
        # If term_subset_file is not"", populate a dictionary of the subset of terms and 
        # only use terms in this dictionary in cohorts.
        if self.term_subset_p:
            term_subset_path = pnames.tv_dir(corpus_root, corpus) + "/" + term_subset_file
            s_term_subset = codecs.open(term_subset_path,  encoding='utf-8')
            for term_line in s_term_subset:
                term_line = term_line.strip("\n")
                term_fields = term_line.split("\t")
                term = term_fields[0]
                self.d_term_subset[term] = True
            s_term_subset.close()
            print "[fan.py Rfreq]Using term subset with %i terms" % len(self.d_term_subset.keys())

        for year in range(start_year, end_year + 1):
            #term_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "terms.2")
            term_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "terms")
            s_term_file = codecs.open(term_file, encoding='utf-8')
            print "[RFreq]loading terms for year: %i" % year
            for term_line in s_term_file:
                term_line = term_line.strip("\n")
                term_fields = term_line.split("\t")
                term = term_fields[0]
                if self.term_subset_p == False or self.d_term_subset.has_key(term):
                    #pdb.set_trace()
                    # freq is the number of docs the term occurred in (this year)
                    freq = term_fields[1]
                    freq = int(freq)

                    ty = tuple([term, year])

                    # save the freq for the year
                    self.d_ty2freq[ty] = freq
                    self.d_y2tcount[year] += 1

                    # record the first appearance year (y1) for the term
                    if not self.d_term2seen[term]:
                        # if the term does not appear in the start year, we will call it
                        # new in this range
                        if year != start_year:
                            self.d_term2new[term] = True
                            self.d_y2ncount[year] += 1
                        self.d_term2y1[term] = year
                        self.d_y2l_cohort[year].append(term)
                        # mark term as seen
                        self.d_term2seen[term] = True
                
            print "Loaded %i terms, %i new" % (self.d_y2tcount[year], self.d_y2ncount[year]) 
            s_term_file.close()

    # we cannot construct the history while populating the data, since it is possible that
    # a seen term in one year may be missing in some later year.  In this case, its history entry
    # needs to be set to 0, not omitted entirely (which would throw off the mapping to years
    # assumed in the history list.
    #def construct_history(self):

    # note also that freq is based on the UNembedded occurrences of terms only.  
    # It does not include phrases for which the term is a subphrase.

    # return a list of [term, freq] pairs of all terms satisfying the constraints
    # rf.filter(1997, 1997, 1998, 1000, 2000, 1000, 2000)

    # To get a set of high growth terms between 1998 and 2006
    # 1998 is year in which term first appears
    # z98 = rf.filter(1998, 1998, 2006, 1, 2000, 30, 2000)
    # Note that the first year in the range is 1997.  Thus many terms will first appear here
    # but they may not be new.  So it is best to use a first year > the start_year.

    # returns a list of [term, reference year freq, target year freq]
    # filter_type is a mnemonic for the ref_year and target_year ranges (e.g. hh, hl - high-high, high-low)

    def filter(self, cohort_year, ref_year, target_year, ref_min, ref_max, target_min, target_max, filter_type):
        l_matches = []
        file_qualifier = "cohort." + filter_type
        cohort_file = pnames.tv_dir_year_file(corpus_root, self.corpus, cohort_year, file_qualifier)
        s_cohort_file = codecs.open(cohort_file, "w", encoding='utf-8')
        # write parameters of the cohort as first line in file
        s_cohort_file.write("#%i\t%i\t%i\t%i\t%i\t%i\t%i\n" % (cohort_year, ref_year, target_year, ref_min, ref_max, target_min, target_max))
        for term in self.d_y2l_cohort[cohort_year]:
            rf = self.d_ty2freq[tuple([term, ref_year])]
            tf = self.d_ty2freq[tuple([term, target_year])]
            if rf >= ref_min and rf <= ref_max and tf >= target_min and tf <= target_max:
                l_matches.append([term, rf, tf])
                # save to a file as well
                s_cohort_file.write("%s\t%i\t%i\n" % (term, rf, tf))
        s_cohort_file.close()
        return(l_matches)

    # for a range of years, create filtered cohort files
    # a cohort is all terms that first appear in a given year.
    # filtering constrains the doc freq in a reference year and target year in the future from the cohort year,
    # e.g. 2 years and 5 years later.
    # hh: ref_year >= 5, target year >= 20
    # rfa22.filter_range(1998, 2007, 2, 5, 5, 10000, 20, 10000, "hh") 
    # hl: ref_year >= 5, target year <= 10
    # rfa22.filter_range(1998, 2007, 2, 5, 5, 10000, 0, 10, "hl") 
    # rfa22.filter_range(1998, 2007, 2, 5, 0, 5, 20, 10000, "lh")
    # rfa22.filter_range(1998, 2007, 2, 5, 5, 10000, 0, 10000, "r5")
    # rfa22.filter_range(1998, 2007, 2, 5, 0, 10000, 0, 10000, "r0")
    def filter_range(self, cohort_start_year, cohort_end_year, ref_offset, target_offset, ref_min, ref_max, target_min, target_max, filter_type):
        end_range = cohort_end_year + 1
        for cohort_year in range(cohort_start_year, end_range):
            ref_year = cohort_year + ref_offset
            target_year = cohort_year + target_offset
            self.filter(cohort_year, ref_year, target_year, ref_min, ref_max, target_min, target_max, filter_type)

# l_cohort is the list returned by Rfreq.filter [[term, rf, tf], ...]
# fan.cohort_features("ln-us-all-600k", 2003, l_cohort, "c98-06_2003_30")
def cohort_features(corpus, year, l_cohort, cohort_name):
    # cohort_term_feature => total freq
    # This accumulates the count of occurrences of a cohort term
    # with a feature in the given year
    d_cf2freq = defaultdict(int)
    # any_term_features => total freq
    # This accumulates the count of occurrences of any term
    # with a feature in the given year
    d_tf2freq = defaultdict(int)
    sum_cohort_feature_occurrences = 0
    sum_term_feature_occurrences = 0

    # keep a dict of all features encountered with cohort terms in the year
    d_feats = defaultdict(bool)

    # score consisting of prob(feature|cohort term) / prob(feature | term)
    d_cf_score = {}

    # cohort terms in dict form
    d_cohort = {}

    # output file for scores
    qualifier = cohort_name + ".fscores"
    score_file = pnames.tv_dir_year_file(corpus_root, corpus, year, qualifier)
    s_score_file = codecs.open(score_file, "w", encoding='utf-8')

    # store cohort list terms in a dict
    for (term, rf, tf) in l_cohort:
        d_cohort[term] = True

    year = str(year)
    tf_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "tf")
    s_tf_file = codecs.open(tf_file, encoding='utf-8')
    print "[RFreq]loading terms for year: %s" % year
    for term_line in s_tf_file:
        term_line = term_line.strip("\n")
        (term, feat, freq, prob) = term_line.split("\t")
        freq = int(freq)
        if d_cohort.has_key(term):
            # update cohort term counts
            d_cf2freq[feat] += freq
            sum_cohort_feature_occurrences += freq
            # keep track of the cohort features seen
            d_feats[feat] = True

        # update all feature counts
        sum_term_feature_occurrences += freq
        d_tf2freq[feat] += freq
        
    sum_cohort_feature_occurrences = float(sum_cohort_feature_occurrences)
    sum_term_feature_occurrences = float(sum_term_feature_occurrences)
    for feat in d_feats.keys():
        prob_fgc = d_cf2freq[feat] / sum_cohort_feature_occurrences
        prob_fgt = d_tf2freq[feat] / sum_term_feature_occurrences
        if prob_fgt == 0:
            pdb.set_trace()
        d_cf_score[feat] = prob_fgc / prob_fgt

    l_scores_sorted = d_cf_score.items()
    l_scores_sorted.sort(key=itemgetter(1), reverse=True)
    for (feat, score) in l_scores_sorted:
        s_score_file.write("%.2f\t%s\t%i\t%i\n" % (score, feat, d_cf2freq[feat], d_tf2freq[feat]))
    s_tf_file.close()
    s_score_file.close()
    print "[fan.cohort_features]Wrote scores to %s" % score_file


# capture prespecified cohorts from the range of year data in rFreq instance for a corpus
# fan.make_cohorts(rfp, "ln-us-cs-500k", 1998)
# each cohort member is written to a file preceded by its cohort code.
def make_cohorts(rfreq, corpus, year):
    
    outfile = tv_dir_year_file(corpus_root, corpus, year, "cohort")
    y2 = year + 2
    y5 = year + 5

    y2_a_min = 0  
    y2_a_max = 5
    y2_b_min = 6 
    y2_b_max = 20
    y2_c_min = 21 
    y2_c_max = 10000
    y5_1_min = 0
    y5_1_max = 10
    y5_2_min = 11
    y5_2_max = 50
    y5_3_min = 51
    y5_3_max = 10000

    d_code2cohort = {}

    d_code2cohort["a1"] = rfreq.filter(year, y2, y5, y2_a_min, y2_a_max, y5_1_min, y5_1_max)
    d_code2cohort["a2"] = rfreq.filter(year, y2, y5, y2_a_min, y2_a_max, y5_2_min, y5_2_max)
    d_code2cohort["a3"] = rfreq.filter(year, y2, y5, y2_a_min, y2_a_max, y5_3_min, y5_3_max)

    d_code2cohort["b1"] = rfreq.filter(year, y2, y5, y2_b_min, y2_b_max, y5_1_min, y5_1_max)
    d_code2cohort["b2"] = rfreq.filter(year, y2, y5, y2_b_min, y2_b_max, y5_2_min, y5_2_max)
    d_code2cohort["b3"] = rfreq.filter(year, y2, y5, y2_b_min, y2_b_max, y5_3_min, y5_3_max)

    d_code2cohort["c1"] = rfreq.filter(year, y2, y5, y2_c_min, y2_c_max, y5_1_min, y5_1_max)
    d_code2cohort["c2"] = rfreq.filter(year, y2, y5, y2_c_min, y2_c_max, y5_2_min, y5_2_max)
    d_code2cohort["c3"] = rfreq.filter(year, y2, y5, y2_c_min, y2_c_max, y5_3_min, y5_3_max)

    d_code2cohort["all"] = rfreq.filter(year, y2, y5, 0, 10000, 0, 10000)

    
    s_outfile = codecs.open(outfile, "w", encoding='utf-8')

    for code in d_code2cohort.keys():
        for (term, y2_freq, y5_freq) in d_code2cohort[code]:
            
            s_outfile.write("%s\t%s\t%i\t%i\n" % (code, term, y2_freq, y5_freq))

    s_outfile.close()

# choose features as those with high term frequency during the reference year for the growth type c3
# cat 1998.growth.c3 | cut -f1,3 | sort | uniq -c | sort -nr | grep '2000    ' | head -20 | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py > 1998.growth.c3.2000.20
# 23      2000    prev_Jpr=such_as

# cat 1998.growth.lw.c3 | cut -f1,2,4 | sort | uniq | grep '^2000' | cut -f1,3 | sort | uniq -c | sort -nr | head -20 | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py > 1998.growth.lw.c3.2000.20
# 11      2000    last_word=system


# output data for graphing features by year and term-frequency
# fan.growth2excel("ln-us-cs-500k", 1998, "c3", "rel" )
# feature type is "rel" for relational features, "lw" for last word in subsuming phrase

# to upload to mac, copy to ~/uploads
# on mac: cd /Users/panick/peter/my_documents/brandeis/fuse/papers/coling_2014_workshop
# scp anick@sarpedon.cs.brandeis.edu:uploads/1998* . 

# input a file containing a list of features of interest (indicator features which
# correlate with high growth terms)

# gtype - growth type
def growth2excel(corpus, y1, gtype, ftype="rel", start_year=1998, end_year=2006):
    if ftype == "rel":
        ftype_qualifier = ""
    else: 
        ftype_qualifier = "lw."
    # We use the same feature file for all gtypes, namely the top features associated with gtype c3
    feature_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".growth." + ftype_qualifier + "c3" + ".2000.20"
    growth_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".growth." + ftype_qualifier + gtype
    yf2tfreq_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".yf2tfreq." + ftype_qualifier + gtype
    graph_cum_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".yf2tfreq." + ftype_qualifier + gtype + ".graph.cum"
    tfy2dfreq_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".yf2tfreq." + ftype_qualifier + gtype + ".graph.tfy2dfreq"
    entropy_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".entropy." + ftype_qualifier + gtype

    l_features = []
    # year and feature => term frequency
    # /// why do we want this??
    d_yf2tfreq = defaultdict(int)
    # capture actual terms for each freq to generate cumulative counts (how
    # many terms have been referred to with this feature since y1)
    d_yf2terms = defaultdict(set)

    # term feature year to doc freq
    d_tfy2dfreq = defaultdict(int)

    # read in the features of interest
    s_feature_file = codecs.open(feature_file, encoding='utf-8')
    for feature_line in s_feature_file:
        feature_line = feature_line.strip("\n")
        (freq, year, feature) = feature_line.split("\t")
        l_features.append(feature)
    s_feature_file.close()

    # read in the growth data for the growth type (e.g. c3)

    # capture terms so we can count the number of terms in this gtype subset
    # to compute prob of features
    l_terms = set()

    term_info = TermInfo()

    s_growth_file = codecs.open(growth_file, encoding='utf-8')
    for growth_line in s_growth_file:
        growth_line = growth_line.strip("\n")
        if ftype == "rel":
            (year, term, feature, ffreq) = growth_line.split("\t")
        elif ftype == "lw":
            (year, term, phrase, feature, ffreq) = growth_line.split("\t")
        # update term_freq for the year/feature combination
        # make year an int to be consistent with tuple when writing output
        year = int(year)
        l_terms.add(term)
        d_yf2tfreq[tuple([feature, year])] += 1
        # set of terms with this year and feature
        d_yf2terms[tuple([feature, year])].add(term)

        # also store term feature year => doc freq
        d_tfy2dfreq[tuple([term, feature, year])] = ffreq

        # Capture info to compute feature entropy for each term
        # create a list of doc counts for each feature occurring with this term this year 
        term_info.store_feat_count(term, year, ftype, feature, ffreq)

    s_growth_file.close()

    num_terms = len(l_terms)
    # output data for excel table (year, feature, tfreq)
    # This captures the fraction of terms in this growth category with cooccur with each 
    # diagnostic feature by year.  For each year, we show the cumulative number of terms, 
    # the new terms (appearing with this feature for the first time), and yearly number of terms.
    # Both raw frequency and probability (fraction of all terms in this growth category) as
    # well as the terms themselves are output.
    s_yf2tfreq_file = codecs.open(yf2tfreq_file, "w", encoding='utf-8')
    d_f2y_cum = defaultdict(list)
    for feature in l_features:
        cum_term_set = set()
        
        for year in range(start_year, end_year + 1):

            new_term_set = d_yf2terms[tuple([feature, year])].copy()
            new_term_set.difference_update(cum_term_set)
            
            cum_term_set.update(d_yf2terms[tuple([feature, year])])
                        
            cum_freq = len(cum_term_set)
            new_freq = len(new_term_set)
            year_freq = len(d_yf2terms[tuple([feature, year])])
            cum_prob = prob2str(cum_freq, num_terms)
            s_yf2tfreq_file.write("%s\t%i\t%i\t%i\t%i\t%s\t%s\t%s\t%s\t%s\n" % (feature, year, year_freq, new_freq, cum_freq, prob2str(year_freq, num_terms),  prob2str(new_freq, num_terms),  cum_prob, cum_term_set, new_term_set))

            d_f2y_cum[feature].append(cum_prob)
            
    s_yf2tfreq_file.close()

    # probability that a term in this growth category will have been seen with this feature
    # by each year (ie. cumulatively).  What fraction of terms will have this feature by each year.
    # This gives a sense on the importance of the feature as a metric.  Do high growth terms tend
    # to cooccur with this feature, and how soon?
    s_graph_cum = codecs.open(graph_cum_file, "w", encoding='utf-8')
    # hard coded header for now
    header = "feature\t1998\t1999\t2000\t2001\t2002\t2003\t2004\t2005\t2006"
    s_graph_cum.write("%s\n" % header)
    for feature in l_features:
        s_graph_cum.write("%s" % feature)
        for prob in d_f2y_cum[feature]:
            s_graph_cum.write("\t%s" % prob)
        s_graph_cum.write("\n")
    s_graph_cum.close()

    # For the diagnostic features, show number of docs containing this feature/term combination
    # for each year.  Shows trends for features for given terms.
    # output a graph-ready table of d_tfy2dfreq[tuple([term, feature, year])] = ffreq
    s_tfy2dfreq = codecs.open(tfy2dfreq_file, "w", encoding='utf-8')
    for term in l_terms:
        for feature in l_features:
            s_tfy2dfreq.write("%s\t%s" % (term, feature))
            for year in range(start_year, end_year + 1):
                s_tfy2dfreq.write("\t%s" % d_tfy2dfreq[tuple([term, feature, year])])
            s_tfy2dfreq.write("\n")
    s_tfy2dfreq.close()

    # This outputs dispersion and entropy info for terms over years.  It is not 
    # based solely on the diagnostic features, since all features contribute to entropy.
    # dispersion is number of different features the term appears with.
    # entropy takes into account the distribution of different features for the term.  The more
    # evenly spread the feature counts, the higher the entropy.
    s_entropy = codecs.open(entropy_file, "w", encoding='utf-8')
    for term in l_terms:

        for year in range(start_year, end_year + 1):
            # compute entropy and create a graph-ready table
            term_info.store_disp_data(term, year, ftype)

            s_entropy.write("%s\t%i" % (term, year))
            disp = term_info.d_term[tuple([term, year, ftype, "disp"])]
            counts_sum = term_info.d_term[tuple([term, year, ftype, "counts_sum"])]
            entropy = term_info.d_term[tuple([term, year, ftype, "entropy"])]
            #pdb.set_trace()
            s_entropy.write("\t%i\t%i\t%f" % (disp, counts_sum, entropy))
            s_entropy.write("\n")
    s_entropy.close()

def growth2disp(corpus, y1, gtype, ftype="rel", ffreq_min=1, start_year=1998, end_year=2006):
    if ftype == "rel":
        ftype_qualifier = ""
    else: 
        ftype_qualifier = "lw."

    growth_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".growth." + ftype_qualifier + gtype
    disp_file = corpus_root + "/" + corpus + "/data/tv/" + str(y1) + ".disp." + ftype_qualifier + gtype + "." + str(ffreq_min)


    # read in the growth data for the growth type (e.g. c3)

    # capture terms so we can count the number of terms in this gtype subset
    # to compute prob of features
    l_terms = set()

    term_info = TermInfo()

    s_growth_file = codecs.open(growth_file, encoding='utf-8')
    for growth_line in s_growth_file:
        growth_line = growth_line.strip("\n")
        if ftype == "rel":
            (year, term, feature, ffreq) = growth_line.split("\t")
        elif ftype == "lw":
            (year, term, phrase, feature, ffreq) = growth_line.split("\t")
        # update term_freq for the year/feature combination
        # make year an int to be consistent with tuple when writing output
        year = int(year)
        ffreq = int(ffreq)
        l_terms.add(term)

        # Capture info to compute feature entropy for each term
        # create a list of doc counts for each feature occurring with this term this year 

        # restrict features to those which appear in >= ffreq_min documents
        #print "[disp]ffreq: %i, ffreq_min: %i" % (ffreq, ffreq_min)
        if ffreq >= ffreq_min:
            term_info.store_feat_count(term, year, ftype, feature, ffreq)

    s_growth_file.close()

    # This outputs dispersion and entropy info for terms over years.  It is not 
    # based solely on the diagnostic features, since all features contribute to entropy.
    # dispersion is number of different features the term appears with.
    # entropy takes into account the distribution of different features for the term.  The more
    # evenly spread the feature counts, the higher the entropy.
    s_disp = codecs.open(disp_file, "w", encoding='utf-8')
    pdb.set_trace()
    for term in l_terms:

        for year in range(start_year, end_year + 1):
            # compute entropy and create a graph-ready table
            term_info.store_disp_data(term, year, ftype)

            s_disp.write("%s\t%i" % (term, year))
            disp = term_info.d_term[tuple([term, year, ftype, "disp"])]
            counts_sum = term_info.d_term[tuple([term, year, ftype, "counts_sum"])]
            entropy = term_info.d_term[tuple([term, year, ftype, "entropy"])]
            #pdb.set_trace()
            s_disp.write("\t%i\t%i\t%f" % (disp, counts_sum, entropy))
            s_disp.write("\n")
    s_disp.close()

# fan.run_growth2excel("ln-us-cs-500k")
def run_growth2excel(corpus):
    #for gtype in ["c1", "c2", "c3", "b1", "b2", "b3"]:
    # omitting a1
    #for gtype in ["c1", "c2", "c3", "b1", "b2", "b3", "a2", "a3"]:
    #for gtype in ["c3", "b3", "a3"]:
    for gtype in ["c1", "c2"]:
        for ftype in ["rel", "lw"]:
            growth2excel(corpus, 1998, gtype, ftype)    

# fan.run_growth2disp("ln-us-cs-500k", 1)
def run_growth2disp(corpus, ffreq_min=1):
    #for gtype in ["c1", "c2", "c3", "b1", "b2", "b3"]:
    # omitting a1
    #for gtype in ["c1", "c2", "c3", "b1", "b2", "b3", "a2", "a3"]:
    #for gtype in ["c3", "b3", "a3"]:
    for gtype in ["c1", "c2", "c3", "a3", "b3", "b2", "b1"]:
        for ftype in ["rel", "lw"]:
            growth2disp(corpus, 1998, gtype, ftype, ffreq_min)    

 
# to prep for naive Bayes analysis
# Remove terms with freq < 2 in ref year (y2) from cohort
# cat 1998.cohort | grep -v '        0       ' | grep -v '   1       ' | sortnr -k4 > 1998.cohort.gcat.tfreq2
# format it as a .terms file (just term and freq in y2)
# cat 1998.cohort.gcat.tfreq2 | cut -f2,3 > 1998.cohort.terms
# [anick@sarpedon tv]$ wc -l 1998.cohort.terms
# 38986 1998.cohort.terms

##### entropy

class TermInfo():
    def __init__(self):
        self.d_term = defaultdict(list)

    def store_feat_count(self, term, year, ftype, feat, count):
        self.d_term[tuple([term, year, ftype, "counts"])].append(int(count))
        self.d_term[tuple([term, year, ftype, "feats"])].append(feat)
        
    # ftype (feature type) is "rel" or "lw"
    def store_disp_data(self, term, year, ftype):
        d_term = self.d_term
        # ftype is "rel" (relational feature such as prev_V), "lw" (last word feature) 
        # counts is a list of the frequency of a feature for the term and year
        # feats is the list of the features themselves
        l_counts = self.d_term[tuple([term, year, ftype, "counts"])]
        l_feats = self.d_term[tuple([term, year, ftype, "feats"])]

        counts_sum = 0
        prob_sum = 0.0
        disp = 0
        l_feat_counts = []
        l_feats_sorted = []

        i = 0
        for count in l_counts:
            # sum up the total frequency of feature occurrences across features
            counts_sum = counts_sum + count
            # count the number of different features appearing with this term
            disp = disp + 1
            l_feat_counts.append([l_feats[i], count])
            #print "l_feat_counts: %s" % l_feat_counts
            i += 1

        # sort the feats by count
        #if counts_sum > 0:
        #    pdb.set_trace()
        l_feats_sorted = l_feat_counts
        l_feats_sorted.sort(key=itemgetter(1), reverse=True)

        # now that we have the counts_sum, we can compute prob for each feat
        for count in l_counts:
            prob = (1.0 * count) / counts_sum
            log2_prob = math.log(prob, 2)
            prob_sum = prob_sum + prob * log2_prob

        #print "s2 for %s, %i: %s" % (term, year, d_head[(term, year, "s2")])

        if prob_sum < 0:
            entropy = -1 * prob_sum
        else: 
            # avoid -0.0; keep it 0.0
            entropy = prob_sum

        #print "s_counts for %s, %i: %s" % (term, year, d_head[(term, year, "s_counts")])
        #print "year: %i, disp: %i, counts_sum: %i, prob_sum: %f" % (year, disp, counts_sum, entropy) 
        #print "terms_sorted: %s\n" % l_feats_sorted
        
        self.d_term[tuple([term, year, ftype, "disp"])] = disp
        self.d_term[tuple([term, year, ftype, "counts_sum"])] = counts_sum
        self.d_term[tuple([term, year, ftype, "entropy"])] = entropy
        self.d_term[tuple([term, year, ftype, "feats"])] = l_feats_sorted
        #return(self.d_term)
        #pdb.set_trace()

# task term analysis
# Assume we have a set of terms labeled as type task.




# TODO:
# Given a list of diagnostic features and a range of years
# create a dict from term,year,feature => count of docs containing the term/feature in the year
# create a dict from term,year,feature => cumulative count of docs containing the term/feature in the year
# create dict from term => first appearance year (within range)

# Test: how much change in top features depending on cohort and year?

# We have determined that we cannot limit terms to a single corpus.  We need to find the start year across multiple corpora.
# Because this will generate a huge number of terms, we will, as a first step, compute the start year of all terms across corpora.
# Then we will filter out any terms that appear in the first year, so that we only have to deal with neologisms in further processing.

# The "all" corpus should be created before running this (with create_all_corpus)
def term_to_year1(start_year, end_year, corpus_list): 
    # value is the first year in which a term appears within any corpus in the corpus_list
    term2year1 = {}
    end_range = end_year + 1

    # write the terms and start years into .tstart file
    year_range = str(start_year) + "_" + str(end_year)
    term_start_file = pnames.tv_dir_year_file(corpus_root, "all", year_range, "tstart")
    print "[term_to_year1] term_start_file: %s" % term_start_file

    # .neo is same as .tstart_file but filtering any terms that first appear in year 1.
    # Thus this includes only neologisms appearing after year 1.
    year_range = str(start_year) + "_" + str(end_year)
    term_neo_file = pnames.tv_dir_year_file(corpus_root, "all", year_range, "neo")
    print "[term_to_year1] term_neo_file: %s" % term_neo_file

    for corpus in corpus_list:
        for year in range(start_year, end_range):
            term_file = pnames.tv_dir_year_file(corpus_root, corpus, str(year), "terms")
            print "[term_to_year1] processing term_file: %s" % term_file
            s_term_file = codecs.open(term_file, encoding='utf-8')
            for term_line in s_term_file:
                term_line = term_line.strip("\n")
                term_fields = term_line.split("\t")
                term = term_fields[0]
                # if the term is not in our table, enter it along with the current year as start year
                if not term2year1.has_key(term):
                    term2year1[term] = year

            s_term_file.close()

    # write the terms and start years into .tstart file
    year_range = str(start_year) + "_" + str(end_year)
    term_start_file = pnames.tv_dir_year_file(corpus_root, "all", year_range, "tstart")
    print "[term_to_year1] term_start_file: %s" % term_start_file
    s_term_start_file = codecs.open(term_start_file, encoding='utf-8')
    s_term_neo_file = codecs.open(term_neo_file, encoding='utf-8')
    for term in term2year1.keys():
        first_year = term2year1[term]
        s_term_start_file.write("%s\t%i\n" % (term, first_year))
        if first_year != start_year:
            # then include term as a neologism
            s_term_neo_file.write("%s\t%i\n" % (term, first_year))

    s_term_start_file.close()
    s_term_neo_file.close()

# create the directory structure for an "all" corpus, where data across multiple corpora will reside
def create_all_corpus():
    tv_subpath = "/data/tv/"
    tv_root = corpus_root + "/" + "all" + tv_subpath
    # Be safe, check if tv_root path exists, and create it if not
    if not os.path.exists(tv_root):
        os.makedirs(tv_root)
        print "Created outroot dir: %s" % tv_root


# we have from 1997 to 2007.
# corpora: ["ln-us-A21-computers", "ln-us-A22-communications", "ln-us-A25-chemical-engineering", "ln-us-A28-mechanical-engineering", "ln-us-A23-semiconductors", "ln-us-A26-organic-chemistry", "ln-us-A29-thermal-technology", "ln-us-A24-optical-systems","ln-us-A27-molecular-biology","ln-us-A30-electrical-circuits"]
# fan.test_term_to_year1()
def test_term_to_year1(): 
    start_year = 1997
    end_year = 1998
    corpus_list = ["ln-us-A29-thermal-technology", "ln-us-A24-optical-systems"]
    term_to_year1(start_year, end_year, corpus_list) 
