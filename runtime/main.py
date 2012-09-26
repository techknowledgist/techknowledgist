"""

Main script for the technology tagger.

Usage:

    % python main.py -l LANGUAGE -o OUTPUT_DIR FILE_LIST

    LANGUAGE is one of ENGLISH, CHINESE and GERMAN
    OUTPUT_DIR is the directory where the HTML files are written
    FILE_LIST is a list with paths to XML files
    
"""


import os, sys, getopt, time, codecs, random, pprint

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
code_dir = os.path.split(script_dir)[0]
sys.path.append(code_dir)

from utils.docstructure.main import Parser
from utils.splitter import Splitter
from utils.tries.matcher import Matcher, Trie
from html import HTML_PREFIX, HTML_END

TRAP_ERRORS = True
TRAP_ERRORS = False


def usage():
    print "Usage: % python main.py -l LANGUAGE -o OUTPUT_DIR FILE_LIST\n"


    
class TechnologyTagger(object):

    """
    Main class, reponsible for:
    - reading the list of files to process
    - running the Document Structure Parser
    - reading in the list of technologies (into a trie)
    - reading patterns (future functionailty)
    - looking up technologies in parts of the documents
    - using weights depending on location in document (future functionailty)
    - collecting and storing results
    - calculate maturity scores for each document
    - calling the Scorer to calculate year-by-year scores and RDG score
    - calling the Exporter to generate output
    """

    def __init__(self, language, output_dir, file_list):
        self.language = language
        self.output_dir = output_dir
        self.file_list = file_list
        self.files = [l.strip() for l in open(file_list).readlines()]
        # a simple list of technologies, or perhaps tuples with maturity scores added
        # (note that the maturity score are time stamped)
        # these will be used for the prefix trie lookup
        self.technologies = OntologyReader().technologies(language)
        self.lookup = Lookup(self.language, self.technologies)
        self.storage = ResultStore()
        self.exporter = Exporter(language, output_dir, '../ontology')

        
    def __str__(self):
        return "<TechnologyTagger on \"%s\" language=\"%s\">" \
               % (self.file_list, self.language)

    def process_files(self):
        count = 0
        # use this to limit how often you iterate, set to 0 if there is not limit
        cap = 10
        for filename in self.files:
            count += 1
            print "%04d Processing %s" % (count, os.path.basename(filename))
            if TRAP_ERRORS:
                try:
                    self.process_file(filename)
                except Exception, e:
                    print e
            else:
                self.process_file(filename)
            if count == cap:
                break
        Scorer().score(self.storage)
        #self.storage.pp()
        self.exporter.export(self.storage)

    def process_file(self, filename):
        """Run the document structure parser, select the section wewant to use, perform
        technology lookup on those sections,and store the results."""
        self.filename = filename
        data = self._get_data_from_document()
        year = data['DATE'][:4]
        filtered_data = self._select_data(data)
        lookup_results = self.lookup.search(filtered_data)
        self.storage.add(os.path.basename(filename), year, lookup_results)
        
    def _get_data_from_document(self):
        """Return a data structure with sections from the document, includes some meta
        data and all sections where we expect to find technologies. It casts a wide net,
        downstream code may select a subset."""
        docparser = Parser()
        docparser.collection = 'LEXISNEXIS'
        docparser.write_files = False
        docparser.language = self.language
        (text_file, tags_file, fact_file, sect_file) = self._set_output_files()
        docparser.process_xml_file(self.filename, text_file, tags_file, fact_file, sect_file)
        data = {}
        for s in docparser.factory.sections:
            # TODO: should we add all paragraphs, in order to help the splitter?
            if 'Meta-Date' in s.types:
                data['DATE'] = s.text
            elif 'Meta-Title' in s.types:
                data['TITLE'] = s.text
            elif 'Technical_Field' in s.types:
                data.setdefault('TECHNICAL_FIELD', []).append(s.text)
            elif 'Background_Art' in s.types:
                data.setdefault('BACKGROUND_ART', []).append(s.text)
            elif 'Abstract' in s.types:
                data.setdefault('ABSTRACTS', []).append(s.text)
            elif 'Examples' in s.types:
                data.setdefault('EXAMPLES', []).append(s.text)
            elif 'Summary' in s.types:
                data.setdefault('SUMMARY', []).append(s.text)
            elif 'claim' in s.types:
                data.setdefault('CLAIMS', []).append(s.text)
            elif 'Description' in s.types:
                if not data.has_key('DESCRIPTION') or len(s.text) > len(data['DESCRIPTION']):
                    data['DESCRIPTION'] = s.text
        return data
        
    def _set_output_files(self):
        extensions = ('txt', 'tags', 'fact', 'sect')
        basename = os.path.basename(self.filename)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        return ["data/tmp/%s-%s.%s" % (timestamp, basename, ext) for ext in extensions]

    def _select_data(self, data):
        """Barebones version. Should return a list of tuples with type and weight:
        ('ABSTRACT', '1.0', 'We describe a ...'). """
        # TODO: make more robust
        return [('ABSTRACT', 1.0, data['ABSTRACTS'][0]),
                ('DESCRIPTION', 0.4, data['DESCRIPTION'])]



class OntologyReader(object):

    def technologies(self, language):
        """Read the technologies as stored in the lists for the three languages."""
        with codecs.open("technologies/technologies-%s.txt" % language, encoding='utf-8') as fh:
            technologies = [t.strip() for t in fh.readlines()]
            return technologies

    
class Lookup(object):

    def __init__(self, language, technologies):
        self.language = language
        self.splitter = Splitter(language)
        self.matcher = Matcher(Trie([(t,'t') for t in technologies]))
        if language == 'CHINESE':
            # TODO: make this less brittle, it now requires that the script is run from
            # this very directory
            library_dir = '../utils/library'
            self.splitter.add_chinese_split_character(library_dir + '/chinese_comma.txt')
            self.splitter.add_chinese_split_character(library_dir + '/chinese_degree.txt')
            
    def search(self, sections):
        use_boundaries = False if self.language == 'CHINESE' else True
        technologies_found = []
        for (sectype, weight, text) in sections:
            fragments = self.splitter.split(text)
            for fragment in fragments:
                self.matcher.lookup(fragment, use_boundaries=use_boundaries)
                for r in self.matcher.result:
                    technologies_found.append((sectype, weight, u''.join(r.found)))
        return technologies_found

    
class ResultStore(object):

    def __init__(self):
        self.data = {}
        self.weights = {}
        self.overall_score = None   # will be added by the Scorer
        
    def add(self, filename, year, results):
        """Adding results, indexing on year and filename."""
        self._ensure_year(year)
        self._ensure_filename(year, filename)
        for (sectype, weight, technology) in results:
            self._ensure_filename_technology(year, filename, technology)
            self.weights[sectype] = weight
            technology_infile = self.get_technology(year, filename, technology)
            technology_inyear = self.get_technology(year, None, technology)
            for tech in (technology_inyear, technology_infile):
                tech[sectype] = tech.setdefault(sectype,0) + 1
    
    def get_years(self):
        return self.data.keys()
    
    def get_filenames(self, year):
        return self.data[year]['FILES'].keys()

    def get_file_scores(self, year):
        return [d['SCORE'] for d in self.data[year]['FILES'].values()]
        
    def get_weight(self, section):
        return self.weights.get(section, 0)

    def get_maturity_score(self, technology, year):
        """Return the maturity level of the technology for the given year. This should
        query the ontology, or the list derived from the ontology that is stored in
        TechnologyTagger.technologies. For now, we just make it up."""
        return random.randint(0,2)

    def get_score(self, year, filename=None):
        if filename is None:
            return self.data[year]['TOTAL']['SCORE']
        else:
            return self.data[year]['FILES'][filename]['SCORE']
    
    def set_score(self, year, filename, score):
        if filename is None:
            self.data[year]['TOTAL']['SCORE'] = score
        else:
            self.data[year]['FILES'][filename]['SCORE'] = score

    def get_technology(self, year, filename, technology):
        if filename is None:
            return self.data[year]['TOTAL']['TECHNOLOGIES'][technology]
        else:
            return self.data[year]['FILES'][filename]['TECHNOLOGIES'][technology]

    def get_technologies(self, year):
        return self.data[year]['TOTAL']['TECHNOLOGIES']
                
    def _ensure_year(self, year):
        self.data.setdefault(year, { 'FILES': {}, 'TOTAL': { 'TECHNOLOGIES': {}}})
        
    def _ensure_filename(self, year, filename):
        self.data[year]['FILES'].setdefault(filename, { 'TECHNOLOGIES': {} })
        
    def _ensure_filename_technology(self, year, filename, technology):
        self.data[year]['FILES'][filename]['TECHNOLOGIES'].setdefault(technology, {})
        self.data[year]['TOTAL']['TECHNOLOGIES'].setdefault(technology, {})

    def collect_tuples(self, year, filename=None):
        """Returns a list of tuples of the form <technology, maturity level, section,
        weight, count>"""
        if filename is None:
            dictionary = self.data[year]['TOTAL']['TECHNOLOGIES']
        else:
            dictionary = self.data[year]['FILES'][filename]['TECHNOLOGIES']
        tuples = []
        for technology, counts in dictionary.items():
            maturity_level = self.get_maturity_score(technology, year)
            for section, count in dictionary[technology].items():
                w = self.get_weight(section)
                tuples.append([technology, maturity_level, section, w, count])
        return tuples

        
    def pp(self):
        """For each year, print the file list and the counts for all technologies. Does
        not print the totals or the numbers for individual files, although those data are
        available."""
        #pprint.PrettyPrinter(indent=4).pprint(self.data)
        print
        for k,v in self.weights.items():
            print v, '-', k
        for year in sorted(self.data.keys()):
            print "\n%s" % year
            for filename in sorted(self.data[year]['FILES'].keys()):
                print '  ', filename
            for technology in sorted(self.data[year]['TOTAL']['TECHNOLOGIES'].keys()):
                print '  ', technology, self.data[year]['TOTAL']['TECHNOLOGIES'][technology]
            if self.data[year]['TOTAL'].has_key('SCORE'):
                print "   SCORE = %.4f" % self.data[year]['TOTAL']['SCORE']
        print "\nAVERAGE MATURITY SCORE = %.2f" % self.overall_score
            
        
class Scorer(object):

    """ The scoring scheme for calculating the average maturity scores over a year from
    the individual technology scores proceeds as follows. Each technology is associated
    with or more tuples of technology name T, maturity level ML for the year, section name
    S, section weight W_s and number of times the technology occurred in the section (N):

       <T, ML, S, Ws, N>

    For each technology, there can be as many tuples as there are section types. Now let
    TUPLES_y = [ TUPLE1 ... TUPLEn ] be the set of tuples for a year. The aggregate
    maturity level is

       SUM(TUPLEi with 1<=i<=n1) [TUPLEi.ML * TUPLEi.Ws * TUPLE.C ]

    That is, multiply the maturity level with the weight and the count, and sum it over
    the set of tuples. In short hand: SUM(ML.Ws.N). This is adjusted for the total count
    adjusted by weights: SUM(Ws.C). This is a number from 0 to 3, which we will map to a
    number between 0 and 1. So the full formula is:

       (SUM(ML.Ws.N) / SUM(Ws.N)) / 3

    This formual may need to be revised. For example, if technology Ti occurs a thousand
    times and technology Tj occurs once, then Ti will count a 1000 more towards the result
    than technology Tj. But in general it may be better to solve these cases by not
    extracting all technologies from a patent, but be sensitive to the ones mentioned in
    certain contexts. """
    
    def score(self, result_store):

        # these two variables are used to calculate the overall score for the RDG
        self.sum_maturity_x_weight_x_count = 0
        self.sum_weight_x_count = 0

        for year in result_store.get_years():
            tuples = result_store.collect_tuples(year)
            score = self.calculate_score(tuples)
            result_store.set_score(year, None, score)
            for filename in result_store.get_filenames(year):
                tuples = result_store.collect_tuples(year, filename)
                score = self.calculate_score(tuples)
                result_store.set_score(year, filename, score)

        total_average_maturity1 = self.sum_maturity_x_weight_x_count / self.sum_weight_x_count
        total_average_maturity2 = total_average_maturity1 / 3
        result_store.overall_score = total_average_maturity2

        
    def calculate_score(self, tuples):
        sum_maturity_x_weight_x_count = sum([t[1]*t[3]*t[4] for t in tuples])
        sum_weight_x_count = sum([t[3]*t[4] for t in tuples])
        self.sum_maturity_x_weight_x_count += sum_maturity_x_weight_x_count
        self.sum_weight_x_count += sum_weight_x_count 
        return (sum_maturity_x_weight_x_count / sum_weight_x_count) / 3
                
    
class Exporter(object):

    # TODO: must use mockup of histogram in year html
    # TODO: must use mockup of ontology entry
    
    def __init__(self, language, html_dir, ontology_dir):
        self.language = language
        self.html_dir = html_dir
        self.ontology_dir = ontology_dir
        
    def export(self, result_store):
        self.result_store = result_store
        for year in result_store.get_years():
            self.export_year(year)

    def export_year(self, year):
        fh = codecs.open(os.path.join(self.html_dir, "%s.html" % year), 'w', encoding='utf-8')
        fh.write(HTML_PREFIX)
        fh.write("<h1>Technological Maturity Scores for %s</h1>\n" % year)
        self.export_maturity_score(fh, year)
        self.export_histogram(fh, year)
        self.export_technologies(fh, year)
        fh.write("\n")
        fh.write(HTML_END)

    def export_maturity_score(self, fh, year):
        fh.write("<h3>Average maturity score for 2006</h3>\n")
        fh.write("<blockquote>\n")
        fh.write("<table cellspacing=0 cellpadding=5 border=1>\n")
        fh.write("<tr>\n")
        fh.write("  <td>AVERAGE_MATURITY_SCORE\n")
        fh.write("    <td>%.4f\n" % self.result_store.get_score(year))
        fh.write("</table>\n")
        fh.write("</blockquote>\n\n")
        
    def export_histogram(self, fh, year):

        scores = self.result_store.get_file_scores(year)
        bins = [0,0,0,0,0,0,0,0,0,0]
        names = ['0.0-0.1', '0.1-0.2', '0.2-0.3', '0.3-0.4', '0.4-0.5',
                 '0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-1.0']
        for score in scores:
            if score == 1:
                bins[9] += 1
            else:
                bins[int(str(score)[2])] += 1
        maxval = sorted(bins)[-1]
        adjustment = 1
        #if max > 100:
        #    adjustment =

        fh.write("<h3>Histogram of Maturity Score Distribution over %s Patents </h3>\n" % year)
        fh.write("<blockquote>\n")
        fh.write("<pre>\n")
        for i in range(9, -1, -1):
            bar_string = "%s | %s" % (names[i], '+' * bins[i])
            fh.write("%s\n" % bar_string)
        bottom_line = '-' * maxval
        fh.write("        +-%s" % bottom_line)
        
        fh.write("\n")
        fh.write("\n")
        fh.write("\n")
        fh.write("</pre>\n")
        fh.write("</blockquote>\n")


        
    def export_technologies(self, fh, year):
        fh.write("<h3>Top 50 technologies referenced, with occurrence count, maturity score, ")
        fh.write("and links to the ontology</h3>\n")
        fh.write("<blockquote>\n")
        fh.write("<table cellspacing=0 cellpadding=3 border=1>\n")
        technologies = self.result_store.get_technologies(year)
        for t in sorted(technologies.keys()):
            #print technologies[t]
            fh.write("<tr>\n")
            fh.write("   <td><a href=#>%s</a>\n" % t)
            fh.write("   <td align=right>%d\n" % sum(technologies[t].values()))
            fh.write("   <td>%s\n" % random.randint(0,2))
        fh.write("</table>\n")
        fh.write("</blockquote>\n")
        fh.write("\n")
        fh.write("\n")
        fh.write("\n")
        fh.write("\n")

        

if __name__ == '__main__':

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'l:o:')
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    language, output_dir = 'ENGLISH', 'data/tmp'
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-o': output_dir = val
    file_list = args[0]

    tagger = TechnologyTagger(language, output_dir, file_list)
    tagger.process_files()
    #tagger.process_file("data/US4192770A.xml")
    #tagger.process_file("data/DE3539484C1.xml")
