"""

Script to create annotation files. The input is assumed to be: (i) a corpus from
which to cull the data, (ii) a file list with filenames from the corpus, (iii)
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


INVENTIONS:

The following command creates a directory with some info files and an annotation
file for inventions:

  $ python step3_annotation.py \
      --inventions \
      --corpus data/patents/201305-en \
      --filelist files-n2.txt \
      --name test2 \
      --chunks 30 \
      --verbose

Options are the same as for --technologies, except that there is an added option
--chunks, which defines the maximum number of chunks per document to put in the
annotation file. The default is 30. Only chunks from the FH_TITLE and
FH_ABSTRACT sections will be used (this is hard-coded).

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
from ontology.utils.file import filename_generator, ensure_path, FileData
from ontology.utils.file import open_input_file, compress, uncompress
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
    print "finding tags..."
    dataset_tags = find_input_dataset(rconfig, 'd2_tag')
    print "finding features..."
    dataset_features = find_input_dataset(rconfig, 'd3_phr_feats')

    if verbose:
        print "\nFILELIST:", filelist
        print "DATASET TAGS: ", dataset_tags
        print "DATASET FEATS:", dataset_features, "\n"

    check_file_availability(dataset_tags, filelist_path)
    check_file_availability(dataset_features, filelist_path)

    dirname = set_dirname(rconfig, 'technologies', name)
    write_info(rconfig, dirname, filelist_path)
    term_contexts = collect_contexts(dataset_tags, dataset_features, filelist_path)
    term_counts = collect_counts(dataset_features, filelist_path)
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
    with open(os.path.join(dirname, 'annotate.info.general.txt'), 'w') as fh:
        fh.write("$ python %s\n\n" % ' '.join(sys.argv))
        fh.write("file_list         =  %s\n" % filelist_path)
        fh.write("config_file       =  %s\n" % \
                     os.path.basename(rconfig.pipeline_config_file))
        fh.write("git_commit        =  %s" % get_git_commit())
    print "Copying %s..." % (filelist_path)
    shutil.copyfile(filelist_path,
                    os.path.join(dirname, 'annotate.info.filelist.txt'))

def collect_contexts(dataset_tags, dataset_feats, filelist):
    """Collect all contexts from the dataset and return them as a dictionary
    indexed on terms. Each value is a list of [year, id, context] triples."""
    tag_files = list(filename_generator(dataset_tags.path, filelist))
    feat_files = list(filename_generator(dataset_feats.path, filelist))
    contexts = {}
    for i in range(len(tag_files)):
        if verbose:
            print '[collect_contexts]', tag_files[i]
            print '[collect_contexts]', feat_files[i]
        fd = FileData(tag_files[i], feat_files[i])
        for term in fd.get_terms():
            term_obj = fd.get_term(term)
            for instance in term_obj.term_instances:
                year = instance.year
                identifier = instance.id
                context = "<file>%s</file><br/>\n%s <np>%s</np> %s" \
                    % (instance.id,
                       instance.context_left(),
                       instance.context_token(),
                       instance.context_right())
                contexts.setdefault(term,[]).append([year, identifier, context])
    return contexts


def collect_counts(dataset, filelist):
    """Return a dictionary with for each term the number of documents it
    appeared in. This assumes that the dataset is a d3_phr_feats dataset."""
    counts = {}
    fnames = filename_generator(dataset.path, filelist)
    for fname in fnames:
        if verbose:
            print '[collect_counts]', fname
        # TODO: this is dangerous because it makes assumptions about the
        # directory structure, something similar was the case in step2 for at
        # least the docfeats generation
        year = os.path.basename(os.path.dirname(fname))
        doc_id = os.path.basename(fname)
        with open_input_file(fname) as fh:
            docfeats = generate_doc_feats(fh, doc_id, year)
            for term in docfeats.keys():
                counts[term] = counts.get(term, 0) + 1
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
    #ensure_path(os.path.join(dirname, 'term.contexts'))
    for term, count in term_count_list:
        term_no += 1
        cumulative += count
        term_str = term.replace(' ', '_')
        google_query = '"' + '+'.join(term.split()) + '"'
        google_url = "https://www.google.com/#sclient=psy-ab&q=%s" % google_query
        google_link = "<a href='%s' target='_bank'>Google</a>" % google_url
        fh_unlab.write("\t%s\n" % term)
        fh_counts.write("%d\t%d\t%d\t%s\n" % (term_no, count, cumulative, term))
        fh_context.write("\n<p>%s (%d documents)</p>\n\n" % (term, count))
        fh_context.write("<blockquote>%s</blockquote>\n\n" % google_link)
        #file_term_context = os.path.join(dirname, 'term.contexts', "%04d.html" % term_no)
        #fh_term_context = codecs.open(file_term_context, 'w', encoding='utf-8')
        random.shuffle(term_contexts[term])
        for year, id, context in term_contexts[term][:10]:
            fh_context.write("<blockquote>\n%s\n</blockquote>\n\n" % context)


def write_html_prefix(fh_context):
    fh_context.write("<html>\n")
    fh_context.write("<head>\n")
    fh_context.write("<style>\n")
    fh_context.write("file { color: darkgreen; }\n")
    fh_context.write("np { color: blue; }\n")
    fh_context.write("p { font-size: 20; }\n")
    fh_context.write("blockquote { font-size: 16; }\n")
    fh_context.write("</style>\n")
    fh_context.write("</head>\n")
    fh_context.write("<body>\n")



def annotate_inventions(name, rconfig, filelist, chunks):
    """Create a directory with annotation files in t0_annotation/<name>."""

    filelist_path = os.path.join(rconfig.config_dir, filelist)
    dataset_tags = find_input_dataset(rconfig, 'd2_tag')
    dataset_feats = find_input_dataset(rconfig, 'd3_phr_feats')
    check_file_availability(dataset_tags, filelist_path)
    check_file_availability(dataset_feats, filelist_path)

    dirname = set_dirname(rconfig, 'inventions', name)
    write_info(rconfig, dirname, filelist_path)
    outfile = os.path.join(dirname, 'annotate.inventions.unlab.txt')
    output_fh = codecs.open(outfile, 'w', encoding='utf-8')
    tag_files = list(filename_generator(dataset_tags.path, filelist_path))
    feat_files = list(filename_generator(dataset_feats.path, filelist_path))

    # add the content of the general info file as a preface
    with open(os.path.join(dirname, 'annotate.info.general.txt')) as fh:
        for line in fh:
            output_fh.write("# %s" % line)
        output_fh.write("\n\n")

    for i in range(len(tag_files)):
        fd = FileData(tag_files[i], feat_files[i])
        _add_file_data_to_annotation_file(output_fh, fd)


def _add_file_data_to_annotation_file(output_fh, fd):
    # TODO: may want to make sure that sentences without terms are included for
    # reference, in that case, use the list of(section, tokens) pair in fg.tags
    # as well as fd.get_term_instances_dictionary()
    instances = []
    # TODO: also need to get the title
    for term in fd.get_terms():
        # all stuff lives in the Term object
        term_obj = fd.get_term(term)
        instances.extend(term_obj.term_instances)
    instances.sort()
    for i in range(chunks):
        inst = instances[i]
        section = inst.feats['section_loc']
        if section.startswith('TITLE') or section.startswith('ABSTRACT'):
            output_fh.write(
                "\t%s\t%s\t%s\t%s <np>%s</np> %s\n" % \
                    (inst.id, inst.year, inst.term,
                     inst.context_left(), inst.context_token(), inst.context_right()))
    output_fh.write("\n")


def annotate_something(name, rconfig, filelist, chunks):

    """This is a stub method that explains a bit more on how to create
    annotation files. Includes scaffolding that shows how to pull information
    out of phrase feature and tag files."""

    # Create the complete path to the file list; the rconfig is an instance of
    # RuntimeConfiguration and is created from the corpus and the pipeline
    # specification
    filelist_path = os.path.join(rconfig.config_dir, filelist)

    # Here is how you get the datasets
    dataset_tags = find_input_dataset(rconfig, 'd2_tag')
    dataset_feats = find_input_dataset(rconfig, 'd3_phr_feats')

    # Check whether files form the file list are available
    check_file_availability(dataset_tags, filelist_path)
    check_file_availability(dataset_feats, filelist_path)

    # Create the directory where the files will be written to
    dirname = set_dirname(rconfig, 'inventions', name)

    # Next would typically be some way of writing down the information, the
    # following writes general information (command used, corpus directory, git
    # commit) and the list of files used.
    write_info(rconfig, dirname, filelist_path)

    # Now we can get the file names, loop over them, and extract the needed
    # information. The code below is some scaffolding if all you need is in one
    # dataset.
    fnames = filename_generator(dataset_feats.path, filelist_path)
    for fname in fnames:
        with open_input_file(fname) as fh:
            # extract data from the line, you may want to put it in some
            # temporary data structure
            for line in fh:
                pass

    # And this is what you do if you need information that is distributed over
    # the feature and tag files.
    tag_files = list(filename_generator(dataset_tags.path, filelist_path))
    feat_files = list(filename_generator(dataset_feats.path, filelist_path))
    for i in range(len(tag_files)):
        # the FileData object
        fd = FileData(tag_files[i], feat_files[i])
        # all term-related stuff lives in the Term object and its term_instances
        # variable, you can print to the annotation file(s) from here or first
        # build som eintermediate data structure and then print the output later
        for term in fd.get_terms():
            term_obj = fd.get_term(term)



if __name__ == '__main__':

    options = ['name=', 'corpus=', 'pipeline=', 'filelist=',
               'technologies', 'inventions', 'chunks=', 'verbose']
    (opts, args) = getopt.getopt(sys.argv[1:], '', options)

    name = None
    target_path = config.WORKING_PATENT_PATH
    pipeline_config = config.DEFAULT_PIPELINE_CONFIGURATION_FILE
    filelist = 'files.txt'
    annotate_technologies_p = False
    annotate_inventions_p = False
    chunks = 30
    verbose = False
    
    for opt, val in opts:
        if opt == '--name': name = val
        if opt == '--corpus': target_path = val
        if opt == '--pipeline': pipeline_config = val
        if opt == '--filelist': filelist = val
        if opt == '--technologies': annotate_technologies_p = True
        if opt == '--inventions': annotate_inventions_p = True
        if opt == '--chunks': chunks = int(val)
        if opt == '--verbose': verbose = True
        
    if name is None:
        exit("ERROR: missing --name option")
        
    rconfig = RuntimeConfig(target_path, None, pipeline_config)
    if verbose:
        rconfig.pp()

    if annotate_technologies_p:
        annotate_technologies(name, rconfig, filelist)
    elif annotate_inventions_p:
        annotate_inventions(name, rconfig, filelist, chunks)
