"""

Run the keyterm extraction code on a list of files.

Usage:

    $ python keyterms.py FILE
    $ python keyterms.py --verbose FILE

    FILE has a list of paths to the input files. In verbose mode, messages will
    be print to the terminal and temporary files in workspace/tmp will not be
    removed.

    Results are printed to results.txt in this directory.

Some runtime results on a set of identical files (th etotal set of 1000 is 40M,
about 32k for each xml file):

       1 file  -   4s
      10 files -   6s
     100 files -  11s
    1000 files -  60s

"""


import os, sys, codecs, subprocess, time

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser
from ontology.creation import txt2tag, tag2chunk
from ontology.classifier.run_iclassify import add_phr_feats_file
from ontology.classifier.run_iclassify import patent_invention_classify
from ontology.classifier.run_iclassify import merge_scores


def process(filelist):
    t1 = time.time()
    infiles = [ f.strip() for f in open(filelist).readlines()]
    chk_files = []
    tagger = txt2tag.get_tagger('en')
    if VERBOSE:
        print '[process] pre processing files'
    for infile in infiles:
        if VERBOSE:
            print '  ', infile
        basename = os.path.basename(infile)
        txt_file = os.path.join('workspace/tmp', basename + '.txt')
        tag_file = os.path.join('workspace/tmp', basename + '.tag')
        chk_file = os.path.join('workspace/tmp', basename + '.chk')
        chk_files.append(chk_file)
        run_xml2txt(infile, txt_file)
        run_txt2tag(txt_file, tag_file, tagger)
        run_tag2chk(tag_file, chk_file)
    run_classifier(chk_files)
    cleanup()
    if VERBOSE:
        print "Time elapsed: %f" % (time.time() - t1)
        
def run_xml2txt(infile, txt_file):
    fact_file = infile + '.fact'
    fh_in = codecs.open(infile)
    fh_out = codecs.open(txt_file, 'w')
    text = fh_in.read()
    for line in open(fact_file):
        tag, begin, end = line.split()
        if tag == 'title':
            begin = int(begin) + 274
            end = int(end) + 274
            title = text[begin:end]
        if tag == 'abstract':
            begin = int(begin) + 648
            end = int(end) + 648
            abstract = text[begin:end]
    fh_out.write("FH_TITLE:\n%s\n" % title.strip())
    fh_out.write("FH_ABSTRACT:\n%s\nEND\n" % abstract.strip())


def run_txt2tag(txt_file, tag_file, tagger):
    txt2tag.tag(txt_file, tag_file, tagger)


def run_tag2chk(tag_file, chk_file):
    tag2chunk.Doc(tag_file, chk_file, '9999', 'en',
                  filter_p=False, chunker_rules='en', compress=False)

def cleanup():
    """Remove all temporary files unless in verbose mode."""
    tmp_dir = "workspace/tmp"
    filelist = [f for f in os.listdir(tmp_dir) if not f == '.gitignore']
    if not VERBOSE:
        for f in filelist:
            os.remove(os.path.join(tmp_dir, f))


def run_classifier(chk_files):
    mallet_file = os.path.join('workspace', 'tmp', 'iclassify.mallet')
    with codecs.open(mallet_file, "w", encoding='utf-8') as s_mallet:
        for chk_file in chk_files:
            add_phr_feats_file(chk_file, s_mallet)
    patent_invention_classify(
        '../classifier/data/models/inventions-standard-20130713/',
        'workspace/tmp',
        verbose=VERBOSE)
    corpus = 'workspace/tmp'
    label_file='iclassify.MaxEnt.label'
    classification = 'workspace/tmp'
    command = "cat %s/%s | egrep -v '^name' | egrep '\|.*\|' | python %s > %s/%s" \
              % (classification, 'iclassify.MaxEnt.out', '../classifier/invention_top_scores.py',
                 classification, label_file)
    if VERBOSE:
        print '$', command
    subprocess.call(command, shell=True)
    # creates the .cat and .merged files
    merge_scores(corpus, classification, label_file, runtime=True, verbose=False)
    os.rename(os.path.join(classification, label_file + '.merged'), 'results.txt')



if __name__ == '__main__':

    VERBOSE = False
    filelist = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[1] == '--verbose':
        VERBOSE = True
        filelist = sys.argv[2]

    filelist = process(filelist)
