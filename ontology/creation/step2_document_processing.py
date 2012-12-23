"""

Run al processing in batch. Very similar to patent_analyzer.py, but approaches the task
from a different angle

The script starts with lists of files pointing to all single files in the external
directory, with a list for each language. these lists have all files for a lnaguage in a
random order
   
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


Usage:
    
    % python patent_analyzer.py [OPTIONS]

    -l LANG      --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -s PATH      --  external source directory with XML files, see below for the default
    -t PATH      --  target directory, default is data/patents
    -n INTEGER   --  number of documents to process
    -r STRING    --  range of documents to take, that is, the postfix of classifier output
     
    --populate   --  populate directory in target path with files from source path
    --xml2txt    --  document structure parsing
    --txt2tag    --  tagging
    --tag2chk    --  creating chunks in context
    --pf2dfeats  --  go from phrase features to document features
    #--summary    --  create summary lists

    All the above long options require a target path and a language (via the -l and -t
    options or their defaults). The long options --init and --populate also require a
    source path (via -s or its default). The -n option is ignored if --init is used.

    --verbose   --  print name of each processed file to stdout

    --config FILE      --  optional configuration file to overrule the default configuration
    --chunk-filter     --  use a filter when proposing technology chunks (the default)
    --no-chunk-filter  --  do not use a filter when proposing technology chunks
    
    
The final results of these steps are in:

    TARGET_PATH/LANGUAGE/phr_occ
    TARGET_PATH/LANGUAGE/phr_feat
    TARGET_PATH/LANGUAGE/ws

    
Examples:

Population follows the paradigm above, taking elements from the list. With the following
you add 10 files to the data/patents/en/xml directory.

% setenv SOURCE_PATENTS /home/j/corpuswork/fuse/fuse-patents/500-patents/DATA/Lexis-Nexis
% python batch.py --populate -l en -n 10 -s $SOURCE_PATENTS/US/Xml/ -t data/patents

Running the document structure parser. From here on, you do not need the source directory
anymore. Just say what you want to do and how many files you want to do. Assumes that
previous processing stages on those files have been done.

% python batch.py --xml2txt -l en -n 10 -t data/patents
% python batch.py --txt2tag -l de -n 10 -t data/patents/

Note that the tagger may only work on machines like pasiphae. The invocation there is
slightly different:

% python2.6 batch.py --txt2tag -l de -n 10 -t data/patents/

"""

import os, sys, time, shutil, getopt, subprocess, codecs, textwrap
from random import shuffle

import config_data
import putils
import xml2txt
import txt2tag
import sdp
import tag2chunk
import cn_txt2seg
import cn_seg2tag
import pf2dfeats
import train
import mallet
import find_mallet_field_value_column
import sum_scores

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser
from ontology.utils.batch import read_stages, update_stages, write_stages
from ontology.utils.batch import files_to_process

# defaults that can be overwritten by command line options
source_path = config_data.external_patent_path
target_path = config_data.working_patent_path
language = config_data.language
verbose = False

    
def run_populate(source_path, target_path, language, limit):
    """Populate xml directory in the target directory with limit files from the source path."""
    print "[--populate] populating %s/%s/xml" % (target_path, language)
    print "[--populate] using %d files from %s" % (limit, source_path)
    stages = read_stages(target_path, language)
    fnames = files_to_process(target_path, language, stages, '--populate', limit)
    count = 0
    for (year, fname) in fnames:
        count += 1
        source_file = os.path.join(source_path, year, fname)
        target_file = os.path.join(target_path, language, 'xml', year, fname)
        if verbose:
            print "[--populate] %04d adding %s" % (count, target_file)
        shutil.copyfile(source_file, target_file)
    update_stages(target_path, language, '--populate', limit)

def run_xml2txt(target_path, language, limit):
    """Takes xml files and runs the document structure parser in onto mode. Adds files
    to the language/txt directory and ds_* directories with intermediate document
    structure parser results."""
    print "[--xml2txt] on %s/%s/xml/" % (target_path, language)
    stages = read_stages(target_path, language)
    xml_parser = Parser()
    xml_parser.onto_mode = True
    mappings = {'en': 'ENGLISH', 'de': "GERMAN", 'cn': "CHINESE" }
    xml_parser.language = mappings[language]
    fnames = files_to_process(target_path, language, stages, '--xml2txt', limit)
    count = 0
    for year, fname in fnames:
        count += 1
        source_file = os.path.join(target_path, language, 'xml', year, fname)
        target_file = os.path.join(target_path, language, 'txt', year, fname)
        if verbose:
            print "[--xml2txt] %04d creating %s" % (count, target_file)
        try:
            xml2txt.xml2txt(xml_parser, source_file, target_file)
        except Exception:
            fh = codecs.open(target_file, 'w')
            fh.close()
            print "[--xml2txt]      WARNING: error on", source_file
    update_stages(target_path, language, '--xml2txt', limit)

def run_txt2tag(target_path, language, limit):
    """Takes txt files and runs the tagger (and segmenter for Chinese) on them. Adds files to
    the language/tag and language/seg directories. Works on pasiphae but not on chalciope."""
    print "[--txt2tag] on %s/%s/txt/" % (target_path, language)
    stages = read_stages(target_path, language)
    tagger = txt2tag.get_tagger(language)
    segmenter = sdp.Segmenter()
    fnames = files_to_process(target_path, language, stages, '--txt2tag', limit)
    count = 0
    for year, fname in fnames:
        count += 1
        txt_file = os.path.join(target_path, language, 'txt', year, fname)
        seg_file = os.path.join(target_path, language, 'seg', year, fname)
        tag_file = os.path.join(target_path, language, 'tag', year, fname)
        if language == 'cn':
            if verbose:
                print "[--txt2tag] %04d creating %s" % (count, seg_file)
            cn_txt2seg.seg(txt_file, seg_file, segmenter)
            if verbose:
                print "[--txt2tag] %04d creating %s" % (count, tag_file)
            cn_seg2tag.tag(seg_file, tag_file, tagger)
        else:
            if verbose:
                print "[--txt2tag] %04d creating %s" % (count, tag_file)
            txt2tag.tag(txt_file, tag_file, tagger)
    update_stages(target_path, language, '--txt2tag', limit)

def run_tag2chk(target_path, language, limit, chunk_filter):
    """Runs the np-in-context code on tagged input. Populates language/phr_occ and
    language/phr_feat. Sets the contents of config-chunk-filter.txt given the value of
    chunk_filter."""
    print "[--tag2chk] on %s/%s/tag/" % (target_path, language)

    filter_setting = "on" if chunk_filter else "off"
    _save_config(target_path, language, 'chunk-filter', value)
    #fh = open(os.path.join(target_path, language, 'config-chunk-filter.txt'), 'w')
    #filter_setting = "on" if chunk_filter else "off"
    #fh.write("chunk-filter %s\n" % filter_setting)
    #fh.close()

    stages = read_stages(target_path, language)
    fnames = files_to_process(target_path, language, stages, '--tag2chk', limit)
    count = 0
    for (year, fname) in fnames:
        count += 1
        tag_file = os.path.join(target_path, language, 'tag', year, fname)
        occ_file = os.path.join(target_path, language, 'phr_occ', year, fname)
        fea_file = os.path.join(target_path, language, 'phr_feats', year, fname)
        if verbose:
            print "[--tag2chk] %04d adding %s" % (count, occ_file)
        tag2chunk.Doc(tag_file, occ_file, fea_file, year, language, filter_p=chunk_filter)
    update_stages(target_path, language, '--tag2chk', limit)

def _save_config(target_path, language, variable, value):
    """Save value of variable in a config file."""
    fh = open(os.path.join(target_path, language, "config-%s.txt" % variable), 'w')
    fh.write("%s %s\n" % (variable, value))
    fh.close()

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

def run_summary(target_path, language, limit):
    """Collect data from directories into workspace area: ws/doc_feats.all,
    ws/phr_feats.all and ws/phr_occ.all. All downstream processing should rely on these
    data and nothing else."""
    print "[--summary] appending to files in ws"
    #subprocess.call("sh ./cat_phr.sh %s %s" % (target_path, language), shell=True)
    stages = read_stages(target_path, language)
    fnames = files_to_process(target_path, language, stages, '--summary', limit)
    doc_feats_file = os.path.join(target_path, language, 'ws', 'doc_feats.all')
    phr_feats_file = os.path.join(target_path, language, 'ws', 'phr_feats.all')
    phr_occ_file = os.path.join(target_path, language, 'ws', 'phr_occ.all')
    fh_doc_feats = codecs.open(doc_feats_file, 'a', encoding='utf-8')
    fh_phr_feats = codecs.open(phr_feats_file, 'a', encoding='utf-8')
    fh_phr_occ = codecs.open(phr_occ_file, 'a', encoding='utf-8')
    for (year, fname) in fnames:
        doc_feats_file = os.path.join(target_path, language, 'doc_feats', year, fname)
        phr_feats_file = os.path.join(target_path, language, 'phr_feats', year, fname)
        phr_occ_file = os.path.join(target_path, language, 'phr_occ', year, fname)
        fh_doc_feats.write(codecs.open(doc_feats_file, encoding='utf-8').read())
        fh_phr_feats.write(codecs.open(phr_feats_file, encoding='utf-8').read())
        fh_phr_occ.write(codecs.open(phr_occ_file, encoding='utf-8').read())
    update_stages(target_path, language, '--summary', limit)




if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:n:r:',
        ['populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 'summary',
         'verbose', 'config=', 'chunk-filter', 'no-chunk-filter'])

    populate = False
    xml_to_txt, txt_to_seg, txt_to_tag = False, False, False
    tag_to_chk, pf_to_dfeats = False, False
    config = None
    #chunk_filter = True
    #summary = False
    limit = 0

    for opt, val in opts:

        if opt == '-l': language = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        
        if opt == '--populate': populate = True
        if opt == '--xml2txt': xml_to_txt = True
        if opt == '--txt2tag': txt_to_tag = True
        if opt == '--tag2chk': tag_to_chk = True
        if opt == '--pf2dfeats': pf_to_dfeats = True
        #if opt == '--summary': summary = True

        if opt == '--verbose': verbose = True
        if opt == '--config': pipeline_config = val
        if opt == '--chunk-filter': chunk_filter = True
        if opt == '--no-chunk-filter': chunk_filter = False


    print opts, args
    print open(os.path.join(target_path, language, 'config', 'config-general.txt')).read()
    
    sys.exit()

    

        
    if populate:
        run_populate(source_path, target_path, language, limit)
    elif xml_to_txt:
        run_xml2txt(target_path, language, config, limit)
    elif txt_to_tag:
        run_txt2tag(target_path, language, config, limit)
    elif tag_to_chk:
        run_tag2chk(target_path, language, config, limit, chunk_filter)
    elif pf_to_dfeats:
        run_pf2dfeats(target_path, language, config, limit)
    #elif summary:
    #    run_summary(target_path, language, config, limit)
