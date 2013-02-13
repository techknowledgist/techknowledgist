"""

Script that manages the part of the processing chain that deals with individual documents,
that is document parsing, segmentation, tagging, chunking and creation of phrase-level and
document-level feature vectors.

USAGE:
   % python step2_document_processing.py [OPTIONS]

OPTIONS:
   --populate   --  import external files
   --xml2txt    --  document structure parsing
   --txt2tag    --  tagging
   --tag2chk    --  creating chunks in context
   --pf2dfeats  --  go from phrase features to document features

   -l LANGUAGE     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
   -t TARGET_PATH  --  target directory, default is 'data/patents'
   -n INTEGER      --  number of documents to process, default is 1

   --verbose        --  print name of each processed file to stdout
   --show-data      --  print all datasets, then exits, requires -t and -l options
   --show-pipeline  --  print all pipelines, then exits, requires -t and -l options,
                          also requires that all pipeline files match 'pipeline-*.txt'
   
   --config FILE -- optional configuration file to overrule the default config this is
                    just the basename not path, so with '--config conf.txt', the config
                    file loaded is TARGET_PATH/LANGUAGE/config/conf.txt
                              
The script assumes an initialzed directory (created with step1_initialize.py) with a set
of external files defined in TARGET_PATH/LANGUAGE/config/files.txt. Default pipeline
configuration settings are in TARGET_PATH/LANGUAGE/config/pipeline-default.txt.

Examples:
   %  python step2_document_processing.py -l en -t data/patents --populate -n 5
   %  python step2_document_processing.py -l en -t data/patents --xml2txt -n 5
   %  python step2_document_processing.py -l en -t data/patents --txt2tag -n 5
   %  python step2_document_processing.py -l en -t data/patents --tag2chk -n 5
   %  python step2_document_processing.py -l en -t data/patents --df2dfeats -n 5

"""

import os, sys, time, shutil, getopt, subprocess, codecs, textwrap

import putils
import xml2txt
import txt2tag
import sdp
import tag2chunk
import cn_txt2seg
import cn_seg2tag
import pf2dfeats

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser
from ontology.utils.batch import GlobalConfig, DataSet
from ontology.utils.file import ensure_path, get_lines, create_file
from step1_initialize import DOCUMENT_PROCESSING_IO


ALL_STAGES = ['--populate', '--xml2txt', '--txt2tag', '--tag2chk', '--pf2dfeats']


def update_state(fun):
    """To be used as a decorator around functions that run one of the processing steps."""
    
    def wrapper(*args):
        t1 = time.time()
        datasets = fun(*args)
        limit = args[1]
        for dataset in datasets:
            dataset.files_processed += limit
            dataset.update_state(limit, t1)

    return wrapper

    

@update_state
def run_populate(config, limit, verbose=False):
    """Populate xml directory in the target directory with limit files from the source path."""

    target_path = config.target_path
    language = config.language
    source = config.source()
    output_names = DOCUMENT_PROCESSING_IO['--populate']['out']
    dataset = DataSet('--populate', output_names[0], config)

    print "[--populate] populating %s" % (dataset)
    print "[--populate] using %d files from %s" % (limit, source)

    # initialize data set if it does not exist, this is not contingent on anything because
    # --populate is the first step
    if not dataset.exists():
        dataset.initialize_on_disk()
        dataset.load_from_disk()

    count = 0
    filenames = get_lines(config.filenames, dataset.files_processed, limit)
    for filename in filenames:
        count += 1
        # strip a leading separator to make path relative so it can be glued to the target
        # directory
        src_file = filename[1:] if filename.startswith(os.sep) else filename
        dst_file = os.path.join(target_path, language, 'data',
                                output_names[0], dataset.version_id, 'files', src_file)
        if verbose:
            print "[--populate] %04d %s" % (count, filename)
        ensure_path(os.path.dirname(dst_file))
        shutil.copyfile(filename, dst_file)

    return [dataset]


@update_state
def run_xml2txt(config, limit, options, verbose=False):

    """Run the document structure parser in onto mode."""

    input_dataset = find_input_dataset('--xml2txt', config)
    output_datasets = find_output_datasets('--xml2txt', config)
    output_dataset = output_datasets[0]
    print_datasets('--xml2txt', input_dataset, output_datasets)
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    doc_parser = make_parser(config.language)
    workspace = os.path.join(config.target_path, config.language, 'data', 'workspace')
    filenames = get_lines(config.filenames, output_dataset.files_processed, limit)
    for filename in filenames:
        count += 1
        print_file_progress('--xml2txt', count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        try:
            xml2txt.xml2txt(doc_parser, file_in, file_out, workspace)
        except Exception:
            fh = codecs.open(file_out, 'w')
            fh.close()
            print "[--xml2txt] WARNING: error on", file_in

    return [output_dataset]


@update_state
def run_txt2tag(config, limit, options, verbose):
    """Takes txt files and runs the tagger (and segmenter for Chinese) on them. Adds files to
    the language/tag and language/seg directories. Works on pasiphae but not on chalciope."""

    input_dataset = find_input_dataset('--txt2tag', config)
    output_datasets = find_output_datasets('--txt2tag', config)
    output_dataset = output_datasets[0]
    print_datasets('--txt2tag', input_dataset, output_datasets)
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    tagger = txt2tag.get_tagger(language)
    filenames = get_lines(config.filenames, output_dataset.files_processed, limit)
    for filename in filenames:
        count += 1
        print_file_progress('--txt2tag', count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        txt2tag.tag(file_in, file_out, tagger)

    return [output_dataset]

    # segmenter = sdp.Segmenter()
    # if language == 'cn':
    #     cn_txt2seg.seg(txt_file, seg_file, segmenter)
    #     cn_seg2tag.tag(seg_file, tag_file, tagger)


@update_state
def run_tag2chk(config, limit, options, verbose):
    """Runs the np-in-context code on tagged input. Populates language/phr_occ and
    language/phr_feat. Sets the contents of config-chunk-filter.txt given the value of
    chunk_filter."""

    candidate_filter = options.get('--candidate-filter', 'off')
    chunker_rules = options.get('--chunker-rules', 'en')

    # TODO: a hack that maps the official name (candidate_filter) to the old name
    filter_p = True if candidate_filter == 'on' else False
    
    input_dataset = find_input_dataset('--tag2chk', config)
    output_datasets = find_output_datasets('--tag2chk', config)
    output_dataset1 = output_datasets[0]
    output_dataset2 = output_datasets[1]
    print_datasets('--txt2tag', input_dataset, output_datasets)
    print "[--tag2chk] using '%s' chunker rules" % chunker_rules
    check_file_counts(input_dataset, output_dataset1, limit)
    check_file_counts(input_dataset, output_dataset2, limit)

    count = 0
    filenames = get_lines(config.filenames, output_dataset1.files_processed, limit)
    for filename in filenames:
        count += 1
        print_file_progress('--tag2chk', count, filename, verbose)
        file_in, file_out1 = prepare_io(filename, input_dataset, output_dataset1)
        file_in, file_out2 = prepare_io(filename, input_dataset, output_dataset2)
        # TODO: handle the year stuff differently (this is a bit of a hack)
        year = os.path.basename(os.path.dirname(filename))
        tag2chunk.Doc(file_in, file_out2, file_out1, year, config.language,
                      filter_p=filter_p, chunker_rules=chunker_rules)

    return output_datasets


@update_state
def run_pf2dfeats(config, limit, options, verbose):
    """Creates a union of the features for each chunk in a doc (for training)."""

    input_dataset = find_input_dataset('--pf2dfeats', config)
    output_datasets = find_output_datasets('--pf2dfeats', config)
    output_dataset = output_datasets[0]
    print_datasets('--pf2dfeats', input_dataset, output_datasets)
    check_file_counts(input_dataset, output_dataset, limit)

    count = 0
    filenames = get_lines(config.filenames, output_dataset.files_processed, limit)
    for filename in filenames:
        count += 1
        print_file_progress('--txt2tag', count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        year = os.path.basename(os.path.dirname(filename))
        doc_id = os.path.basename(filename)
        pf2dfeats.make_doc_feats(file_in, file_out, doc_id, year)

    return [output_dataset]


def show_datasets(target_path, language, config):
    """Print all datasets in the data directory."""
    for stage in ALL_STAGES:
        dataset_types = DOCUMENT_PROCESSING_IO[stage]['out']
        for dataset_type in dataset_types:
            print "\n===", dataset_type, "===\n"
            path = os.path.join(target_path, language, 'data', dataset_type)
            datasets1 = [ds for ds in os.listdir(path) if ds.isdigit()]
            datasets2 = [DataSet(stage, dataset_type, config, ds) for ds in datasets1]
            for ds in datasets2:
                print ds
                for e in ds.pipeline_trace:
                    print "   ", e[0], e[1]
                print "   ", ds.pipeline_head[0], ds.pipeline_head[1]

def show_pipelines(target_path, language):
    path = os.path.join(target_path, language, 'config')
    pipeline_files = [f for f in os.listdir(path) if f.startswith('pipeline')]
    for pipeline_file in sorted(pipeline_files):
        if pipeline_file[-1] == '~':
            continue
        print "\n[%s]" % pipeline_file
        for line in open(os.path.join(path, pipeline_file)).readlines():
            line = line.strip()
            if not line or line[0] == '#':
                continue
            print '  ', line
    print


    
## AUXILIARY METHODS
    
def find_input_dataset(stage, config):
    """Find the input data set and return it. Print a warning and exit if no dataset or more
    than one dataset was found."""

    # Use the stage-to-data mapping to find the input name
    input_name = DOCUMENT_PROCESSING_IO[stage]['in']
    # Get all data sets D for input name
    dirname = os.path.join(target_path, language, 'data', input_name)
    datasets1 = [ds for ds in os.listdir(dirname) if ds.isdigit()]
    datasets2 = [DataSet(stage, input_name, config, ds) for ds in datasets1]
    # Filer the datasets making sure that d.trace + d.head matches
    # config.pipeline(txt).trace
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

    
def find_output_datasets(stage, config):
    """Find the output data set and return it. Print a warning and exit if no dataset or more
    than one dataset was found."""

    # Use the stage-to-data mapping to find the output names
    output_names = DOCUMENT_PROCESSING_IO[stage]['out']
    output_datasets = []
    for output_name in output_names:
        # Get all data sets D for input name
        dirname = os.path.join(target_path, language, 'data', output_name)
        datasets1 = [ds for ds in os.listdir(dirname) if ds.isdigit()]
        datasets2 = [DataSet(stage, output_name, config, ds) for ds in datasets1]
        # Filer the datasets making sure that d.trace + d.head matches
        # config.pipeline(txt).trace
        datasets3 = [ds for ds in datasets2 if ds.output_matches_global_config()]
        #print output_name, dirname, datasets1, datasets3
        # If there is one result, return it, otherwise write a warniong and exit
        if len(datasets3) == 1:
            output_datasets.append( datasets3[0])
        elif len(datasets3) > 1:
            print "WARNING, more than one approriate training set found:"
            for ds in datasets3:
                print '  ', ds
            sys.exit("Exiting...")
        elif len(datasets3) == 0:
            highest_id = max([0] + [int(ds) for ds in datasets1])
            new_id = "%02d" % (highest_id + 1)
            dataset = DataSet(stage, output_name, config, new_id)
            if not dataset.exists():
                dataset.initialize_on_disk()
                dataset.load_from_disk()
            print "[%s] created %s" % (stage, dataset)
            output_datasets.append(dataset)
    return output_datasets
    

def print_datasets(stage, input_dataset, output_datasets):
    print "[%s] input %s" % (stage, input_dataset)
    for output_dataset in output_datasets:
        print "[%s] output %s" % (stage, output_dataset)

def print_file_progress(stage, count, filename, verbose):
    if verbose:
        print "[%s] %04d %s" % (stage, count, filename)

def check_file_counts(input_dataset, output_dataset, limit):
    if input_dataset.files_processed < output_dataset.files_processed + limit:
        print "WARNING: input dataset does not have enough processed files"
        print "        ", input_dataset
        print "        ", output_dataset
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
    longopts = ['populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 
                'verbose', 'config=', 'show-data', 'show-pipelines']
    try:
        return getopt.getopt(sys.argv[1:], 'l:t:n:', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))

        
if __name__ == '__main__':

    # default values of options
    target_path, language, stage = 'data/patents', 'en', None
    pipeline_config = 'pipeline-default.txt'
    verbose, show_data_p, show_pipelines_p = False, False, False
    limit = 1
    
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        if opt == '--verbose': verbose = True
        if opt == '--config': pipeline_config = val
        if opt == '--show-data': show_data_p = True
        if opt == '--show-pipelines': show_pipelines_p = True
        if opt in ALL_STAGES:
            stage = opt

    config = GlobalConfig(target_path, language, pipeline_config)
    options = config.get_options(stage)
    #config.pp()

    if show_data_p:
        show_datasets(target_path, language, config)
    elif show_pipelines_p:
        show_pipelines(target_path, language)

    elif stage == '--populate':
        run_populate(config, limit, verbose)
    elif stage == '--xml2txt':
        run_xml2txt(config, limit, options, verbose)
    elif stage == '--txt2tag':
        run_txt2tag(config, limit, options, verbose)
    elif stage == '--tag2chk':
        run_tag2chk(config, limit, options, verbose)
    elif stage == '--pf2dfeats':
        run_pf2dfeats(config, limit, options, verbose)
