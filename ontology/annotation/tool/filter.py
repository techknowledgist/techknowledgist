"""filter.py

Take a contexts file and a list of terms and create a new contexts file that has
only the terms in the list of terms.

Usage:

   python filter.py CONTEXTS_IN CONTEXTS_OUT TERM_LIST

Example:

   python filter.py annotate.terms.context.txt annotate.terms.filtered.context.txt good_terms.txt

"""


import sys, codecs
from utils import TermContexts

infile = sys.argv[1]
outfile = sys.argv[2]
termfile = sys.argv[3]

contexts = TermContexts(infile, termfile)
#contexts.pp()

out = codecs.open(outfile, 'w', encoding='utf-8')

out.write(contexts.info)
out.write("# ## filtering notes\n")
out.write("#\n")
out.write("# Created with filter.py from %s\n" % infile)
out.write("# Keeping only the terms in %s\n" % termfile)
out.write("#\n")
for t in contexts.terms:
    t.write_as_raw_data(out)
