"""
Script to run the matcher on a corpus.

Usage:

    $ python collect_frequencies.py OPTIONS

Options:

    --corpus - the corpus to run the matcher on

    --filelist - list of files from the corpus to process, it is expected to be
      in the config directory of the corpus, defaults to files.txt

    --batch - directory in data/o1_index to write the results to

    --verbose - print progress

Takes all the d3_phr_feats from a corpus and collects the terms and all the
locations they occur in. Creates four files in the batch directory:

    index.locs.txt
    index.info.general.txt
    index.info.config.txt
    index.info.filelist.txt

Example:

    $ python collect_frequencies.py \
      --corpus data/patents/201306-computer-science \
      --filelist files_testing_01.txt \
      --batch batch-01 \
      --verbose


WISHLIST:

- Remove dependency on directories inside the corpus. The filelist now has to be
  inside the config dir and the results have to be written to o2_matcher. Leave
  these as a default, but allow files/directories in other spots.

- Add runtime statistics like time elapsed and perhaps specifications of the
  machine it ran on.

"""


import os, sys, getopt, shutil, codecs, time, subprocess

sys.path.append(os.path.abspath('../..'))
from ontology.utils.batch import RuntimeConfig, DataSet
from ontology.utils.batch import find_input_dataset, check_file_availability
from ontology.utils.file import filename_generator, ensure_path, open_input_file
from ontology.utils.file import parse_feats_line
from ontology.utils.git import get_git_commit

VERBOSE = False


class Collector(object):

    def __init__(self, rconfig, filelist, batch):
        self.rconfig = rconfig
        self.file_list = os.path.join(rconfig.config_dir, filelist)
        self.batch = batch
        self.data_dir = os.path.join(self.rconfig.target_path, 'data')
        self.index_dir = os.path.join(self.data_dir, 'o1_index')
        self.batch_dir = os.path.join(self.index_dir, batch)
        self.locations_file = os.path.join(self.batch_dir, "index.locs.txt")
        self.info_file_general = os.path.join(self.batch_dir, "index.info.general.txt")
        self.info_file_config = os.path.join(self.batch_dir, "index.info.config.txt")
        self.info_file_filelist = os.path.join(self.batch_dir, "index.info.filelist.txt")

    def __str__(self):
        return "<Collector on '%s' for '%s'>" % (self.rconfig.corpus, self.batch)

    def run(self):
        self.time = time.time()
        self._find_datasets()
        self._create_info_files()
        fnames = filename_generator(self.input_dataset.path, self.file_list)
        count = 0
        fh = codecs.open(self.locations_file, 'w', encoding='utf-8')
        for fname in fnames:
            count += 1
            #if count > 5: break
            print_file_progress("Collector", count, fname, VERBOSE)
            self._process_file(fname, fh)
        self._finish()

    def pp(self):
        print "\n<Collector on '%s'>" % self.rconfig.corpus
        print "   index_dir =", self.index_dir
        print "   batch_dir =", self.batch_dir
        rconfig.pp()

    def _process_file(self, fname, fh):
        self.locations = {}
        infile = open_input_file(fname)
        for l in infile:
            parsed_line = parse_feats_line(l)
            year = parsed_line[1]
            term = parsed_line[2] 
            feats = parsed_line[3] 
            path = year + os.sep + os.path.splitext(parsed_line[0])[0]
            line = feats.get('doc_loc', '-1')
            key = path + "\t" + term
            if not self.locations.has_key(key):
                self.locations[key] = []
            self.locations[key].append(line)
        for key, lines in self.locations.items():
            path, term = key.split("\t", 1)
            fh.write("%s\t%s\t%s\t%s\n" % (path, term, len(lines), ' '.join(lines)))    
            
    def _find_datasets(self):
        """Select data sets and check whether all files are available."""
        # TODO: this is the same as the method on TrainerClassifier
        print "[Collector] finding dataset and checking file availability"
        self.input_dataset = find_input_dataset(self.rconfig, 'd3_phr_feats')
        print "[Collector]", self.input_dataset
        check_file_availability(self.input_dataset, self.file_list)

    def _create_info_files(self):
        if os.path.exists(self.info_file_general):
            sys.exit("WARNING: already ran indexer for batch %s" % self.batch)
        print "[Collector] initializing data/o1_index/%s directory" %  self.batch
        ensure_path(self.batch_dir)
        with open(self.info_file_general, 'w') as fh:
            fh.write("$ python %s\n\n" % ' '.join(sys.argv))
            fh.write("batch        =  %s\n" % self.batch)
            fh.write("file_list    =  %s\n" % self.file_list)
            fh.write("config_file  =  %s\n" % os.path.basename(rconfig.pipeline_config_file))
            fh.write("git_commit   =  %s\n" % get_git_commit())
        shutil.copyfile(self.rconfig.pipeline_config_file, self.info_file_config)
        shutil.copyfile(self.file_list, self.info_file_filelist)

    def _finish(self):
        with open(self.info_file_general, 'a') as fh:
            fh.write("\nprocessing time: %d seconds\n" % (time.time() - self.time))


def print_file_progress(stage, count, filename, verbose):
    # copied from step2_document_processing
    if verbose:
        print "[%s] %05d %s" % (stage, count, filename)


def read_opts():
    longopts = ['corpus=', 'filelist=', 'batch=', 'pipeline=', 'language=', 'verbose' ]
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
    # object, but for now we keep it
    rconfig = RuntimeConfig(corpus, None, None, language, pipeline_config)
    rconfig.pp()

    Collector(rconfig, filelist, batch).run()
