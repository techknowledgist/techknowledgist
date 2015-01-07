import pdb
import utils
from collections import defaultdict
import math
import codecs

import pnames
import roles_config

corpus_root = roles_config.CORPUS_ROOT

# sort features associated with tasks by the number of different terms they cooccur with
# l_tf = task.task2top_features("ln-us-A21-computers", "2005.act.cat.w0.0.t", "2005.task.feats", 1000)
def task2top_features(corpus, term_subset_file, output_feats_file, n):
    term_subset_path = pnames.tv_dir(corpus_root, corpus) + "/" + term_subset_file
    s_term_subset = codecs.open(term_subset_path,  encoding='utf-8')

    output_feats_path = pnames.tv_dir(corpus_root, corpus) + "/" + output_feats_file
    s_feats_subset = codecs.open(output_feats_path, "w", encoding='utf-8')

    d_feat2term_count = defaultdict(int)

    for term_line in s_term_subset:
        term_line = term_line.strip("\n")
        term_fields = term_line.split("\t")
        features_string = term_fields[9]
        l_features = features_string.split(" ")
        for feat_count in l_features:
            #print "feat_count: %s" % feat_count
            #if feat_count[0:10] != 'last_word=':
            if feat_count[0:2] != 'la':
                # get the feature (without the count) and increment its term count
                d_feat2term_count[feat_count.split("^")[0]] += 1

        # sort the features by term count (number of different terms that occur with this feature (in the year)
        l_feat_term_count = []
        #pdb.set_trace()
        for feat in d_feat2term_count.keys():
            l_feat_term_count.append([feat, d_feat2term_count[feat]])

    s_term_subset.close()
    
    # pdb.set_trace()
    for item in sorted(l_feat_term_count, key=lambda x: (x[1],x[1]), reverse=True)[0:n]:
        s_feats_subset.write("%s\t%i\n" % (item[0], item[1])) 

    s_feats_subset.close()

# for a set of terms (tasks) and features,
# store the doc_freq of each feature for a given year for each term
# TBD: Also compute dispersion and entropy, using all features.

# task
# tyff = task.term_year_feat_freq("ln-us-A21-computers", "1998.cohort.filt", "2005.task.feats", 100, 1998, 2000)
class term_year_feat_freq():

    def __init__(self, corpus, term_file, feat_file, num_feats, start_year=1997, end_year=2007):
        # open input files
        term_path = pnames.tv_dir(corpus_root, corpus) + "/" + term_file
        feat_path = pnames.tv_dir(corpus_root, corpus) + "/" + feat_file
        s_term = codecs.open(term_path,  encoding='utf-8')
        s_feat = codecs.open(feat_path,  encoding='utf-8')

        self.d_term = {}
        self.d_feat2rank = {}
        self.d_rank2feat = {}
        self.d_term_year_feat2freq = defaultdict(int)
        self.d_term_year2disp = defaultdict(int)
        self.d_term_year2feats = defaultdict(list)

        # load the terms
        for line in s_term:
            line = line.strip("\n")
            fields = line.split("\t")
            self.d_term[fields[0]] = True

        # load the features in term cooccurrence frequency order
        rank = 1
        for line in s_feat:
            line = line.strip("\n")
            fields = line.split("\t")
            self.d_feat2rank[fields[0]] = rank
            self.d_rank2feat[rank] = fields[0]
            rank += 1


        # for each year, store freq of feature for the term (using .tf data)
        end_range = end_year + 1
        for year in range(start_year, end_range):
            tf_file = pnames.tv_dir_year_file(corpus_root, corpus, year, "tf") 
            s_tf = codecs.open(tf_file,  encoding='utf-8')
            for line in s_tf:
                line = line.strip("\n")
                fields = line.split("\t")
                term = fields[0]
                feat = fields[1]
                freq = fields[2]
                if self.d_term.has_key(term):
                    #increment dispersion count for each new feature appearing with a term in a year
                    self.d_term_year2disp[tuple([term, year])] += 1
                    # todo/// add entropy here
                    if self.d_feat2rank.has_key(feat):
                        self.d_term_year_feat2freq[tuple([term, year, feat])] = freq
                        self.d_term_year2feats[tuple([term, year])].append([feat, freq])

            s_tf.close()

        s_term.close()
        s_feat.close()

    # lfs = tyff.term_rank_freq("security transactions", 20, 1998, 2000)
    def term_rank_freq(self, term, max_rank, start_year, end_year):
        end_range = end_year + 1
        l_freq_string = []
        freq_string = ""
        for year in range(start_year, end_range):
            rank = 1
            freq_string = term + " " + str(year)
            while rank <= max_rank:
                #pdb.set_trace()
                freq_string += " " + str(self.d_term_year_feat2freq[tuple([term, year, self.d_rank2feat[rank]])])
                rank += 1
            l_freq_string.append(freq_string)
            print "freq_string: %s" % freq_string
        return(l_freq_string)
        

