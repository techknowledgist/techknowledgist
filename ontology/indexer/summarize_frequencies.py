"""

Script to take the output of frequency collection and generate corpus-wide
frequencies.

Usage:
    $ python summarize_frequencies.py OPTIONS

Options:
    --corpus   -  the corpus to run the matcher on
    --batch    -  directory in data/o2_index to read from and write to
    --verbose  -  print progress

The script takes the file index.locs.txt in the batch directory and creates
index.locs.summ.txt. It also creates a file index.info.summ.txt with some
information on the run.

Example:
    $ python summarize_frequencies.py \
      --corpus data/patents/201306-computer-science \
      --batch standard \
      --verbose

"""


import os, sys, getopt, shutil, codecs, time, subprocess

sys.path.append(os.path.abspath('../..'))

from ontology.utils.file import open_input_file
from ontology.utils.git import get_git_commit


VERBOSE = False


def summarize(corpus, batch):
    # TODO: add existence check??
    batch_dir = os.path.join(corpus, 'data', 'o1_index', batch)
    infile = os.path.join(batch_dir, 'index.locs.txt')
    outfile = os.path.join(batch_dir, 'index.locs.summ.az.txt')
    infofile = os.path.join(batch_dir, 'index.info.summ.txt')
    fh_in = codecs.open(infile, encoding='utf-8')
    fh_out = codecs.open(outfile, 'w', encoding='utf-8')
    create_info_file(infofile, batch, infile, outfile)
    frequencies = {}
    count = 0
    print "\nReading", infile
    for line in fh_in:
        count += 1
        if count % 100000 == 0 and VERBOSE: print '  ', count
        (doc, term, freq, lines) = line.split("\t")
        frequencies[term] = frequencies.get(term, 0) + int(freq)
    count = 0
    # TODO: maybe get rid of the sorting
    print "\nWriting", outfile
    for t in sorted(frequencies.keys()):
        # TODO: this is much slower than the reading (and that is not counting
        # the sorting), why?
        count += 1
        if count % 100000 == 0 and VERBOSE: print '  ', count
        fh_out.write("%s\t%s\n" % (frequencies[t], t))

def create_info_file(filename, batch, infile, outfile):
    with open(filename, 'w') as fh:
        fh.write("$ python %s\n\n" % ' '.join(sys.argv))
        fh.write("batch         =  %s\n" % batch)
        fh.write("source file   =  %s\n" % infile)
        fh.write("summary file  =  %s\n" % outfile)
        fh.write("git_commit    =  %s\n" % get_git_commit())


def read_opts():
    longopts = ['corpus=', 'batch=', 'verbose' ]
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))



if __name__ == '__main__':

    corpus = None
    batch = None

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--batch': batch = val
        elif opt == '--verbose': VERBOSE = True

    summarize(corpus, batch)
