# functions for use in pagerank interpretation of polarity

import codecs
from collections import defaultdict
import os
import pdb

"""
Compare probs for features/terms in positive and 
Consider raw diff in prob as well as relative to the sum of probs in the two graphs

item pos_pr neg_pr neutral_pr pos-neg pos/neg diff/sum

"""

#polarity.pr_diff("/home/j/anick/patent-classifier/ontology/roles/data/polarity/bio_2003", "pr.can.p.t.200.no_lw", "pr.can.n.t.200.no_lw", "pr.can.t.200.no_lw", "diff.can.t.200.no_lw")
#polarity.pr_diff("/home/j/anick/patent-classifier/ontology/roles/data/polarity/bio_2003", "pr.can.p.f.200.no_lw", "pr.can.n.f.200.no_lw", "pr.can.f.200.no_lw", "diff.can.f.200.no_lw")


def pr_diff(dir, pos_file, neg_file, neutral_file, diff_file):
    item_set = set()
    d_pos2pr = defaultdict(int)
    d_neg2pr = defaultdict(int)
    d_neutral2pr = defaultdict(int)

    pos_file = os.sep.join([dir, pos_file])
    neg_file = os.sep.join([dir, neg_file])
    neutral_file = os.sep.join([dir, neutral_file])
    diff_file = os.sep.join([dir, diff_file])
    s_pos_file = codecs.open(pos_file, encoding='utf-8')
    s_neg_file = codecs.open(neg_file, encoding='utf-8')
    s_neutral_file = codecs.open(neutral_file, encoding='utf-8')
    s_diff_file = codecs.open(diff_file, "w", encoding='utf-8')

    # populate dictionaries of item to pagerank
    for line in s_pos_file:
        line = line.strip()
        l_fields = line.split("\t")
        item = l_fields[0]
        pr = float(l_fields[1])
        d_pos2pr[item] = pr
        item_set.add(item)

    for line in s_neg_file:
        line = line.strip()
        l_fields = line.split("\t")
        item = l_fields[0]
        pr = float(l_fields[1])
        d_neg2pr[item] = pr
        item_set.add(item)

    for line in s_neutral_file:
        line = line.strip()
        l_fields = line.split("\t")
        item = l_fields[0]
        pr = float(l_fields[1])
        d_neutral2pr[item] = pr
        item_set.add(item)

    # compute stats for each item encountered
    for item in item_set:
        pos_pr = d_pos2pr[item]
        neg_pr = d_neg2pr[item]
        neutral_pr = d_neutral2pr[item]

        diff_pos_neg = pos_pr - neg_pr
        ratio_pos_neg = pos_pr / (neg_pr + .00001)
        ratio_neg_pos = neg_pr / (pos_pr + .00001)

        try:
            diff_sum_ratio_pos_neg = diff_pos_neg / (pos_pr + neg_pr + .00001)
        except:
            pdb.set_trace()
        ratio_pos_neutral = pos_pr / (neutral_pr + .00001)
        ratio_neg_neutral = neg_pr / (neutral_pr + .00001)
        diff_pos_neutral = pos_pr - neutral_pr
        diff_neg_neutral = neg_pr -neutral_pr
        ratio_diff_neutral_pos_neg = diff_pos_neutral / (diff_neg_neutral + .00001)
        ratio_diff_neutral_neg_pos = diff_neg_neutral / (diff_pos_neutral + .00001)
        
        #pdb.set_trace()
        s_diff_file.write("%s\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\n" % (item, pos_pr, neg_pr, neutral_pr, diff_pos_neg, ratio_pos_neg, ratio_neg_pos, diff_sum_ratio_pos_neg, ratio_diff_neutral_pos_neg, ratio_diff_neutral_neg_pos))
        
    s_pos_file.close()
    s_neg_file.close()
    s_neutral_file.close()
    s_diff_file.close()
    

#polarity.pr_diff("/home/j/anick/patent-classifier/ontology/roles/data/polarity/bio_2003/abstract", "pr.abs.can.p.t.200.no_lw", "pr.abs.can.n.t.200.no_lw", "pr.abs.can.t.200.no_lw", "diff.can.t.200.no_lw")
#polarity.pr_diff("/home/j/anick/patent-classifier/ontology/roles/data/polarity/bio_2003/abstract", "pr.abs.can.p.f.200.no_lw", "pr.abs.can.n.f.200.no_lw", "pr.abs.can.f.200.no_lw", "diff.can.f.200.no_lw")

#subdir is the dir under data/polarity.  Do not start or end with slash.
# polarity.do_diff("bio_2003")
def do_diff(subdir):
    base_dir = "/home/j/anick/patent-classifier/ontology/roles/data/polarity/"
    full_dir = base_dir + subdir
    abstract_dir = full_dir + "/abstract"
    pr_diff(full_dir, "pr.can.p.t.200.no_lw", "pr.can.n.t.200.no_lw", "pr.can.t.200.no_lw", "diff.can.t.200.no_lw")
    pr_diff(full_dir, "pr.can.p.f.200.no_lw", "pr.can.n.f.200.no_lw", "pr.can.f.200.no_lw", "diff.can.f.200.no_lw")
    pr_diff(abstract_dir, "pr.can.p.t.200.no_lw", "pr.can.n.t.200.no_lw", "pr.can.t.200.no_lw", "diff.can.t.200.no_lw")
    pr_diff(abstract_dir, "pr.can.p.f.200.no_lw", "pr.can.n.f.200.no_lw", "pr.can.f.200.no_lw", "diff.can.f.200.no_lw")
