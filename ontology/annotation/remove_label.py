"""

Script to take an anotation file and strip all judgements.

Each input line is of the form

     y|n|? TAB term

The output lie has the the first character removed.

"""

import sys, codecs

(infile, outfile) = (sys.argv[1], sys.argv[2])

outfh = codecs.open(outfile, 'w', encoding='utf-8')

for line in codecs.open(infile, encoding='utf-8'):
    fields = line.split("\t")
    if len(fields) == 2:
        term = fields[1]
        outfh.write("\t%s" % term)
