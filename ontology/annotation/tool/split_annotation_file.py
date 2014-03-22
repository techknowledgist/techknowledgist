"""split_annotation_file.py

Usage:

    $ python split_annotation_file.py SPLIT_SIZE INFILE

"""


import sys, codecs
from utils import TermContexts

def write_batch(contexts, infile, batch, size):
    outfile = "%s.%d" % (infile, batch)
    print outfile
    out = codecs.open(outfile, 'w', encoding='utf-8')
    out.write(contexts.info)
    out.write("# ## splitting notes\n")
    out.write("#\n")
    out.write("# Created with split_annotation_file.py from %s\n" % infile)
    out.write("# Batch = %d\n" % (batch))
    out.write("# Maximum batch size = %d\n" % (size))
    out.write("#\n")
    end = batch * size
    begin = end - size
    for t in contexts.terms[begin:end]:
        t.write_as_raw_data(out)


if __name__ == '__main__':
    
    size = int(sys.argv[1])
    infile = sys.argv[2]
    contexts = TermContexts(infile)
    terms = len(contexts.terms)
    batch = 0
    while terms > 0:
        batch += 1
        write_batch(contexts, infile, batch, size)
        terms = terms - size


