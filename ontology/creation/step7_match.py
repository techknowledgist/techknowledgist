"""

$ python step7_match.py \
    --corpus data/patents/201306-computer-science \
    --filelist files_testing_01.txt \
    --batch batch-01

"""

import os, sys, getopt, shutil, codecs

import path

from ontology.utils.batch import RuntimeConfig, DataSet
from ontology.utils.batch import find_input_dataset, check_file_availability
from ontology.utils.file import filename_generator, ensure_path, open_input_file
from ontology.utils.git import get_git_commit


VERBOSE = False



class Matcher(object):

    def __init__(self, rconfig, filelist, batch):
        self.rconfig = rconfig
        self.file_list = os.path.join(rconfig.config_dir, filelist)
        self.batch = batch
        self.data_dir = os.path.join(self.rconfig.target_path, 'data')
        self.match_dir = os.path.join(self.data_dir, 'o2_matcher')
        self.batch_dir = os.path.join(self.match_dir, batch)
        self.results_file = os.path.join(self.batch_dir, "match.results.txt")
        self.info_file_general = os.path.join(self.batch_dir, "match.info.general.txt")
        self.info_file_config = os.path.join(self.batch_dir, "match.info.config.txt")
        self.info_file_filelist = os.path.join(self.batch_dir, "match.info.filelist.txt")

    def __str__(self):
        return "<Matcher on '%s' for '%s'>" % (self.rconfig.corpus, self.batch)

    def run(self):
        self._find_datasets()
        self._create_info_files()
        fnames = filename_generator(self.input_dataset.path, self.file_list)
        with codecs.open(self.results_file, 'w', encoding='utf-8') as fh:
            count = 0
            for fname in fnames:
                count += 1
                print_file_progress("Matcher", count, fname, VERBOSE)
                if count > 10:
                    break
                self.run_matcher_on_file(fname, fh)

    def run_matcher_on_file(self, fname, fh):
        infile = open_input_file(fname)
        for line in infile:
            (id, year, term, feats) = parse_feats_line(line)
            prev_V = feats.get('prev_V', None)
            #initial_V = feats.get('initial_V', None)
            #chunk_lead_VBG = feats.get('chunk_lead_VBG', None)
            if prev_V is not None:
                fh.write("%s\t%s\t%s\n" % (year, term , prev_V))


    def pp(self):
        print "\n<Matcher on '%s'>" % self.rconfig.corpus
        print "   match_dir =", self.match_dir
        print "   batch_dir =", self.batch_dir
        rconfig.pp()

    def _find_datasets(self):
        """Select data sets and check whether all files are available."""
        # TODO: this is the same as the method on TrainerClassifier
        print "[Matcher] finding dataset and checking file availability"
        self.input_dataset = find_input_dataset(self.rconfig, 'd3_phr_feats')
        #check_file_availability(self.input_dataset, self.file_list)

    def _create_info_files(self):
        if os.path.exists(self.info_file_general):
            sys.exit("WARNING: already ran matcher for batch %s" % self.batch)
        print "[Matcher] initializing datat/o2_matcher/%s directory" %  self.batch
        ensure_path(self.batch_dir)
        with open(self.info_file_general, 'w') as fh:
            fh.write("$ python %s\n\n" % ' '.join(sys.argv))
            fh.write("batch        =  %s\n" % self.batch)
            fh.write("file_list    =  %s\n" % self.file_list)
            fh.write("config_file  =  %s\n" % os.path.basename(rconfig.pipeline_config_file))
            fh.write("git_commit   =  %s" % get_git_commit())
        shutil.copyfile(self.rconfig.pipeline_config_file, self.info_file_config)
        shutil.copyfile(self.file_list, self.info_file_filelist)


def parse_feats_line(line):
    (id, year, term, feats) = line.strip().split("\t", 3)
    feats = feats.split("\t")
    feats = dict((k,v) for (k,v) in [f.split('=', 1) for f in feats])
    return (id, year, term, feats)
    
def print_file_progress(stage, count, filename, verbose):
    # copied from step2_document_processing
    if verbose:
        print "[%s] %05d %s" % (stage, count, filename)


def read_opts():
    longopts = ['corpus=', 'filelist=', 'batch=', 'pipeline=', 'verbose' ]
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))




if __name__ == '__main__':

    # default values of options
    corpus = None
    language = 'en'
    batch = None
    filelist = 'files.txt'
    pipeline_config = 'pipeline-default.txt'

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--language': language = val
        elif opt == '--filelist': filelist = val
        elif opt == '--batch': batch = val
        elif opt == '--pipeline': pipeline_config = val
        elif opt == '--verbose': VERBOSE = True

    # TODO: language should not be an option after step1_initialize since it is
    # associated with a corpus, should therefore also not be given to the config
    # object
    rconfig = RuntimeConfig(corpus, language, pipeline_config)

    matcher = Matcher(rconfig, filelist, batch)
    matcher.pp()
    matcher.run()
