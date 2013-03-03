"""

Script to build an index over files with document features.

Indexing is done on top of the results of the classifier. It does this by using the
--dataset option, which points to a dataset created by the classifier. For convenience, it
also relies on access to the classifier's phr_feats summary files.

Much of the work on the batches involves building a large in-memory datastructure to
collect summary counts, therefore the batches are going to be limited to a certain
yet-to-be-determined size.

OPTIONS

    -l LANG     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -t PATH     --  target directory, default is data/patents
    -n INTEGER  --  number of documents to process

    --collect-data  --  run in batch mode to collect data from a set of documents
    --build-index   --  combine the results from available batches

    --dataset STRING   --  dataset to collect data from, taken from a t2_classify dataset
    --config FILENAME  --  file with pipeline configuration
    --files FILENAME   --  contains files to process, either for training or testing

    --verbose          --  set verbose printing to stdout
    --track-memory     --  use this to track memory usage
    --show-data        --  print available datasets, then exits
    --show-pipelines   --  print defined pipelines, then exits


Example for --batch:
$ python step6_index.py -t data/patents -l en --collect-data --dataset standard.batch-001-030 --verbose

Example for --build:
$

"""

import os, sys, shutil, getopt, codecs, resource

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from ontology.utils.batch import GlobalConfig
from ontology.utils.file import ensure_path
from ontology.utils.git import get_git_commit
from step2_document_processing import show_datasets, show_pipelines


def measure_memory_use(fun):
    """Print the increased memory use after the wrapped function exits."""
    def wrapper(*args):
        m1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result = fun(*args)
        m2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if track_memory:
            print "[%s] increase in memory use: %d" % (fun.__name__, m2 - m1)
        return result
    return wrapper

def run_collect_data(config, dataset):
    """Data collections proceeds off of a classify dataset, using the
    classify.features.doc_feats.txt and classify.features.phr_feats.txt files (or the file
    list and then get the files from the doc_feats and phr_feats datasets)."""
    data_dir = os.path.join(config.target_path, config.language, 'data')
    classify_dir = os.path.join(data_dir, 't2_classify', dataset)
    index_dir = os.path.join(data_dir, 'o1_index', dataset)
    generate_info_files(config, dataset, index_dir, classify_dir)
    collect_statistics(classify_dir, index_dir)

def generate_info_files(config, dataset, index_dir, classify_dir):
    """Copy statistics from t2_classify to o1_index data sets. In some cases the
    statistics can be different, overwrite the classifier values with the indexer values
    (for example for the git commit)."""
    ensure_path(index_dir)
    fh = open(os.path.join(index_dir, 'index.info.general.txt'), 'w')
    fh.write("$ python %s\n\n" % ' '.join(sys.argv))
    fh.write("dataset=%s\n" % dataset)
    fh.write("config_file=%s\n" % os.path.basename(config.pipeline_config_file))
    fh.write("git_commit=%s" % get_git_commit())
    for info_file in ('info.config.txt', 'info.filelist.txt'):
        shutil.copyfile(os.path.join(classify_dir, 'classify.' + info_file),
                        os.path.join(index_dir, 'index.' + info_file))

def collect_statistics(classify_dir, index_dir):
    """Collect statistics from the phr_feats file(s) and the scores file and write them to
    files in the index directory."""
    statistics = {}
    feats_fh = codecs.open(os.path.join(classify_dir, 'classify.features.phr_feats.txt'))
    scores_fh = codecs.open(os.path.join(classify_dir, 'classify.MaxEnt.out.s2.y.nr'))
    summary_fh = codecs.open(os.path.join(index_dir, 'index.count.summary.txt'), 'w')
    expanded_fh = codecs.open(os.path.join(index_dir, 'index.count.expanded.txt'), 'w')
    print "[collect_statistics] reading scores"
    scores = load_scores(scores_fh)
    print "[collect_statistics] reading phr_feats"
    process_phr_feats(statistics, scores, feats_fh, expanded_fh)
    print_summary_statistics(statistics, scores, summary_fh)

@measure_memory_use
def load_scores(scores_fh):
    """Return a scores object with the scores i scores_fh"""
    return Scores(scores_fh)

@measure_memory_use
def process_phr_feats(statistics, scores, feats_fh, expanded_fh):
    """Repeatedly take the next document from the phr_feats summary file (where a document
    is a list of lines) and process the lines for each document."""
    fr = FeatureReader(feats_fh)
    while True:
        next_doc = fr.next_document()
        if not next_doc:
            break
        process_phr_feats_doc(statistics, scores, next_doc, expanded_fh)

def process_phr_feats_doc(statistics, scores, lines, expanded_fh):
    """Process the phr_feats lines for a document and write a counts line for each
    docid-year-term triple, including the score and the list of occurrences."""
    doc = {}
    for line in lines:
        (term, year, docid, feats, loc_feat) = parse_phr_feats_line(line)
        update_summary_statistics(statistics, docid, year, term, loc_feat)
        doc.setdefault(term,{})
        doc[term].setdefault(loc_feat, 0)
        doc[term][loc_feat] += 1
    for term in sorted(doc.keys()):
        locs = "\t".join(["%s %d" % (loc, count) for loc, count in doc[term].items()])
        score = scores.get_score(term, year, docid)
        expanded_fh.write("%s\t%s\t%s\t%s\t%s\n" % (docid, year, score, term, locs))

def update_summary_statistics(statistics, docid, year, term, loc_feat):
    statistics.setdefault(term,{})
    statistics[term].setdefault(year,{'scores': [], 'documents': {}, 'instances': 0, 'section_counts': {}})
    statistics[term][year]['documents'][docid] = True
    statistics[term][year]['instances'] += 1
    statistics[term][year]['section_counts'].setdefault(loc_feat, 0)
    statistics[term][year]['section_counts'][loc_feat] += 1

def print_summary_statistics(statistics, scores, fh):
    for term in sorted(statistics.keys()):
        for year in statistics[term]:
            data = statistics[term][year]
            average_score = scores.get_average_score(term, year)
            fh.write("%s\t%s\t%s\t%d\t%d" % (term, year, average_score,
                                             len(data['documents']), data['instances']))
            for section, count in data['section_counts'].items():
                fh.write("\t%s %d" % (section, count))
            fh.write("\n")


class Scores(object):

    def __init__(self, scores_fh):
        self.scores = {}
        for line in scores_fh:
            identifier, score = line.strip().split("\t")
            (year, docid, term) = identifier.split('|', 2)
            term = term.replace('_', ' ')
            self.scores.setdefault(term, {})
            self.scores[term].setdefault(year, {})
            if self.scores[term][year].has_key(docid):
                print "[Scores.__init__] WARNING: duplicate score for '%s' in year %s for document %s" \
                    % (term, year, docid)
            self.scores[term][year][docid] = score

    def get_score(self, term, year, docid):
        try:
            score = self.scores[term][year][docid]
            return "%.4f" % float(score)
        except KeyError:
            return 'None'

    def get_average_score(self, term, year):
        try:
            term_scores = self.scores[term][year].values()
            average_score = sum([float(s) for s in term_scores]) / len(term_scores)
            average_score = "%.4f" % average_score
        except KeyError:
            average_score = 'None'
        except ZeroDivisionError:
            average_score = 'None'
        return average_score


class FeatureReader(object):

    """Interface to the phr_features summary file. You can either iterate over all the
    lines or ask for the next document. """

    ## TODO: this could be generalzied by passing in the function that picks the document
    ## identifier (or any other identifier) from the line, now it has a hard-coded call to
    ## get_docid_from_phr_feats_line()

    def __init__(self, feats_fh):
        self.fh = feats_fh
        self.buffer = None

    def __iter__(self):
        return self

    def next(self):
        """Returns the next line, which could be on the one-line buffer."""
        if self.buffer is not None:
            next_line = self.buffer
            self.buffer = None
            return next_line
        else:
            next = self.fh.readline()
            if next:
                return next
            else:
                raise StopIteration

    def next_document(self):
        """Return a list of lines, where all lines have the same document
        identifier. Return an empty list when there are no more documents."""
        lines = []
        try:
            next_line = self.next()
            #print '=>', next_line,
            lines.append(next_line)
            docid = get_docid_from_phr_feats_line(next_line)
            self.current_document = docid
            while True:
                next_line = self.next()
                #print '+>', next_line,
                if next_line is None:
                    return lines
                docid = get_docid_from_phr_feats_line(next_line)
                if not docid == self.current_document:
                    #print '-> putting back line'
                    self.buffer = next_line
                    return lines
                else:
                    lines.append(next_line)
        except StopIteration:
            return lines


def parse_phr_feats_line(line):
    """Parse a line from the phr_feats file and return a tuple with term, year, docid,
    features and locfeat. For the docid, the count at the end is stripped, for example
    'US09123404.xml_217' is turned into 'US09123404.xml'."""
    vector = line.strip().split("\t")
    (docid, year, term) = vector[0:3]
    docid = docid.rstrip('0123456789')[:-1]
    feats = vector[3:]
    loc_feats = [f[12:] for f in feats if f.startswith('section_loc=')]
    loc_feat = loc_feats[0] if loc_feats else None
    return (term, year, docid, feats, loc_feat)

def get_docid_from_phr_feats_line(line):
    """Return the docid from a phr_feats line."""
    return parse_phr_feats_line(line)[2]



def build_index(config, dataset):
    """In this case, dataset is actually a regular expression that can match many
    datasets, or a comma-separated list of regular expressions"""
    pass



def read_opts():
    longopts = ['config=', 'collect-data', 'build-index', 'version=', 'dataset=', 
                'track-memory', 'verbose', 'show-data', 'show-pipelines']
    try:
        return getopt.getopt(sys.argv[1:], 'l:t:n:', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))



if __name__ == '__main__':

    # default values of options
    target_path, language = 'data/patents', 'en'
    dataset = None
    collect_data = False
    build_index = False
    pipeline_config = 'pipeline-default.txt'
    verbose, track_memory = False, False
    show_data_p, show_pipelines_p = False, False

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '--dataset': dataset = val
        if opt == '--collect-data': collect_data = True
        if opt == '--build-index': build_index = True
        if opt == '--show-data': show_data_p = True
        if opt == '--show-pipelines': show_pipelines_p = True
        if opt == '--verbose': verbose = True
        if opt == '--track-memory': track_memory = True

    config = GlobalConfig(target_path, language, pipeline_config)
    if verbose:
        config.pp()

    if show_data_p:
        show_datasets(target_path, language, config)
    elif show_pipelines_p:
        show_pipelines(target_path, language)

    elif collect_data:
        run_collect_data(config, dataset)

    elif build_index:
        run_build_index(config, dataset)
