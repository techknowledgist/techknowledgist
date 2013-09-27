"""

Script that manages the part of the processing chain that deals with individual documents,
that is document parsing, segmentation, tagging, chunking and creation of phrase-level and
document-level feature vectors.

USAGE:
  % python step2_document_processing.py OPTIONS

OPTIONS:
  --populate   import external files
  --xml2txt    document structure parsing
  --txt2tag    tagging (English and German)
  --txt2seg    segmenting (Chinese only)
  --seg2tag    tagging segemented text (Chinese only)
  --tag2chk    creating chunks in context and adding features

  --corpus TARGET_PATH  corpus directory, default is data/patents
  --l en|cn|de          provides the language, default is 'en'
  --n INTEGER           number of documents to process, default is 1

  --verbose:
       print name of each processed file to stdout

  --show-data:
       print all datasets, then exits, requires the -t option
       if --verbose is used, will also print the pipelines for each dataset

  --show-pipeline
       print all pipelines, then exits, requires the -t option, also assumes
       that all pipeline files match 'pipeline-*.txt'

  --pipeline FILE:
      optional pipeline configuration file to overrule the default pipeline; this is just
      the basename not path, so with '--pipeline conf.txt', the config file loaded is
      TARGET_PATH/LANGUAGE/config/conf.txt
                              
The script assumes an initialized directory (created with step1_initialize.py)
with a set of external files defined in TARGET_PATH/config/files.txt. Default
pipeline configuration settings are in TARGET_PATH/config/pipeline-default.txt.

Examples:
   %  python step2_document_processing.py --corpus data/patents/en --populate -n 5
   %  python step2_document_processing.py --corpus data/patents/en --xml2txt -n 5
   %  python step2_document_processing.py --corpus data/patents/en --txt2tag -n 5
   %  python step2_document_processing.py --corpus data/patents/en --tag2chk -n 5

"""

# TODO

# The run_X methods all update the count in state/processed.txt every STEP
# files. And at the end of each method, the final remainder is added and the
# state/processing_hiistory fiel is updated. We may want to update the history
# with every STEP files as well and at the end get a final tally. Currently,
# there is not guaranteed to be an entry when an error happens.

# It might be a good idea to have a general way to catch exceptions for the
# run_X methods. We could either have a try-except in each method or use a with
# statement and a class for each run_X method. A superclass could deal with
# errors and perhaps with bookkeeping to (instead of the decorator function).


import os, sys, time, shutil, getopt, subprocess, codecs, textwrap

import config
import xml2txt
import txt2tag
import sdp
import tag2chunk
import cn_txt2seg
import cn_seg2tag
import path

from utils.docstructure.main import Parser
from ontology.utils.batch import RuntimeConfig, DataSet
from ontology.utils.batch import show_datasets, show_pipelines
from ontology.utils.file import ensure_path, get_lines, create_file
from ontology.utils.file import compress, uncompress, get_year


POPULATE = '--populate'
XML2TXT = '--xml2txt'
TXT2TAG = '--txt2tag'
TXT2SEG = '--txt2seg'
SEG2TAG = '--seg2tag'
TAG2CHK = '--tag2chk'

ALL_STAGES = [POPULATE, XML2TXT, TXT2TAG, TXT2SEG, SEG2TAG, TAG2CHK]


# definition of mappings from document processing stage to input and output data
# directories (named processing areas above)
DOCUMENT_PROCESSING_IO = \
    { POPULATE: { 'in': 'external', 'out': 'd0_xml' },
      XML2TXT: { 'in': 'd0_xml', 'out': 'd1_txt' },
      TXT2TAG: { 'in': 'd1_txt', 'out': 'd2_tag' },
      TXT2SEG: { 'in': 'd1_txt', 'out': 'd2_seg' },
      SEG2TAG: { 'in': 'd2_seg', 'out': 'd2_tag' },
      TAG2CHK: { 'in': 'd2_tag', 'out': 'd3_phr_feats' }}

# This variable governs after how many files the files_processed counter in the
# state directory is updated, this way we still have a reasonably recent count
# if there is an error that is not trapped.
STEP = 100


def update_state(fun):
    """To be used as a decorator around functions that run one of the processing steps."""
    def wrapper(*args):
        t1 = time.time()
        files_processed, datasets = fun(*args)
        for dataset in datasets:
            dataset.files_processed += files_processed
            dataset.update_state(args[1], t1)
    return wrapper


@update_state
def run_populate(rconfig, limit, verbose=False):
    """Populate xml directory in the target directory with limit files from the
    source file list or the source directory."""

    output_name = DOCUMENT_PROCESSING_IO[POPULATE]['out']
    dataset = DataSet(POPULATE, output_name, rconfig)

    # initialize data set if it does not exist, this is not contingent on
    # anything because --populate is the first step
    if not dataset.exists():
        dataset.initialize_on_disk()
        dataset.load_from_disk()

    fspecs = get_lines(rconfig.filenames, dataset.files_processed, limit)
    print "[--populate] adding %d files to %s" % (len(fspecs), dataset)
    count = 0
    for fspec in fspecs:
        count += 1
        src_file = fspec.source
        dst_file = os.path.join(rconfig.target_path, 'data', output_name,
                                dataset.version_id, 'files', fspec.target)
        if verbose:
            print "[--populate] %04d %s" % (count, dst_file)
        ensure_path(os.path.dirname(dst_file))
        shutil.copyfile(src_file, dst_file)
        if rconfig.language == 'en':
            compress(dst_file)
        # TODO: does this mean that you miss some if total_count % STEP != 0
        if count % STEP == 0:
            dataset.update_processed_count(STEP)

    return (count % STEP, [dataset])


@update_state
def run_xml2txt(rconfig, limit, options, verbose=False):
    """Run the document structure parser in onto mode."""

    input_dataset = find_input_dataset(XML2TXT, rconfig)
    output_dataset = find_output_dataset(XML2TXT, rconfig)
    print_datasets(XML2TXT, input_dataset, output_dataset)
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    doc_parser = make_parser(rconfig.language)
    workspace = os.path.join(rconfig.target_path, 'data', 'workspace')
    fspecs = get_lines(rconfig.filenames, output_dataset.files_processed, limit)
    for fspec in fspecs:
        count += 1
        filename = fspec.target
        print_file_progress(XML2TXT, count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        uncompress(file_in)
        try:
            xml2txt.xml2txt(doc_parser, file_in, file_out, workspace)
        except Exception as e:
            # just write an empty file that can be consumed downstream
            fh = codecs.open(file_out, 'w')
            fh.close()
            print "[--xml2txt] WARNING: error on", file_in
            print "           ", e
        if rconfig.language == 'en':
            compress(file_in, file_out)
        if count % STEP == 0:
            output_dataset.update_processed_count(STEP)

    return (count % STEP, [output_dataset])


@update_state
def run_txt2tag(rconfig, limit, options, verbose):
    """Takes txt files and runs the tagger on them."""

    input_dataset = find_input_dataset(TXT2TAG, rconfig)
    output_dataset = find_output_dataset(TXT2TAG, rconfig)
    print_datasets(TXT2TAG, input_dataset, output_dataset)
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    tagger = txt2tag.get_tagger(language)
    fspecs = get_lines(rconfig.filenames, output_dataset.files_processed, limit)
    for fspec in fspecs:
        count += 1
        filename = fspec.target
        print_file_progress(TXT2TAG, count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        uncompress(file_in)
        txt2tag.tag(file_in, file_out, tagger)
        if rconfig.language == 'en':
            compress(file_in, file_out)
        if count % STEP == 0:
            output_dataset.update_processed_count(STEP)

    return (count % STEP, [output_dataset])


@update_state
def run_txt2seg(rconfig, limit, options, verbose):
    """Takes txt files and runs the Chinese segmenter on them."""

    input_dataset = find_input_dataset(TXT2SEG, rconfig)
    output_dataset = find_output_dataset(TXT2SEG, rconfig)
    print_datasets(TXT2SEG, input_dataset, output_dataset)
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    segmenter = sdp.Segmenter()
    fspecs = get_lines(rconfig.filenames, output_dataset.files_processed, limit)
    for fspec in fspecs:
        count += 1
        filename = fspec.target
        print_file_progress(TXT2SEG, count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        #uncompress(file_in)
        cn_txt2seg.seg(file_in, file_out, segmenter)
        #compress(file_in, file_out)
        if count % STEP == 0:
            output_dataset.update_processed_count(STEP)

    return (count % STEP, [output_dataset])


@update_state
def run_seg2tag(rconfig, limit, options, verbose):
    """Takes seg files and runs the Chinese tagger on them."""

    input_dataset = find_input_dataset(SEG2TAG, rconfig)
    output_dataset = find_output_dataset(SEG2TAG, rconfig)
    print_datasets(SEG2TAG, input_dataset, output_dataset)
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    tagger = txt2tag.get_tagger(language)
    fspecs = get_lines(rconfig.filenames, output_dataset.files_processed, limit)
    for fspec in fspecs:
        count += 1
        filename = fspec.target
        print_file_progress(SEG2TAG, count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        #uncompress(file_in)
        cn_seg2tag.tag(file_in, file_out, tagger)
        #compress(file_in, file_out)
        if count % STEP == 0:
            output_dataset.update_processed_count(STEP)

    return (count % STEP, [output_dataset])


@update_state
def run_tag2chk(rconfig, limit, options, verbose):
    """Runs the np-in-context code on tagged input. Populates d3_phr_feat."""

    candidate_filter = options.get('--candidate-filter', 'off')
    chunker_rules = options.get('--chunker-rules', 'en')

    # this is a hack that maps the value of the new official name to the value
    # expected by the old name
    filter_p = True if candidate_filter == 'on' else False
    
    input_dataset = find_input_dataset(TAG2CHK, rconfig)
    output_dataset = find_output_dataset(TAG2CHK, rconfig)
    print_datasets(TAG2CHK, input_dataset, output_dataset)
    print "[--tag2chk] using '%s' chunker rules" % chunker_rules
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    fspecs = get_lines(rconfig.filenames, output_dataset.files_processed, limit)
    for fspec in fspecs:
        count += 1
        filename = fspec.target
        print_file_progress(TAG2CHK, count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        year = get_year(filename)
        tag2chunk.Doc(file_in, file_out, year, rconfig.language,
                      filter_p=filter_p, chunker_rules=chunker_rules)
        if rconfig.language == 'en':
            compress(file_in, file_out)
        if count % STEP == 0:
            output_dataset.update_processed_count(STEP)

    return (count % STEP, [output_dataset])



## UTILITY METHODS

def find_input_dataset(stage, rconfig, data_type=None):
    """Find the input data set for a processing stage for a given configuration and return
    it. Print a warning and exit if no dataset or more than one dataset was found. If a
    data type is passed in, the dat type lookup for the stage is bypassed."""

    # Use the stage-to-data mapping to find the data_type if none was handed in
    if data_type is None:
        data_type = DOCUMENT_PROCESSING_IO[stage]['in']
    # Get all data sets D for input name
    dirname = os.path.join(rconfig.target_path, 'data', data_type)
    datasets1 = [ds for ds in os.listdir(dirname) if ds.isdigit()]
    datasets2 = [DataSet(stage, data_type, rconfig, ds) for ds in datasets1]
    # Filer the datasets making sure that d.trace + d.head matches
    # rconfig.pipeline(txt).trace
    datasets3 = [ds for ds in datasets2 if ds.input_matches_global_config()]
    # If there is one result, return it, otherwise write a warning and exit
    if len(datasets3) == 1:
        return datasets3[0]
    elif len(datasets3) > 1:
        print "WARNING, more than one approriate training set:"
        for ds in datasets3:
            print '  ', ds
        sys.exit("Exiting...")
    elif len(datasets3) == 0:
        print "WARNING: no datasets available to meet input requirements"
        sys.exit("Exiting...")

    
def find_output_dataset(stage, rconfig, data_type=None):
    """Find the output data set of a stage for a given configuration and return
    it. Print a warning and exit if no dataset or more than one dataset was
    found."""

    # Use the stage-to-data mapping to find the output names
    if data_type is None:
        data_type = DOCUMENT_PROCESSING_IO[stage]['out']
    #for output_name in data_types:
    # Get all data sets D for input name
    dirname = os.path.join(rconfig.target_path, 'data', data_type)
    datasets1 = [ds for ds in os.listdir(dirname) if ds.isdigit()]
    datasets2 = [DataSet(stage, data_type, rconfig, ds) for ds in datasets1]
    # Filer the datasets making sure that d.trace + d.head matches
    # rconfig.pipeline(txt).trace
    datasets3 = [ds for ds in datasets2 if ds.output_matches_global_config()]
    # If there is one result, return it, if there are more than one, write a
    # warning and exit, otherwise, initialize a dataset and return it
    if len(datasets3) == 1:
        return datasets3[0]
    elif len(datasets3) > 1:
        print "WARNING, more than one approriate training set found:"
        for ds in datasets3:
            print '  ', ds
        sys.exit("Exiting...")
    elif len(datasets3) == 0:
        highest_id = max([0] + [int(ds) for ds in datasets1])
        new_id = "%02d" % (highest_id + 1)
        dataset = DataSet(stage, data_type, rconfig, new_id)
        if not dataset.exists():
            dataset.initialize_on_disk()
            dataset.load_from_disk()
        print "[%s] created %s" % (stage, dataset)
        return dataset
    

def print_datasets(stage, input_dataset, output_dataset):
    print "[%s] input %s" % (stage, input_dataset)
    print "[%s] output %s" % (stage, output_dataset)

def print_file_progress(stage, count, filename, verbose):
    if verbose:
        print "[%s] %04d %s" % (stage, count, filename)

def check_file_counts(input_dataset, output_dataset, limit):
    if input_dataset.files_processed < output_dataset.files_processed + limit:
        print "[check_file_counts] " + \
              "WARNING: input dataset does not have enough processed files"
        sys.exit("Exiting...")

def prepare_io(filename, input_dataset, output_dataset):
    """Generate the file paths for the datasets and make sure the path to the file exists for
    the output dataset. May need to add a version that deals with multiple output datasets."""
    file_id = filename[1:] if filename.startswith(os.sep) else filename
    file_in = os.path.join(input_dataset.path, 'files', file_id)
    file_out = os.path.join(output_dataset.path, 'files', file_id)
    ensure_path(os.path.dirname(file_out))
    return file_in, file_out

def make_parser(language):
    """Return a document structure parser for language."""
    parser = Parser()
    parser.onto_mode = True
    mappings = {'en': 'ENGLISH', 'de': "GERMAN", 'cn': "CHINESE" }
    parser.language = mappings[language]
    return parser

def read_opts():
    options = ['corpus=', 'populate',
               'xml2txt', 'txt2tag', 'txt2seg', 'seg2tag', 'tag2chk',
               'verbose', 'pipeline=', 'show-data', 'show-pipelines']
    try:
        return getopt.getopt(sys.argv[1:], 'l:n:', options)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))

        
if __name__ == '__main__':

    # default values of options
    corpus = config.WORKING_PATENT_PATH
    language = config.LANGUAGE
    stage = None
    pipeline_config = 'pipeline-default.txt'
    verbose, show_data_p, show_pipelines_p = False, False, False
    limit = 1
    
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        if opt == '-l': language = val
        if opt == '-n': limit = int(val)
        if opt == '--verbose': verbose = True
        if opt == '--pipeline': pipeline_config = val
        if opt == '--show-data': show_data_p = True
        if opt == '--show-pipelines': show_pipelines_p = True
        if opt in ALL_STAGES:
            stage = opt

    # NOTE: this is named rconfig to avoid confusion with config.py
    rconfig = RuntimeConfig(corpus, None, language, pipeline_config)
    options = rconfig.get_options(stage)
    #rconfig.pp()

    if show_data_p:
        show_datasets(rconfig, config.DATA_TYPES, verbose)
    elif show_pipelines_p:
        show_pipelines(rconfig)

    elif stage == POPULATE:
        run_populate(rconfig, limit, verbose)
    elif stage == XML2TXT:
        run_xml2txt(rconfig, limit, options, verbose)
    elif stage == TXT2TAG:
        run_txt2tag(rconfig, limit, options, verbose)
    elif stage == TXT2SEG:
        run_txt2seg(rconfig, limit, options, verbose)
    elif stage == SEG2TAG:
        run_seg2tag(rconfig, limit, options, verbose)
    elif stage == TAG2CHK:
        run_tag2chk(rconfig, limit, options, verbose)
