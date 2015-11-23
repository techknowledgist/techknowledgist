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

    ratio_file = diff_file + ".pnr"

    ratio_file = os.sep.join([dir, ratio_file])
    pos_file = os.sep.join([dir, pos_file])
    neg_file = os.sep.join([dir, neg_file])
    neutral_file = os.sep.join([dir, neutral_file])
    diff_file = os.sep.join([dir, diff_file])
    s_pos_file = codecs.open(pos_file, encoding='utf-8')
    s_neg_file = codecs.open(neg_file, encoding='utf-8')
    s_neutral_file = codecs.open(neutral_file, encoding='utf-8')
    s_diff_file = codecs.open(diff_file, "w", encoding='utf-8')
    s_ratio_file = codecs.open(ratio_file, "w", encoding='utf-8')

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

    d_item2pn_ratio = {}
    # norm of a ratio is the square root of sum of squared values
    cumulative_pn_ratio_norm = 0.0

    # compute stats for each item encountered
    for item in item_set:
        pos_pr = d_pos2pr[item]
        neg_pr = d_neg2pr[item]
        neutral_pr = d_neutral2pr[item]

        diff_pos_neg = pos_pr - neg_pr
        diff_neg_pos = neg_pr - pos_pr
        ratio_pos_neg = pos_pr / (neg_pr + .00001)
        ratio_neg_pos = neg_pr / (pos_pr + .00001)

        try:
            diff_sum_ratio_pos_neg = diff_pos_neg / (pos_pr + neg_pr + .00001)
            diff_sum_ratio_neg_pos = diff_neg_pos / (pos_pr + neg_pr + .00001)
        except:
            pdb.set_trace()
        ratio_pos_neutral = pos_pr / (neutral_pr + .00001)
        ratio_neg_neutral = neg_pr / (neutral_pr + .00001)
        diff_pos_neutral = pos_pr - neutral_pr
        diff_neg_neutral = neg_pr -neutral_pr
        ratio_diff_neutral_pos_neg = diff_pos_neutral / (diff_neg_neutral + .00001)
        ratio_diff_neutral_neg_pos = diff_neg_neutral / (diff_pos_neutral + .00001)

        # probability of item in pos graph * not item in neg graph
        prob_pvsn = pos_pr * (1 - neg_pr)
        prob_nvsp = neg_pr * (1 - pos_pr)
        prob_both = pos_pr * neg_pr

        
        # save the ratio_pos_neg values to do normalization
        d_item2pn_ratio[item] = ratio_pos_neg
        cumulative_pn_ratio_norm += (ratio_pos_neg)**2

        #pdb.set_trace()
        s_diff_file.write("%s\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.10f\t%.10f\t%.10f\n" % (item, pos_pr, neg_pr, neutral_pr, diff_pos_neg, ratio_pos_neg, ratio_neg_pos, diff_sum_ratio_pos_neg, diff_sum_ratio_neg_pos, ratio_diff_neutral_pos_neg, ratio_diff_neutral_neg_pos, prob_pvsn, prob_nvsp, prob_both ))

        # so far, diff_sum_ratio_pos_neg (bash field 8 seems to work best)

    """
    # compute normalized ratios
    for item in d_item2pn_ratio.keys():
        norm_ratio = d_item2pn_ratio[item] / cumulative_pn_ratio_norm
        s_ratio_file.write("%s\t%.10f\n" % (item, norm_ratio))
    """

    s_pos_file.close()
    s_neg_file.close()
    s_neutral_file.close()
    s_diff_file.close()
    s_ratio_file.close()

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

# polarity.test_diff("ln-us-A21-computers/data/tv_ta")
def test_diff(subdir):
    #subdir = "ln-us-A23-semiconductors/data/tv_ta"
    base_dir = "/home/j/anick/patent-classifier/ontology/roles/data/patents/"
    full_dir = base_dir + subdir
    #pr_diff(full_dir, "2002.t.p.200", "2002.t.n.200", "2002.t.x.200", "2002.t.test.200")
    
    pr_diff(full_dir, "2002.t.p.0", "2002.t.n.0", "2002.t.x.0", "2002.t.test.0")
    pr_diff(full_dir, "2002.f.p.0", "2002.f.n.0", "2002.f.x.0", "2002.f.test.0")


"""
diff file fields

1 item, 
2 pos_pr, 
3 neg_pr, 
4 neutral_pr, 
5 diff_pos_neg, 
6 ratio_pos_neg, 
7 ratio_neg_pos, 
8 diff_sum_ratio_pos_neg, 
9 diff_sum_ratio_neg_pos,
10 ratio_diff_neutral_pos_neg, 
11 ratio_diff_neutral_neg_pos

for computer features, field 8 is good

"""
