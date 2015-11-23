import networkx as nx
from operator import itemgetter
import os
import pdb
import polarity

# ------------------------------------------------------------------------------------------------------------
# Creates 2 tab separated files of PageRank results (terms and features) for a given .tf file
# in_dir = path to directory containing tf_file
# out_dir = path to output directory
# out_prefix = a string of file name prefix, typically the year. 
# alpha = teleportation parameter
# seed_label should be n,p, or np (both), x (none)
# res_size = maximal number of terms/features to write into file (in descending order according to score)
# in_feat_list = a list of features to include in the graph (and no other features)
# ex_feat_list = a list of (substrings of) features to exclude from the graph (elements look like "prev_V")
# seed = a dictionayy of seed features as keys and weights as values (weights can have any numeric value)
# wt_type = {"cp", "mi"} indicating which file to expect at wt_file and which fields to use as weights for 
# pagerank graphs
# ------------------------------------------------------------------------------------------------------------
def page_rank(in_dir, out_dir, wt_file, out_prefix, seed_label, alpha = 0.85, res_size = 200, in_feat_list = [], ex_feat_list = [], seed = {}, wt_type="mi"):

    wt_file = os.sep.join([in_dir, wt_file])
    print "[run_pr.py]wt_file: %s" % wt_file
    l_wt_file_lines = open(wt_file).readlines()

    # Create feature include and exclude dictionaries from feature list arguments
    ex_dict = dict.fromkeys(ex_feat_list, None)
    in_dict = dict.fromkeys(in_feat_list, None)

    # Building the graph
    G = nx.DiGraph()
    for line in l_wt_file_lines:
        line = line.strip()
        fields = line.split('\t')
        term = fields[0]
        feature = fields[1]
        # Skip features in ex_list
        #if ex_dict.has_key(feature.split('=')[0]+'='):
        if ex_dict.has_key(feature.split('=')[0]):
            continue
        # Skip features not in in_list if the list is not empty
        if in_feat_list != []:
            if not in_dict.has_key(feature):
                continue   

        #pdb.set_trace()        
        if wt_type == "cp":
            # version using tf.py and conditional probs as weights
            p_f_t = fields[4]
            p_t_f = fields[5]
            G.add_edge(term, feature, weight=float(p_f_t))
            G.add_edge(feature, term, weight=float(p_t_f))


        elif wt_type == "mi":
            # version using normalized pointwise mutual information a weights 
            # assume the .tf file contains npmi in field 9 
            npmi = fields[9]

            # Assign the npmi weight to both directional links between feature and term
            # normalized PMI runs from -1 to 1.  Any negative values will be turned to 0 here.

            npmi = float(npmi)
            if npmi < 0 :
                npmi = 0.0

            #print "[run_pr.py]%s\t%s\t%f" % (term, feature, npmi)
            G.add_edge(term, feature, weight=npmi)
            G.add_edge(feature, term, weight=npmi)
            #pdb.set_trace()
        else:
            print "[run_pr.py]Unknown wt_type: %s.  Exiting." % wt_type
            
    # Creating the personalization vector (adding zero as weight for non seed nodes)

    if seed == {}:
        pers_vec = None
    else:
        pers_vec = seed
        for v in G.nodes():
            if pers_vec.has_key(v):
                continue
            else:
                pers_vec[v] = 0.0

    
    # run pagerank
    pr = nx.pagerank(G, alpha = alpha, personalization = pers_vec, dangling = pers_vec, max_iter=100)

    # Sort result by pr score and reverse the list
    #sorted_pr = sorted(pr.items(),key=itemgetter(1))
    #sorted_pr = sorted_pr[::-1]
    sorted_pr = sorted(pr.items(),key=itemgetter(1), reverse=True)
    
    # Separate terms and features
    fea_sorted_pr = [e for e in sorted_pr if '=' in e[0]]
    term_sorted_pr = [e for e in sorted_pr if '=' not in e[0]]

    # Print into 2 files res_size results
    term_file = make_pr_file_name(out_prefix, "t", seed_label, wt_type, res_size)
    feature_file = make_pr_file_name(out_prefix, "f", seed_label, wt_type, res_size)

    #pdb.set_trace()
    term_path = os.sep.join([out_dir, term_file])
    feature_path = os.sep.join([out_dir, feature_file])

    f_term = open(term_path, 'w')
    f_feat = open(feature_path, 'w')

    # if res_size == 0, keep all terms/feats
    if res_size != 0:
        term_sorted_pr = term_sorted_pr[:res_size]
        fea_sorted_pr = fea_sorted_pr[:res_size]
    for term in term_sorted_pr:
        f_term.write(str(term[0])+'\t'+str(term[1])+'\n')
    for f in fea_sorted_pr:
        f_feat.write(str(f[0])+'\t'+str(f[1])+'\n')

    f_term.close()
    f_feat.close()

    print "Created " + term_file
    print "Created " + feature_file

# get_seeds(["n", "p"])
def get_seeds(l_labels):
    # get seed features from file
    d_seed = {}
    seed_file = "/home/j/anick/patent-classifier/ontology/roles/seed.pn.en.canon.dat"
    s_seed = open(seed_file)
    for line in s_seed:
        line = line.strip()
        (label, feature) = line.split("\t")
        if label in l_labels:
            d_seed[feature] = 1.0
    s_seed.close()
    return(d_seed)

# prefix - typically the year
# tf_label - {t,f}
# seed_label - {p,n,x,b}
# wt_type = {"cp", "mi"}
# size - integer indicating the top n results of pagerank

def make_pr_file_name(prefix, tf_label, seed_label, wt_type, size):
    file_name = ".".join([str(prefix), tf_label, seed_label, wt_type, str(size)]) 
    return(file_name)


""" ------------------------------------------------------------------------------------------------------------
sample runs
databases: 
ln-us-A27-molecular-biology
ln-us-A23-semiconductors
ln-us-A21-computers

results of pagerank are placed in <database>/data/tv_ta and tv_tas
where _ta indicates data includes title and abstract only
and _tas indicates title, abstract, summary and background sections
Data is assumed to be canonicalized
# ------------------------------------------------------------------------------------------------------------
"""

# run_pr.run_prs("ln-us-A23-semiconductors", 2002, "tv", size=0, wt_type="cp")
def run_prs(db, year, tv_dir, size=200, wt_type="mi"):
    patents_dir = "/home/j/anick/patent-classifier/ontology/roles/data/patents"
    file_prefix = str(year)
    tf_file = file_prefix + ".a.tf" 
    dir_path = os.sep.join([patents_dir, db, "data", tv_dir])
    # e.g. /home/j/anick/patent-classifier/ontology/roles/data/patents/ln-us-A23-semiconductors/data/tv_ta        

    d_seed_n = get_seeds(["n"])
    d_seed_p = get_seeds(["p"])    
    d_seed_both = get_seeds(["n", "p"])    


    # don't include last_word feature in pagerank graph
    ex_feat_list = ["last_word", "prev_J"]

    #page_rank(in_dir, out_dir, tf_file, out_prefix, alpha = 0.85, res_size = 200, in_feat_list = [], ex_feat_list = [], seed = {})
    page_rank(dir_path, dir_path, tf_file, file_prefix, "n", alpha=0.85, res_size=size, in_feat_list=[], ex_feat_list=ex_feat_list, seed=d_seed_n, wt_type=wt_type)
    page_rank(dir_path, dir_path, tf_file, file_prefix, "p", alpha=0.85, res_size=size, in_feat_list=[], ex_feat_list=ex_feat_list, seed=d_seed_p, wt_type=wt_type)
    page_rank(dir_path, dir_path, tf_file, file_prefix, "b", alpha=0.85, res_size=size, in_feat_list=[], ex_feat_list=ex_feat_list, seed=d_seed_both, wt_type=wt_type)
    # no seeds (x)
    page_rank(dir_path, dir_path, tf_file, file_prefix, "x", alpha=0.85, res_size=size, in_feat_list=[], ex_feat_list=ex_feat_list, seed={}, wt_type=wt_type)

    # now create diff files for the pr output
    for tf_label in ["t", "f"]:
        pos_file = make_pr_file_name(year, tf_label, "p", wt_type, size)
        neg_file = make_pr_file_name(year, tf_label, "n",  wt_type, size)
        neutral_file = make_pr_file_name(year, tf_label, "x", wt_type, size)
        diff_file = make_pr_file_name(year, tf_label, "diff", wt_type, size)
        print "[run_pr.py] Creating diff file for pos %s, neg %s, netural %s: %s" % ( pos_file, neg_file, neutral_file, diff_file)
        polarity.pr_diff(dir_path, pos_file, neg_file, neutral_file, diff_file)
        


