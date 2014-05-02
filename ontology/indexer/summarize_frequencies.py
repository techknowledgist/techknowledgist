"""
Script to run the matcher on a corpus.

Usage:

    $ python run_matcher.py OPTIONS

Options:

    --corpus - the corpus to run the matcher on

    --batch - directory in data/o2_index to read from and write to

    --verbose - print progress


Example:

    $ python run_matcher.py \
      --corpus data/patents/201306-computer-science \
      --batch batch-01 \
      --verbose


WISHLIST:

- Remove dependency on directories inside the corpus. The filelist now has to be
  inside the config dir and the results have to be written to o2_matcher. Leave
  these as a default, but allow files/directories in other spots.

- Add runtime statistics like time elapsed and perhaps specifications of the
  machine it ran on.

"""


import os, sys, getopt, shutil, codecs, time, subprocess

sys.path.append(os.path.abspath('../..'))

from ontology.utils.file import open_input_file
from ontology.utils.git import get_git_commit


VERBOSE = False


def summarize(corpus, batch):
    # TODO: add existence check??
    batch_dir = os.path.join(corpus, 'data', 'o1_index', batch)
    infile = os.path.join(batch_dir, 'index.locs.10k.txt')
    outfile = os.path.join(batch_dir, 'index.locs.10k.summ.txt')
    infofile = os.path.join(batch_dir, 'index.info.summ.txt')
    fh_in = codecs.open(infile, encoding='utf-8')
    fh_out = codecs.open(outfile, 'w', encoding='utf-8')
    create_info_file(infofile, batch, infile, outfile)
    print 'IN: ', infile
    print 'OUT:', outfile
    frequencies = {}
    count = 0
    for line in fh_in:
        count += 1
        if count % 1000 == 0: print count
        (doc, term, freq, lines) = line.split("\t")
        frequencies[term] = frequencies.get(term, 0) + int(freq)
    for t in sorted(frequencies.keys()):
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
