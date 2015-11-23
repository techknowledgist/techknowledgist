# tf_sent.py
# map terms and features to the sentences they appear in


from ontology.utils import file
import config

def tf2sent_files(corpus, year, fature_list, section_list):
    
    # tv_subpath
    tv_subpath = "/data/tv"

    # output files will go here
    tv_root = corpus_root + "/" + corpus + tv_subpath

    # to get the set of features relevant to act or pn classification ///

