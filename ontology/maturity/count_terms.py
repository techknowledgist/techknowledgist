"""

Takes a couple of usage files and creates a file with terms that occur 25 times or more.

Usage:

    python count_terms.py data/usage-*.txt

    Output is written to terms-0025.txt.
    
"""


import sys, codecs


TERMS = {}


def collect_term_counts(fnames):
    
    for fname in fnames:
        print fname
        fh = codecs.open(fname, encoding='utf8')
        for line in fh:
            if line.startswith('#'):
                continue
            fields = line.split("\t")
            term = fields[-1].strip()
            freq = int(fields[2])
            TERMS[term] = TERMS.get(term, 0) + freq
        print 'terms:', len(TERMS)


def print_terms(frequency):
    fname = "terms-%04d.txt" % frequency
    fh = codecs.open(fname, 'w', encoding='utf8')
    for term in TERMS:
        freq = TERMS[term]
        if freq >= frequency:
            fh.write("%d\t%s\n" % (freq, term))
            

    
if __name__ == '__main__':

    fnames = sys.argv[1:]
    collect_term_counts(fnames)
    print_terms(25)

 
