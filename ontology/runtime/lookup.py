"""

Script to look up all known terms in a set of patents.


Usage:

    $ python lookup.py OPTIONS


OPTIONS:

--filelist FILE
   Contains a list of paths to the input files. This is the only required
   option.

--run-id
   The optional run-id option defines an identifier for the current run. The
   default is to use the current timestamp. The run-id determines where results
   file are written to. For example, with a run-id of 'run-018', result files
   are written to workspace/results/run-018.

--full-text
   Lookup either occurs on all text or on just the title, abstract, summary and
   claims. The latter is the default. Use this option to do a full text search.
   
-v
--verbose
   Print progress and other information to the terminal

--profile
   Run the profiler. Writes files with the 'profile-' prefix to the current
   working directory. Use utils/show_profile.py to viwe the results. Will not
   print statistics to the terminal, even in verbose mode.


Typical examples:

    $ python lookup.py --filelist workspace/data/list-010.txt
    $ python lookup.py --filelist workspace/data/list-010.txt --full-text
    $ python lookup.py -v --run-id lookup-024 --filelist workspace/data/list-010.txt


The code uses a set of in-memory Python hashes to store all known terms. These
terms are assumed to be in workspace/terms/source-split, but the expected files
are not part of the git repository and need to be downloaded separately. As of
December 9th 2013, the list of terms consists of 31,453,657 elements.


Wishlist:

1- The list of terms contains some 'terms' like 'said' and other verbs. These
   are in the term list due to tagging errors when creating the term
   ontology. But since they are high-frequency in general they make the results
   on an individual files look bad. Solve this by either tagging the patentsd
   (which would increase processing time a lot) or by using a filter to get rid
   of the main culprits.

2- The script slows down on some documents, taking over three seconds or more on
   them. These documents have noting in common and using the profiler shows that
   the slowdown appears to occurr in otherwise harmless, yet frequently used,
   methods. There is probably some memory issue causing the script to write to
   the disk. Getting rid of these outliers could shave off as much as 30% of the
   processing time (for full text search, performance is about 4 patents per
   second).

3- The script uses STRUCTURE tags from the fact file to feed a simple sentence
   splitter and chunker. We get some bad tokens hower due to things like
   'Figure<i>1</i>' since the current fact files do not have a representation
   for the <i> tag. Once these are added as EMPHASIS structure types, this
   script can be updated to take advantage of that information.

"""


import os, sys, codecs, time, sqlite3, random, getopt, cProfile
from operator import itemgetter

from utils.text import parse_fact_line, build_section_tree, build_section_list
from utils.text import SentenceSplitter, Chunker
from utils.tokenizer import Tokenizer
from utils.misc import read_filelist, default_id


SECTION_TYPES = ('TITLE', 'ABSTRACT', 'SUMMARY',
                 'SECTITLE', 'TEXT', 'EMPHASIS',
                 'TEXT_CHUNK', 'RELATED_APPLICATIONS', 'CLAIMS')

LOOKUP_SECTIONS = ('TITLE', 'SECTITLE', 'TEXT')

TERMS_DATABASE = None

SIZES = {}


def process(filelist, run_id, full_text):
    t1 = time.time()
    infiles = read_filelist(filelist)
    if VERBOSE: print '[process] looking up terms in files'
    all_c, all_sc = 0, 0
    results_dir = os.path.join('workspace', 'results', run_id)
    os.mkdir(results_dir)
    for text_file, fact_file in infiles:
        t2 = time.time()
        basename = os.path.splitext(os.path.basename(text_file))[0]
        term_file = "%s/%s.terms" % (results_dir, basename)
        if RUN_PROFILER:
            command = "process_file('%s', '%s', '%s', %s)" \
                      % (text_file, fact_file, term_file, full_text)
            cProfile.run(command, 'profile-' + basename)
        else:
            c, sc = process_file(text_file, fact_file, term_file, full_text)
            all_c += c
            all_sc += sc
            if VERBOSE:
                print "   %s  %.4fs  chunks/subchunks: %d/%s" \
                      % (text_file, time.time() - t2, c, sc)
    if VERBOSE:
        print "Total chunks/subchunks: %d/%d" % (all_c, all_sc)
        print "Total time elapsed: %f" % (time.time() - t1)
        #for size in sorted(SIZES.keys()): print size, SIZES[size]



def process_file(text_file, fact_file, terms_file, full_text):

    fh_text = codecs.open(text_file, encoding='utf-8')
    fh_fact = codecs.open(fact_file, encoding='utf-8')
    fh_terms = codecs.open(terms_file, 'w', encoding='utf-8')

    doc = fh_text.read()
    sections = build_section_list(fact_file, SECTION_TYPES)

    if full_text:
        terms, all_c, all_sc = lookup_terms_in_all_sections(doc, sections)
    else:
        terms, all_c, all_sc = lookup_terms_in_some_sections(doc, sections)
        
    counted_terms = count_terms(terms)
    for t,v in counted_terms.items():
        fh_terms.write("%s\t%s\n" % (v,t))

    return all_c, all_sc


def count_terms(file_terms):
    counted_terms = {}
    for term in file_terms:
        t = term[2]
        counted_terms[t] = counted_terms.get(t,0) + 1
    return counted_terms


def lookup_terms_in_all_sections(doc, sections):
    """Look up terms in all title and text sections."""
    file_terms = []
    all_c, all_sc = 0, 0
    for start, end, ftype in sections:
        if ftype in LOOKUP_SECTIONS:
            c, sc, section_terms = lookup_section(doc, ftype, start, end)
            file_terms.extend(section_terms)
            all_c += c
            all_sc += sc
    return file_terms, all_c, all_sc

def lookup_terms_in_some_sections(doc, sections):
    """Look up terms in the title, abstract, summary and claims."""
    tree = build_section_tree(sections)
    tree.index()
    terms = []
    all_c, all_sc = 0, 0
    for section in [('title', tree.title), ('abstract', tree.abstract),
                    ('summary', tree.summary), ('claims', tree.claims)]:
        name, s = section
        if s is None:
            if VERBOSE:
                print "      WARNING: missing %s in document" % name
            continue
        c, sc, section_terms = lookup_section(doc, s.label, s.start, s.end)
        terms.extend(section_terms)
        all_c += c
        all_sc += sc
    return terms, all_c, all_sc


def lookup_section(doc, ftype, start, end):

    global SIZES
    global TERMS_DATABASE

    section_terms = []
    text = doc[start:end]
    #print_section(ftype, start, end, text, print_text=False)

    chunks = chunk_text(text)
    all_c, all_subc = 0, 0
    for chunk in chunks:
        chunk_length = len(chunk)
        if chunk_length == -1:
            try: print chunk_length, ' '.join(chunk)
            except: pass
        if chunk_length <= 10:
            SIZES[chunk_length] = SIZES.get(chunk_length, 0) + 1
            c, subc, chunk_terms = lookup_chunk(chunk)
            section_terms.extend(chunk_terms)
            all_c += c
            all_subc += subc

    return all_c, all_subc, section_terms


def chunk_text(text, tokenize=False):
    splitter = SentenceSplitter()
    chunker = Chunker()
    if tokenize:
        # NOT YET FINISHED
        tokenized_text = Tokenizer(text).tokenize_text()
    else:
        text = text.lower()
        sentences = splitter.split(text)
        chunker.chunk(sentences, len(text))
        #chunker.pp_chunks()
        return chunker.get_chunks()


def lookup_chunk(chunk):
    verbose = True if len(chunk) == -1 else False
    if verbose: print '>>>', chunk
    subs = []
    for i in range(len(chunk)):
        for j in range(len(chunk) + 1):
            if i < j and j - i <= 10:
                sub = chunk[i:j]
                subs.append([i, j, ' '.join(sub), len(sub)])
    terms = lookup_terms(subs)
    if verbose:
        for sc in subs:
            print '  ', ' '.join(sc[2])
        print len(subs)
    return len(chunk), len(subs), terms


def lookup_terms(terms):
    verbose = False
    terms = [(i, j, term, len) for (i, j, term, len)
             in terms if TERMS_DATABASE.exists(term)]
    terms = list(reversed(sorted(terms, key=itemgetter(3,1))))
    filtered_terms = []
    seen = {}
    for t in terms:
        tseen = False
        for i in range(t[0], t[1]):
            if i in seen:
                tseen = True
                continue
        if not tseen:
            for i in range(t[0], t[1]):
                seen[i] = True
            filtered_terms.append(t)
    if verbose:
        for t in terms: print "%s %s %s %s\n" % (t[0], t[1], t[3], t[2])
        for t in filtered_terms: print "  %s %s %s %s\n" % (t[0], t[1], t[3], t[2])
    return filtered_terms


def print_section(ftype, start, end, text, print_text=False):
    if VERBOSE:
        if ftype == 'TITLE' or ftype == 'SECTITLE':
            print_text = True
        ptext = '- ' + text if print_text else ''
        print ftype, start, end, ptext



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
        return random.random() > 0.5


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
                #if lines > 100000: break
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

    options = ['filelist=', 'run-id=', 'verbose', 'profile', 'full-text']
    (opts, args) = getopt.getopt(sys.argv[1:], 'v', options)

    VERBOSE = False
    RUN_PROFILER = False
    filelist = None
    run_id = default_id()
    full_text = False
    
    for opt, val in opts:
        if opt == '-v': VERBOSE = True
        if opt == '--verbose': VERBOSE = True
        if opt == '--profile': RUN_PROFILER = True
        if opt == '--filelist': filelist = val
        if opt == '--run-id':  run_id = val
        if opt == '--full-text': full_text = True

    #initialize_term_db(empty=True, verbose=VERBOSE)
    initialize_term_db(in_memory=True, verbose=VERBOSE)
    #initialize_term_db(in_memory=False, verbose=VERBOSE)

    filelist = process(filelist, run_id, full_text)
