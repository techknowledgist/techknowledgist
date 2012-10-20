"""

Takes the index in BASE_DIR/language/idx/index and the NPS in context that were deemed
technologies in BASE_DIR/language/selector/phr_occ4.tab (which contains a list of patterns
that matched) and creates a file BASE_DIR/language/selector/phr_occ5.tab, which has
maturity scores added.

It currently works by simply counting occurrences because the results from the pattern
matcher are not good enough.

The output is a list that can be consumed by the runtime system.

TODO: the data seem to indicate that the three-way classification should really be a
binary switch (unavailable versus available). This would also be very helpful for
evaluation because it looks to be quite complicated to do this for the immature class.

"""

import glob, os, sys, codecs, shelve

from config import BASE_DIR
from utils import read_opts

LANGUAGE = 'en'


def usage():
    print "Usage:"
    print "% python maturity.py [-l LANGUAGE]"



def maturity(index_file, phr_occ4_file, phr_occ5_file, language):

    #INDEX = shelve.open(index_file)
    INDEX = read_frequencies(index_file)

    infile = codecs.open(phr_occ4_file)
    outfile = codecs.open(phr_occ5_file, 'w')

    DONE = {}
    
    for line in infile:
        (match_id, year, term, sentence, patterns) = line.strip().split("\t")
        if DONE.has_key(term):
            continue
        maturity = calculate_maturity(INDEX, patterns, term)
        outfile.write("%s\t%s\n" % \
                      (term, ' '.join(maturity)))
        DONE[term] = True

        
def read_frequencies(file):
    print file
    freqs = {}
    for fname in glob.glob('/shared/home/marc/batch/en/idx/*tab'):
        year = os.path.basename(fname).split('.')[0]
        print year, fname
        for line in codecs.open(fname):
            (np, freq) = line.strip().split("\t")
            freqs.setdefault(np,{})
            freqs[np][year] = int(freq)
    return freqs


def calculate_maturity(INDEX, patterns, term):
    frequencies = INDEX.get(term,{})
    if not frequencies:
        print "WARNING: no frequencies found for term '%s'" % term
    total_instances = sum(frequencies.values())
    immature = None
    mature = None
    for year in sorted(frequencies.keys()):
        if frequencies[year] > 2 and immature is None:
            immature = year
        if frequencies[year] >= 5 and mature is None:
            mature = year
    if immature is None:
        immature = str(9999)
    if mature is None:
        mature = str(9999)
    return (immature, mature)



if __name__ == '__main__':

    language = LANGUAGE
    (opts, args) = read_opts('l:', [], usage)
    for opt, val in opts:
        if opt == '-l': language = val

    index_file = os.path.join(BASE_DIR, language, 'idx', 'index')
    phr_occ4_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ4_selector.tab')
    phr_occ5_file = os.path.join(BASE_DIR, language, 'selector', 'phr_occ5_maturity.tab')
    
    maturity(index_file, phr_occ4_file, phr_occ5_file, language)
