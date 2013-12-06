"""Run the keyterm extraction code on a list of files.


Usage:

   $ python keyterms.py OPTIONS

OPTIONS:

--filelist FILE
   Contains a list of paths to the input files. This is the only required
   option.

--run-id STRING
   The optional run-id option defines an identifier for the current run. The
   default is to use the current timestamp. The run-id determines where
   temporary and results file are written to. For example, with a run-id of
   'run-018', temporary files are written to workspace/tmp/run-018 and result
   files are written to workspace/results/run-018.

--verbose
   In verbose mode, messages will be printed to the terminal and temporary files
   in workspace/tmp will not be removed. 

--mallet-dir PATH
--stanford-tagger-dir PATH
   These can be used to overrule the default directories for the mallet
   classifier and the stanford tagger. There are actually two ways of doing
   this. One is to edit the config.py file in this directory. The other is to
   use these options. If both are used, the command line options overrule the
   values in config.py. See config.py for more information.

--condense-results
   When this flag is on, not all result files will be present in the results
   directory. Only the two tab files (iclassify.MaxEnt.label.merged.tab and
   iclassify.MaxEnt.label.relations.tab) and the info file will be written.


Typical examples:

   $ python keyterms.py --filelist workspace/data/list-010.txt


Needed input files are text files and the BAE fact files. Each line in FILE is
in one of two formats. In the first format a line has a path to the text file,
followed by a tab, followed by the path to the fact file. In the second format,
one file is listed without the extension. In that case, the script assumes that
text and fact files are in the same directory and adds the extensions to the
path, for example, a path data/US6682507B2 would be expanded to include both
data/US6682507B2.txt and data/US6682507B2.fact. There is an example file in
workspace/data/list-010.txt with examples of both formats (which may both be
used in the same file).

The script relies on two kinds of facts in the fact file, both from the generic
structural parsing by BAE:

    STRUCTURE TYPE="TITLE" START=3302 END=3329
    STRUCTURE TYPE="ABSTRACT" START=10475 END=11178

Results are printed to a set of files in the results directory (see the
explanation of --run-id above for where exactly in the results directory), they
all have the prefix 'iclassify':

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


import os, sys, codecs, subprocess, time, getopt

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
from ontology.runtime.utils.text import parse_fact_line


# the model used by this invention classifier
MODEL = '../classifier/data/models/inventions-standard-20130713/'


def process(filelist, run_id, mallet_path, stanford_path, condense_results):
    update_directories(mallet_path, stanford_path)
    os.mkdir('workspace/tmp/' + run_id)
    os.mkdir('workspace/results/' + run_id)
    t1 = time.time()
    infiles = read_filelist(filelist)
    chk_files = []
    tagger = txt2tag.get_tagger('en')
    if VERBOSE: print '[process] pre-processing files'
    for text_file, fact_file in infiles:
        if VERBOSE: print '  ', text_file
        basename = os.path.splitext(os.path.basename(text_file))[0]
        txt_file = os.path.join("workspace/tmp/%s/%s.txt" % (run_id, basename))
        tag_file = os.path.join("workspace/tmp/%s/%s.tag" % (run_id, basename))
        chk_file = os.path.join("workspace/tmp/%s/%s.chk" % (run_id, basename))
        chk_files.append(chk_file)
        run_xml2txt(text_file, fact_file, txt_file)
        run_txt2tag(txt_file, tag_file, tagger)
        run_tag2chk(tag_file, chk_file)
    run_classifier(chk_files, run_id, condense_results)
    cleanup(run_id)
    if VERBOSE: print "Time elapsed: %f" % (time.time() - t1)

def default_id():
    return time.strftime('%Y%m%d-%H%M%S')

def update_directories(mallet_path, stanford_path):
    """Updates the MALLET_DIR and STANFORD_TAGGER_DIR paths in the module
    ontology.creation.config and ontology.classifier.config with the values in
    the local module ontology.runtime.config or the values handed in by command
    line options."""
    # TODO: this a bit of a hack and I would like to have a better way to deal
    # with all the directory settings.
    import config
    import ontology.creation.config
    import ontology.classifier.config
    # check the local config
    for var in ('MALLET_DIR', 'STANFORD_TAGGER_DIR'):
        path = config.__dict__.get(var)
        if path is not None:
            if os.path.isdir(path):
                ontology.creation.config.__dict__[var] = path
                ontology.classifier.config.__dict__[var] = path
            else:
                exit("Invalid %s directory: %s" % (var, path))
    # check the values from the command line options
    if mallet_path is not None:
        if os.path.isdir(mallet_path):
            ontology.creation.config.__dict__['MALLET_DIR'] = mallet_path
            ontology.classifier.config.__dict__['MALLET_DIR'] = mallet_path
        else:
            exit("Invalid mallet directory: " + mallet_path)
    if stanford_path is not None:
        if os.path.isdir(stanford_path):
            ontology.creation.config.__dict__['STANFORD_TAGGER_DIR'] = stanford_path
            ontology.classifier.config.__dict__['STANFORD_TAGGER_DIR'] = stanford_path
        else:
            exit("Invalid stanford directory: " + stanford_path)
    if VERBOSE:
        print 'MALLET_DIR =', ontology.classifier.config.MALLET_DIR
        print 'STANFORD_TAGGER_DIR =', ontology.creation.config.STANFORD_TAGGER_DIR

def read_filelist(filelist):
    infiles = []
    for line in open(filelist):
        files = line.strip().split("\t")
        if len(files) == 1:
            infiles.append([files[0]+'.txt', files[0]+'.fact'])
        elif len(files) == 2:
            infiles.append([files[0], files[1]])
        else:
            print "WARNING: unexpected line in filelist"
            print "        ", line
    return infiles


def run_xml2txt(text_file, fact_file, outfile):
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

def run_txt2tag(txt_file, tag_file, tagger):
    txt2tag.tag(txt_file, tag_file, tagger)

def run_tag2chk(tag_file, chk_file):
    tag2chunk.Doc(tag_file, chk_file, '9999', 'en',
                  filter_p=False, chunker_rules='en', compress=False)

def cleanup(run_id):
    """Remove all temporary files unless in verbose mode."""
    tmp_dir = "workspace/tmp/" + run_id
    if not VERBOSE:
        for f in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f))

def run_classifier(chk_files, run_id, condense_results):
    results_dir = os.path.join('workspace', 'results', run_id)
    mallet_file = os.path.join(results_dir, 'iclassify.mallet')
    with codecs.open(mallet_file, "w", encoding='utf-8') as s_mallet:
        for chk_file in chk_files:
            add_phr_feats_file(chk_file, s_mallet)
    patent_invention_classify(MODEL, results_dir, verbose=VERBOSE)
    label_file='iclassify.MaxEnt.label'
    create_info_file(results_dir)
    command = "cat %s/%s | egrep -v '^name' | egrep '\|.*\|' | python %s > %s/%s" \
              % (results_dir, 'iclassify.MaxEnt.out', '../classifier/invention_top_scores.py',
                 results_dir, label_file)
    if VERBOSE: print '$', command
    subprocess.call(command, shell=True)
    process_label_file(results_dir, results_dir, label_file, VERBOSE)
    if condense_results:
        for fname in ['iclassify.MaxEnt.label', 'iclassify.MaxEnt.label.cat',
                      'iclassify.MaxEnt.label.merged', 'iclassify.MaxEnt.out',
                      'iclassify.MaxEnt.stderr', 'iclassify.mallet' ]:
            os.remove(os.path.join(results_dir, fname))

def create_info_file(classification):
    with open(os.path.join(classification, 'iclassify.info'), 'w') as fh:
        fh.write("$ python %s\n\n" % ' '.join(sys.argv))
        fh.write("classification        =  %s\n" % classification)
        fh.write("git_commit            =  %s\n" % get_git_commit())



if __name__ == '__main__':

    options = ['runid=', 'mallet-dir=', 'stanford-tagger-dir=',
               'filelist=', 'verbose', 'condense-results']
    (opts, args) = getopt.getopt(sys.argv[1:], '', options)

    VERBOSE = False
    filelist = None
    run_id = default_id()
    mallet_path = None
    stanford_path = None
    condense_results = False

    for opt, val in opts:
        if opt == '--verbose': VERBOSE = True
        if opt == '--filelist': filelist = val
        if opt == '--run-id':  run_id = val
        if opt == '--mallet-dir': mallet_path = val
        if opt == '--stanford-tagger-dir': stanford_path = val
        if opt == '--condense-results': condense_results = True

    process(filelist, run_id, mallet_path, stanford_path, condense_results)
