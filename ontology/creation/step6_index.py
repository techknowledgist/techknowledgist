"""

Script to build an index over files with document features.

Indexing is done on top of the results of the classifier. It does this by using
the --dataset option, which points to a dataset created by the classifier. For
convenience, it also relies on access to the classifier's phr_feats summary
files.

Much of the work on the batches involves building a large in-memory
datastructure to collect summary counts, therefore the batches are going to be
limited to a certain yet-to-be-determined size.

OPTIONS

   -l LANG     provides the language, one of ('en, 'de', 'cn'), default is 'en'.
   -t PATH     target directory, default is data/patents.
   -n INTEGER  number of documents to process.

   --collect-data
         run in batch mode to collect data from a set of documents.

   --build-index:
       Combine the results from available batches.

   --config FILENAME:
       File with pipeline configuration.

   --index-name STRING:
       Name of index directory being created (--build-index only).

   --dataset STRING:
       Classifier dataset to collect data from or indexer datasets that are to
       be combined into the index, in the letter case the value can be a unix
       filename pattern with '*', '?' and '[]'. Note that if you use wildcards
       in the string you need to surround them in quotes.

   --balance INTEGER:
       If this options is used with the --build-index option, the number of
       documents used per year is balanced by taking INTEGER to be the maximum
       number of documents that can be used for a given year. Note that this
       does not necesarily mean that we have a good balance since (i) we do not
       adjust for the size of documents and (ii) we could have a number smaller
       than INTEGER if the year simply only has a few documents.

   --verbose          set verbose printing to stdout
   --track-memory     use this to track memory usage
   --show-data        print available datasets, then exits
   --show-pipelines   print defined pipelines, then exits


Example for --collect-data:
$ python step6_index.py -t data/patents -l en --collect-data --dataset standard.001-020
$ python step6_index.py -t data/patents -l en --collect-data --dataset standard.021-040

Example for --build-index:
$ python step6_index.py -t data/patents -l en --build-index --index-name standard.idx --dataset 'standard.???-???' 

"""

import os, sys, time, shutil, getopt, codecs, resource, glob

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
from np_db import YearsDatabase, SummaryDatabase


VERBOSE = False
TRACK_MEMORY = False


def measure_memory_use(fun):
    """Print the increased memory use after the wrapped function exits."""
    def wrapper(*args):
        m1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result = fun(*args)
        m2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if TRACK_MEMORY:
            print "[%s] increase in memory use: %dMB" % (fun.__name__, (m2 - m1) / 1000)
        return result
    return wrapper


#### OPTION --collect-data

def run_collect_data(config, dataset):
    """Data collections proceeds off of a classify dataset, using the
    classify.features.doc_feats.txt and classify.features.phr_feats.txt files (or the file
    list and then get the files from the doc_feats and phr_feats datasets)."""
    data_dir = os.path.join(config.target_path, config.language, 'data')
    classify_dir = os.path.join(data_dir, 't2_classify', dataset)
    index_dir = os.path.join(data_dir, 'o1_index', dataset)
    generate_collect_info_files(config, dataset, index_dir, classify_dir)
    m1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t1 = time.time()
    collect_counts(classify_dir, index_dir)
    print_processing_statistics(index_dir, m1, t1)

def generate_collect_info_files(config, dataset, index_dir, classify_dir):
    """Copy information from t2_classify to o1_index data sets. In some cases the
    statistics can be different, overwrite the classifier values with the indexer values
    (for example for the git commit)."""
    ensure_path(index_dir)
    fh = open(os.path.join(index_dir, 'index.info.general.txt'), 'w')
    fh.write("$ python %s\n\n" % ' '.join(sys.argv))
    fh.write("dataset      =  %s\n" % dataset)
    fh.write("config_file  =  %s\n" % os.path.basename(config.pipeline_config_file))
    fh.write("git_commit   =  %s" % get_git_commit())
    for info_file in ('info.config.txt', 'info.filelist.txt'):
        shutil.copyfile(os.path.join(classify_dir, 'classify.' + info_file),
                        os.path.join(index_dir, 'index.' + info_file))

def collect_counts(classify_dir, index_dir):
    """Collect statistics from the phr_feats file(s) and the scores file and write them to
    files in the index directory."""
    term_statistics = {}
    feats_fh = codecs.open(os.path.join(classify_dir, 'classify.features.phr_feats.txt'))
    scores_fh = codecs.open(os.path.join(classify_dir, 'classify.MaxEnt.out.s2.y.nr'))
    summary_fh = codecs.open(os.path.join(index_dir, 'index.count.summary.txt'), 'w')
    years_fh = codecs.open(os.path.join(index_dir, 'index.count.years.txt'), 'w')
    expanded_fh = codecs.open(os.path.join(index_dir, 'index.count.expanded.txt'), 'w')
    print "[collect_statistics] reading scores"
    scores = load_scores(scores_fh)
    print "[collect_statistics] reading phr_feats"
    process_phr_feats(term_statistics, scores, feats_fh, expanded_fh, years_fh)
    print_summary_statistics(term_statistics, scores, summary_fh)

@measure_memory_use
def load_scores(scores_fh):
    """Return a scores object with the scores i scores_fh"""
    return Scores(scores_fh)

@measure_memory_use
def process_phr_feats(statistics, scores, feats_fh, expanded_fh, years_fh):
    """Repeatedly take the next document from the phr_feats summary file (where a document
    is a list of lines) and process the lines for each document."""
    fr = FeatureReader(feats_fh)
    years = {}
    while True:
        next_doc = fr.next_document()
        if not next_doc:
            break
        process_phr_feats_doc(statistics, years, scores, next_doc, expanded_fh)
    for year in sorted(years.keys()):
        years_fh.write("%s\t%d\n" % (year, years[year]))

def process_phr_feats_doc(statistics, years, scores, lines, expanded_fh):
    """Process the phr_feats lines for a document and write a counts line for each
    docid-year-term triple, including the score and the list of occurrences."""
    doc = {}
    for line in lines:
        (term, year, docid, feats, loc_feat) = parse_phr_feats_line(line)
        update_summary_statistics(statistics, docid, year, term, loc_feat)
        doc.setdefault(term,{})
        doc[term].setdefault(loc_feat, 0)
        doc[term][loc_feat] += 1
    years.setdefault(year,0)
    years[year] += 1
    for term in sorted(doc.keys()):
        locs = "\t".join(["%s %d" % (loc, count) for loc, count in doc[term].items()])
        score = scores.get_score(term, year, docid)
        expanded_fh.write("%s\t%s\t%s\t%s\t%s\n" % (docid, year, score, term, locs))

def update_summary_statistics(statistics, docid, year, term, loc_feat):
    statistics.setdefault(term,{})
    statistics[term].setdefault(year,{'scores': [], 'documents': {}, 'instances': 0,
                                      'section_counts': {}})
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
                print "[Scores.__init__] WARNING: duplicate score for '%s'" % term,
                print "in year %s for document %s" % (year, docid)
            self.scores[term][year][docid] = score

    def get_score(self, term, year, docid):
        try:
            score = self.scores[term][year][docid]
            return float(score)
        except KeyError:
            return 'None'

    def get_average_score(self, term, year):
        try:
            term_scores = self.scores[term][year].values()
            average_score = sum([float(s) for s in term_scores]) / len(term_scores)
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



#### OPTION --build-index

def run_build_index(config, index_name, dataset_exp, balance):
    """Build the index databases from a set of datasets, descirbed by the dataset_ep
    regular expression. Balance is not implemented yet, but could be used to limit the
    number of documents used for each year."""
    index_dir = os.path.join(config.target_path, config.language, 'data', 'o1_index')
    build_dir = os.path.join(index_dir, index_name)
    datasets = glob.glob(os.path.join(index_dir, dataset_exp))
    generate_build_info_files(config, index_name, datasets, balance, build_dir)
    build_years_index(build_dir, datasets)
    build_summary_index(build_dir, datasets)
    build_expanded_index(build_dir, datasets)

def generate_build_info_files(config, index_name, datasets, balance, build_dir):
    """Write files with information on the build."""
    ensure_path(build_dir)
    fh = open(os.path.join(build_dir, 'index.info.general.txt'), 'w')
    fh.write("$ python %s\n\n" % ' '.join(sys.argv))
    fh.write("config_file=%s\n" % os.path.basename(config.pipeline_config_file))
    fh.write("index_name=%s\n" % index_name)
    for ds in datasets:
        fh.write("dataset=%s\n" % ds)
    fh.write("balance=%d\n" % balance)
    fh.write("git_commit=%s" % get_git_commit())

def build_years_index(build_dir, datasets):
    """Add years to the database, not just the count but also a ratio (for
    example ,if 1990 has 20 document sut of a total of 100, then it gets the 0.2
    ratio (this is done in read_years, replacing the count with a <count, ratio>
    pair)."""
    db_file = os.path.join(build_dir, 'db-years.sqlite')
    stats_file = os.path.join(build_dir, 'index.stats.years.txt')
    years, document_count = read_years(datasets)
    print_years(years, document_count, stats_file)
    db = YearsDatabase(db_file)
    for year in years.keys():
        count, ratio = years[year]
        db.add(year, count, ratio)
    db.commit_and_close()

def read_years(datasets):
    """This is just to let the user see how many documents are involved and what the
    distributionover the years is."""
    years = {}
    total_count = 0
    for ds in datasets:
        for line in open(os.path.join(ds, 'index.count.years.txt')):
            year, count = line.strip().split("\t")
            count = int(count)
            years[year] = years.setdefault(year,0) + count
            total_count += count
    for year, count in years.items():
        years[year] = (count, float(count)/total_count)
    return years, total_count

def print_years(years, document_count, stats_file):
    with open(stats_file, 'w') as fh:
        fh.write("\nSize of combined datasets (in documents)\n\n")
        for y in sorted(years.keys()):
            fh.write("   %s  %6d  %.4f\n" % (y, years[y][0], years[y][1]))
        fh.write("\n   TOTAL %6d  %.4f\n\n" % (document_count, 1))


def build_summary_index(build_dir, datasets):

    db = SummaryDatabase(os.path.join(build_dir, 'db-summary.sqlite'))
    log = open(os.path.join(build_dir, 'index.stats.processing.txt'), 'w')
    for ds in datasets:
        t1 = time.time()
        fh = codecs.open(os.path.join(ds, 'index.count.summary.txt'), encoding='utf-8')
        for line in fh:
            fields = line.strip().split(u"\t")
            (term, year, score, doc_count, instance_count) = fields[:5]
            section_counts = fields[5:]
            if score == 'None':
                continue
            db.add_to_summary(term, year, float(score), int(doc_count), int(instance_count))
            db.add_to_sections(term, year, section_counts)
        print "[build_summary_index] added %s (%.2fs)" % (ds, time.time() - t1)
        log.write("Time used to add %s to summary:  %.2fs\n" % (ds, time.time() - t1))
    db.commit_and_close()


@measure_memory_use
def build_expanded_index(build_dir, datasets):
    """Add the individual scores to the histogram stored in the datase. Note
    that this actually updates the summary database so the name of this method
    is wrong. There are a few other things that this method could do, but many
    of them do not seem useful right now. One that is still in play is to simply
    get a table that stored all the documents in which a term exists. The
    approach below uses a dictionary to gather results before putting them into
    the database. Could choose to empty the thing every 1000 lines or so or
    after each dataset, but memory use should level of and is bound by the
    number of terms."""

    def update_score(terms, term, year, score):
        """Increment the term score. TODO: may want to use the array module here
        and initilize a 10-element integer array, check whether this is better
        memor-wise."""
        score = "%.2f" % float(score)
        score_range = score[-2]
        terms.setdefault((term, year), {})
        terms[(term, year)].setdefault(score_range, 0)
        terms[(term, year)][score_range] += 1

    terms = {}
    db = SummaryDatabase(os.path.join(build_dir, 'db-summary.sqlite'))
    for ds in datasets:
        t1 = time.time()
        fh = codecs.open(os.path.join(ds, 'index.count.expanded.txt'), encoding='utf-8')
        for line in fh:
            fields = line.strip().split(u"\t")
            (docid, year, score, term) = fields[:4]
            if score != 'None':
                update_score(terms, term, year, score)
    for (term, year) in terms.keys():
        scores = terms[(term, year)]
        db.add_scores(term, year, scores)
    db.commit_and_close()


#### UTILITIES

def print_processing_statistics(index_dir, m1, t1):
    m2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t2 = time.time()
    fh = open(os.path.join(index_dir, 'index.info.stats.txt'), 'w')
    fh.write("processing_time = %d\n" % (t2 - t1))
    fh.write("memory before = %dMB\n" % (m1 / 1000))
    fh.write("memory after = %dMB\n" % (m2 / 1000))


def read_opts():
    longopts = ['config=', 'collect-data', 'build-index', 'index-name=', 'dataset=', 
                'balance=', 'track-memory', 'verbose', 'show-data', 'show-pipelines']
    try:
        return getopt.getopt(sys.argv[1:], 'l:t:n:', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))


if __name__ == '__main__':

    # default values of options
    target_path, language = 'data/patents', 'en'
    collect_data, build_index = False, False
    index_name, dataset, balance = None, None, 9999999
    pipeline_config = 'pipeline-default.txt'
    show_data_p, show_pipelines_p = False, False

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '--collect-data': collect_data = True
        if opt == '--build-index': build_index = True
        if opt == '--index-name': index_name = val
        if opt == '--dataset': dataset = val
        if opt == '--balance': balance = int(val)
        if opt == '--show-data': show_data_p = True
        if opt == '--show-pipelines': show_pipelines_p = True
        if opt == '--verbose': VERBOSE = True
        if opt == '--track-memory': TRACK_MEMORY = True

    config = GlobalConfig(target_path, language, pipeline_config)
    if VERBOSE:
        config.pp()

    if show_data_p:
        show_datasets(target_path, language, config)
    elif show_pipelines_p:
        show_pipelines(target_path, language)
    elif collect_data:
        run_collect_data(config, dataset)
    elif build_index:
        run_build_index(config, index_name, dataset, balance)
