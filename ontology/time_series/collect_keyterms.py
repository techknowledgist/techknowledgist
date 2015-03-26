"""

Collect keyterms from classification files and write them out as time series.

Usage:

    $ python collect_keyterms.py

To control parameters for the script, edit the values of YEARS, CORPUS,
KEYTERMS_CLASS and KEYTERMS_SERIES.

"""


import os, sys, codecs, StringIO
from utils import filter_term_en, filter_term
sys.path.append(os.path.abspath('../..'))
from ontology.utils.file import open_input_file


YEARS = range(1995, 2013 + 1)
#YEARS = range(1995, 1996 + 1)

YEAR_STRINGS = ["%s" % y for y in YEARS]

CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-all-600k'
KEYTERMS_CLASS =  os.path.join(CORPUS, 'classifications', 'keyterms-20150215')
KEYTERMS_SERIES = os.path.join(CORPUS, 'time-series-v4', 'keyterms')
#KEYTERMS_SERIES = '.'


def read_roles(year):
    roles = {}
    fname = os.path.join(KEYTERMS_CLASS, year, 'iclassify.MaxEnt.label.merged.tab')
    print fname
    c = 0
    for line in open_input_file(fname):
        c += 1
        if c % 100000 == 0: print c
        #if c > 1000: break
        (id, basename, role, term) = line.rstrip("\n\r\f").split("\t")
        roles[term][role] = roles.setdefault(term,{}).get(role, 0) + 1
    return roles

def print_roles(roles, year):
    print "Writing roles to", KEYTERMS_SERIES
    # use StringIO because writing to nsf-share line-by-line is sooooo slow
    s_ct = StringIO.StringIO()
    s_ca = StringIO.StringIO()
    s_i = StringIO.StringIO()
    for term in roles:
        # note that we do not include the type here
        ct = roles[term].get('ct', 0)
        ca = roles[term].get('ca', 0)
        i = roles[term].get('i', 0)
        all = sum([i, ca, ct])
        s_ct.write("%s\t%d\t%.2f\n" % (term, ct, float(ct)/(all+0.00000001)))
        s_ca.write("%s\t%d\t%.2f\n" % (term, ca, float(ca)/(all+0.00000001)))
        s_i.write("%s\t%d\t%.2f\n" % (term, i, float(i)/(all+0.00000001)))
    print_from_stream(s_ct, 'ct', year)
    print_from_stream(s_ca, 'ca', year)
    print_from_stream(s_i, 'i', year)

def print_from_stream(stream, role, year):
    outfile = os.path.join(KEYTERMS_SERIES, "roles-%s-%s.txt" % (role, year))
    fh = codecs.open(outfile, 'w', encoding='utf8')
    fh.write(stream.getvalue())


if __name__ == '__main__':

    for year in YEAR_STRINGS:
        roles = read_roles(year)
        print_roles(roles, year)

