"""


USAGE:
    % python patent_analyzer.py [OPTIONS]

OPTIONS:
    --populate   --  import external files
    --xml2txt    --  document structure parsing
    --txt2tag    --  tagging
    --tag2chk    --  creating chunks in context
    --pf2dfeats  --  go from phrase features to document features

    -l LANGUAGE     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -t TARGET_PATH  --  target directory
    -n INTEGER      --  number of documents to process
    --verbose       --  print name of each processed file to stdout
    
    --config FILE         --  optional configuration file to overrule the default config
                              this is just the basename not path
                              
    --section-filter-on   --  use a filter when proposing technology chunks
    --section-filter-off  --  do not use the filter (this is the default)
    
The final results of these steps are in:

    TARGET_PATH/LANGUAGE/data/d3_phr_occ
    TARGET_PATH/LANGUAGE/data/d3_phr_feat

The script starts with lists of files pointing to all single files in the external
directory, with a list for each language. these lists have all files for a lnaguage in a
random order


NOTES

Maintains a file for each lannguage which stores what what was done for each processing
stage. Lines in that file look as follows:

   --xml2txt 500
   --txt2tag 200
   --tag2chk 100

These lines indicate that the first 500 lines of the input have gone through the xml2txt
stage, 200 through the txt2tag stage and 100 through the tag2chk phase. Initially this
file is empty but when a value is first retrieved it is initialized to 0.
   
The input to the scipt is a stage and a number of documents to process. For example:

   % python batch.py --xml2txt -n 100

This sends 100 documents through the xml2txt phase (using a default data directory), after
which the lines in the progress file are updated to

   --xml2txt 600
   --txt2tag 200
   --tag2chk 100

Unlike patent_analyzer.opy, this script does not call directory level methods like
xml2txt.patents_xml2txt(...), but instead calls methods that process one file only, doing
all the housekeeping itself.

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
from ontology.utils.batch import read_stages, update_stages, write_stages
from ontology.utils.batch import files_to_process, GlobalConfig, DataSet
from ontology.utils.file import ensure_path, get_lines, create_file
from step1_initialize import DOCUMENT_PROCESSING_IO


def update_state(fun):
    """To be used as a decorator around funcitons that run one of the processing steps."""
    
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
    dataset = DataSet('--populate', output_names, config)

    print "[--populate] populating %s/%s/xml" % (target_path, language)
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


#@update_state
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
    segmenter = sdp.Segmenter()
    filenames = get_lines(config.filenames, output_dataset.files_processed, limit)
    for filename in filenames:
        count += 1
        print_file_progress('--txt2tag', count, filename, verbose)
        file_in, file_out = prepare_io(filename, input_dataset, output_dataset)
        #txt2tag.tag(file_in, file_out, tagger)

    return [output_dataset]

    # if language == 'cn':
    #     cn_txt2seg.seg(txt_file, seg_file, segmenter)
    #     cn_seg2tag.tag(seg_file, tag_file, tagger)


#@update_state
def run_tag2chk(config, limit, options, verbose):
    """Runs the np-in-context code on tagged input. Populates language/phr_occ and
    language/phr_feat. Sets the contents of config-chunk-filter.txt given the value of
    chunk_filter."""

    section_filter_p = None
    if options.has_key('--section-filter-on'):
        section_filter_p = True
    if options.has_key('--section-filter-off'):
        section_filter_p = False

    input_dataset = find_input_dataset('--tag2chk', config)
    output_datasets = find_output_datasets('--tag2chk', config)
    output_dataset1 = output_datasets[0]
    output_dataset2 = output_datasets[1]
    print_datasets('--txt2tag', input_dataset, output_datasets)
    check_file_counts(input_dataset, output_dataset1, limit)
    check_file_counts(input_dataset, output_dataset2, limit)

    count = 0
    filenames = get_lines(config.filenames, output_dataset1.files_processed, limit)
    for filename in filenames:
        count += 1
        print_file_progress('--tag2chk', count, filename, verbose)
        file_in, file_out1 = prepare_io(filename, input_dataset, output_dataset1)
        file_in, file_out2 = prepare_io(filename, input_dataset, output_dataset2)
        #tag2chunk.Doc(file_in, file_out2, file_out1, year, config.language, filter_p=section_filter_p)

    return output_datasets

    count = 0
    for (year, fname) in fnames:
        count += 1
        tag_file = os.path.join(target_path, language, 'tag', year, fname)
        occ_file = os.path.join(target_path, language, 'phr_occ', year, fname)
        fea_file = os.path.join(target_path, language, 'phr_feats', year, fname)
        if verbose:
            print "[--tag2chk] %04d adding %s" % (count, occ_file)
        tag2chunk.Doc(tag_file, occ_file, fea_file, year, language, filter_p=section_filter_p)
    update_stages(target_path, language, '--tag2chk', limit)


def run_pf2dfeats(target_path, language, limit):
    """Creates a union of the features for each chunk in a doc (for training)."""
    print "[--pf2dfeats] on %s/%s/phr_feats/" % (target_path, language)
    stages = read_stages(target_path, language)
    fnames = files_to_process(target_path, language, stages, '--pf2dfeats', limit)
    count = 0
    for (year, fname) in fnames:
        count += 1
        doc_id = os.path.splitext(os.path.basename(fname))[0]
        phr_file = os.path.join(target_path, language, 'phr_feats', year, fname)
        doc_file = os.path.join(target_path, language, 'doc_feats', year, fname)
        if verbose:
            print "[--pf2dfeats] %04d adding %s" % (count, doc_file)
        pf2dfeats.make_doc_feats(phr_file, doc_file, doc_id, year)
    update_stages(target_path, language, '--pf2dfeats', limit)



## AUXILIARY METHODS
    
def find_input_dataset(stage, config):
    """Find the input data set and return it. Print a warning and exit if no dataset or more
    than one dataset was found."""

    # Use the stage-to-data mapping to find the input name
    input_name = DOCUMENT_PROCESSING_IO[stage]['in']
    # Get all data sets D for input name
    dirname = os.path.join(target_path, language, 'data', input_name)
    datasets1 = [ds for ds in os.listdir(dirname) if ds.isdigit()]
    datasets2 = [DataSet(stage, [input_name], config, ds) for ds in datasets1]
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
        datasets2 = [DataSet(stage, [output_name], config, ds) for ds in datasets1]
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
            dataset = DataSet(stage, output_names, config, new_id)
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
    file_in = os.path.join(input_dataset.path1, 'files', file_id)
    file_out = os.path.join(output_dataset.path1, 'files', file_id)
    ensure_path(os.path.dirname(file_out))
    return file_in, file_out

def make_parser(language):
    """Return a document structure parser for language."""
    parser = Parser()
    parser.onto_mode = True
    mappings = {'en': 'ENGLISH', 'de': "GERMAN", 'cn': "CHINESE" }
    parser.language = mappings[language]
    return parser



if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:t:n:',
        ['populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 
         'verbose', 'config='])

    # default values of options
    language = 'en'
    target_path = 'data/patents'
    pipeline_config = 'pipeline-default.txt'
    verbose = False
    limit = 0
    stage = None
    
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        if opt == '--verbose': verbose = True
        if opt == '--config': pipeline_config = val
        if opt in ['--populate', '--xml2txt', '--txt2tag', '--tag2chk', '--pf2dfeats']:
            stage = opt

        #if opt == '--section-filter-on': section_filter_p = True
        #if opt == '--section-filter-off': section_filter_p = False

    config = GlobalConfig(target_path, language, pipeline_config)
    options = config.get_options(stage)
    config.pp()
    
    if stage == '--populate':
        run_populate(config, limit, verbose)
    elif stage == '--xml2txt':
        run_xml2txt(config, limit, options, verbose)
    elif stage == '--txt2tag':
        run_txt2tag(config, limit, options, verbose)
    elif stage == '--tag2chk':
        run_tag2chk(config, limit, options, verbose)
    elif stage == '--pf2dfeats':
        run_pf2dfeats(config, limit, options, verbose)
