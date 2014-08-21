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

# TODO: compute cumulative feature scores

import pdb
import utils
from collections import defaultdict
from operator import itemgetter
import math
import codecs

import pnames
import roles_config

# for WoS
# sources are in, e.g. /home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k/subcorpora/2000/data/d0_xml/01/files/WoS.out.2000000024

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

# modified from phran.py to be independent of ACT role labels
class phrInfo():
    def __init__(self, corpus, year):
        year = str(year)
        # term file is used for extracting the doc frequency of terms for the year
        #term_file = corpus_root + "/" + corpus + "/data/tv/" + year + ".tf.f"
        term_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "tf.f")

        self.d_term2heads = defaultdict(list)
        self.d_term2mods =  defaultdict(list)
        self.d_head2terms = defaultdict(list)
        self.d_mod2terms =  defaultdict(list)
        self.d_head2count = defaultdict(int)
        self.d_mod2count = defaultdict(int)
        self.term_count = 0
        self.headed_term_count = 0
        self.modified_term_count = 0
        self.d_term_freq = defaultdict(int)
        self.d_term_cat = defaultdict(str)
        self.l_singletons = []
        # list sorted by freq [[term, freq],...]
        self.l_tf = []

        # open the file and import list of terms
        s_term_file = codecs.open(term_file, encoding='utf-8')
        for term_line in s_term_file:
            term_line = term_line.strip("\n")
            (term, freq) = term_line.split("\t")
            freq = int(freq)
            self.d_term_freq[term] = freq
            #self.d_term_cat[term] = cat
            self.term_count += 1
            self.l_tf.append([term, freq])
        s_term_file.close()

        # sort the term list
        self.l_tf.sort(utils.list_element_2_sort)

        self.compute_heads_mods()

    def compute_heads_mods(self):
        for term in self.d_term_freq.keys():
            l_words = term.split(" ")
            if len(l_words) > 1:
                # term is a phrase.  Check for head and mod.
                term_no_mod = " ".join(l_words[1:])
                if self.d_term_freq.has_key(term_no_mod):
                    # Then subterm exists on its own
                    mod = l_words[0]
                    self.d_term2mods[term_no_mod].append(mod)
                    self.d_mod2terms[mod].append(term_no_mod)
                    self.modified_term_count += 1
                    self.d_mod2count[mod] += 1
                term_no_head = " ".join(l_words[0:len(l_words) - 1])
                if self.d_term_freq.has_key(term_no_head):
                    # Then subterm exists on its own
                    head = l_words[-1]
                    self.d_term2heads[term_no_head].append(head)
                    self.d_head2terms[head].append(term_no_head)
                    self.headed_term_count += 1
                    self.d_head2count[head] += 1
            else:
                # we have a single word term
                self.l_singletons.append(term)

    def sort_heads(self):
        l_head_counts = []
        for head in self.d_head2count.keys():
            l_head_counts.append([head, self.d_head2count[head]])
        l_head_counts.sort(utils.list_element_2_sort)
        return(l_head_counts)


# store frequency info for a year of a corpus
# not necessary, use RFreq instead.
class YFreq():
    def __init__(self, corpus, year):
        self.d_t2freq = defaultdict(int)
        self.term_count = 0
        root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
        term_file = root + corpus + "/data/tv/" + str(year) + ".tf.f"
        s_term_file = codecs.open(term_file, encoding='utf-8')
        for term_line in s_term_file:
            term_line = term_line.strip("\n")
            (term, freq) = term_line.split("\t")
            freq = int(freq)
            self.d_term_freq[term] = freq
            self.term_count += 1

        s_term_file.close()



# store a range of term,year=>freq dictionaries
# rfcs = fan.RFreq("ln-us-cs-500k", 1997, 2006)
# rf = fan.RFreq("ln-us-all-600k", 1997, 2006)
# rfw = fan.RFreq("wos-cs-520k", 1997, 2006)
# Range frequencies
# Depends on: <year>.tf.f files must exist for all years in range
# These are created by make_tf_f.sh 
# e.g. sh make_tf_f.sh ln-us-cs-500k
class RFreq():

    def __init__(self, corpus, start_year, end_year):
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
        for year in range(start_year, end_year + 1):
            term_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "tf.f")
            s_term_file = codecs.open(term_file, encoding='utf-8')
            print "[RFreq]loading terms for year: %i" % year
            for term_line in s_term_file:
                term_line = term_line.strip("\n")
                (term, freq) = term_line.split("\t")
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
    def filter(self, cohort_year, ref_year, target_year, ref_min, ref_max, target_min, target_max):
        l_matches = []
        for term in self.d_y2l_cohort[cohort_year]:
            rf = self.d_ty2freq[tuple([term, ref_year])]
            tf = self.d_ty2freq[tuple([term, target_year])]
            if rf >= ref_min and rf <= ref_max and tf >= target_min and tf <= target_max:
                l_matches.append([term, rf, tf])
        return(l_matches)

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

# TODO:
# Given a list of diagnostic features and a range of years
# create a dict from term,year,feature => count of docs containing the term/feature in the year
# create a dict from term,year,feature => cumulative count of docs containing the term/feature in the year
# create dict from term => first appearance year (within range)

# Test: how much change in top features depending on cohort and year?
