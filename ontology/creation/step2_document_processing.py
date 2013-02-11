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
from ontology.utils.batch import files_to_process, GlobalConfig, read_pipeline_config
from ontology.utils.file import ensure_path, get_lines, create_file
from ontology.utils.git import get_git_commit
from step1_initialize import DOCUMENT_PROCESSING_IO


class DataSet(object):

    """
    Instance variables:
       stage_name - name of the stage creating files in the data set
       output_name - name of the directory where
       version_id - subdir in the output, None for the --populate stage
    """

    @classmethod
    def pipeline_component_as_string(cls, trace):
        elements = []
        for element in trace:
            elements.append(element[0] + " " +
                            " ".join(["%s=%s" % (k,v) for k,v in element[1].items()]))
        return "\n".join(elements).strip() + "\n"
    
    
    def __init__(self, stage_name, output_names, config, id='01'):
        self.stage_name = stage_name
        self.output_name1 = output_names[0]
        self.output_name2 = output_names[1] if len(output_names) > 1 else None
        self.version_id = id
        self.files_processed = 0
        self.global_config = config
        self.local_config = None
        self.pipeline_head = None
        self.pipeline_trace = None
        self.base_path = os.path.join(config.target_path, config.language, 'data')
        self.path1 = os.path.join(self.base_path, self.output_name1, self.version_id)
        self.path2 = None
        if self.output_name2 is not None:
            self.path2 = os.path.join(self.base_path, self.output_name2, self.version_id)


    def __str__(self):
        return "<DataSet on '%s' exists=%s processed=%d>" % (self.path1, self.exists(),
                                                             self.files_processed)
    
    def initialize_on_disk(self):
        """All that is guaranteed to exist is a directory like data/patents/en/d1_txt, but sub
        structures is not there. Create the substructure and initial versions of all
        needed files in configuration and state directories."""
        for subdir in ('config', 'state', 'files'):
            ensure_path(os.path.join(self.path1, subdir))
        if self.path2 is not None:
            for subdir in ('config', 'state', 'files'):
                ensure_path(os.path.join(self.path2, subdir))
        create_file(os.path.join(self.path1, 'state', 'processed.txt'), "0\n")
        create_file(os.path.join(self.path1, 'state', 'processing-history.txt'))
        trace, head = self.split_pipeline()
        trace_str = DataSet.pipeline_component_as_string(trace)
        head_str = DataSet.pipeline_component_as_string([head])
        create_file(os.path.join(self.path1, 'config', 'pipeline-head.txt'), head_str)
        create_file(os.path.join(self.path1, 'config', 'pipeline-trace.txt'), trace_str)
        self.files_processed = 0
        
    def split_pipeline(self):
        """Return a pair of pipeline trace and pipeline head from the config.pipeline given the
        current processing step in self.stage_name."""
        trace = []
        for step in self.global_config.pipeline:
            if step[0] == self.stage_name:
                return trace, step
            else:
                trace.append(step)
        print "WARNING: did not find processing step in pipeline"
        return None
        
    def load_from_disk(self):
        """Get the state and the local configuration from the disk. Does not need to get the
        processing history since all we need to do to it is to append that information
        from the latest processing step."""
        fname1 = os.path.join(self.path1, 'state', 'processed.txt')
        fname2 = os.path.join(self.path1, 'config', 'pipeline-head.txt')
        fname3 = os.path.join(self.path1, 'config', 'pipeline-trace.txt')
        self.pipeline_head = read_pipeline_config(fname2)[0]
        self.pipeline_trace = read_pipeline_config(fname3)
        self.files_processed = int(open(fname1).read().strip())
    
    def exists(self):
        """Return True is the data set exists on disk, False otherwise."""
        return os.path.exists(self.path1)

    def update_state(self, limit, t1):
        """Update the content of state/processed.txt and state/processing-history.txt."""
        time_elapsed =  time.time() - t1
        processed = "%d\n" % self.files_processed
        create_file(os.path.join(self.path1, 'state', 'processed.txt'), processed)
        history_file = os.path.join(self.path1, 'state', 'processing-history.txt')
        fh = open(history_file, 'a')
        fh.write("%d\t%s\t%s\t%s\n" % (limit, time.strftime("%Y:%m:%d-%H:%M:%S"),
                                       get_git_commit(), time_elapsed))
        
    def pp(self):
        """Simplistic pretty print."""
        print "DataSet"
        print "    %s" % self.path1
        if self.path2 is not None:
            print "    %s" % self.path2

    
    
def run_populate(config, limit, verbose=False):
    """Populate xml directory in the target directory with limit files from the source path."""

    t1 = time.time()
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
                                output_names[0], dataset.version_id, src_file)
        if verbose:
            print "%04d %s" % (count, filename)
        ensure_path(os.path.dirname(dst_file))
        shutil.copyfile(filename, dst_file)
    dataset.files_processed += limit
    dataset.update_state(limit, t1)



def run_xml2txt(target_path, language, limit):
    """Takes xml files and runs the document structure parser in onto mode. Adds files
    to the language/txt directory and ds_* directories with intermediate document
    structure parser results."""
    print "[--xml2txt] on %s/%s/xml/" % (target_path, language)

    config.pp()
    print dataset
    
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




if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:t:n:',
        ['populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 
         'verbose', 'config=', 'section-filter-on', 'section-filter-off'])

    # default values of options
    language = 'en'
    target_path = 'data/patents'
    pipeline_config = 'pipeline-default.txt'
    verbose = False
    populate = False
    xml_to_txt, txt_to_tag = False, False
    tag_to_chk, pf_to_dfeats = False, False
    section_filter_p = False
    limit = 0
    
    for opt, val in opts:

        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '-n': limit = int(val)
        
        if opt == '--populate': populate = True
        if opt == '--xml2txt': xml_to_txt = True
        if opt == '--txt2tag': txt_to_tag = True
        if opt == '--tag2chk': tag_to_chk = True
        if opt == '--pf2dfeats': pf_to_dfeats = True

        if opt == '--verbose': verbose = True
        if opt == '--config': pipeline_config = val
        if opt == '--section-filter-on': section_filter_p = True
        if opt == '--section-filter-off': section_filter_p = False


    config = GlobalConfig(target_path, language, pipeline_config)
    
    if populate:
        run_populate(config, limit, verbose)
    elif xml_to_txt:
        run_xml2txt(config, limit)
    elif txt_to_tag:
        run_txt2tag(config, limit)
    elif tag_to_chk:
        run_tag2chk(config, limit, chunk_filter_p)
    elif pf_to_dfeats:
        run_pf2dfeats(config, limit)
