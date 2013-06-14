"""

Script to create annotation files. The input is assumed to be: (i) a corpus from
which to cull the ddata, (ii) a file list with filenames from the corpus, (iii)
a name of the annotation set created, and (iv) a marker that indicates what kind
of annotation files are created (now only --technologies, with a stump method
for --inventions).

There are two options that indicate the main mode of the script: one for
technologies and one for inventions:

   --technologies
   --inventions


TECHNOLOGIES

To create technology annotation files do something like:

  $ python step3_annotation.py \
      --technologies \
      --name test1 \
      --corpus data/patents/201305-en \
      --filelist files-testing.txt \
      --verbose

Options:

   --corpus CORPUS_DIRECTORY - the directory where the corpus lives

   --pipeline FILENAME - the kind of pipeline that is expected for the input
       data, defaults to default-pipeline.txt

   --filelist FILENAME - this is a file inside of CORPUS_DIRECTORY/config which creates
       a list of filenames in the corpus, the annotation file are taken from
       these files

   --name STRING - the name for the annotation set, this will be used as a
       directory name inside CORPUS_DIRECTORY/data/t0_annotation

   --verbose - switch on verbose mode


"""

import os, sys, shutil, getopt, codecs, random

import config
import putils

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from ontology.utils.batch import RuntimeConfig, find_input_dataset
from ontology.utils.batch import check_file_availability
from ontology.utils.file import filename_generator, ensure_path
from ontology.utils.file import compress, uncompress
from ontology.utils.git import get_git_commit
from pf2dfeats import generate_doc_feats


def annotate_technologies(name, rconfig, filelist):

    """Create input for manually annotation (that is, creation of a labeled list
    of terms). Given a runtime configuration for a corpus and a file list,
    creates three files: (1) list of unlabeled terms, ordered on frequency, (2)
    list of ordered terms with frequency information, and (3) an ordered list of
    terms with contexts. For contexts, a maximum of 10 is printed, selected
    randomly."""

    filelist_path = os.path.join(rconfig.config_dir, filelist)
    dataset1_occurrences = find_input_dataset(rconfig, 'd3_phr_occ')
    dataset2_features = find_input_dataset(rconfig, 'd3_phr_feats')

    if verbose:
        print "\nFILELIST:", filelist
        print "DATASET1:", dataset1_occurrences
        print "DATASET2:", dataset2_features, "\n"

    check_file_availability(dataset1_occurrences, filelist_path)
    check_file_availability(dataset2_features, filelist_path)

    dirname = set_dirname(rconfig, 'technologies', name)
    write_info(rconfig, dirname, filelist_path)
    term_contexts = collect_contexts(dataset1_occurrences, filelist_path)
    term_counts = collect_counts(dataset2_features, filelist_path)
    term_count_list = sorted(list(term_counts.items()))
    term_count_list.sort(lambda x, y: cmp(y[1],x[1]))
    print_annotation_files(dirname, term_count_list, term_contexts)


def set_dirname(rconfig, annotation_type, name):
    """Returns the directory where all annotation files will be written. Exit if
    the directory already exists, otherwise create it and return it. The two
    current annotation_types are 'technologies' and 'inventions'. The name is
    given by the user and is used as the name of a subdirectory."""
    dirname = os.path.join(rconfig.target_path,
                           'data', 't0_annotate', annotation_type, name)
    if os.path.exists(dirname):
        exit("WARNING: exiting, already created annotation files in %s" % dirname)
    ensure_path(dirname)
    return dirname

def write_info(rconfig, dirname, filelist_path):
    """Generate a file with general information and copy the file list to the
    annotation directory."""
    print "Writing general info..."
    fh = open(os.path.join(dirname, 'annotate.info.general.txt'), 'w')
    fh.write("$ python %s\n\n" % ' '.join(sys.argv))
    fh.write("file_list         =  %s\n" % filelist_path)
    fh.write("config_file       =  %s\n" % \
             os.path.basename(rconfig.pipeline_config_file))
    fh.write("git_commit        =  %s" % get_git_commit())
    print "Copying %s..." % (filelist_path)
    shutil.copyfile(filelist_path,
                    os.path.join(dirname, 'annotate.info.filelist.txt'))

def collect_contexts(dataset, filelist):
    """Collect all contexts from the dataset and return them as a dictionary
    indexed on terms. Each key is a list of [year, id, context] lists."""
    if verbose:
        print "\nGathering contexts..."
    contexts = {}
    fnames = filename_generator(dataset.path, filelist)
    for fname in fnames:
        uncompress(fname)
        if verbose:
            print '  ', fname
        with codecs.open(fname, encoding="utf-8") as fh:
            for line in fh:
                (id, year, term, context) = line.strip().split("\t")
                contexts.setdefault(term,[]).append([year, id, context])
        compress(fname)
    return contexts

    for term in sorted(term_contexts.keys()):
        print term


def collect_counts(dataset, filelist):
    """Return a dictionary with for each term the number of documents it
    appeared in. This assumes that the dataset is a d3_phr_feats dataset."""
    if verbose:
        print "\nGathering counts..."
    counts = {}
    fnames = filename_generator(dataset.path, filelist)
    for fname in fnames:
        if verbose:
            print '  ', fname
        uncompress(fname)
        # TODO: this is dangerous because it makes assumptions about the
        # directory structure, something similar is the case in step2 for at
        # least the docfeats generation
        year = os.path.basename(os.path.dirname(fname))
        doc_id = os.path.basename(fname)
        with codecs.open(fname, encoding="utf-8") as fh:
            docfeats = generate_doc_feats(fh, doc_id, year)
            for term in docfeats.keys():
                counts[term] = counts.get(term, 0) + 1
        compress(fname)
    return counts

    
def print_annotation_files(dirname, term_count_list, term_contexts):

    """Print the three annotation files in dirname, using the list of term
    counts and the dictionary of contexts."""
    
    file_unlab = os.path.join(dirname, 'annotate.terms.unlab.txt')
    file_counts = os.path.join(dirname, 'annotate.terms.counts.txt')
    file_context = os.path.join(dirname, 'annotate.terms.context.html')

    fh_unlab = codecs.open(file_unlab, 'w', encoding='utf-8')
    fh_counts = codecs.open(file_counts, 'w', encoding='utf-8')
    fh_context = codecs.open(file_context, 'w', encoding='utf-8')
    write_html_prefix(fh_context)

    term_no = 0
    cumulative = 0
    for term, count in term_count_list:
        term_no += 1
        cumulative += count
        fh_unlab.write("\t%s\n" % term)
        fh_counts.write("%d\t%d\t%d\t%s\n" % (term_no, count, cumulative, term))
        fh_context.write("\n<p>%s (%d documents)</p>\n" % (term, count))
        random.shuffle(term_contexts[term])
        for year, id, context in term_contexts[term][:10]:
            fh_context.write("<blockquote>%s</blockquote>\n" % context)


def write_html_prefix(fh_context):
    fh_context.write("<html>\n")
    fh_context.write("<head>\n")
    fh_context.write("<style>\n")
    fh_context.write("np { color: blue; }\n")
    fh_context.write("p { font-size: 20; }\n")
    fh_context.write("blockquote { font-size: 16; }\n")
    fh_context.write("</style>\n")
    fh_context.write("</head>\n")
    fh_context.write("<body>\n")



def annotate_inventions(name, rconfig, filelist):

    """This is an example method that show how pull information out of feature
    or occurrences files."""

    # Create the complete path to the file list; the rconfig is an instance of
    # RuntimeCOnfiguration and is created from the corpus and the pipeline
    # specification
    filelist_path = os.path.join(rconfig.config_dir, filelist)

    # Do this if you want to take data from d3_phr_occ. You can data from
    # d3_phr_occ, d3_phr_feats and d4_doc_feats.
    dataset = find_input_dataset(rconfig, 'd3_phr_occ')

    # Check whether files form the file list are available
    check_file_availability(dataset, filelist_path)

    # Create the directory where the files will be written to
    dirname = set_dirname(rconfig, 'technologies', name)

    # Next would typically be some way of writing down the information, the
    # following writes general information (command used, corpus directory, git
    # commit) and the list of files used.
    write_info(rconfig, dirname, filelist_path)

    # Now we can get the file names, loop over them, and extract the needed
    # information.
    fnames = filename_generator(dataset.path, filelist)
    for fname in fnames:
        with codecs.open(fname, encoding="utf-8") as fh:
            for line in fh:
                # extract data from the line, you probably want to put it in
                # some temporary data structure
                pass

    # Print file(s) to the dirname directory
    pass



if __name__ == '__main__':

    options = ['name=', 'corpus=', 'pipeline=', 'filelist=',
               'technologies', 'inventions', 'verbose']
    (opts, args) = getopt.getopt(sys.argv[1:], '', options)

    name = None
    target_path = config.WORKING_PATENT_PATH
    pipeline_config = config.DEFAULT_PIPELINE_CONFIGURATION_FILE
    filelist = 'files.txt'
    annotate_technologies_p = False
    annotate_inventions_p = False
    verbose = False
    
    for opt, val in opts:
        if opt == '--name': name = val
        if opt == '--corpus': target_path = val
        if opt == '--pipeline': pipeline_config = val
        if opt == '--filelist': filelist = val
        if opt == '--technologies': annotate_technologies_p = True
        if opt == '--inventions': annotate_inventions_p = True
        if opt == '--verbose': verbose = True
        
    if name is None:
        exit("ERROR: missing --name option")
        
    rconfig = RuntimeConfig(target_path, None, pipeline_config)
    if verbose:
        rconfig.pp()

    if annotate_technologies_p:
        annotate_technologies(name, rconfig, filelist)
    elif annotate_inventions_p:
        annotate_inventions(name, rconfig, filelist)
