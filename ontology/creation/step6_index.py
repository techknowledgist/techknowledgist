"""

Script to build an index over files with document features.

Indexing is done on top of the results of the classifier. It does this by using
the --dataset option, which points to a dataset created by the classifier.

Much of the work on the batches involves building a large in-memory data
structure to collect term counts, therefore the batches are going to be limited
to a certain yet-to-be-determined size.



OPTIONS

   --language en|cn|de  provides the language, default is 'en'
   --corpus PATH        target directory

   --build-index:
       Add term data from a dataset to the index.

   --analyze-index:
       Analyze the contents of the index in various ways.

   --index-name STRING:
       Name of index directory being created or analyzed.

   --dataset STRING:
       Classifier dataset to collect data from or indexer datasets that are to
       be combined into the index, in the latter case the value can be a unix
       filename pattern with '*', '?' and '[]'. Note that if you use wildcards
       in the string you need to surround the string in quotes.

   --balance INTEGER:
       If this options is used with the --build-index option, the number of
       documents used per year is balanced by taking INTEGER to be the maximum
       number of documents that can be used for a given year. Note that this
       does not necesarily mean that we have a good balance since (i) we do not
       adjust for the size of documents and (ii) we could have a number smaller
       than INTEGER if the year simply only has a few documents.

   --verbose          set verbose printing to stdout
   --track-memory     use this to track memory usage


Example for --build-index:
$ python step6_index.py --build-index --corpus data/patents/en --index-name standard.idx --dataset 'standard.batch1'

Example for --analyze-index:
$ python step6_index.py --analyze-index --corpus data/patents/en --index-name standard.idx

"""

import os, sys, time, shutil, getopt, codecs, resource, glob, StringIO

import config
import path

from ontology.utils.batch import RuntimeConfig, show_datasets, show_pipelines
from ontology.utils.batch import find_input_dataset, check_file_availability
from ontology.utils.file import ensure_path, open_input_file
from ontology.utils.git import get_git_commit
from ontology.utils.html import HtmlDocument
from np_db import InfoDatabase, YearsDatabase, TermsDatabase, SummaryDatabase


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

def run_collect_data(rconfig, dataset):
    """Data collections proceeds off of a classify dataset, using the
    classify.features.doc_feats.txt and classify.features.phr_feats.txt files
    (or the file list and then get the files from the doc_feats and phr_feats
    datasets)."""
    data_dir = os.path.join(rconfig.target_path, 'data')
    classify_dir = os.path.join(data_dir, 't2_classify', dataset)
    index_dir = os.path.join(data_dir, 'o1_index', dataset)
    generate_collect_info_files(rconfig, dataset, index_dir, classify_dir)
    m1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t1 = time.time()
    collect_counts(classify_dir, index_dir)
    print_processing_statistics(index_dir, m1, t1)

def generate_collect_info_files(rconfig, dataset, index_dir, classify_dir):
    """Copy information from t2_classify to o1_index data sets. In some cases
    the statistics can be different, overwrite the classifier values with the
    indexer values (for example for the git commit)."""
    ensure_path(index_dir)
    fh = open(os.path.join(index_dir, 'index.info.general.txt'), 'w')
    fh.write("$ python %s\n\n" % ' '.join(sys.argv))
    fh.write("dataset      =  %s\n" % dataset)
    fh.write("config_file  =  %s\n" % os.path.basename(rconfig.pipeline_config_file))
    fh.write("git_commit   =  %s" % get_git_commit())
    for info_file in ('info.config.txt', 'info.filelist.txt'):
        shutil.copyfile(os.path.join(classify_dir, 'classify.' + info_file),
                        os.path.join(index_dir, 'index.' + info_file))

def collect_counts(classify_dir, index_dir):
    """Collect statistics from the phr_feats file(s) and the scores file and
    write them to files in the index directory."""
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
    """Return a scores object with the scores in scores_fh"""
    return Scores(scores_fh)

@measure_memory_use
def process_phr_feats(statistics, scores, feats_fh, expanded_fh, years_fh):
    """Repeatedly take the next document from the phr_feats summary file (where
    a document is a list of lines) and process the lines for each document."""
    self.input_dataset = find_input_dataset(self.rconfig, 'd3_phr_feats')
    check_file_availability(self.input_dataset, self.file_list)
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

    """Interface to scores for terms in each year. Loads a file with basename
    classify.MaxEnt.out.s2.y.nr and provides access to the scores therein."""

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

    """Interface to the phr_features summary file. You can either iterate over
    all the lines or ask for the next document."""

    ## TODO: this could be generalized by passing in the function that picks the
    ## document identifier (or any other identifier) from the line, now it has a
    ## hard-coded call to get_docid_from_phr_feats_line()

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
    """Parse a line from the phr_feats file and return a tuple with term, year,
    docid, features and locfeat. For the docid, the count at the end is
    stripped, for example 'US09123404.xml_217' is turned into 'US09123404.xml'."""
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
    """Build the index databases from a set of datasets, described by the dataset_exp
    regular expression. Balance is not implemented yet, but could be used to limit the
    number of documents used for each year."""
    index_dir = os.path.join(rconfig.target_path, 'data', 'o1_index')
    build_dir = os.path.join(index_dir, index_name)
    datasets = glob.glob(os.path.join(index_dir, dataset_exp))
    generate_build_info_files(rconfig, index_name, datasets, balance, build_dir)
    build_years_index(build_dir, datasets)
    build_summary_index(build_dir, datasets)
    build_expanded_index(build_dir, datasets)

def generate_build_info_files(rconfig, index_name, datasets, balance, build_dir):
    """Write files with information on the build."""
    ensure_path(build_dir)
    fh = open(os.path.join(build_dir, 'index.info.general.txt'), 'w')
    fh.write("$ python %s\n\n" % ' '.join(sys.argv))
    fh.write("config_file  =  %s\n" % os.path.basename(rconfig.pipeline_config_file))
    fh.write("index_name   =  %s\n" % index_name)
    for ds in datasets:
        fh.write("dataset      =  %s\n" % ds)
    fh.write("balance      =  %d\n" % balance)
    fh.write("git_commit   =  %s" % get_git_commit())

def build_years_index(build_dir, datasets):
    """Add years to the database, not just the count but also a ratio (for example,
    if 1990 has 20 documents out of a total of 100, then it gets the 0.2 ratio (this
    is done in read_years, replacing the count with a <count, ratio> pair)."""
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
    """This is to expose how many documents are involved and what the distribution over
    the years is. First collect all the counts for each dataset, then calculate the
    distribution."""
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
    """Add sumary information on term-year pairs to index summary database."""
    sdb = SummaryDatabase(os.path.join(build_dir, 'db-summary.sqlite'))
    tdb = TermsDatabase(os.path.join(build_dir, 'db-terms.sqlite'))
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
            sdb.add_to_summary(term, year, float(score), int(doc_count), int(instance_count))
            sdb.add_to_sections(term, year, section_counts)
            tdb.add(term, float(score), int(doc_count), int(instance_count))
        print "[build_summary_index] added %s (%.2fs)" % (ds, time.time() - t1)
        log.write("Time used to add %s to summary:  %.2fs\n" % (ds, time.time() - t1))
        fh.close()
    log.close()
    sdb.commit_and_close()
    tdb.commit_and_close()


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
        and initialize a 10-element integer array, check whether this is better
        memory-wise."""
        score = "%.2f" % float(score)
        score_range = score[-2]
        terms.setdefault((term, year), {})
        terms[(term, year)].setdefault(score_range, 0)
        terms[(term, year)][score_range] += 1

    terms = {}
    db = SummaryDatabase(os.path.join(build_dir, 'db-summary.sqlite'))
    for ds in datasets:
        t1 = time.time()
        fh = codecs.open(os.path.join(ds, 'index.count.expanded.txt'),
                         encoding='utf-8')
        for line in fh:
            fields = line.strip().split(u"\t")
            (docid, year, score, term) = fields[:4]
            if score != 'None':
                update_score(terms, term, year, score)
    for (term, year) in terms.keys():
        scores = terms[(term, year)]
        db.add_scores(term, year, scores)
    db.commit_and_close()


    
### OPTION --build-index

def run_add_dataset_to_index(corpus, index_name, dataset):
    """Adds the data in dataset to index_name, creating the index if it does not
    yet exist."""
    idx = Index(corpus, index_name, dataset)
    idx.add_technology_scores()
    idx.finish()


class Index(object):

    def __init__(self, corpus, index_name, dataset):
        self.corpus = corpus
        self.index_name = index_name
        self.dataset = dataset
        self.idx_dir = os.path.join(corpus, 'data', 'o1_index', index_name)
        self.classify_dir = os.path.join(corpus, 'data', 't2_classify', dataset)
        ensure_path(self.idx_dir)
        self.db_info = InfoDatabase(self.idx_dir, 'db-info.sqlite')
        self.db_years = YearsDatabase(self.idx_dir, 'db-years.sqlite')
        self.db_terms = TermsDatabase(self.idx_dir, 'db-terms.sqlite')
        self.pp()
        self.check()

    def _update_info_files(self):
        """Write files with information on the build."""
        fh = open(os.path.join(self.idx_dir, 'index.info.general.txt'), 'a')
        fh.write("$ python %s\n\n" % ' '.join(sys.argv))
        fh.write("index_name   =  %s\n" % self.index_name)
        fh.write("dataset      =  %s\n" % self.dataset)
        fh.write("git_commit   =  %s\n" % get_git_commit())
        fh.write("timestamp    =  %s\n\n" % time.strftime('%Y%m%d-%H%M%S'))

    def check(self):
        if self.dataset in self.db_info.list_datasets():
            exit("WARNING: dataset %s already loaded" % self.dataset)

    def add_technology_scores(self):
        fname = os.path.join(self.classify_dir, 'classify.MaxEnt.out.s2.y.nr')
        fh = open_input_file(fname)
        years = {}
        terms = {}
        print "Collecting terms..."
        for line in fh:
            (id, score) = line.rstrip().split("\t")
            (year, doc, term) = id.split("|", 2)
            score = float(score)
            self._update_years_idx(year, doc, years)
            self._update_terms_idx(term, year, score, terms)
        print "Updating databases..."
        self._update_years_db(years)
        self._update_terms_db(terms)

    def _update_years_idx(self, year, doc, years):
        years.setdefault(year, {})[doc] = True

    def _update_terms_idx(self, term, year, score, terms):
        if filter_term(term):
            return
        idx = get_bin_index(score)
        terms.setdefault(term, {})
        if terms[term].has_key(year):
            count = terms[term][year]['doc_count']
            old_average = terms[term][year]['score']
            new_average = (old_average * count + score) / (count + 1)
            terms[term][year]['doc_count'] = count + 1
            terms[term][year]['score'] = new_average
            terms[term][year]['bins'][idx] += 1
            #print old_average, count, score, new_average, year, term
        else:
            terms[term][year] = { 'score': score,
                                  'doc_count': 1,
                                  'bins': [0,0,0,0,0,0,0,0,0,0] }
            terms[term][year]['bins'][idx] = 1

    def _update_years_db(self, years):
        for year in years:
            current_count = self.db_years.get_count(year)
            if current_count == 0:
                self.db_years.add(year, len(years[year]))
            else:
                self.db_years.update(year, current_count + len(years[year]))

    def _update_terms_db(self, terms):
        count = 0
        step = 50000
        t1 = time.time()
        for term in terms:
            for year in terms[term]:
                count += 1
                score = terms[term][year]['score']
                doc_count = terms[term][year]['doc_count']
                bins = terms[term][year]['bins']
                self.db_terms.add(term, year, score, doc_count, bins)
                if count % step == 0:
                    t2 = time.time() 
                    print "Inserted/updated %d rows in %d seconds" % (step, t2 - t1)
                    t1 = t2

    def finish(self):
        self.db_info.add_dataset(self.dataset)
        self.db_info.commit_and_close()
        self.db_years.commit_and_close()
        self.db_terms.commit_and_close()
        self._update_info_files()

    def pp(self):
        print "\nINDEX %s on %s" % (self.index_name, self.corpus)
        print "   datasets:", self.db_info.list_datasets()
        print

def filter_term(term):
    """used to filter out the obvious crap. Do not allow (i) terms with spaces,
    (ii) terms with three or more hyphens/underscores in a row, and (iii) terms
    that ar elonger than 75 characters. The latter avoids loading what could be
    huge outliers."""
    # TODO: character limit is not optimal for Chinese
    if term.find(' ') > -1: return True
    if term.find('---') > -1: return True
    if term.find('___') > -1: return True
    return len(term) > 75

def get_bin_index(score):
    if score < 0.1: idx = 0
    elif score < 0.2: idx = 1
    elif score < 0.3: idx = 2
    elif score < 0.4: idx = 3
    elif score < 0.5: idx = 4
    elif score < 0.6: idx = 5
    elif score < 0.7: idx = 6
    elif score < 0.8: idx = 7
    elif score < 0.9: idx = 8
    elif score <= 1.0: idx = 9
    else:
        idx = None
        print "WARNING: unexpected score:", type(score), score
    return idx



#### OPTION --analyze-index

def run_analyze_index(rconfig, index_name, min_docs, min_score):
    index_dir = os.path.join(rconfig.target_path, 'data', 'o1_index')
    db_file = os.path.join(index_dir, index_name, 'db-summary.sqlite')
    analyzer = IndexAnalyzer(db_file, min_docs, min_score)
    analyzer.analyze_terms()
    analyzer.write_html()
    analyzer.close()


class IndexAnalyzer(object):

    def __init__(self, db_file, min_docs, min_score):
        self.db = SummaryDatabase(db_file)
        self.db_file = db_file
        self.index_dir = os.path.dirname(db_file)
        self.html_dir = os.path.join(self.index_dir, 'html')
        self.min_docs = min_docs
        self.min_score = min_score

    def close(self):
        self.db.close()

    def analyze_terms(self):
        terms = self.select_terms()
        print "[analyze_terms] number of terms selected:", len(terms)
        self.terms = []
        term_id = 0
        for (term, score, docs, instances) in terms:
            term_id += 1
            raw_data = self.db.get_term_data(term)
            term = Term(term, term_id, score, docs, instances, raw_data, self.index_dir)
            self.terms.append(term)

    def select_terms(self):
        """Select and return all terms that match the user specification on
        frequency and technology score."""
        db = TermsDatabase(os.path.join(self.index_dir, 'db-terms.sqlite'))
        return db.select_terms(self.min_docs, self.min_score)

    def write_html(self):
        ensure_path(self.html_dir)
        self.write_index_file()
        for term in self.terms:
            term_file = os.path.join(self.html_dir, "%05d.html" % term.id)
            term_fh = codecs.open(term_file, 'w', encoding='utf-8')
            term.generate_html(fh=term_fh)

    def write_index_file(self):
        index_file = os.path.join(self.html_dir, 'index.html')
        fh = codecs.open(index_file, 'w', encoding='utf-8')
        doc = HtmlDocument(fh, 'Term Browser')
        doc.add_paragraph(None,
                          "Terms that occur in %s or more documents" % self.min_docs +
                          " and that have a technology score of %.2f " % self.min_score +
                          "or higher")
        doc.add_raw('<blockquote>')
        table = doc.add_table(class_name='indent')
        table.add_row(('&nbsp;',), ('term',), ('score',), ('documents',), ('instances',))
        for term in self.terms:
            table.add_row(
                ('right', term.id,),
                ('left', "<a href=%05d.html>%s</a>\n" % (term.id, term.term)),
                ('right', "%.2f" % term.average_score),
                ('right', "%d" % term.document_count),
                ('right', "%d" % term.instance_count))
        doc.add_raw('</blockquote>')
        doc.print_html()


class Term(object):

    def __init__(self, term, term_id, score, docs, insts, raw_data, directory):
        """Put the summary data on top level variables and stroe the raw data
        from the database."""
        self.term = term
        self.id = term_id
        self.average_score = score
        self.document_count = docs
        self.instance_count = insts
        self.raw_data = raw_data
        self.index_dir = directory
        self._check_counts()
        self._analyze()

    def _check_counts(self):
        """This is a sanity check that compares the summary statistics to the
        ones derived from the raw data."""
        document_count = sum([r[3] for r in self.raw_data])
        instance_count = sum([r[4] for r in self.raw_data])
        average_score = sum([r[2] * r[3] for r in self.raw_data]) / self.document_count
        if not fequal(document_count, self.document_count):
            print 'doc_count', document_count, self.document_count
        if not fequal(instance_count, self.instance_count):
            print 'ins_count', instance_count, self.instance_count
        if not fequal(average_score, self.average_score):
            print 'avg_score', average_score, self.average_score

    def _analyze(self):
        self.year_scores = {}
        self.total_scores = {}
        self._collect_scores()
        self._normalize_scores()

    def _collect_scores(self):
        """Get the scores from the raw data."""
        for row in self.raw_data:
            year = row[1]
            # keep the number of documents, the number of instances and the raw
            # distribution data
            self.year_scores[year] = [row[3], row[4], row[5:]]
        self.total_scores = [self.document_count, self.instance_count, [0] * 10]
        for year_data in self.raw_data:
            year_scores = year_data[5:]
            for i in range(10):
                self.total_scores[2][i] += year_scores[i]

    def _normalize_scores(self):
        """Normalize distribution of total scores and year scores."""
        for i in range(10):
            self.total_scores[2][i] = (self.total_scores[2][i] /
                                       float(self.document_count))
        for year, scores in self.year_scores.items():
            total = scores[0]
            distribution = list(scores[2])
            for i in range(len(distribution)):
                distribution[i] = (distribution[i] / float(total))
            self.year_scores[year][2] = distribution

    def generate_html(self, fh=sys.stdout):

        doc = HtmlDocument(fh, "Term Browser on '%s'" % self.term)
        doc.add_style(".graph", 'margin-left: 20px', 'padding: 10px',
                      'background-color: lightyellow')
        doc.add_style(".boxed", 'border: thin dotted black')
        doc.add_style(".small", 'font-size: 12px', 'width: 400px')

        doc.add_h2(None, self.term)

        summary_table = doc.add_table(class_name='indent')
        summary_table.add_row(('document count',), ('right', self.document_count))
        summary_table.add_row(('instance count',), ('right', self.instance_count))
        summary_table.add_row(('technology score',), ('right', "%.2f" % self.average_score))
        
        doc.add_paragraph(None, "Distribution of technology scores")
        scores_table = doc.add_table(class_name='indent', border=0)
        graph = Graph(self.term, 'TOTAL', self.total_scores[2])
        scores_table.add_row(("<pre class='graph boxed'>%s</pre>" % graph,))
        
        for year in sorted(self.year_scores.keys()):
            doc_count, term_count, scores = self.year_scores[year]
            doc.add_paragraph(None, "Distribution for %s (%d documents, %d instances)"
                              %  (year, doc_count, term_count))
            year_table = doc.add_table(class_name='indent', border=0)
            graph = Graph(self.term, year, scores)
            year_table.add_row(("<pre class='graph boxed'>%s</pre>" % graph,))

        doc.print_html()


    def draw_graphs(self, fh=sys.stdout):
        for year in sorted(self.year_scores.keys()):
            fh.write("\n%s - %s\n\n" % (year, self.term))
            doc_count, term_count, scores = self.year_scores[year]
            graph = Graph(self.term, year, scores).draw(fh=fh, indent='   ')
        fh.write("\n%s - %s\n\n" % ('TOTAL', self.term))
        Graph(self.term, 'TOTAL', self.total_scores[2]).draw(fh=fh, indent='   ')

    def pp(self):
        print "\n<<<%s>>>\n" % self.term
        print "Total documents: %4d" % self.document_count
        print "Total instances: %4d" % self.instance_count
        print "\nDistribution:\n"
        for year in sorted(self.year_scores.keys()):
            doc_count, term_count, scores = self.year_scores[year]
            print "   %s   %6d %5d   [%s]" % \
                  (year, term_count, doc_count,
                   ' '.join(["%.2f" % score for score in scores]))
        print "\n   TOTAL  %6d %5d   [%s]\n" % \
              (self.instance_count,
               self.document_count,
               ' '.join(["%.2f" % score for score in self.total_scores[2]]))



class Graph(object):

    """A Graph is initialized with a set of values. It's only task is to write these in a
    graph format to an output stream. The implementation is geared towards the graph you
    would draw to show the distribution of technology scores. For example, it assumes an
    x-axis with 10 fixed values (0.0 through 0.9). It should be generalized so we can also
    use it for distribution over years."""

    def __init__(self, term, year, term_data):
        self.term = term
        self.year = year
        self.data = term_data

    def __str__(self):
        string = StringIO.StringIO()
        self.draw(fh=string)
        return string.getvalue()
    
    def draw(self, graph_height=10, fh=sys.stdout, indent=""):
        graph_data = [int(round(i * graph_height)) for i in self.data]
        for i in reversed(range(graph_height)):
            y_value = i + 1
            fh.write("%s%.2f |" % (indent, y_value / float(graph_height)))
            for value in graph_data:
                if value >= y_value:
                    fh.write(' *** ')
                else:
                    fh.write('     ')
            fh.write("\n")
        fh.write("%s     +%s\n%s      " % (indent, '-' * 50, indent))
        for i in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            fh.write(" %.1f " % i)
        fh.write("\n")


#### UTILITIES

def fequal(float1, float2):
    """Test equality of two floats up to the 12th decimal."""
    return abs(float1-float2) < 1E-12

def print_processing_statistics(index_dir, m1, t1):
    m2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t2 = time.time()
    fh = open(os.path.join(index_dir, 'index.info.stats.txt'), 'w')
    fh.write("processing_time  =  %d\n" % (t2 - t1))
    fh.write("memory before    =  %dMB\n" % (m1 / 1000))
    fh.write("memory after     =  %dMB\n" % (m2 / 1000))

def read_opts():
    longopts = ['corpus=', 'language=', 'build-index', 'analyze-index',
                'index-name=', 'dataset=', 'balance=', 'track-memory', 'verbose']
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))




if __name__ == '__main__':

    # default values of options
    corpus, language = 'data/patents', 'en'
    build_index, analyze_index = False, False
    index_name, dataset, balance = None, None, 9999999

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--language': language = val
        if opt == '--corpus': corpus = val
        if opt == '--build-index': build_index = True
        if opt == '--analyze-index': analyze_index = True
        if opt == '--index-name': index_name = val
        if opt == '--dataset': dataset = val
        #if opt == '--balance': balance = int(val)
        if opt == '--verbose': VERBOSE = True
        #if opt == '--track-memory': TRACK_MEMORY = True

    if build_index:
        run_add_dataset_to_index(corpus, index_name, dataset)
    elif analyze_index:
        run_analyze_index(rconfig, index_name, min_docs, min_score)
