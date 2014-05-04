"""

Usage:
    $ python get_terms.py OPTIONS

Options:
    --corpus  -  the corpus where the index is
    --batch   -  directory in data/o2_index that contains the database

Example:
    $ python get_terms.py \
      --corpus data/patents/201306-computer-science \
      --batch standard

"""

DEFAULT_CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k/subcorpora/2000'
DEFAULT_BATCH = 'standard'

import os, sys, getopt
from db import TermDB


def get(corpus, batch, terms):
    index_dir = os.path.join(corpus, 'data', 'o1_index', batch)
    tdb = os.path.join(index_dir, 'db.terms.sqlite')
    ldb = os.path.join(index_dir, 'db.locations.sqlite')
    db = TermDB(tdb, ldb)
    return db.get(terms)


def read_opts():
    try:
        return getopt.getopt(sys.argv[1:], '', ['corpus=', 'batch='])
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))


def test_terms(corpus, batch):
    examples = ['invention', 'computer', 'protective film',
                'laser device', 'friction backsheet']
    terms = get(corpus, batch, examples)
    for term in terms:
        print term
    

if __name__ == '__main__':

    corpus = DEFAULT_CORPUS
    batch = DEFAULT_BATCH
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--batch': batch = val

    test_terms(corpus, batch)
