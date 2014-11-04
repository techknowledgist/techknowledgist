"""Script to run the matcher on a corpus.

Usage:

    $ python run_matcher.py OPTIONS

Options:

    --corpus - the corpus to run the matcher on

    --filelist - list of files from the corpus to process, it is expected to be
         in the config directory of the corpus, defaults to files.txt, which
         includes all files in the corpus; if no corpus was specified, this
         option is to specify a file list that points to files that can be
         anywhere, that is, they are not restricted to be in a corpus, in that
         case, the list is not expected to be found inside the configuration
         directory of a corpus

    --patterns - pattern set to use, either MATURITY or PROMISE, defaults to the
         first of those

    --ouput - directory to write the results to, if a corpus was specified then
         this will be a subdirectory of in data/o2_matcher in the corpus, if
         not, the directory is taken as a path relative to the script directory
         (unless it is an absolute path)

    --verbose - print progress

Results are written to the output directory in two files, one with a line for
each match and one with a summary where the number of matches for each term is
printed. Also writes a couple of general information files to the output
directory and a file with statistics on the number of features found in the
input.

Examples:

    $ python run_matcher.py \
      --corpus ../doc_processing/data/patents/corpora/sample-us \
      --patterns MATURITY \
      --output maturity \
      --verbose

    $ python run_matcher.py \
      --filelist ../classifier/lists/list-sample-us.txt \
      --patterns MATURITY \
      --output maturity \
      --verbose

These two command will process the same files since the file list specified in
the second command points to all files in the corpus of the first command. The
main difference is that the first command writes to a directory named 'maturity'
inside of the 'data/o2_matcher' directory inside the corpus, whereas the second
writes to a directory 'maturity' in the directory that the run_matcher.py script
lives in.


WISHLIST:

- Should also allow using more than one pattern set. Also, the code that
  consumes the patterns (eg maturity.py) needs to be adapted.

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



class Matcher(object):

    def __init__(self, rconfig, filelist, output):
        self.output = output
        self.rconfig = rconfig
        self.file_list = filelist
        self.output_dir = output
        # this avoids using the config directory to find the file list, which
        # would happen if there was no corpus specified in the input
        if rconfig.config_dir is not None:
            self.file_list = os.path.join(rconfig.config_dir, filelist)
            self.data_dir = os.path.join(self.rconfig.target_path, 'data')
            self.match_dir = os.path.join(self.data_dir, 'o2_matcher')
            self.output_dir = os.path.join(self.match_dir, output)
        self.results_file1 = os.path.join(self.output_dir, "match.results.full.txt")
        self.results_file2 = os.path.join(self.output_dir, "match.results.summ.txt")
        self.info_file_general = os.path.join(self.output_dir, "match.info.general.txt")
        self.info_file_config = os.path.join(self.output_dir, "match.info.config.txt")
        self.info_file_filelist = os.path.join(self.output_dir, "match.info.filelist.txt")
        self.info_file_featlist = os.path.join(self.output_dir, "match.info.features.txt")
        self.feature_statistics = FeatureStatistics(self.info_file_featlist)
        self.patterns = PATTERNS

    def __str__(self):
        return "<Matcher on '%s' for '%s'>" % (self.rconfig.corpus, self.output)

    def run(self):
        self.time = time.time()
        if self.rconfig.corpus is not None:
            self._find_datasets()
            fnames = filename_generator(self.input_dataset.path, self.file_list)
            print fnames.next()
        else:
            fnames = [f.strip() for f in open(self.file_list).readlines()]
            print 11, fnames[0], 22
        self._create_info_files()
        with codecs.open(self.results_file1, 'w', encoding='utf-8') as fh:
            print "[--matcher] applying patterns to files"
            count = 0
            for fname in fnames:
                count += 1
                print_file_progress("Matcher", count, fname, VERBOSE)
                # if count > 10: break
                self.run_matcher_on_file(fname, fh)
        self.create_summary()
        self.feature_statistics.write_to_file()
        self._finish()

    def run_matcher_on_file(self, fname, fh):
        infile = open_input_file(fname)
        for line in infile:
            (id, year, term, feats) = parse_feats_line(line)
            self.feature_statistics.add(feats)
            prev_V = feats.get('prev_V', None)
            #initial_V = feats.get('initial_V', None)
            #chunk_lead_VBG = feats.get('chunk_lead_VBG', None)
            #if prev_V is not None:
            #    fh.write("%s\t%s\t%s\t%s\n" % (year, id, term , prev_V))
            for pattern in self.patterns:
                matched_features = pattern.matches(feats)
                if matched_features is not None:
                    fh.write("%s\t%s\t%s\t%s\t%s\n" %
                             (year, id, pattern.name, term , matched_features))

    def create_summary(self):
        """Creates a summary of all the matches. Now simply collects the number of
        matches for each term. This only works for now because all patterns are
        patterns that indicate usage. If promise patterns are added this method
        should generate two numbers. Also, the number is now a simple count that
        does not yet take the pattern weights into account. """
        command = "cut -f4 %s | sort -T . | uniq -c > %s" % \
                  (self.results_file1, self.results_file2)
        print "[--matcher] creating summary"
        print "[--matcher]", command
        subprocess.call(command, shell=True)

    def pp(self):
        if self.rconfig.corpus:
            print "\n<Matcher on '%s'>" % self.rconfig.corpus
            print "   match_dir =", self.match_dir
            print "   output_dir =", self.output_dir
        else:
            print "\n<Matcher on '%s'>" % self.file_list
            print "   output_dir =", self.output_dir
        rconfig.pp()

    def _find_datasets(self):
        """Select data sets and check whether all files are available."""
        # TODO: this is the same as the method on TrainerClassifier
        print "[Matcher] finding dataset and checking file availability"
        self.input_dataset = find_input_dataset(self.rconfig, 'd3_phr_feats')
        #print self.input_dataset
        check_file_availability(self.input_dataset, self.file_list)

    def _create_info_files(self):
        if os.path.exists(self.info_file_general):
            sys.exit("WARNING: already have matcher results in %s" % self.output)
        print "[Matcher] initializing data/o2_matcher/%s directory" %  self.output
        ensure_path(self.output_dir)
        with open(self.info_file_general, 'w') as fh:
            fh.write("$ python %s\n\n" % ' '.join(sys.argv))
            fh.write("output       =  %s\n" % self.output)
            fh.write("file_list    =  %s\n" % self.file_list)
            #fh.write("config_file  =  %s\n" % os.path.basename(rconfig.pipeline_config_file))
            fh.write("config_file  =  %s\n" % rconfig.pipeline_config_file)
            fh.write("git_commit   =  %s\n" % get_git_commit())
        if self.rconfig.pipeline_config_file is not None:
            shutil.copyfile(self.rconfig.pipeline_config_file, self.info_file_config)
        shutil.copyfile(self.file_list, self.info_file_filelist)

    def _finish(self):
        with open(self.info_file_general, 'a') as fh:
            fh.write("\nprocessing time: %d seconds\n" % (time.time() - self.time))


class FeatureStatistics(object):

    """An instance of this class can be used to keep track of feature statistics
    that are input to the matcher."""

    def __init__(self, fname):
        self.fname = fname
        self.feats = {}

    def add(self, feats):
        for feat in feats:
            self.feats[feat] = self.feats.get(feat, 0) + 1

    def write_to_file(self):
        with codecs.open(self.fname, 'w', encoding='utf-8') as fh:
            self.pp(fh)

    def pp(self, fh=sys.stdout):
        for feat in sorted(self.feats.keys()):
            count = self.feats[feat]
            fh.write("%5d  %s\n" % (count, feat))


class Pattern(object):

    def __init__(self, name, score, elements):
        self.name = name
        self.score = score
        self.elements = elements

    def __str__(self):
        return "<Pattern %s %.2f {%s}>" % (self.name, self.score, self.elements)

    def matches(self, feats):
        matched_features = []
        for k, v in self.elements.items():
            if feats.get(k) in v:
                matched_features.append("%s=%s" % (k, feats.get(k)))
            else:
                return None
        return ' '.join(matched_features)

    def pp(self):
        print self.name, '==> {',
        for feat, vals in self.elements.items():
            print "%s = [ %s ]" % (feat, ' , '.join(vals)),
        print '}'

def load_chinese_patterns():
    # TODO: use this for all patterns for all languages, need a more stable
    # syntax for the pattern file.
    global MATURITY_PATTERNS
    MATURITY_PATTERNS = []
    pattern_fh = codecs.open('patterns-cn.txt', encoding='utf-8')
    for line in pattern_fh:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        fields = line.split("\t")
        if len(fields) > 1:
            MATURITY_PATTERNS.append(
                Pattern(fields[0], 0.7, { 'prev_V': fields[1:] }))
    for p in MATURITY_PATTERNS: p.pp()

def print_file_progress(stage, count, filename, verbose):
    # copied from step2_document_processing
    if verbose:
        print "[%s] %05d %s" % (stage, count, filename)

def check_output(corpus, output):
    """Checks whether the ouput directory already exists, exits if that's the case"""
    dir_to_check = output
    if corpus is not None:
        dir_to_check = os.path.join(corpus, 'data', 'o2_matcher', output)
    if os.path.exists(dir_to_check):
        exit("Output directory '%s' allready exists, exiting..." % dir_to_check)

def read_opts():
    longopts = ['corpus=', 'filelist=', 'output=', 'pipeline=', 'patterns=', 'language=', 'verbose' ]
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))



MATURITY_PATTERNS = [

    #Pattern("maturity-", 0.7, { 'prev_V': ('', '', '', '') }),

    Pattern("maturity-use", 0.9,
            { 'prev_V': ('use', 'uses', 'used', 'using') }),

    Pattern("maturity-have", 0.7,
            { 'prev_V': ('has', 'have', 'had', 'having') }),

    Pattern("maturity-stored", 0.7,
            { 'prev_V': ('stored_in',) }),

    Pattern("maturity-provide", 0.7,
            { 'prev_V': ('provide', 'provides', 'providing', 'provided') }),

    Pattern("maturity-connect", 0.7,
            { 'prev_V': ('connect', 'connects', 'connected', 'connecting') }),

    Pattern("maturity-received", 0.7,
            { 'prev_V': ('received_from', 'receive_from', 'receives_from', 'receiving_from') }),

    Pattern("maturity-select", 0.7,
            { 'prev_V': ('select', 'selects', 'selected', 'selecting') }),

    Pattern("maturity-access", 0.7,
            { 'prev_V': ('access', 'accesses', 'accessed', 'accessing') }),

    Pattern("maturity-activate", 0.7,
            { 'prev_V': ('activate', 'activated', 'activates', 'activating') }),

    Pattern("maturity-detect", 0.7,
            { 'prev_V': ('detect', 'detects', 'detected', 'detecting') }),

    Pattern("maturity-obtain", 0.7,
            { 'prev_V': ('obtain', 'obtains', 'obtained', 'obtaining') }),

    Pattern("maturity-store", 0.7,
            { 'prev_V': ('store', 'stores', 'stored', 'storing') }),

    Pattern("maturity-generate", 0.7,
            { 'prev_V': ('generate', 'generates', 'generated', 'generating') }),
    ]


PROMISE_PATTERNS = [

    Pattern("promise-", 0.7, { '': ('', '', '', '') }),

    # this one appeared to be way too generic and return things like 'promising
    # method' and 'interesting approach'

    #Pattern("promise-promising", 0.7,
    #        { 'initial_J': ('promising', 'interesting') }),

    Pattern("promise-is_promising", 0.7,
            { 'next_n2': ('are_promising', 'is_promising'),
              'next_n3': ('is_a_promising', 'are_promising_.', 'is_promising_.',
                          'is_very_promising', 'are_very_promising',
                          'is_promising_for', 'are_promising_and') }),

    Pattern("promise-show_promise", 0.7,
            { 'next_n2': ('shows_promising', 'shows_promise', 'show_promising'),
              'next_n3': ('show_promising_results', 'shows_promising_results') }),

    Pattern("promise-with_of", 0.7,
            { 'next_n2': ('with_promising', 'of_promising'),
              'next_n3': ('with_promising_results') }),

    Pattern("promise-a_promising", 0.7,
            { 'next_n2': ('a_promising'),
              'next_n3': ('a_promising_new') }),
    ]

# Some promise patterns that may be used at some point, but not in their current
# shape:
#
#    features-prev_n2.txt:16 promise_for
#    features-prev_n2.txt:12 promise_of
#    features-prev_n2.txt:11 promising_new
#    features-prev_n2.txt:9  promising_in
#    features-prev_n3.txt:8  the_promise_of
#    features-prev_n3.txt:8  a_promising_new
#    features-prev_n3.txt:6  very_promising_for
#    features-prev_n3.txt:6  promising_approach_to
#    features-prev_n3.txt:6  promising_area_of



if __name__ == '__main__':

    # default values of options
    corpus = None
    language = 'en'
    patterns = 'MATURITY'
    output = None
    filelist = 'files.txt'
    pipeline_config = 'pipeline-default.txt'

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--language': language = val
        elif opt == '--filelist': filelist = val
        elif opt == '--patterns': patterns = val
        elif opt == '--output': output = val
        elif opt == '--pipeline': pipeline_config = val
        elif opt == '--verbose': VERBOSE = True

    check_output(corpus, output)

    if language == 'cn':
        load_chinese_patterns()

    if patterns == 'MATURITY':
        PATTERNS = MATURITY_PATTERNS
    elif patterns == 'PROMISE':
        PATTERNS = PROMISE_PATTERNS
    else:
        exit("ERROR: unknown pattern set '%s'" % patterns)

    # TODO: language should not be an option after step1_initialize since it is
    # associated with a corpus, should therefore also not be given to the config
    # object, but for now we keep it
    rconfig = RuntimeConfig(corpus, None, None, language, pipeline_config)

    matcher = Matcher(rconfig, filelist, output)
    matcher.pp()
    matcher.run()
