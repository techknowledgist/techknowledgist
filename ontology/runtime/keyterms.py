"""

Run the keyterm extraction code on a list of files.

Usage:

    $ python keyterms.py FILE
    $ python keyterms.py --verbose FILE

    FILE has a list of paths to the input files. In verbose mode, messages will
    be printed to the terminal and temporary files in workspace/tmp will not be
    removed.

Needed input files are text files and the BAE fact files. The script adds the
extensions to the path, for example, a path data/US6682507B2 would be expanded
to include both data/US6682507B2.txt and data/US6682507B2.fact. There is an
example file in workspace/data/list-010.txt. The script relies on two kinds of
facts in the fact file, both from the generic structural parsing by BAE:

    STRUCTURE TYPE="TITLE" START=3302 END=3329
    STRUCTURE TYPE="ABSTRACT" START=10475 END=11178
    
Results are printed to a set of files in this directory, they all have the
prefix 'iclassify'. Most usable may be iclassify.MaxEnt.label.merged.tab, which
has five columns:

    9999    6674661 US6674661B1.txt i       dense metal programmable rom
    9999    6674661 US6674661B1.txt i       metal programmable rom
    9999    6674661 US6674661B1.txt ct      terminals
    9999    6674661 US6674661B1.txt ct      memory transistor
    9999    6674661 US6674661B1.txt ct      depth
    9999    6674661 US6674661B1.txt ct      wordlines
    9999    6674661 US6674661B1.txt ct      width
    9999    6674661 US6674661B1.txt ct      bitlines
    9999    6674661 US6674661B1.txt ct      group
    9999    6674661 US6674661B1.txt ct      bitline
    9999    6674661 US6674661B1.txt ct      memory cell
    9999    6674661 US6674661B1.txt ct      end
    9999    6674661 US6674661B1.txt ca      memory cell array
    9999    6674661 US6674661B1.txt ca      memory cells
    9999    6674661 US6674661B1.txt ca      ground conection
    9999    6674661 US6674661B1.txt ca      memory cell group
    9999    6674661 US6674661B1.txt ca      memory cell transistor

The first column is the year of the patent, which is actually taken from the
directory structure and which defaults to 9999 if that structure is not
available. The year is followed by the patent id and the basename of the file
processed. The fourth column has the type of the term: i (invention), t
(invention type), ct (contextual term), ca (component/attribute).

More human-readable results are in iclassify.MaxEnt.label.merged, which has
a paragraph for each file and also includes the title of the patent:
    
   [9999 US6674661B1.txt]
   title: Dense metal programmable ROM with the terminals of a programmed ...
   invention type: 
   invention descriptors: dense metal programmable rom, metal programmable rom
   contextual terms: terminals, memory transistor, depth, wordlines, width, ...
   components/attributes: memory cell array, memory cells, ground conection, ...

Runtime result on the set of 200 sample files provided by BAE: 16 seconds.

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
from ontology.classifier.run_iclassify import generate_tab_format


def process(filelist):
    t1 = time.time()
    infiles = [ f.strip() for f in open(filelist).readlines()]#[:10]
    chk_files = []
    tagger = txt2tag.get_tagger('en')
    if VERBOSE:
        print '[process] pre-processing files'
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
        
def run_xml2txt(infile, outfile):
    text_file = infile + '.txt'
    fact_file = infile + '.fact'
    fh_in = codecs.open(text_file, encoding='utf-8')
    fh_out = codecs.open(outfile, 'w', encoding='utf-8')
    text = fh_in.read()
    title, abstract = None, None
    for line in open(fact_file):
        fields = line.split()
        if fields[0] == 'STRUCTURE':
            fclass, ftype, start, end = parse_fact_line(fields)
            if ftype == 'TITLE':
                if title is None:
                    title = text[start:end]
                else:
                    print "WARNING: more than one title"
            if ftype == 'ABSTRACT':
                if abstract is None:
                    abstract = text[start:end]
                else:
                    print "WARNING: more than one abstract"
    if title is None: title = ''
    if abstract is None: abstract = ''
    fh_out.write("FH_TITLE:\n%s\n" % title.strip())
    fh_out.write("FH_ABSTRACT:\n%s\nEND\n" % abstract.strip())

def parse_fact_line(fields):
    fact_class = fields.pop(0)
    fact_type, start, end = None, None, None
    for keyval in fields:
        try:
            key, val = keyval.split('=')
            val = val.strip('"')
            if key == 'TYPE': fact_type = val
            if key == 'START': start = int(val)
            if key == 'END': end = int(val)
        except ValueError:
            # this happens when more complicated fact lines have spaces in the
            # values, for example for title strings
            pass
    return (fact_class, fact_type, start, end)
        
def run_xml2txt_OLD(infile, txt_file):
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
    generate_tab_format(classification, VERBOSE)
    command = "mv %s/iclassify* ." % classification
    if VERBOSE:
        print '$', command
    subprocess.call(command, shell=True)
    #os.rename(os.path.join(classification, label_file + '.merged'), 'results.txt')



if __name__ == '__main__':

    VERBOSE = False
    filelist = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[1] == '--verbose':
        VERBOSE = True
        filelist = sys.argv[2]
    filelist = process(filelist)
