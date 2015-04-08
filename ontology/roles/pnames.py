# pnames.py
# functions to construct path names

import os
import roles_config

def tv_filepath(corpus_root, corpus, year, file_type, subset, cat_type=""):
    # check for illegal parameter values
    # note: for file_type, we allow values of the form "cat.<cutoff>"
    if file_type not in ["diff", "tf", "cs", "cat", "cat_prob", "fc", "fc_kl", "fc_prob", "fc_uc", "tc", "tcs", "tfc", "feats", "terms", "ds", "filt.gold", "feats.1000", "unlab", "train", "tstart"] and not file_type[0:5] == "cat.w":
        print "[tv_filepath]WARNING: unknown file type: %s" % file_type
        
    if subset not in ["", "a", "t", "c"]:
        # note: subset can be empty string
        print "[tv_filepath]ERROR: unknown subset: %s" % subset
        quit
    if cat_type not in ["", "pn", "act"]:
        print "[tv_filepath]ERROR: unknown cat_type: %s" % cat_type
        quit
    tv_subpath = "/data/tv/"
    # make sure we don't create double slashes in the name
    if corpus_root[-1] != "/":
        corpus_root += "/"
    if cat_type != "":
        cat_type = "." + cat_type
    if subset != "":
        subset = "." + subset
    full_filename = corpus_root + corpus + tv_subpath + str(year) + subset + cat_type + "." + file_type
    print "[tv_filepath]file: %s" % full_filename
    return(full_filename)

# sections is ta or tas, depending on the sections included (title, abstract, summary)
def tf_dir(corpus_root, corpus, sections="tas"):
    tf_subpath = "/data/term_features/"
    if sections == "ta":
        tf_subpath = "/data/term_features_ta/"
    # make sure we don't create double slashes in the name
    if corpus_root[-1] != "/":
        corpus_root += "/"
    full_filename = corpus_root + corpus + tv_subpath
    print "[tf_filepath]file: %s" % full_filename
    return(full_filename)

def tv_dir(corpus_root, corpus):
    tv_subpath = "/data/tv/"
    # make sure we don't create double slashes in the name
    if corpus_root[-1] != "/":
        corpus_root += "/"

    full_filename = corpus_root + corpus + tv_subpath 
    print "[tv_filepath]file: %s" % full_filename
    return(full_filename)

# creates full tv filepath, including year prefix and qualifier
def tv_dir_year_file(corpus_root, corpus, year, qualifier):
    year = str(year)
    path = tv_dir(corpus_root, corpus)
    full_filename = path + year + "." + qualifier
    return(full_filename)

# full name of file containing the list of files for a given patent corpus and application year
# e.g. /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-A21-computers/subcorpora/1997/config/files.txt
def fuse_filelist(fuse_corpus_root, corpus, year):
    year = str(year)
    full_filename = os.path.join(fuse_corpus_root, corpus, "subcorpora", year, "config", "files.txt")
    return(full_filename)

# e.g., /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-A21-computers/subcorpora/1997/data/d3_phr_feats/01/files/1998    
def fuse_phr_feats_file(fuse_corpus_root, corpus, pipeline_step, year, filename):
    year = str(year)
    full_filename = os.path.join(fuse_corpus_root, corpus, "subcorpora", year, "data", pipeline_step, "01", "files", filename)
    return(full_filename)

