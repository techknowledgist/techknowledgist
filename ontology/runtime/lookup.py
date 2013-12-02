"""

$ python lookup.py --verbose workspace/data/list-010.txt
$ python lookup.py workspace/data/list-010.txt


"""


import os, sys, codecs, time, sqlite3

from utils.text import parse_fact_line, build_section_tree, DocNode
from utils.tokenizer import Tokenizer


SECTIONS = ('TITLE', 'ABSTRACT', 'SUMMARY',
            'SECTITLE', 'TEXT', 'EMPHASIS',
            'TEXT_CHUNK', 'RELATED_APPLICATIONS', 'CLAIMS')

LOOKUP_SECTIONS = ('TITLE', 'SECTITLE', 'TEXT')

TERMS_DATABASE = None



# tokens that start a chunk
STARTS_CHUNK = [ 'the', 'a', 'an' ]

# tokens that are never in a chunk
NOT_IN_CHUNK = [
    '.', ',', '?', '!', '"', "'", '', '(', ')', '[', ']', '#', '%',
    'in', 'of', 'over', 'under', 'on', '', '',
    'and', 'or', 'but', 'therefore', 'hence', 'although',
    ]

STARTS_CHUNK = dict.fromkeys(STARTS_CHUNK, True)
NOT_IN_CHUNK = dict.fromkeys(NOT_IN_CHUNK, True)


def process(filelist):
    t1 = time.time()
    infiles = [ f.strip() for f in open(filelist).readlines()]
    if VERBOSE: print '[process] looking up terms in files'
    for infile in infiles:
        if VERBOSE: print '  ', infile
        basename = os.path.basename(infile)
        text_file = infile + '.txt'
        fact_file = infile + '.fact'
        term_file = infile + '.terms'
        process_file(text_file, fact_file, term_file)
        #break
    if VERBOSE: print "Time elapsed: %f" % (time.time() - t1)


def process_file(text_file, fact_file, terms_file):

    fh_text = codecs.open(text_file, encoding='utf-8')
    fh_fact = codecs.open(fact_file, encoding='utf-8')
    fh_terms = codecs.open(terms_file, 'w', encoding='utf-8')

    doc = fh_text.read()
    sections = []
    for line in open(fact_file):
        fields = line.split()
        if fields[0] == 'STRUCTURE':
            fclass, ftype, start, end = parse_fact_line(fields)
            #print ftype
            if ftype in SECTIONS:
                sections.append((start, end, ftype))
    sections.sort()
    tree = build_section_tree(sections)
    #tree.pp()

    t1 = time.time()
    count = 0
    for start, end, ftype in sections:
        if ftype in LOOKUP_SECTIONS:
            count += 1
            #if count > 2: break
            result = lookup(doc, ftype, start, end, fh_terms)
    if VERBOSE:
        print "lookup time: %f" % (time.time() - t1)


def lookup(doc, ftype, start, end, fh_terms):
    global TERMS_DATABASE
    text = doc[start:end]
    #print_section(ftype, start, end, text, print_text=False)
    chunked_text = chunk_text(text)
    tokens = text.split()
    fh_terms.write("%s %s %s\n" % (ftype, start, end))
    fh_terms.write("%s\n\n" % text)
    for t in tokens:
        TERMS_DATABASE.exists(t)

def print_section(ftype, start, end, text, print_text=False):
    if VERBOSE:
        if ftype == 'TITLE' or ftype == 'SECTITLE':
            print_text = True
        ptext = '- ' + text if print_text else ''
        print ftype, start, end, ptext

def chunk_text(text):
    """Simple version of chunker, just tokenization and perhaps a few little
    tricks like putting chunk boundaries at punctuation or at some words that
    are known to not occur in chunks (hopefully some function words, which
    actually makes sense for the current version of the chunker, which does not
    include any determiners, prepositions or conjunctions)."""
    for t in text.split():
        if t[-1] in ['.',',', '?', '!']: t = t[:-1]
        STARTS_CHUNK.get(t)
        NOT_IN_CHUNK.get(t)
    return
    tokenizer = Tokenizer(text)
    sentences = tokenizer.tokenize_text().as_string().strip().split("\n")
    #print "\n".join(sentences)
    for sentence in sentences:
        chunked_sentence = chunk_sentence(sentence)

def chunk_sentence(sentence):
    pass


def initialize_term_db(in_memory=True, verbose=True, empty=False):
    """Initializes TERMS_DATABASE by putting in some object that understands the
    exists() method."""
    global TERMS_DATABASE
    if TERMS_DATABASE is not None:
        return
    t1 = time.time()
    if empty:
        TERMS_DATABASE = EmptyDB()
    elif in_memory:
        TERMS_DATABASE = HashTermDB('workspace/terms/source-split')
    else:
        TERMS_DATABASE = SqliteTermDB('workspace/terms/db')
    t2 = time.time()
    if verbose:
        print "loading time: %f" % (t2 - t1)



class EmptyDB(object):
    """Place holder database."""
    def exists(self, term):
        return False


class SqliteTermDB(object):

    """Interface to the sqlite databases with terms."""

    def __init__(self, db_path):
        self.path = db_path
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.alphabet_idx = {}
        for c in self.alphabet:
            self.alphabet_idx[c] = True
        self.terms = {}
        for c in self.alphabet + '0':
            self.terms[c] = {}
            self.terms[c]['connection'] = sqlite3.connect("%s/terms_%s.db" % (self.path, c))
            self.terms[c]['cursor'] = self.terms[c]['connection'].cursor()

    def exists(self, term):
        term = term.lower()
        if not term:
            cursor = self.terms['0']['cursor']
        else:
            first = term[0]
            if self.alphabet_idx.has_key(first):
                cursor = self.terms[first]['cursor']
            else:
                cursor = self.terms['0']['cursor']
        cursor.execute('SELECT * FROM terms WHERE term=?', (term,))
        result = cursor.fetchone()
        return True if result is not None else False


class HashTermDB(object):

    """Interface to the lists with terms. Loads all terms into memory"""

    def __init__(self, db_path):
        self.path = db_path
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.alphabet_idx = {}
        for c in self.alphabet:
            self.alphabet_idx[c] = True
        self.terms = {}
        for c in '0' + self.alphabet:
            self.terms[c] = {}
            print "loading", c
            lines = 0
            for line in codecs.open("%s/terms_%s.txt" % (self.path, c), encoding='utf-8'):
                lines += 1
                if lines % 100000 == 0: print '  ', lines
                if lines > 100000: break
                self.terms[c][line.strip()] = True
            #print self.terms[c]

    def exists(self, term):
        term = term.lower()
        if not term:
            hash = self.terms['0']
        else:
            first = term[0]
            if self.alphabet_idx.has_key(first):
                hash = self.terms[first]
            else:
                hash = self.terms['0']
        return hash.get(term, False)


def test_db():
    global TERMS_DATABASE
    for t in ('', 'ox5f', 'ad g5', 'ad g5xx',
              'slip type tag', 'server state cycle' 'strap configuration'):
        print t, TERMS_DATABASE.exists(t)




if __name__ == '__main__':

    VERBOSE = False
    filelist = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[1] == '--verbose':
        VERBOSE = True
        filelist = sys.argv[2]

    initialize_term_db(empty=True, verbose=VERBOSE)
    #initialize_term_db(in_memory=True, verbose=VERBOSE)
    #initialize_term_db(in_memory=False, verbose=VERBOSE)
    #test_db()

    filelist = process(filelist)
