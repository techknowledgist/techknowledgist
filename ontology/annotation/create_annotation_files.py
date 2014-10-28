"""

Script to create annotation files. The input is assumed to be: (i) a corpus from
which to cull the data, (ii) a file list with filenames from the corpus, (iii) a
name of the annotation set created, and (iv) a marker that indicates what kind
of annotation files are created (now only --technologies and --inventions).

There are three options that indicate the main mode of the script: one for
technologies, one for inventions and one for terms (for maturity scores):

   --technologies
   --inventions
   --terms

   
TECHNOLOGIES

To create technology annotation files do something like:

  $ python create_annotation_files.py \
      --technologies \
      --ouput test-annotate-technologies \
      --corpus ../doc_processing/data/patents/corpora/sample-us \
      --filelist files.txt \
      --print-context \
      --verbose

The following does the same, but is more compact:

  $ python create_annotation_files.py --technologies -o test-annotate-technologies -c ../doc_processing/data/patents/corpora/sample-us --print-context -v

Four annotation files are created (in addition to a couple of info files):

    annotate.terms.context.html
    annotate.terms.context.txt
    annotate.terms.counts.txt
    annotate.terms.unlab.txt

The first two present the term in context in html or text format. The first is
not strictly an annotation file but a file that provides pretty printed context
for the annotator. The context text file can be used as input to a command line
annotation tool. For each term, it gives a maximum of 5 contexts, with a
preference for contexts earlier in a document. The counts file gives counts and
cumulative counts for the term list. Finally, the unlab file simply has the term
and a space for the label before it.

Options:

   --corpus CORPUS_DIRECTORY - the directory where the corpus lives

   --pipeline FILENAME - the kind of pipeline that is expected for the input
       data, defaults to default-pipeline.txt in the config directory

   --filelist FILENAME - this is a file inside of CORPUS_DIRECTORY/config which
       creates a list of filenames in the corpus, the annotation file are taken
       from these files

   --output DIRNAME - the name for the annotation set, this will be used as a
       directory name

   --verbose - switch on verbose mode

   --print-context - prints the two annotation context files, which are not
       printed by default

   --sort-terms - with this option, terms are printed in order of frequency, by
       default, they are randomly ordered

There are short options for --corpus (-c), --pipeline (-p), --filelist (-f),
--output (-o) and --verbose (-v).


INVENTIONS

Options include the first five options mentioned for --technologies plus the
added option --chunks, which defines the maximum number of chunks per document
to put in the annotation file. The default is 30. Only chunks from the FH_TITLE
and FH_ABSTRACT sections will be used (this is hard-coded).

The following command creates a directory with some info files and an annotation
file for inventions:

  $ python create_annotation_files.py \
      --inventions \
      --corpus ../doc_processing/data/patents/corpora/sample-us \
      --filelist files.txt \
      --output test-annotate-inventions \
      --chunks 30 \
      --verbose

This does the same, but uses short option names and the defaults for --filelist
and --chunks:

  $ python create_annotation_files.py --inventions -c ../doc_processing/data/patents/corpora/sample-us -o test-annotate-inventions -v


TERMS

This is a bit of an odd duck since it does not work of a list of files but off a
list of terms, each with some instances where the instances are given through
the document name and line number.

  $ python step3_annotation.py \
      --terms \
      --corpus ../doc_processing/data/patents/corpora/sample-us \
      --instances en/maturity/terms-locations.txt \
      --output test-annotate-terms \
      --verbose

Compact version:

  $ python step3_annotation.py --terms -c ../doc_processing/data/patents/corpora/sample-us --instances en/maturity/terms-locations.txt -o test-annotate-terms -v

"""

import os, sys, shutil, getopt, codecs, random, textwrap

sys.path.append(os.path.abspath('../..'))

from ontology.utils.batch import RuntimeConfig, find_input_dataset
from ontology.utils.batch import check_file_availability, generate_doc_feats
from ontology.utils.file import filename_generator, ensure_path, FileData
from ontology.utils.file import open_input_file, compress, uncompress
from ontology.utils.git import get_git_commit

sys.stdout = codecs.getwriter('utf8')(sys.stdout)


def annotate_technologies(dirname, rconfig, filelist, sort_terms_p, print_context_p):

    """Create input for manually annotation (that is, creation of a labeled list
    of terms). Given a runtime configuration for a corpus and a file list,
    creates three files: (1) list of unlabeled terms, ordered on frequency, (2)
    list of ordered terms with frequency information, and (3) an ordered list of
    terms with contexts. For contexts, a maximum of 10 is printed, selected
    randomly."""

    print "finding tags..."
    dataset_tags = find_input_dataset(rconfig, 'd2_tag')
    print "finding features..."
    dataset_features = find_input_dataset(rconfig, 'd3_phr_feats')

    if verbose:
        print "\nFILELIST:", filelist
        print "DATASET TAGS: ", dataset_tags
        print "DATASET FEATS:", dataset_features, "\n"

    check_file_availability(dataset_tags, filelist)
    check_file_availability(dataset_features, filelist)

    write_info(rconfig, dirname, filelist)
    term_contexts = {}
    if print_context_p:
        term_contexts = collect_contexts(dataset_tags, dataset_features,
                                         filelist)
    term_counts = collect_counts(dataset_features, filelist)
    term_count_list = sorted(list(term_counts.items()))
    term_count_list.sort(lambda x, y: cmp(y[1],x[1]))
    print_annotation_files(dirname, term_count_list, term_contexts,
                           sort_terms_p, print_context_p)

def write_info(rconfig, dirname, filelist):
    """Generate a file with general information and copy the file list to the
    annotation directory."""
    print "Writing general info..."
    ensure_path(dirname)
    with open(os.path.join(dirname, 'annotate.info.general.txt'), 'w') as fh:
        fh.write("$ python %s\n\n" % ' '.join(sys.argv))
        fh.write("corpus            =  %s\n" % os.path.abspath(rconfig.corpus))
        fh.write("file_list         =  %s\n" % os.path.abspath(filelist))
        fh.write("config_file       =  %s\n" % \
                     os.path.basename(rconfig.pipeline_config_file))
        fh.write("git_commit        =  %s" % get_git_commit())
    print "Copying %s..." % (filelist)
    shutil.copyfile(filelist,
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
                contexts.setdefault(term,[]).append(instance)
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

    
def print_annotation_files(dirname, term_count_list, term_contexts,
                           sort_terms_p, print_context_p):

    """Print the three annotation files in dirname, using the list of term
    counts and the dictionary of contexts."""

    file_unlab = os.path.join(dirname, 'annotate.terms.unlab.txt')
    file_counts = os.path.join(dirname, 'annotate.terms.counts.txt')
    file_context_txt = os.path.join(dirname, 'annotate.terms.context.txt')
    file_context_html = os.path.join(dirname, 'annotate.terms.context.html')
    fh_unlab = codecs.open(file_unlab, 'w', encoding='utf-8')
    fh_counts = codecs.open(file_counts, 'w', encoding='utf-8')
    if print_context_p:
        fh_context_txt = codecs.open(file_context_txt, 'w', encoding='utf-8')
        fh_context_html = codecs.open(file_context_html, 'w', encoding='utf-8')
        _initialize_context_files(fh_context_txt, fh_context_html, dirname)

    # suffle the terms if they are not supposed to be sorted
    if not sort_terms_p:
        random.shuffle(term_count_list)

    term_no = 0
    cumulative = 0
    for term, count in term_count_list:
        term_no += 1
        cumulative += count
        term_str = term.replace(' ', '_')
        google_query = '"' + '+'.join(term.split()) + '"'
        google_url = "https://www.google.com/#sclient=psy-ab&q=%s" % google_query
        google_link = "<a href='%s' target='_bank'>Google</a>" % google_url
        fh_unlab.write("\t%s\n" % term)
        fh_counts.write("%d\t%d\t%d\t%s\n" % (term_no, count, cumulative, term))
        if print_context_p:
            fh_context_txt.write("%s\n" % term)
            fh_context_html.write("\n<p>%s (%d documents)</p>\n\n" % (term, count))
            fh_context_html.write("<blockquote>%s</blockquote>\n\n" % google_link)
            random.shuffle(term_contexts[term])
            # order the contexts on position in the document
            contexts = sorted(term_contexts[term])
            for instance in contexts[:10]:
                instance.print_as_tabbed_line(fh_context_txt)
                fh_context_html.write("<blockquote>\n")
                instance.print_as_html(fh_context_html)
                fh_context_html.write("</blockquote>\n\n")


def _initialize_context_files(fh_context_txt, fh_context_html, dirname):
    for info_file in ('annotate.info.general.txt', 'annotate.info.filelist.txt'):
        path = os.path.join(dirname, info_file)
        lines = open(path).readlines()
        fh_context_txt.write("# ## %s\n#\n" % info_file)
        for l in lines:
            fh_context_txt.write("# %s\n" % l.rstrip())
        fh_context_txt.write("#\n")
    _write_html_prefix(fh_context_html)
    return fh_context_txt, fh_context_html

def _write_html_prefix(fh_context):
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



def annotate_inventions(dirname, rconfig, filelist, chunks):
    """Create a directory with annotation files in t0_annotation/<name>."""

    dataset_tags = find_input_dataset(rconfig, 'd2_tag')
    dataset_feats = find_input_dataset(rconfig, 'd3_phr_feats')
    check_file_availability(dataset_tags, filelist)
    check_file_availability(dataset_feats, filelist)

    write_info(rconfig, dirname, filelist)
    outfile = os.path.join(dirname, 'annotate.inventions.unlab.txt')
    output_fh = codecs.open(outfile, 'w', encoding='utf-8')
    tag_files = list(filename_generator(dataset_tags.path, filelist))
    feat_files = list(filename_generator(dataset_feats.path, filelist))

    # add the content of the general info file as a preface
    with open(os.path.join(dirname, 'annotate.info.general.txt')) as fh:
        for line in fh:
            output_fh.write("# %s\n" % line.rstrip())
        output_fh.write("#\n")

    for i in range(len(tag_files)):
        fd = FileData(tag_files[i], feat_files[i])
        _add_file_data_to_annotation_file(output_fh, fd)


def _add_file_data_to_annotation_file(output_fh, fd):
    # TODO: may want to make sure that sentences without terms are included for
    # reference, in that case, use the list of (section, tokens) pairs in
    # fg.tags as well as fd.get_term_instances_dictionary()
    output_fh.write("# %s\n" % fd.get_title())
    output_fh.write("#\n")
    for abstract_line in textwrap.wrap(fd.get_abstract(), 76):
        output_fh.write("#   %s\n" % abstract_line)
    output_fh.write("#\n")
    instances = []
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
    output_fh.write("#\n")


def annotate_something(dirname, rconfig, filelist, chunks):

    """This is a stub method that explains a bit more on how to create
    annotation files. Includes scaffolding that shows how to pull information
    out of phrase feature and tag files. This is for cases when you use a list
    of files."""

    # Here is how you get the datasets
    dataset_tags = find_input_dataset(rconfig, 'd2_tag')
    dataset_feats = find_input_dataset(rconfig, 'd3_phr_feats')

    # Check whether files from the file list are available
    check_file_availability(dataset_tags, filelist)
    check_file_availability(dataset_feats, filelist)

    # Next would typically be some way of writing down the information, the
    # following writes general information (command used, corpus directory as
    # well as git commit) and the list of files used. This also creates the
    # output directory.
    write_info(rconfig, dirname, filelist)

    # Now we can get the file names, loop over them, and extract the needed
    # information. The code below is some scaffolding if all you need is in one
    # dataset.
    fnames = filename_generator(dataset_feats.path, filelist)
    for fname in fnames:
        with open_input_file(fname) as fh:
            # extract data from the line, you may want to put it in some
            # temporary data structure
            for line in fh:
                pass

    # And this is what you do if you need information that is distributed over
    # the feature and tag files.
    tag_files = list(filename_generator(dataset_tags.path, filelist))
    feat_files = list(filename_generator(dataset_feats.path, filelist))
    for i in range(len(tag_files)):
        # the FileData object
        fd = FileData(tag_files[i], feat_files[i])
        # all term-related stuff lives in the Term object and its term_instances
        # variable, you can print to the annotation file(s) from here or first
        # build some intermediate data structure and then print the output later
        for term in fd.get_terms():
            term_obj = fd.get_term(term)


def annotate_terms(dirname, rconfig, instances_file):

    """Create an annotation file for term instances."""

    # Get the datasets
    dataset_tags = find_input_dataset(rconfig, 'd2_tag')
    dataset_feats = find_input_dataset(rconfig, 'd3_phr_feats')
    print dataset_feats.path
    print dataset_tags.path

    # Create the directory where the files will be written to; write info; and
    # open the output file, intializing it with info
    write_info(rconfig, dirname, instances_file)
    outfile = os.path.join(dirname, 'annotate.terms.context.txt')
    out = codecs.open(outfile, 'w', encoding='utf8')
    # add the content of the general info file as a preface
    with open(os.path.join(dirname, 'annotate.info.general.txt')) as fh:
        for line in fh:
            out.write("# %s\n" % line.rstrip())
        out.write("#\n")
                           
    # time to get the terms
    terms = _read_terms(instances_file)
    _reduce_terms(terms)
    #_print_terms(terms)

    for term, locations in terms.items():
        count = 0
        for doc, lines in locations:
            #sys.stdout.write("%s %s %s" % (term, doc, lines))
            print term, doc, lines
            phr_file =  os.path.join(dataset_feats.path, 'files', doc) + '.xml'
            tag_file =  os.path.join(dataset_tags.path, 'files', doc) + '.xml'
            fd = FileData(tag_file, phr_file)
            term_obj = fd.get_term(term)
            # this helps just getting the first instance in a line
            done = {}
            for inst in term_obj.term_instances:
                if inst.doc_loc in lines and inst.doc_loc not in done:
                    done[inst.doc_loc] = True
                    count += 1
                    out.write("%s - %d\n" % (term, count))
                    inst.print_as_tabbed_line(out)


def _read_terms(instances_file):
    terms = {}
    current_term = None
    fh = codecs.open(instances_file, encoding='utf8')
    for line in fh:
        if line.startswith('<Term'):
            current_term = line.split(' freq=')[0][7:-1]
            if verbose:
                print "[_read_terms] Adding '%s'" % current_term
            terms[current_term] = []
        else:
            fields = line.split("\t")
            if len(fields) == 3:
                doc = fields[1]
                lines = [int(l) for l in fields[2].split()]
            terms[current_term].append((doc, lines))
    return terms

def _reduce_terms(terms):
    MAX_TERMS = 30
    for term in terms.keys():
        locations = []
        for doc, lines in terms[term]:
            for line in lines:
                locations.append((doc, line))
        random.shuffle(locations)
        locations = locations[:MAX_TERMS]
        grouped_locations = {}
        for doc, line in locations:
            grouped_locations.setdefault(doc,[]).append(line)
        terms[term] = []
        for doc, lines in grouped_locations.items():
            terms[term].append((doc, lines))

def _print_terms(terms):
    for term in terms.keys():
        print term
        for doc, lines in terms[term]:
            print '  ', doc, lines




if __name__ == '__main__':

    options = ['technologies', 'inventions', 'terms',
               'output=', 'corpus=', 'pipeline=', 'filelist=', 'sort-terms',
               'print-context', 'chunks=', 'instances=', 'verbose']
    (opts, args) = getopt.getopt(sys.argv[1:], 'o:c:f:p:v', options)

    output = None
    corpus = None
    pipeline_config = 'pipeline-default.txt'
    filelist = 'files.txt'
    annotate_technologies_p = False
    annotate_inventions_p = False
    annotate_terms_p = False
    sort_terms_p = False
    print_context_p = False
    chunks = 30
    instances = "../annotation/en/maturity/terms-locations.txt"
    #instances = "../annotation/cn/maturity/terms-locations.txt"
    verbose = False
    
    for opt, val in opts:
        
        if opt == '--technologies': annotate_technologies_p = True
        if opt == '--inventions': annotate_inventions_p = True
        if opt == '--terms': annotate_terms_p = True

        if opt in ('--output', '-o'): output = val
        if opt in ('--corpus', '-c'): corpus = val
        if opt in ('--filelist', '-f'): filelist = val
        if opt in ('--pipeline', '-p'): pipeline_config = val
        if opt in ('--verbose', '-v'): verbose = True

        if opt == '--sort-terms': sort_terms_p = True
        if opt == '--print-context': print_context_p = True
        if opt == '--chunks': chunks = int(val)
        if opt == '--instances': instances = val

    if corpus is None:
        exit("ERROR: no corpus specified with --corpus option")
    if not os.path.exists(corpus):
        exit("ERROR: corpus '%s' does not exist" % corpus)
    if not os.path.exists(filelist):
        saved_filelist = filelist
        filelist = os.path.join(corpus, 'config', filelist)
        if not os.path.exists(filelist):
            exit("ERROR: the file list '%s' does not exist" % saved_filelist)
    if output is None:
        exit("ERROR: no output directory specified with the --output option")
    if os.path.exists(output):
        exit("ERROR: already created annotation files in %s" % output)

    rconfig = RuntimeConfig(corpus, None, None, None, pipeline_config)
    if verbose:
        rconfig.pp()

    if annotate_technologies_p:
        annotate_technologies(output, rconfig, filelist,
                              sort_terms_p, print_context_p)
    elif annotate_inventions_p:
        annotate_inventions(output, rconfig, filelist, chunks)

    elif annotate_terms_p:
        annotate_terms(output, rconfig, instances)
