"""

Classify whether something is a technology. Placeholder for Peter's classification
code. Simply takes the list of items annotated globally as technologies and use this to
determine whether an NP in context is a technology.

The script need to be run from this directory.

"""

import glob, os, sys, codecs

from config import BASE_DIR
from utils import read_opts, read_frequencies

LANGUAGE = 'en'

def usage():
    print "Usage:"
    print "% python matcher.py [-l LANGUAGE]"


def classify(source_dir1, source_dir2, phr_occ3_file, index_file, language):

    #frequencies = shelve.open(index_file)
    frequencies = read_frequencies(os.path.dirname(index_file))
    technologies = load_annotation_examples(language)
    more_technologies = load_classifier_results(language, source_dir2)
    technologies.update(more_technologies)

    filtered_technologies = {}
    for t in technologies.keys():
        #print t, frequencies.get(t, {})
        # skip the ones that occur in one year only
        if len(frequencies.get(t, {}).keys()) > 1:
            filtered_technologies[t] = technologies[t]
            
    out = codecs.open(phr_occ3_file, 'w')

    technologies = filtered_technologies
    subdirs = glob.glob(os.path.join(source_dir1, "*"))
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


def load_classifier_results(language, source_dir2):
    classifications_file = os.path.join(source_dir2, 'utest.1.MaxEnt.out.scores.sum.nr')
    technologies = {}
    for line in codecs.open(classifications_file):
        (np, score, rest) = line.strip().split("\t", 2)
        if float(score) < 0.9:
            break
        #print np, score
        technologies[np] = score
    return technologies



if __name__ == '__main__':

    language = LANGUAGE
    (opts, args) = read_opts('l:', [], usage)
    for opt, val in opts:
        if opt == '-l': language = val

    index_file = os.path.join(BASE_DIR, language, 'idx', 'index')
    source_dir1 = os.path.join(BASE_DIR, language, 'phr_occ')
    source_dir2 = os.path.join(BASE_DIR, language, 'test')
    phr_occ3_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ3_classifier.tab')
    classify(source_dir1, source_dir2, phr_occ3_file, index_file, language)
