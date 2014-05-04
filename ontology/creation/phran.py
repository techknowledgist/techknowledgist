# phran.py
# phrasal analysis of heads and mods

# given a list of terms in a file
# return an instance of a phr_info object
# dict d_term2heads with key = term, value a list of heads occurring with the term
# dict d_term2mods with key = term, value a list of mods occurring with the term
# dict d_head2count with key = a term used as a head, value = count of terms it occurs with
# dict d_mod2count with key = a term used as a mod, value = count of terms it occurs with
# headed_term_count = # terms that appear with a head
# modified_term_count = # terms that appear with a modifier

import pdb
import utils
from collections import defaultdict
import codecs

# for WoS
# sources are in, e.g. /home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k/subcorpora/2000/data/d0_xml/01/files/WoS.out.2000000024

# Before running this, the corpus tv dir should contain all yearly tf.f files, which are
# created by running
# sh make_tf_f.sh ln-us-cs-500k
# sh make_tf_f.sh wos-cs-520k 

# p97 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/1997.tf.f")
# p97 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/wos-cs-520k/data/tv/1997.tf.f")

# term file should be a year file of the form: term category freq
# 

# rewrite to use .tf file instead of gt1 (which comes from w0.0).  
# The w0.0 file might not be able to classify some terms in a year, which
# will result in their freq looking like 0.  So it is better to 
# generate the frequency info first and then add the category data from the gt1 file.
# DONE


corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents"

# return a sorted (by descending numeric value) list of key-value pairs for a dict. 
def sort_dict_num_values(dict):
    l_key_values = []
    for key in dict.keys():
        l_key_values.append([key, dict[key]])

    l_key_values.sort(utils.list_element_2_sort)
    return(l_key_values)

class phrInfo():
    def __init__(self, corpus, year):
        year = str(year)
        # term file is used for extracting the doc frequency of terms for the year
        term_file = corpus_root + "/" + corpus + "/data/tv/" + year + ".tf.f"
        # gt1 file is used for selecting high growth terms for terms labeled with categories
        gt1_file = corpus_root + "/" + corpus + "/data/tv/" + year + ".act.gt1"
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
        # lists by category sorted by freq [[term, freq],...]
        self.l_c = []
        self.l_a = []
        self.l_t = []

        # open the file and import list of terms
        s_term_file = codecs.open(term_file, encoding='utf-8')
        for term_line in s_term_file:
            term_line = term_line.strip("\n")
            (term, freq) = term_line.split("\t")
            freq = int(freq)
            self.d_term_freq[term] = freq
            #self.d_term_cat[term] = cat
            self.term_count += 1

        s_term_file.close()

        # open the gt1 file and import list of terms with category labels
        s_gt1_file = codecs.open(gt1_file, encoding='utf-8')
        for term_line in s_gt1_file:
            term_line = term_line.strip("\n")
            (term, cat, freq) = term_line.split("\t")
            freq = int(freq)
            #self.d_term_freq[term] = freq
            self.d_term_cat[term] = cat
            #self.term_count += 1
            if cat == "c":
                self.l_c.append([term, freq])
            elif cat == "t":
                self.l_t.append([term, freq])
            elif cat == "a":
                self.l_a.append([term, freq])

        s_gt1_file.close()

        # sort the category term lists
        self.l_c.sort(utils.list_element_2_sort)
        self.l_t.sort(utils.list_element_2_sort)
        self.l_a.sort(utils.list_element_2_sort)

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
# rf = phran.RFreq("ln-us-cs-500k", 1997, 1998)
# 
class RFreq():
    
    def __init__(self, corpus, start_year, end_year):
        root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
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
            term_file = root + corpus + "/data/tv/" + str(year) + ".tf.f"
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
    # assumed in the histoy list.
    #def construct_history(self):

    # note also that freq is based on the unembedded occurrences of terms.  It does not include phrases for
    # which the term is a subphrase.

    # return a list of [term, freq] pairs of all terms satisfying the constraints
    # rf.filter(1997, 1997, 1998, 1000, 2000, 1000, 2000)
    def filter(self, cohort_year, ref_year, target_year, ref_min, ref_max, target_min, target_max):
        l_matches = []
        for term in self.d_y2l_cohort[cohort_year]:
            rf = self.d_ty2freq[tuple([term, ref_year])]
            tf = self.d_ty2freq[tuple([term, target_year])]
            if rf >= ref_min and rf <= ref_max and tf >= target_min and tf <= target_max:
                l_matches.append([term, rf, tf])
        return(l_matches)
                              


# a98 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/1998.act.gt1")
# nt = phran.get_hf_terms(a06, a97, a98, "t", "ln-us-cs-500k")
# nc = phran.get_hf_terms(a06, a97, a98, "c", "ln-us-cs-500k")
# find terms with high freq in 2006 with 0 freq in 1997, 1998
# use only terms that are categorized in the target year with some a,c,t category
# Assume this to be the category for the term in the ref years.  Note that a term
# may not have been categorized in the ref year.
def get_hf_terms(target_year_pi, ref_year1_pi, ref_year2_pi, cat, corpus):
    root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    outfile = root + corpus + "/data/tv/" + "growth." + cat
    target_terms = []
    if cat == "c":
        target_terms = target_year_pi.l_c
    elif cat == "t":
        target_terms = target_year_pi.l_t
    elif cat == "a":
        target_terms = target_year_pi.l_a

    # new terms occur in target year and not in ref year
    # term_freq is a list of a term and its freq.
    l_new_terms = []

    s_outfile = codecs.open(outfile, "w", encoding='utf-8')

    for term_freq in target_terms:
         if (not ref_year1_pi.d_term_freq.has_key(term_freq[0])) and (not ref_year2_pi.d_term_freq.has_key(term_freq[0])):
             l_new_terms.append(term_freq)

    for (term, freq) in l_new_terms:
        s_outfile.write("%s\t%i\n" % (term, freq))
    s_outfile.close()
    
    return(l_new_terms)

             

# to create the input file:
# cat 2006.act.cat.w0.0 | cut -f1,4,5 | egrep -v '  1$' > 2006.act.gt1

# Before running get_hf_terms(target_year_pi, ref_year1_pi, ref_year2_pi, cat, corpus) :
"""
>>> import phran
>>> a98 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/1998.act.gt1") 
>>> a97 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/1997.act.gt1") 
>>> a06 = phran.phrInfo("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/2006.act.gt1") 
>>> a97 = phran.phrInfo("ln-us-cs-500k", 1997)
>>> nt = phran.get_hf_terms(a06, a97, a98, "t") 
>>> nc = phran.get_hf_terms(a06, a97, a98, "c") 
>>> nc[0:100]

"""

# after running get_hf_terms:
# create a file with occurrences of high growth terms in categories t and c.
# sh occ.sh ln-us-cs-500k t 100 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.t.100  
# sh occ.sh ln-us-cs-500k c 100 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.c.100  

# process the output:
# cat growth.c.100 | cut -f2,3 | sort | uniq | cut -f2 | sort | uniq -c | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py | sortnr -k1 > growth.c.100.uc
# cat growth.c.100 | cut -f2,3 | sort | uniq | cut -f2 | sort | uniq -c | sortnr -k1 > growth.c.100.uc
# cat growth.t.100 | cut -f2,3 | sort | uniq | cut -f2 | sort | uniq -c | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py | sortnr -k1 > growth.t.100.uc
# This tells us which features have the broadest use across the set of high growth terms.  For the set of years,
# how many different terms appeared with this feature?

# create a file with freq of all phrases starting with a high growth term
# sh lw.sh ln-us-cs-500k c 100 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.c.100.lw
# sh lw.sh ln-us-cs-500k t 100 > /home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.t.100.lw

# process the output:
#### cat growth.c.3.lw | cut -f2,4 | sort | uniq | cut -f2 | sort | uniq -c | sortnr -k1 > growth.c.3.lw.uc
# cat growth.c.100.lw | cut -f2,4 | sort | uniq | cut -f2 | sort | uniq -c | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py | sortnr -k1 > growth.c.100.lw.uc
# cat growth.t.100.lw | cut -f2,4 | sort | uniq | cut -f2 | sort | uniq -c | python /home/j/anick/patent-classifier/ontology/creation/reformat_uc1.py | sortnr -k1 > growth.t.100.lw.uc
# This tells us which features have the broadest use across the set of high growth terms.  For the set of years,
# how many different terms appeared with this feature?

############################################
# prob analysis of features for high growth terms

# create all feature pairs for the top <n=feature_count> features (i.e., lines) in the feature_file
# read features from a frequency sorted file of the form:
# doc_count\tfeature
# such as growth.t.100.uc

#tf = phran.make_feature_pairs("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-cs-500k/data/tv/growth.t.100.uc", 4)

def make_feature_pairs(feature_file, feature_count):
    s_feature_file = codecs.open(feature_file, encoding='utf-8')
    i = 0
    l_features = []
    for line in s_feature_file:
        line = line.strip("\n")
        (freq, feature) = line.split("\t")
        l_features.append(feature)
        i += 1
        if i == feature_count:
            break
    s_feature_file.close()

    # now create pairs of features, putting the pair in alphabetical order
    l_pairs = []
    l_features2 = list(l_features)
    
    for feature1 in l_features:
        for feature2 in l_features2:
            #print "considering %s, %s" % (feature1, feature2)
            if feature1 < feature2:
                # make tuples so we can use them as dictionary keys
                l_pairs.append(tuple([feature1, feature2]))
            # note that we don't create a pair of the same features (when feature1 == feature2)

    return(l_pairs)

# Compute probabilities for feature relationships (e.g., appearance order)
# A range of years is assumed (given the files used as input have already been constructed
# using a fixed range of years, e.g. 1997-2006)
# cat is "t" or "c".  count is some number of terms to be analyzed (e.g. 100)
# We assume that the following files (or equivalent) exist:
# growth.t.100.lw
# growth.t.100
# growth.t.100.uc
# growth.c.100.lw
# growth.c.100
# growth.c.100.uc

# fit = phran.featInfo("ln-us-cs-500k", "t", 100)
# fic = phran.featInfo("ln-us-cs-500k", "c", 100)
class featInfo():
    def __init__(self, corpus, cat, term_count, feature_count=20, lw_count=20):
        term_count = str(term_count)
        term_feature_file = corpus_root + "/" + corpus + "/data/tv/" + "growth." + cat + "." + term_count
        term_lw_file = term_feature_file + ".lw"
        feature_file = term_feature_file + ".uc"
        lw_file = term_lw_file + ".uc"
    
        self.l_terms = set()
        # Create feature pairs for the top ranked features for this category of terms
        # These are tuples, so can be used as dictionary keys.
        self.feature_pairs = make_feature_pairs(feature_file, feature_count)
        self.lw_pairs = make_feature_pairs(lw_file, lw_count)

        # term and feature to first year that this feature occurs with this term
        self.d_tf2year = {}
        # term to first year that the term occurs in 1 doc
        self.d_t2year = {}
        # relyear, term, feature to doc frequency 
        self.d_rtf2dcount = defaultdict(int)

        # count the number of times a pair of features occurs in temporal order (based on
        # year of first appearance with a term)
        self.d_ff2lt = defaultdict(int)
        self.d_ff2gt = defaultdict(int)
        self.d_ff2eq = defaultdict(int)
        # count of times both features occur with term within range of years
        self.d_ff2tcount = defaultdict(int)
        # count of times a feature occurs with some term within range of years
        self.d_f2tcount = defaultdict(int)
        # count of # of terms that have a feature in relyear
        self.d_rf2tcount = defaultdict(int)
        # count of # of terms that are included in relyear
        # Note that not all terms start in the same year.  So higher relyears will
        # have fewer terms participating.
        self.d_r2tcount = defaultdict(int)
        # cumulative count of feature occurring with term over a range of years
        # i.e. feature occurred with 10 terms in year 1 and 20 terms in year 2 => count = 30
        self.d_f2count = defaultdict(int)
        # number of docs a term occurs in in a relyear
        self.d_rt2dcount = defaultdict(int)

        # list of features encountered in a relyear
        self.d_r2l_feats = defaultdict(set)
        # list of headwords encountered in a relyear
        self.d_r2l_heads = defaultdict(set)

        # populate d_tf2year
        # file is sorted by year within term, so the first year encountered for a term_feature combination
        # can be used as the year of first appearance for the combination.
        s_term_feature_file = codecs.open(term_feature_file, encoding='utf-8')
        for line in s_term_feature_file:
            line = line.strip("\n")
            (year, term, feature, doc_freq) = line.split("\t")
            year = int(year)
            tf = tuple([term, feature])
            # add the term to our set of terms
            self.l_terms.add(term)
            # if the tf has not yet been seen, make this the year of appearance
            if not self.d_tf2year.has_key(tf):
                self.d_tf2year[tf] = year
                # increment the term count for this feature
                self.d_f2tcount[feature] += 1
            # If we encounter a term for the first time, store the year
            if not self.d_t2year.has_key(term):
                self.d_t2year[term] = year
            # update the feature occurrence count
            self.d_f2count[feature] += 1
        s_term_feature_file.close()

        # now we need to reread the term_feature_file to store relative year (relyear) counts
        s_term_feature_file = codecs.open(term_feature_file, encoding='utf-8')
        for line in s_term_feature_file:
            line = line.strip("\n")
            (year, term, feature, doc_freq) = line.split("\t")
            year = int(year)
            doc_freq = int(doc_freq)
            relyear = year - self.d_t2year[term]
            rf = tuple([relyear, feature])
            rt = tuple([relyear, term])
            self.d_rf2tcount[rf] += 1
            if feature[0:9] == "last_word":
                # The last_word feature occurs once for every year in which the term occurs.
                # use it to signal when to increment the term count for the relyear
                self.d_r2tcount[relyear] += 1
                self.d_rt2dcount[rt] = doc_freq
            else: 
                # add the feature to the set of features found in this relyear
                self.d_r2l_feats[relyear].add(feature)

            # store actual doc_freq for the term and feature within relyear
            rtf = tuple([relyear, term, feature])
            self.d_rtf2dcount[rtf] = doc_freq

        s_term_feature_file.close()

        # now add the last_word feature
        #2004    bluetooth       bluetooth specification last_word=specification 10
        s_term_lw_file = codecs.open(term_lw_file, encoding='utf-8')
        for line in s_term_lw_file:
            line = line.strip("\n")
            (year, term, phrase, feature, doc_freq) = line.split("\t")
            year = int(year)
            doc_freq = int(doc_freq)
            tf = tuple([term, feature])
            # add the term to our set of terms
            #self.l_terms.add(term)
            # if the tf has not yet been seen, make this the year of appearance
            if not self.d_tf2year.has_key(tf):
                self.d_tf2year[tf] = year
                # increment the term count for this feature
                self.d_f2tcount[feature] += 1

            # update the relyear feature count as well
            relyear = year - self.d_t2year[term]
            rf = tuple([relyear, feature])
            self.d_rf2tcount[rf] += 1

            # update the feature occurrence count so that last_word features are included
            self.d_f2count[feature] += 1

            # add the last_word to the set of features found in this relyear
            self.d_r2l_heads[relyear].add(feature)

            # store actual doc_freq for the term and feature within relyear
            rtf = tuple([relyear, term, feature])
            self.d_rtf2dcount[rtf] = doc_freq


        s_term_lw_file.close()

        # use the d_tf2year data to populate our ff dictionaries
        all_feature_pairs = self.feature_pairs + self.lw_pairs
        for pair in all_feature_pairs:
            f1 = pair[0]
            f2 = pair[1]
            pair = tuple(pair)
            for term in self.l_terms:
                # create the keys for d_tf2year
                tf1 = tuple([term, f1])
                tf2 = tuple([term, f2])
            
                if self.d_tf2year.has_key(tf1) and self.d_tf2year.has_key(tf2):
                    # increment # terms that have both features
                    self.d_ff2tcount[pair] += 1
                    # increment appropriate temporal relation count for the feature pair
                    if self.d_tf2year[tf1] < self.d_tf2year[tf2]:
                        self.d_ff2lt[pair] += 1
                    elif self.d_tf2year[tf1] > self.d_tf2year[tf2]:
                        self.d_ff2gt[pair] += 1
                    else:
                        self.d_ff2eq[pair] += 1

        #pdb.set_trace()
        print "d_ff2tcount:"
        l_kv = []
        for kv in sort_dict_num_values(self.d_ff2tcount):
            key = kv[0]
            total = kv[1]
            pdiff = (self.d_ff2lt[key] - self.d_ff2gt[key]) / float(total)
            if pdiff < 0:
                # reverse the feature order if pdiff is negative
                new_key = tuple([key[1], key[0]])
                pdiff = -1 * pdiff
                # switch the order of the feature data to correspond to feature reversal
                l_kv.append([new_key, total, pdiff, self.d_ff2gt[key], self.d_ff2lt[key], self.d_ff2eq[key]])
            else:
                l_kv.append([key, total, pdiff, self.d_ff2lt[key], self.d_ff2gt[key], self.d_ff2eq[key]])
            #print "%s %f %i %i %i" % (kv, pdiff, self.d_ff2lt[key], self.d_ff2gt[key], self.d_ff2eq[key])

        l_kv.sort(utils.list_element_2_sort)
        for kv in l_kv:
            print "%s %i %f %i %i %i" % (kv[0], kv[1], kv[2], kv[3], kv[4], kv[5])


        # print relyear info
        for relyear in self.d_r2tcount.keys():
            print "relyear: %i, tcount: %i" % (relyear, self.d_r2tcount[relyear])

        # get features with highest overall occurrence
        l_feat_counts = []
        for feature in self.d_f2count.keys():
            l_feat_counts.append([feature, self.d_f2count[feature]])
        l_feat_counts.sort(utils.list_element_2_sort)
        for fc in l_feat_counts[0:50]:
            feature = fc[0]
            count = fc[1]
            print "feature: %s, count: %i" % (feature, count)
            for relyear in range(0,8):
                rf = tuple([relyear, feature])
                prob = self.d_rf2tcount[rf] / (float(self.d_r2tcount[relyear]) + .00001)
                print "%i: %i, %i, %i, %i, %f" % (relyear, self.d_rf2tcount[rf], self.d_r2tcount[relyear], len(self.d_r2l_feats[relyear]), len(self.d_r2l_heads[relyear]),prob)
        #pdb.set_trace()

                                 
    def rtf2dcount(self, term, feature):
        for relyear in range(0,8):
            rtf = tuple([relyear, term, feature])
            rt = tuple([relyear, term])
            rtf_dcount = self.d_rtf2dcount[rtf]
            rt_dcount = self.d_rt2dcount[rt] + .000001

            prob = rtf_dcount / float(rt_dcount)
            print "%i\t%i\t%f" % (rtf_dcount, rt_dcount, prob)

    def rt2dcount(self, term):
        feature_list = ["prev_Jpr=such_as", "last_word=standard", "prev_V=include", "prev_V=called", "prev_V=including", "prev_Npr=use_of", "prev_V=includes", "prev_V=use", "last_word=standards", "prev_V=relates_to", "prev_J=such", "last_word=module", "prev_J=conventional", "prev_V=associated_with", "prev_J=other"]
        print "term: %s" % term
        for feature in feature_list:
            print "%s" % feature
            self.rtf2dcount(term, feature)

