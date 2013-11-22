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
prefix 'iclassify':

    iclassify.info - some minimal info about the completed run
    iclassify.mallet - input file for the mallet classifier
    iclassify.MaxEnt.out - output file of the cassifier
    iclassify.MaxEnt.stderr - messages from the classifier

    iclassify.MaxEnt.label - condensed verison of classifier output
    iclassify.MaxEnt.label.cat - minimal keyterm information
    iclassify.MaxEnt.label.merged - keyterms per document
    iclassify.MaxEnt.label.merged.tab - tabbed version of the previous
    iclassify.MaxEnt.label.relations.tab - relations between terms

Most usable for the inventions may be iclassify.MaxEnt.label.merged.tab, which
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
processed. The fourth column has the type of the term: i for invention, t for
invention type, ct for contextual term, and ca for component/attribute.

More human-readable results are in iclassify.MaxEnt.label.merged, which has
a paragraph for each file and also includes the title of the patent:

    [9999 US6674661B1.txt]
    title: Dense metal programmable ROM with the terminals of a programmed ...
    invention type:
    invention descriptors: dense metal programmable rom, metal programmable rom
    contextual terms: terminals, memory transistor, depth, wordlines, width, ...
    components/attributes: memory cell array, memory cells, ground conection, ...

Note that the files contain several abbreviations for term types, not just the
four mentioned above (i, t, ct, ca):

    o - other terms
    r - (not sure what this is)
    c - same as ca
    m - same as ct

The file iclassify.MaxEnt.label.relations.tab contains relations between
terms. There are now three types of relations that are extracted:

    i-ca   relation between invention and a component/attribute
    i-ct   relation between an invention and a contextual term
    ca-ca  two terms that are both components/attributes of the same invention

The file itself has three columns, the relation type, the first term and the
second term. Here are the relations for patent US6672019B1:

    i-ca    multi-storey parking garage     ceiling beams
    i-ca    multi-storey parking garage     floor plates
    i-ca    multi-storey parking garage     passable surface
    i-ca    multi-storey parking garage     skeleton support structure
    i-ct    multi-storey parking garage     body
    i-ct    multi-storey parking garage     ceiling beam
    i-ct    multi-storey parking garage     elastic plastic material
    i-ct    multi-storey parking garage     end
    i-ct    multi-storey parking garage     gap
    i-ct    multi-storey parking garage     horizontal ceiling beams
    i-ct    multi-storey parking garage     interposition
    i-ct    multi-storey parking garage     longitudinal direction
    i-ct    multi-storey parking garage     supports
    ca-ca   ceiling beams   floor plates
    ca-ca   ceiling beams   passable surface
    ca-ca   ceiling beams   skeleton support structure
    ca-ca   floor plates    passable surface
    ca-ca   floor plates    skeleton support structure
    ca-ca   passable surface        skeleton support structure

Runtime performance on the set of 200 sample files provided by BAE:

    16 seconds

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
from ontology.classifier.run_iclassify import process_label_file
from ontology.utils.git import get_git_commit


# the model used by this invention classifier
MODEL = '../classifier/data/models/inventions-standard-20130713/'


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
        #run_xml2txt(infile, txt_file)
        #run_txt2tag(txt_file, tag_file, tagger)
        #run_tag2chk(tag_file, chk_file)
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
    patent_invention_classify(MODEL, 'workspace/tmp', verbose=VERBOSE)
    corpus = 'workspace/tmp'
    label_file='iclassify.MaxEnt.label'
    classification = 'workspace/tmp'
    create_info_file(classification)
    command = "cat %s/%s | egrep -v '^name' | egrep '\|.*\|' | python %s > %s/%s" \
              % (classification, 'iclassify.MaxEnt.out', '../classifier/invention_top_scores.py',
                 classification, label_file)
    if VERBOSE: print '$', command
    subprocess.call(command, shell=True)
    process_label_file(corpus, classification, label_file, VERBOSE)
    # move the results from the temporary workspace directory
    command = "mv %s/iclassify* ." % classification
    subprocess.call(command, shell=True)

def create_info_file(classification):
    with open(os.path.join(classification, 'iclassify.info'), 'w') as fh:
        fh.write("$ python %s\n\n" % ' '.join(sys.argv))
        fh.write("classification        =  %s\n" % classification)
        fh.write("git_commit            =  %s\n" % get_git_commit())



if __name__ == '__main__':

    VERBOSE = False
    filelist = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[1] == '--verbose':
        VERBOSE = True
        filelist = sys.argv[2]
    filelist = process(filelist)
