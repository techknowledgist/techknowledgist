"""

Provides some code to get information from the terms database. 

Usage:
    $ python get_terms.py OPTIONS

Options:
    --corpus  -  the corpus where the index is
    --batch   -  directory in data/o2_index that contains the database

Example:
    $ python get_terms.py \
      --corpus data/patents/201306-computer-science \
      --batch standard

This example doesn't show what will actually happen. This is a scipts that
changes often. When using it, you need to adapt the bits at the end and execute
a method. Three example methods are:

    test_terms()
    test_query()
    find_terms_for_us_maturity_evaluation()

See the docstring with these methods.

"""

DEFAULT_CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k/subcorpora/2000'
DEFAULT_CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000'
DEFAULT_BATCH = 'standard'

import os, sys, getopt
from db import TermDB


def get_db(corpus, batch):
    index_dir = os.path.join(corpus, 'data', 'o1_index', batch)
    tdb = os.path.join(index_dir, 'db.terms.sqlite')
    ldb = os.path.join(index_dir, 'db.locations.sqlite')
    return TermDB(tdb, ldb)
    
def get_terms(corpus, batch, terms):
    db = get_db(corpus, batch)
    return db.get(terms)

def query_terms(corpus, batch, query):
    db = get_db(corpus, batch)
    return db.query_terms(query)


def read_opts():
    try:
        return getopt.getopt(sys.argv[1:], '', ['corpus=', 'batch='])
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))


def test_terms(corpus, batch):
    """Retrieve some term objects and print them"""
    examples = ['invention', 'computer', 'protective film', 'laser device',
                'friction backsheet', 'friction blacksheet']
    terms = get_terms(corpus, batch, examples)
    for term in terms:
        print term

def test_query(corpus, batch):
    """Test a query on the terms database."""
    query = 'select count(*) from terms where frequency=200'
    print "\n", query
    result = query_terms(corpus, batch, query)
    print result[0][0]

def find_terms_for_us_maturity_evaluation(corpus, batch):
    """These are the queries used for finding a set of evaluation terms for the
    English maturity evaluation. For the end of phase 2B. This resulted in a
    total of 31 terms, that were than manually culled down by removing some
    obvious non-technology terms."""
    queries = [
        'select term from terms where frequency=200 and technology_score > 0.5',
        'select term from terms where frequency=201 and technology_score > 0.5' ]
    for q in queries:
        print "\n", q
        result = query_terms(corpus, batch, q)
        print "\n".join([row[0] for row in result])

def find_terms_for_cn_maturity_evaluation(corpus, batch, add_maturity_score=True):
    if add_maturity_score:
        find_terms_for_cn_maturity_evaluation1(corpus, batch)
    else:
        find_terms_for_cn_maturity_evaluation2(corpus, batch):
            
def find_terms_for_cn_maturity_evaluation1(corpus, batch):
    """Like the previous, but now for Chinese. This one resulted in 57
    terms. Note that you cannot use the default setting for the corpus."""
    queries = [
        'select term from terms where frequency=99 and technology_score > 0.5',
        'select term from terms where frequency=100 and technology_score > 0.5',
        'select term from terms where frequency=101 and technology_score > 0.5',
        'select term from terms where frequency=102 and technology_score > 0.5',
        'select term from terms where frequency=103 and technology_score > 0.5' ]
    for q in queries:
        print "\n", q
        result = query_terms(corpus, batch, q)
        print "\n".join([row[0] for row in result])
        
def find_terms_for_cn_maturity_evaluation2(corpus, batch):
    """Like the above, but also prints the maturity score."""
    queries = [
        'select term, maturity_score from terms where frequency=99 and technology_score > 0.5',
        'select term, maturity_score from terms where frequency=100 and technology_score > 0.5',
        'select term, maturity_score from terms where frequency=101 and technology_score > 0.5',
        'select term, maturity_score from terms where frequency=102 and technology_score > 0.5',
        'select term, maturity_score from terms where frequency=103 and technology_score > 0.5' ]
    for q in queries:
        print "\n", q
        result = query_terms(corpus, batch, q)
        print "\n".join(["%s\t%s" % (row[0], row[1]) for row in result])
        

if __name__ == '__main__':

    corpus = DEFAULT_CORPUS
    batch = DEFAULT_BATCH
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--batch': batch = val

    test_terms(corpus, batch)
    # test_query(corpus, batch)
    # find_terms_for_us_maturity_evaluation(corpus, batch)
    find_terms_for_cn_maturity_evaluation(corpus, batch)
