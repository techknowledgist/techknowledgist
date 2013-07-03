"""

Script to build an index over files with document features.

Indexing is done on top of the results of the classifier. It does this by using
the --dataset option, which points to a dataset created by the classifier.

Much of the work on the batches involves building a large in-memory data
structure to collect term counts, therefore the batches are going to be limited
in size size, this size appears to be around 25K patents, in which case the
in-memory datastructure takes up about 2-3Gb.


OPTIONS

   --corpus PATH:
       Corpus directory.

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

   --min-docs INT:
       Number of documents in which a term accurs, filter on term analysis.

   --min-score FLOAT:
       Minimum tech score, filter on terms being analyzed.

   --verbose          set verbose printing to stdout
   --track-memory     use this to track memory usage


Example for --build-index:
$ python step6_index.py --build-index --corpus data/patents/en --index-name standard.idx --dataset 'standard.batch1'

Example for --analyze-index:
$ python step6_index.py --analyze-index --corpus data/patents/en --index-name standard.idx --min-docs 100 --min-score 0.7

"""

import os, sys, time, shutil, getopt, codecs, resource, glob, StringIO

import config
import path

from ontology.utils.batch import RuntimeConfig, show_datasets, show_pipelines
from ontology.utils.batch import find_input_dataset, check_file_availability
from ontology.utils.file import ensure_path, open_input_file
from ontology.utils.git import get_git_commit
from ontology.utils.html import HtmlDocument
from np_db import InfoDatabase, YearsDatabase, TermsDatabase


VERBOSE = False
TRACK_MEMORY = False


def add_dataset_to_index(corpus, index_name, dataset):
    """Adds the data in dataset to index_name, creating the index if it does not
    yet exist."""
    idx = Index(corpus, index_name)
    idx.add_dataset(dataset)
    idx.finish()

def analyze_terms(corpus, index_name, min_docs, min_score):
    idx = Index(corpus, index_name)
    #db_file = os.path.join(index_dir, index_name, 'db-summary.sqlite')
    #analyzer = IndexAnalyzer(db_file, min_docs, min_score)
    #analyzer.analyze_terms()
    #analyzer.write_html()
    #analyzer.close()




class Index(object):

    def __init__(self, corpus, index_name):
        self.corpus = corpus
        self.index_name = index_name
        self.idx_dir = os.path.join(corpus, 'data', 'o1_index', index_name)
        ensure_path(self.idx_dir)
        self.db_info = InfoDatabase(self.idx_dir, 'db-info.sqlite')
        self.db_years = YearsDatabase(self.idx_dir, 'db-years.sqlite')
        self.db_terms = {}
        self.pp()

    def add_dataset(self, dataset):
        self._check_dataset(dataset)
        self.dataset = dataset
        logfile = "index.log.dataset.%s.txt" % self.dataset
        self.log = open(os.path.join(self.idx_dir, logfile), 'w')
        self.classify_dir = os.path.join(corpus, 'data', 't2_classify', dataset)
        fname = os.path.join(self.classify_dir, 'classify.MaxEnt.out.s2.y.nr')
        fh = open_input_file(fname)
        years = {}
        terms = {}
        self.log.write("$ python %s\n\n" % ' '.join(sys.argv))
        self._write_message("Collecting terms...")
        count = 0
        t1 = time.time()
        step = 100000
        for line in fh:
            count += 1
            #if count > 100000: break
            if count % step == 0:
                t2 = time.time()
                self._write_message(
                    "   loaded %s classifier lines in %.2f seconds (%sK done)" 
                    % (step, t2 - t1, count / 1000))
                t1 = t2
            (id, score) = line.rstrip().split("\t")
            (year, doc, term) = id.split("|", 2)
            score = float(score)
            self._update_years_idx(year, doc, years)
            self._update_terms_idx(term, year, score, terms)
        self._write_message("Updating databases...")
        self._update_years_db(years)
        self._update_terms_db(terms)

    def finish(self):
        self.db_info.add_dataset(self.dataset)
        self.db_info.commit_and_close()
        self.db_years.commit_and_close()
        for year in sorted(self.db_terms.keys()):
            self.db_terms[year].commit_and_close()
        self._update_info_files()

    def pp(self):
        print "\nINDEX %s on %s" % (self.index_name, self.corpus)
        print "   datasets:", self.db_info.list_datasets()
        print

    def _check_dataset(self, dataset):
        if dataset in self.db_info.list_datasets():
            exit("WARNING: dataset %s already loaded" % dataset)

    def _update_years_idx(self, year, doc, years):
        years.setdefault(year, {})[doc] = True

    def _update_terms_idx(self, term, year, score, terms):
        if filter_term(term):
            return
        idx = get_bin_index(score)
        terms.setdefault(year, {})
        if terms[year].has_key(term):
            count = terms[year][term]['doc_count']
            old_average = terms[year][term]['score']
            new_average = (old_average * count + score) / (count + 1)
            terms[year][term]['doc_count'] = count + 1
            terms[year][term]['score'] = new_average
            terms[year][term]['bins'][idx] += 1
            #print old_average, count, score, new_average, year, term
        else:
            terms[year][term] = { 'score': score,
                                  'doc_count': 1,
                                  'bins': [0,0,0,0,0,0,0,0,0,0] }
            terms[year][term]['bins'][idx] = 1

    def _update_years_db(self, years):
        for year in years:
            current_count = self.db_years.get_count(year)
            if current_count == 0:
                self.db_years.add(year, len(years[year]))
            else:
                self.db_years.update(year, current_count + len(years[year]))

    def _update_terms_db(self, terms):
        count = 0
        step = 100000
        t1 = time.time()
        for year in sorted(terms.keys()):
            db_file = "db-terms-%s.sqlite" % year
            self._write_message("Inserting into %s..." % db_file)
            self.db_terms[year] = TermsDatabase(self.idx_dir, db_file)
            for term in terms[year]:
                count += 1
                score = terms[year][term]['score']
                doc_count = terms[year][term]['doc_count']
                bins = terms[year][term]['bins']
                self.db_terms[year].add(term, score, doc_count, bins)
                if count % step == 0:
                    t2 = time.time()
                    self._write_message(
                        "   inserted/updated %d rows in %.2f seconds (done %dK)" 
                        % (step, t2 - t1, count / 1000))
                    t1 = t2
            self._write_message("   inserts: %6d" % self.db_terms[year].inserts)
            self._write_message("   updates: %6d" % self.db_terms[year].updates)

    def _update_info_files(self):
        """Write files with information on the build."""
        fh = open(os.path.join(self.idx_dir, 'index.info.general.txt'), 'a')
        fh.write("$ python %s\n\n" % ' '.join(sys.argv))
        fh.write("index_name   =  %s\n" % self.index_name)
        fh.write("dataset      =  %s\n" % self.dataset)
        fh.write("git_commit   =  %s\n" % get_git_commit())
        fh.write("timestamp    =  %s\n\n" % time.strftime('%Y%m%d-%H%M%S'))

    def _write_message(self, message):
        print message
        self.log.write(message + "\n")
        self.log.flush()


class IndexAnalyzer(object):

    def __init__(self, db, min_docs, min_score):
        self.db = db
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

def filter_term(term):
    """Filter out some obvious crap. Do not allow (i) terms with spaces, (ii)
    terms with three or more hyphens/underscores in a row, and (iii) terms that
    ar elonger than 75 characters. The latter avoids loading what could be huge
    outliers."""
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
                'index-name=', 'dataset=', 'balance=', 'track-memory', 'verbose',
                'min-docs=', 'min-score=']
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))




if __name__ == '__main__':

    # default values of options
    corpus, language = None, 'en'
    build_index, analyze_index = False, False
    index_name, dataset, balance = None, None, 9999999
    min_docs, min_score = 100, 0.7
    
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--build-index': build_index = True
        if opt == '--analyze-index': analyze_index = True
        if opt == '--corpus': corpus = val
        if opt == '--index-name': index_name = val
        if opt == '--dataset': dataset = val
        if opt == '--min-docs': mid_docs = int(val)
        if opt == '--min-score': dataset = float(val)
        #if opt == '--balance': balance = int(val)
        if opt == '--verbose': VERBOSE = True
        if opt == '--track-memory': TRACK_MEMORY = True

    if build_index:
        add_dataset_to_index(corpus, index_name, dataset)
    elif analyze_index:
        analyze_terms(corpus, index_name, min_docs, min_score)
