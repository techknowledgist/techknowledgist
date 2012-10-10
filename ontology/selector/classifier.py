"""

Classify whether something is a technology. Placeholder for Peter's classification
code. Simply takes the list of items annotated globally as technologies and use this to
determine whether an NP in context is a technology.

The script need to be run from this directory.

"""

import glob, os, sys, codecs

from config import BASE_DIR
from utils import read_opts

LANGUAGE = 'en'

def usage():
    print "Usage:"
    print "% python matcher.py [-l LANGUAGE]"


def classify(source_dir, phr_occ3_file, language):

    technologies = load_annotation_examples(language)
    out = codecs.open(phr_occ3_file, 'w')

    subdirs = glob.glob(os.path.join(source_dir, "*"))
    for subdir in subdirs:
        print subdir
        year = os.path.basename(subdir)
        files = glob.glob(os.path.join(subdir, "*.xml"))
        for fname in files:
            infile = codecs.open(fname)
            for line in infile:
                (match_id, year, term, sentence) = line.strip().split("\t")
                #technology = 'y' if technologies.has_key(term) else 'n'
                #out.write("%s %s\n" % (match_id, technology))
                if technologies.has_key(term):
                    #out.write("%s\t%s\n" % (match_id, term))
                    out.write("%s\n" % (match_id))


def load_annotation_examples(language):
    annotations_file = os.path.join('..', 'annotation', language, 'phr_occ.lab')
    technologies = {}
    for line in codecs.open(annotations_file):
        if line.startswith('y'):
            term = line.strip().split("\t")[1]
            technologies[term] = True
    return technologies



if __name__ == '__main__':

    language = LANGUAGE
    (opts, args) = read_opts('l:', [], usage)
    for opt, val in opts:
        if opt == '-l': language = val

    source_dir = os.path.join(BASE_DIR, language, 'phr_occ')
    phr_occ3_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ3_classifier.tab')
    classify(source_dir, phr_occ3_file, language)
