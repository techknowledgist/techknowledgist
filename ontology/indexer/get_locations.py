"""

Find locations of the terms in a file.

Usage:
    $ python get_locations.py OPTIONS

Options:
    --corpus PATH  -  the corpus where the index is
    --batch DIR    -  directory in data/o2_index that contains the database
    --terms PATH   -  file with a list of terms
    --filter       -  filter locations not usefull for maturity evaluation
    
The filter is off by default and is used for when finding locations for the
maturity evaluation. If it is on, the following terms and locations will be
filtered out: (1) terms that occur in fewer than 20 documents are considered
too idiosyncratic, (2) terms with a maturity score of -1, which is an artifact
of the maturity scorer not having enough occurrences to work with. 

Results are written to tmp-locations.txt, which will be overwritten if it
already exists.

Example:
    $ python get_terms.py \
      --corpus data/patents/201306-computer-science \
      --batch standard \
      --terms ../annotation/en/maturity/terms-selected.txt \
      --filter

"""

# Note that filter test number (2) above is a bit puzzling since we start off
# with 200 occurrences, this needs to be investigated. As a first result, it
# turns out that if you remove the terms that occur in fewer than 4 documents
# then the terms with a maturity score of -1 also disappear. This seems to
# suggest that the code to find maturity scores throws out some cases where
# there are enough occurrences to work with.

# There used to be an extra test for terms, which is that the document with the
# most term occurrences is removed since this could be the document where the
# term is introduced. This was needed for one term with 17 document occurrences
# with the overwhelming majority of occurrences in one term. Test (1) applies to
# this so this extra test was removed, but would have to b eput back in if we
# reduce the threshold.


DOMAIN = 'us'
DOMAIN = 'cn'

FUSE_CORPORA = "/home/j/corpuswork/fuse/FUSEData/corpora"
DEFAULT_CORPUS = FUSE_CORPORA + "/ln-us-all-600k/subcorpora/2000"
DEFAULT_TERMS = "../annotation/en/maturity/terms-selected.txt"
DEFAULT_BATCH = 'standard'

if DOMAIN == 'cn':
    DEFAULT_CORPUS = FUSE_CORPORA + "/ln-cn-all-600k/subcorpora/2000"
    DEFAULT_TERMS = "../annotation/cn/maturity/terms-selected.txt"

MIN_DOCUMENTS = 20 if DOMAIN == 'us' else 10


import os, sys, getopt, codecs
from db import TermDB


def find_locations(corpus, batch, terms_file, filter=False):
    fh = codecs.open(terms_file, encoding='utf-8')
    fh_out = codecs.open("tmp-locations.txt", 'w', encoding='utf-8')
    terms = [l.strip() for l in fh.readlines()]
    terms = get_terms(corpus, batch, terms)
    if filter:
        terms = filter_terms(terms)
    for t in terms:
        fh_out.write(unicode(t) + u"\n")
        for location in t.locations:
            fh_out.write("\t%s\t%s\n" % (location.doc,
                                         ' '.join([str(l) for l in location.lines])))
    print "Done, output written to 'tmp-locations.txt'"

def filter_terms(terms):
    def keep_term(term):
        if term.documents < MIN_DOCUMENTS: return False
        return True
    return [term for term in terms if keep_term(term)]

def get_db(corpus, batch):
    index_dir = os.path.join(corpus, 'data', 'o1_index', batch)
    tdb = os.path.join(index_dir, 'db.terms.sqlite')
    ldb = os.path.join(index_dir, 'db.locations.sqlite')
    return TermDB(tdb, ldb)

def get_terms(corpus, batch, terms):
    db = get_db(corpus, batch)
    return db.get(terms)


def read_opts():
    longopts = ['corpus=', 'batch=', 'terms=', 'filter']
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))

        

if __name__ == '__main__':

    corpus = DEFAULT_CORPUS
    batch = DEFAULT_BATCH
    terms = DEFAULT_TERMS
    filter = False
    
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--batch': batch = val
        elif opt == '--terms': terms = val
        elif opt == '--filter': filter = True

    find_locations(corpus, batch, terms, filter)
