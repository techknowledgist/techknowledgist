# nbayes.py
# Perform naive Bayes classification
# 
# probability data:
# feature\tweight\tlfgc0 lfgc1 lfgc2 ...
# where a feature is of the form prev_V=manage
# weight is used as a threshold, e.g. kl-divergence
# lfgc(n) is the log of the conditional prob of a feature given a category
# We assume the number of categories is the same for all records and in a predetermined order
# e.g., a c o t (for affected, constituent, obstacle, task)

##################################################
# Sequence of steps to produce the nbayes output for a domain, including polarity
# (1) sh run_term_features_multi.sh which extracts the features of interest for each file in the source
# directories and puts them into a local directory (...corpus/term_root/<year>)  
# (2) role.run_tf_steps("ln-us-12-chemical", 1997, 1997, "act", ["tf", "tc", "tcs", "fc", "uc", "prob"], "")
# (3) nbayes.run_steps("ln-us-12-chemical", 1997, ["nb", "ds", "cf"])
# (4) nbayes.run_filter_tf_file("ln-us-12-chemical", 1997, "0.0") # create a.tf, needed for running polarity
# (5) role.run_tf_steps("ln-us-12-chemical", 1997, 1997, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")
# (6) nbayes.run_steps("ln-us-12-chemical", 1997, ["nb", "ds", "cf"], cat_type="pn", subset="a") 

# nbayes.run_filter_tf_file("ln-us-12-chemical", 1997, "0.0")

# runs
# ln-us-all-600k
# nbayes.run_steps("ln-us-all-600k", 1997, ["nb"])   

# file formats
# cat.w0.0:
# created by classify
# term num_diagnostic_feats num_doc_feature_instances max_cat doc_freq score_string feat_list
# where score_string gives scores in the order ACT or PN
# note that doc_freq means number of docs the term occurs in, regardless of existence of diagnostic features,
# so this can be larger than num_doc_feature_instances.

import pdb
import codecs
import sys
import math
from collections import defaultdict
#from role import tv_filepath
import role
import pnames

# populate the conditional probability table
# lfcg[feature] -> [prefix, wt, [<lfgc>+]]

# input file line example (1997.fc_kl):
# prev_V=improving        a      a+ c-   275     2.514945                -0.249762837589 -1.90682879901  -4.01096295328  -2.73002910782              -4.90099344745  -10.2646354049  -8.91492178304  -8.46281913295

# ///todo: add a similarity metric to determine which classes are not strongly discriminated.  This is best used for 
# polarity to determine non-polar attributes.
# compute a ratio to estimate the similarity of two scores.  Separate out the sign and put the larger number in the denominator.
def sim_ratio(v1, v2):
    return( v1 / v2)

# d_lfgc = nbayes.populate_lfgc("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.fc_kl")
def populate_lfgc(infile):
    print "[populate_lfgc]infile: %s" % infile
    # dict of weight, log(feature given category)
    # weight is kl-divergence score for the feature
    d_lfgc = {}
    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        l_fields = line.split("\t")
        feature = l_fields[0]
        prefix = feature.split("=")[0]
        # weight is the kl-divergence score for this feature
        weight = float(l_fields[4])
        # list of conditional probs for each category
        #l_lfgc_strings = l_fields[6].split(" ")
        #pdb.set_trace()
        # get the log probs for feature given category 
        l_lfgc = [float(i) for i in l_fields[6].strip().split(" ")]
        d_lfgc[feature] = [prefix, weight, l_lfgc]

    s_infile.close()
    return(d_lfgc)

# populate prior prob table
# This is an ordered list, with the same order of cats as the lfgc list
# priors = [<prior>+]
# example of line (1997.fc.cat_prob): cat freq prob
# a       28900   0.021762

# returns a list of 2 lists:
# ordered names of categories
# ordered priors for each category
# (l_cats, l_priors) = nbayes.populate_priors("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.fc.cat_prob")
def populate_priors(infile):
    l_cats = []
    l_priors = []
    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        l_fields = line.split("\t")
        cat = l_fields[0]
        l_cats.append(cat)
        prob = l_fields[2]
        l_priors.append(float(prob))

    s_infile.close()
    return([l_cats, l_priors])


# thresholds = [<threshold>+]

# populate term/feature dictionary
# restricted to certain prefixes (e.g. prev_VNP=)
# feature_prefixes = []
# d_term2feats[term] => [<feature>+]

# input file example (1997.tf):
# protected amidino group prev_V=represents       1       0.000050
# d_term2feats = nbayes.populate_terms("/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.tf")
# create a dict with key = term and value = [feature, doc_frequency (for the term-feature pair)]
def populate_terms(infile):
    d_term2feats = defaultdict(list)

    s_infile = codecs.open(infile, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        feature = l_fields[1]
        freq = int(l_fields[2])
        d_term2feats[term].append([feature, freq])

    s_infile.close()
    return(d_term2feats)

# term2freq_file is <year>.terms
# input file line should start with term\tdoc-freq
# return a dict with key term and value its document frequency
def populate_term2freq(term2freq_file):
    d_term2freq = {}

    s_infile = codecs.open(term2freq_file, encoding='utf-8')
    for line in s_infile:
        line = line.strip("\n")
        #(term, doc_freq, corpus_freq, prob ) = line.split("\t")
        l_fields = line.split("\t")
        term = l_fields[0]
        doc_freq = l_fields[1]
        d_term2freq[term] = doc_freq

    s_infile.close()
    return(d_term2freq)

    
# create a.tf and t.tf by filtering out any terms not labeled as a or t in
# <year>.act.cat.w0.2


def filter_tf_file(corpus_root, corpus, year, act_file_type):
    #tf_file = tv_root + str(year) + ".tf"
    tfa_subset = "a"
    tft_subset = "t"

    tf_file =  pnames.tv_filepath(corpus_root, corpus, year, "tf", "", cat_type="")
    tfa_file =  pnames.tv_filepath(corpus_root, corpus, year, "tf", tfa_subset, cat_type="")
    tft_file =  pnames.tv_filepath(corpus_root, corpus, year, "tf", tft_subset, cat_type="")
    print "[filter_tf_file]Creating tfa_file: %s" % tfa_file
    print "[filter_tf_file]Creating tft_file: %s" % tft_file

    act_file =  pnames.tv_filepath(corpus_root, corpus, year, act_file_type, "", "act")
    print "[filter_tf_file]Reading from act_file: %s" % act_file
    
    s_tfa = codecs.open(tfa_file, "w", encoding='utf-8')
    s_tft = codecs.open(tft_file, "w", encoding='utf-8')

    d_term2cat = defaultdict(str)

    # store the category of each term labeled a and t 
    s_act_file = codecs.open(act_file, encoding='utf-8')
    for line in s_act_file:
        line = line.strip("\n")
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[3]
        d_term2cat[term] = cat
        #print "term: %s, cat: %s" % (term, cat)
    s_act_file.close()

    # create subset files of .tf for the a and t terms
    s_tf_file = codecs.open(tf_file, encoding='utf-8')
    for line in s_tf_file:
        # don't bother to strip off newline
        # just grab the term
        term = line.split("\t")[0]
        cat = d_term2cat[term]
        if cat == "a":
            s_tfa.write(line)
        elif cat == "t":
            s_tft.write(line)

    s_tf_file.close()
    s_tfa.close()
    s_tft.close()

# For each term in d_term2features,
# for each cat, we compute the posterior prob using the log of the prior x product of fgc probs.
# compute priors[cat_idx] + sum of lfgc[feature][cat_idx] for all features with wt over threshold 
# Choose category as cat with highest score.
# max_cat

# nbayes.classify(l_cats, l_priors, d_lfgc, d_term2feats, 0.7, "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.cat.0.7")
# nbayes.classify(l_cats, l_priors, d_lfgc, d_term2feats, 0.7, "/home/j/anick/patent-classifier/ontology/creation/data/patents/ln-us-14-health/data/tv/1997.cat.0.7")

# output is: term #diagnostic-features #term-feature-instances class doc_freq scores features
# min_weight is the minimum kl_divergence score for the feature (in .fc_kl) to be 
# utilized as a feature in NB.
def classify(l_cats, l_priors, d_lfgc, d_term2feats, d_term2freq, min_weight, outfile):
    s_outfile = codecs.open(outfile, "w", encoding='utf-8')
    unlabeled_count = 0
    for term in d_term2feats.keys():
        #print "term: %s" % term
        # initialize small dictionary to accumulate scores per category for the term
        d_cat_scores = dict(zip(l_cats, l_priors))
        # iterate over the features for the term, accumulating the score for each 
        # category from the feature's log conditional prob.
        #pdb.set_trace()
        num_diagnostic_feats = 0
        num_doc_feature_instances = 0
        # accumulate all features into a list to create a string of feats for output
        # Here is where we do feature selection, so we compute the size of the 
        # feature vocabulary here (needed for Laplace "add one" smoothing in the NB calculation.)
        feat_list = []
        for (feat, freq) in d_term2feats[term]:
            # lfgc: log feature given class
            if d_lfgc.has_key(feat) and (d_lfgc[feat][1] > min_weight):
                #pdb.set_trace()
                num_diagnostic_feats += 1
                num_doc_feature_instances += freq
                feat_list.append(feat + "^" + str(freq))
                cat_idx = 0
                #pdb.set_trace()
                # for each category, add the score for this feature to the accumulating score
                # for the category.  The score multiplies the freq by the log(feature given category prob)
                # Example: d_lfgc["prev_V=make"]   is  [u'prev_V', 0.210119, [-0.21130909366699999, -1.6582280765999999]]
                for cat in l_cats:
                    #score = d_lfgc[feat][1] * freq
                    #print "feat: %s, weight: %f" % (feat, score)
                    if d_lfgc[feat][2][cat_idx] > 0:
                        pdb.set_trace()
                    d_cat_scores[cat] += (d_lfgc[feat][2][cat_idx]) * freq
                    cat_idx += 1
        # find the category with the highest (i.e. max cat) score
        # default the category output to "u" for unknown if there are no diagnostic features
        max_cat = "u"
        score_string = ""
        # Remember how many diagnostic features were used and number of (doc)instances of this term with a diagnostic feature
        # That is, we only count a term-feature pair once per doc.
        output_string = term + "\t" + str(num_diagnostic_feats) + "\t" + str(num_doc_feature_instances)
        if num_diagnostic_feats > 0:
            max_cat_score = -1000000000
            max_cat = ""
            #print "%s:" % (term)
            score_string = ""
            for cat in l_cats:
                score = d_cat_scores[cat]
                score_string = score_string + "\t" + str(score)
                #print "%s: %s" % (cat, score)
                if score > max_cat_score:
                    max_cat = cat
                    max_cat_score = score
        else:
            unlabeled_count += 1
        if d_term2freq.has_key(term):
            # note: we have found some cases where a term in .tf does not have a corresponding entry in d_term2freq
            # (see comments in role.py)  To prevent a key error we check that key exists first, even though all terms
            # should be keys in d_term2freq

            # get the term's document frequency
            doc_freq = str(d_term2freq[term])

            output_string = output_string + "\t" + max_cat + "\t" + doc_freq +  "\t" + score_string + "\t" + ' '.join(feat_list)
            #print "output: %s" % output_string

            # save space by not outputting the unknown lines (lines that were not categorized)
            if max_cat != "u":
                s_outfile.write("%s\n" % output_string)

    print "unlabeled terms (no category assigned): %i" % unlabeled_count

    s_outfile.close()


# NOTE:
# For running "act" classifications, use the .tf file (terms_subset = "")
# For running "pn" classification, use a subset of .tf filtered by type (subset="a" or "t")
# This way we are classifying only terms already known to be aspects or tasks

# nbayes.classify(l_cats, l_priors, d_lfgc, d_term2feats, .5)
# nbayes.run_classify("ln-us-14-health", 1997, "act", "")
# nbayes.run_classify("ln-us-14-health", 2002, "act")
# nbayes.run_classify("ln-us-14-health", 1997, "pn")
# nbayes.run_classify("ln-us-cs-500k", 1997, "act", "")
# nbayes.run_classify("ln-us-cs-500k", 1997, "pn", "a")
# nbayes.run_classify("ln-us-cs-500k", 1997, "pn", "a")
# nbayes.run_classify("ln-us-all-600k", 1997, "act", "")  
# nbayes.run_classify("ln-us-cs-500k", 1997, "pn", "a")
# nbayes.run_classify("ln-us-all-600k", 1997, "pn", "a")
# nbayes.run_classify("ln-us-14-health", 1997, "pn", "a")

def run_classify(corpus, year, cat_type, subset=""):

    corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    #tv_loc = "/data/tv/"
    outfile_qualifier = "cat"
    priors_qualifier = "cat_prob"
    terms_qualifier = "tf"
    term2freq_qualifier = "terms"
    lfgc_qualifier = "fc_kl"

    ################ variable parts of path
    outfile_year = str(year)
    year_cat_name = outfile_year + "." + cat_type
    #corpus = "ln-us-cs-500k"
    #corpus = "ln-us-12-chemical"
    ################

    #print "[run_classify]Output dir: %s" % tv_loc

    #path_to_terms_file = outroot + corpus + tv_loc + outfile_year + "."
    #path_to_terms_file =  pnames.tv_filepath(corpus_root, corpus, year, "tf", subset, "")
    #path_to_file = outroot + corpus + tv_loc + year_cat_name + "."
    #priors_file = path_to_file + priors_qualifier
    priors_file =  pnames.tv_filepath(corpus_root, corpus, year, priors_qualifier, subset, cat_type)
    #terms_file = path_to_terms_file + terms_qualifier
    terms_file =  pnames.tv_filepath(corpus_root, corpus, year, terms_qualifier, subset, "")

    #lfgc_file = path_to_file + lfgc_qualifier
    lfgc_file =  pnames.tv_filepath(corpus_root, corpus, year, lfgc_qualifier, subset, cat_type)

    #term2freq_file = path_to_terms_file + term2freq_qualifier
    term2freq_file =  pnames.tv_filepath(corpus_root, corpus, year, term2freq_qualifier, "", "")
    

    # compute l_cats, l_priors, d_lfgc, d_term2feats once and use them to run several thresholds
    print "[nbayes.py]priors_file: %s" % priors_file 
    (l_cats, l_priors) = populate_priors(priors_file)

    print "[nbayes.py]lfgc_file: %s" % lfgc_file 
    d_lfgc = populate_lfgc(lfgc_file)

    print "[nbayes.py]terms_file: %s" % terms_file 
    d_term2feats = populate_terms(terms_file)

    print "[nbayes.py]term2freq_file: %s" % term2freq_file 
    d_term2freq = populate_term2freq(term2freq_file)
    
    # min_weight = .2
    #for min_weight in [.1, .2]:
    for cutoff in [ .1, .05, .0]:
        cutoff_qualifier = role.cat_cutoff_file_type(cutoff)
        #outfile = path_to_file + outfile_qualifier + ".w" + cutoff_qualifier
        outfile =  pnames.tv_filepath(corpus_root, corpus, year, cutoff_qualifier, subset, cat_type)
        print "[nbayes.py]classifying into outfile: %s" % outfile 
        classify(l_cats, l_priors, d_lfgc, d_term2feats, d_term2freq, cutoff, outfile)

# nbayes.run_filter_tf_file("ln-us-all-600k", 1997, "0.1")        
# nbayes.run_filter_tf_file("ln-us-cs-500k", 1997, "0.0")        
# nbayes.run_filter_tf_file("ln-us-14-health", 1997, "0.0")        
# nbayes.run_filter_tf_file("ln-us-12-chemical", 1997, "0.0")        
def run_filter_tf_file(corpus, year, cutoff="0.1"):
    corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    #tv_loc = "/data/tv/"
    #tv_root = outroot + corpus + tv_loc 
    #year = str(year)
    # e.g., act file: 1997.act.cat.w0.2
    
    #act_file = tv_root + year + ".act.cat.w" + cutoff
    #act_file =  pnames.tv_filepath(corpus_root, corpus, year, file_type, subset, cat_type=""):
    #print "[run_filter_tf_file]Creating .tf.a and .tf.t from %s" % act_file
    #filter_tf_file(tv_root, year, act_file)
    act_file_type = role.cat_cutoff_file_type(cutoff)
    filter_tf_file(corpus_root, corpus, year, act_file_type)

# compute a domain specificity score using freq within the domain corpus and freq within a generic
# corpus of the same year.
def domain_score(f_terms1, c1_size, f_terms2, c2_size, outfile):

    print "[domain_score]f_terms1: %s, f_terms2: %s, outfile: %s" % (f_terms1, f_terms2, outfile)

    # f_terms1 should be the domain corpus file
    # f_terms2 should be a generic (or random) corpus file
    s_terms1 = codecs.open(f_terms1, encoding='utf-8')
    s_terms2 = codecs.open(f_terms2, encoding='utf-8')
    s_domain_score = codecs.open(outfile, "w", encoding='utf-8')

    # Default to a frequency of 1 for unknown words in a corpus 
    d_terms1_freq = {}
    d_terms2_freq = {}

    # score = log (prob(term1)/prob(term2))
    # prob_term1 = freq_term1 / c1_size
    # prob_term2 = freq_term2 / c2_size
    # Taking the log:
    # score = log(freq_term1) - log(freq_term2) + (log(c1_size) - log(c2_size))
    # we can compute the (log(c1_size) - log(c2_size)) once, since this is constant

    c1_size = int(c1_size)
    c2_size = int(c2_size)

    log_corpus_sizes = math.log(c1_size) - math.log(c2_size)

    print "c1_size: %i, c2_size: %i, log_corpus_sizes: %f" % (c1_size, c2_size, log_corpus_sizes)

    #pdb.set_trace()
    # populate the frequency dictionary for the domain1
    count = 0
    for line in s_terms1:
        line = line.strip()
        (term, term_freq, term_instance_freq, term_prob) = line.split("\t")
        d_terms1_freq[term] = int(term_freq)
        count += 1
    print "[domain_score]s_terms1 count: %i" % count

    count = 0
    for line in s_terms2:
        line = line.strip()
        (term, term_freq2, term_instance_freq, term_prob) = line.split("\t")
        d_terms2_freq[term] = int(term_freq2)
        count += 1
    print "[domain_score]s_terms2 count: %i" % count

    for term in d_terms1_freq.keys():
        term1_freq = d_terms1_freq[term]
        if d_terms2_freq.has_key(term):
            term2_freq = d_terms2_freq[term]
            count += 1
        else:
            term2_freq = 1
        domain_score = math.log(term1_freq) - math.log(term2_freq) + log_corpus_sizes
        #pdb.set_trace()
        s_domain_score.write("%s\t%i\t%i\t%f\n" % (term, term1_freq, term2_freq, domain_score))
    print "[domain_score]d_terms1_freq count: %i" % count

    s_terms1.close()
    s_terms2.close()
    s_domain_score.close()

# first file should be the more recent year
# This must be run after domain specificity for later year (.ds) has been computed
def diff_score(f_terms1, y1_size, f_terms2, y2_size, f_ds1, cat_file, outfile):

    print "[diff_score]f_terms1: %s, f_terms2: %s, outfile: %s" % (f_terms1, f_terms2, outfile)

    # f_terms1 should be the corpus file for the later year
    # f_terms2 should be an equivalent earlier corpus file
    s_terms1 = codecs.open(f_terms1, encoding='utf-8')
    s_terms2 = codecs.open(f_terms2, encoding='utf-8')
    s_domain_score = codecs.open(f_ds1, encoding='utf-8')
    s_cat_file = codecs.open(cat_file, encoding='utf-8')
    s_diff = codecs.open(outfile, "w", encoding='utf-8')

    # Default to a frequency of 1 for unknown words in a corpus 
    d_terms1_freq = {}
    d_terms2_freq = {}
    d_ds = {}
    d_cat ={}

    # score = log (prob(term1)/prob(term2))
    # prob_term1 = freq_term1 / c1_size
    # prob_term2 = freq_term2 / c2_size
    # Taking the log:
    # score = log(freq_term1) - log(freq_term2) + (log(c1_size) - log(c2_size))
    # we can compute the (log(c1_size) - log(c2_size)) once, since this is constant

    y1_size = int(y1_size)
    y2_size = int(y2_size)

    log_corpus_sizes = math.log(y1_size) - math.log(y2_size)

    print "y1_size: %i, y2_size: %i, log_corpus_sizes: %f" % (y1_size, y2_size, log_corpus_sizes)

    #pdb.set_trace()
    # populate the frequency dictionary for the year1
    for line in s_terms1:
        line = line.strip()
        (term, term_freq, term_instance_freq, term_prob) = line.split("\t")
        d_terms1_freq[term] = int(term_freq)

    for line in s_terms2:
        line = line.strip()
        (term, term_freq2, term_instance_freq, term_prob) = line.split("\t")
        d_terms2_freq[term] = int(term_freq2)

    for line in s_domain_score:
        line = line.strip()
        (term, term1_freq, term2_freq, domain_score) = line.split("\t")
        d_ds[term] = float(domain_score)

    for line in s_cat_file:
        #pdb.set_trace()
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[3]
        d_cat[term] = cat

    for term in d_terms1_freq.keys():
        term1_freq = d_terms1_freq[term]
        if d_terms2_freq.has_key(term):
            term2_freq = d_terms2_freq[term]
        else:
            term2_freq = 1
        diff_score = math.log(term1_freq) - math.log(term2_freq) + log_corpus_sizes
        domain_score = d_ds[term]
        if d_cat.has_key(term):
            cat = d_cat[term]
        else:
            cat = "u"
        #pdb.set_trace()
        s_diff.write("%s\t%s\t%i\t%i\t%f\t%f\n" % (term, cat, term1_freq, term2_freq, diff_score, domain_score))

    s_terms1.close()
    s_terms2.close()
    s_domain_score.close()
    s_cat_file.close()
    s_diff.close()

def cat_filter(corpus_root, corpus, year, cat_type, subset, min_freq, min_domain_score, max_freq):
    cat_file_type = "cat.w0.0"
    f_cat =  pnames.tv_filepath(corpus_root, corpus, year, cat_file_type, subset, cat_type)
    f_ds =   pnames.tv_filepath(corpus_root, corpus, year, "ds", "", "")
    out_file_type = cat_file_type + "_r" + str(min_freq) + "-" + str(max_freq) + "_ds" + str(min_domain_score)
    f_out =  pnames.tv_filepath(corpus_root, corpus, year, out_file_type, subset, cat_type)

    d_term2cat = {}
    d_term2ds = {}

    s_cat = codecs.open(f_cat, encoding='utf-8')
    s_ds = codecs.open(f_ds, encoding='utf-8')
    s_out = codecs.open(f_out, "w", encoding='utf-8')

    # store domain_scores
    for line in s_ds:
        line = line.strip()
        #proximal zone   5       1       1.841114 
        (term, freq, generic_freq, domain_score) = line.split("\t")
        d_term2ds[term] = float(domain_score)

    # categorized terms
    for line in s_cat:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        cat = l_fields[3]
        try:
            freq = int(l_fields[4])
        except:
            print "[cat_filter]In line: %s" % line
            print "[cat_filter]Illegal integer in field 4: [%s][%s][%s][%s][%s][%s]" % (l_fields[0], l_fields[1], l_fields[2], l_fields[3], l_fields[4], l_fields[5])
            quit
        ds = d_term2ds[term]
        # filter and output
        if ds >= min_domain_score and (freq >= min_freq and freq <= max_freq):
            s_out.write("%s\t%s\t%i\t%f\n" % (term, cat, freq, ds))


    s_cat.close()
    s_ds.close()
    s_out.close()

# Create a subset of labeled terms with min freq and min domain score)
# This is useful to generate a set of terms for evaluation.
# nbayes.run_act_ds("ln-us-14-health", 1997, 10, 2)
# nbayes.run_act_ds("ln-us-cs-500k", 1997, 10, 2)
def run_cat_filter(corpus, year, min_freq, min_domain_score, max_freq, cat_type, subset):
    corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    cat_filter(corpus_root, corpus, year, cat_type, subset, min_freq, min_domain_score, max_freq)

# Generate domain scores (<year>.ds) for a corpus using a general corpus from the same year for comparison.
# nbayes.run_domain_score("ln-us-cs-500k", 18555 , "ln-us-all-600k", 15941, 1997)
# nbayes.run_domain_score("ln-us-14-health", 20097 , "ln-us-all-600k", 15941, 1997)
def run_domain_score(corpus1, corpus1_size, corpus2, corpus2_size, year):
    corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    #outfile_name = corpus1 + "_" + corpus2 + ".ds"
    outfile =  pnames.tv_filepath(corpus_root, corpus1, year, "ds", "", "")
    f_terms1 =  pnames.tv_filepath(corpus_root, corpus1, year, "terms", "", "")
    f_terms2 =  pnames.tv_filepath(corpus_root, corpus2, year, "terms", "", "")
    
    domain_score(f_terms1, corpus1_size, f_terms2, corpus2_size, outfile)

# nbayes.run_diff_score("ln-us-cs-500k", 2002, 1997)
# nbayes.run_diff_score("ln-us-14-health", 2002, 1997)
def run_diff_score(corpus, year1, year2):
    corpus_root = "/home/j/anick/patent-classifier/ontology/creation/data/patents/"
    outfile_years = str(year1) + "_" + str(year2)
    outfile =  pnames.tv_filepath(corpus_root, corpus, outfile_years, "diff", "", "")
    f_terms1 =  pnames.tv_filepath(corpus_root, corpus, year1, "terms", "", "")
    f_terms2 =  pnames.tv_filepath(corpus_root, corpus, year2, "terms", "", "")
    cat_file =  pnames.tv_filepath(corpus_root, corpus, year1, "cat.w0.0", "", "act")
    f_ds1 =  pnames.tv_filepath(corpus_root, corpus, year1, "ds", "", "")

    # read in the corpus sizes
    y1_size_file =  pnames.tv_filepath(corpus_root, corpus, year1, "cs", "", "")
    y2_size_file =  pnames.tv_filepath(corpus_root, corpus, year2, "cs", "", "")
    y1_size = 0
    y2_size = 0
    with open(y1_size_file, 'r') as f:
        y1_size = int(f.readline().strip("\n"))

    with open(y2_size_file, 'r') as f:
        y2_size = int(f.readline().strip("\n"))

    diff_score(f_terms1, y1_size, f_terms2, y2_size, f_ds1, cat_file, outfile)

# nbayes.run_steps("ln-us-cs-500k", 2002, ["nb", "ds", "cf"])
# nbayes.run_steps("ln-us-cs-500k", 1997, ["nb", "ds", "cf"])
# nbayes.run_steps("ln-us-cs-500k", 1997, ["cf"])
# nbayes.run_steps("ln-us-cs-500k", 2002, ["nb", "ds", "cf"])
# nbayes.run_steps("ln-us-cs-500k", 2002, ["cf"], ranges=[[10, 100000, 3.0], [2,10, 3.0]])
# nbayes.run_steps("ln-us-14-health", 2002, ["nb", "ds", "cf"], ranges=[[10, 100000, 1.0], [2,10, 1.0]])
# nbayes.run_steps("ln-us-14-health", 2002, ["cf"], ranges=[[10, 100000, 1.0], [2,10, 1.0]])
# nbayes.run_steps("ln-us-14-health", 2002, ["cf"], ranges=[[10, 100000, 0.05], [2,10, 0.05]])
# nbayes.run_steps("ln-us-14-health", 2002, ["nb"], cat_type="pn", subset="a")



# To generate a subset of attrs for use in evaluation min-freq =10, ds = 1.0
# nbayes.run_steps("ln-us-14-health", 2002, ["cf"], cat_type="pn", subset="a", ranges=[[10, 100000, 1.0]])
# nbayes.run_steps("ln-us-14-health", 2002, ["cf"], cat_type="pn", subset="a", ranges=[[10, 100000, 0.05]])
# nbayes.run_steps("ln-us-cs-500k", 2002, ["cf"], cat_type="pn", subset="a", ranges=[[10, 100000, 1.5]])

# min_freq = 5, ds = 1.0
# nbayes.run_steps("ln-us-14-health", 2002, ["cf"], cat_type="pn", subset="a", ranges=[[5, 100000, 1.0]])
# nbayes.run_steps("ln-us-cs-500k", 2002, ["cf"], cat_type="pn", subset="a", ranges=[[5, 100000, 3.0]])

# nbayes.run_steps("ln-us-12-chemical", 1997, ["nb", "ds", "cf"])
# nbayes.run_steps("ln-us-12-chemical", 1997, ["nb", "ds", "cf"], cat_type="pn", subset="a")

# todo_list.  
# nb: run the classifier (cat_type = act or pn [if pn, use subset a])
# ds: compute domain specificity scores
# cf: filter classified results by domain score and term frequency 
def run_steps(corpus, year, todo_list=["nb", "ds", "cf"], ranges=[[10, 100000, 1.5], [2,10, 1.5]], cat_type="act", subset=""):
    #parameters
    code_root = "/home/j/anick/patent-classifier/ontology/creation/"
    # path to corpus
    corpus_root = code_root + "data/patents/"
    corpus1_size_file =  pnames.tv_filepath(corpus_root, corpus, year, "cs", "", "")
    # generic corpus for domain specificity computation
    corpus2 = "ln-us-all-600k"
    corpus2_size_file =  pnames.tv_filepath(corpus_root, corpus2, year, "cs", "", "")

    # read in the corpus sizes
    with open(corpus1_size_file, 'r') as f:
        corpus1_size = int(f.readline().strip("\n"))

    with open(corpus2_size_file, 'r') as f:
        corpus2_size = int(f.readline().strip("\n"))
        
    if "nb" in todo_list:
        # from .fc_kl, create act.cat.w0.0
        print "[run_steps]step nb, Creating .cat.w0.0"
        run_classify(corpus, year, cat_type, subset)
    if "ds" in todo_list:
        # from , create .ds
        print "[run_steps]step ds, Creating .cat.w0.0_gt10_ds2"
        run_domain_score(corpus, corpus1_size, corpus2, corpus2_size, year)
    if "cf" in todo_list:

        # run cat_filter for each range
        for (min_freq, max_freq, min_domain_score) in ranges:

            # from .ds and act.cat.w0.0, create .cat.w0.0_gt5_ds2
            print "[run_steps]step cf, Creating .act.cat.w0.0_gt?_ds?"
            #min_freq = 5
            #min_domain_score = 2
            run_cat_filter(corpus, year, min_freq, min_domain_score, max_freq, cat_type, subset)

    print "[run_steps]Reached end of todo_list"

# run everything for a corpus and year

# nbayes.run_corpus_year(["ln-us-10-agriculture", "ln-us-11-construction"], [1997, 2002]) 
# nbayes.run_corpus_year(["wos-cs-520k"], [1997]) 
def run_corpus_year(corpus_list, year_list):
    for corpus in corpus_list:
        for year in year_list:
            year = int(year)
            print "[run_corpus_year]Processing corpus: %s for year: %i" % (corpus, year)
            role.run_tf_steps(corpus, 1997, 1997, "act", ["tf", "tc", "tcs", "fc", "uc", "prob"], "")
            run_steps(corpus, 1997, ["nb", "ds", "cf"])
            run_filter_tf_file(corpus, 1997, "0.0") # create a.tf, needed for running polarity
            role.run_tf_steps(corpus, 1997, 1997, "pn", ["tc", "tcs", "fc", "uc", "prob"], "a")
            run_steps(corpus, 1997, ["nb", "ds", "cf"], cat_type="pn", subset="a") 

        print "[run_corpus_year] Completed."


# run the nbayes act analysis for a range of years for a single corpus
# nbayes.run_nbayes_years("ln-us-cs-500k", 1998, 2007)
def run_nbayes_years(corpus, start_year, end_year):
    start_range = int(start_year)
    end_range = int(end_year) + 1
    for year in range(start_range, end_range):
        run_steps(corpus, year, todo_list=["nb", "ds", "cf"])
