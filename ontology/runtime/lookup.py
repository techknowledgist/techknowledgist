import os, sys, codecs, time, sqlite3

from utils.text import parse_fact_line, build_section_tree, DocNode


SECTIONS = ('TITLE', 'ABSTRACT', 'SUMMARY',
            'SECTITLE', 'TEXT', 'EMPHASIS',
            'TEXT_CHUNK', 'RELATED_APPLICATIONS', 'CLAIMS')

LOOKUP_SECTIONS = ('TITLE', 'SECTITLE', 'TEXT')


TERMS_DATABASE = None


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
        break
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
    yes, no = 0, 0
    for start, end, ftype in sections:
        if ftype in LOOKUP_SECTIONS:
            result = lookup(doc, ftype, start, end, fh_terms)
            if result:
                yes += 1
            else:
                no += 1
    print "yes: %d, no: %d" % (yes, no)
    t2 = time.time()
    if VERBOSE:
        print "lookup time: %f" % (t2 - t1)


def lookup(doc, ftype, start, end, fh_terms):
    global TERMS_DATABASE
    text = doc[start:end]
    tokens = text.split()
    fh_terms.write("%s %s %s\n" % (ftype, start, end))
    fh_terms.write("%s\n\n" % text)
    #if ftype == 'TITLE' or ftype == 'SECTITLE':
    #    print ftype, start, end, '-', text
    #else:
    #    print ftype, start, end
    for t in tokens:
        TERMS_DATABASE.exists(t)


def initialize_term_db(in_memory=True, verbose=True):

    global TERMS_DATABASE

    if TERMS_DATABASE is not None:
        return
    t1 = time.time()
    if in_memory:
        TERMS_DATABASE = HashTermDB('workspace/terms/source-split')
    else:
        TERMS_DATABASE = SqliteTermDB('workspace/terms/db')
    t2 = time.time()
    if verbose:
        print "loading time: %f" % (t2 - t1)



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

    """Interface to the lists with terms."""

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

    initialize_term_db(in_memory=True, verbose=VERBOSE)
    #initialize_term_db(in_memory=False, verbose=VERBOSE)
    #test_db()

    filelist = process(filelist)
