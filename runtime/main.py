"""

Main script for the technology tagger.

Usage:

    % python main.py -l LANGUAGE -o OUTPUT_DIR FILE_LIST

    LANGUAGE is one of ENGLISH, CHINESE and GERMAN
    OUTPUT_DIR is the directory where the HTML files are written
    FILE_LIST is a list with paths to XML files
    
"""


import os, sys, codecs

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
code_dir = os.path.split(script_dir)[0]
sys.path.append(code_dir)

import sys, getopt, time
from utils.docstructure.main import Parser
from utils.splitter import Splitter
from utils.tries.matcher import Matcher, Trie

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
        for filename in self.files[:2]:  # let's cap it for now
            count += 1
            print "%04d Processing %s" % (count, os.path.basename(filename))
            if TRAP_ERRORS:
                try:
                    self.process_file(filename)
                except Exception, e:
                    print e
            else:
                self.process_file(filename)
        self.storage.pp()
        # TODO: use Scorer to process data from DataCollector (RDG level and per year)
        Scorer().score(self.storage)
        # TODO: use Exporter to write html files, one for each year and one for the RDG
        self.exporter.export(self.storage)

    def process_file(self, filename):
        """Run the document structure parser, select the section wewant to use, perform
        technology lookup on those sections,and store the results."""
        self.filename = filename
        data = self._get_data_from_document()
        year = data['DATE'][:4]
        filtered_data = self._select_data(data)
        lookup_results = self.lookup.search(filtered_data)
        self.storage.add(filename, year, lookup_results)
        
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
        
    def add(self, filename, year, results):
        """Adding results, indexing on year, but for now ignoring the filename."""
        if not self.data.has_key(year):
            self.data[year] = {}
        for (sectype, weight, technology) in results:
            self.weights[sectype] = weight
            technology = self.data[year].setdefault(technology, { 'TOTAL': 0 })
            technology[sectype] = technology.setdefault(sectype,0) + 1
            technology['TOTAL'] += 1
                                                    
    def pp(self):
        print "\nWEIGHTS:"
        for k,v in self.weights.items():
            print '  ', v, '-', k
        print "\nTECHNOLOGIES:"
        for year in sorted(self.data.keys()):
            print "\n%s" % year
            for technology in sorted(self.data[year].keys()):
                print "   %4d %s" % ( self.data[year][technology]['TOTAL'], technology),
                counts = []
                for sectype, count in self.data[year][technology].items():
                    if sectype == 'TOTAL':
                        continue
                    counts.append("%s=%d" % (sectype, count))
                print " { " + ' , '.join(counts) + " }"

            
        
class Scorer(object):

    # TODO: must use mockup scores for the technologies
    # TODO: calculate yearly scores, add scores instvar to result_store
    
    def score(self, result_store):
        pass


class Exporter(object):

    # TODO: must use mockup of histogram in year html
    # TODO: must use mockup of ontology entry
    
    def __init__(self, language, html_dir, ontology_dir):
        self.language = language
        self.html_dir = html_dir
        self.ontology_dir = ontology_dir
        
    def export(self, result_store):
        pass



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
    print tagger
    tagger.process_files()
    #tagger.process_file("data/US4192770A.xml")
    #tagger.process_file("data/DE3539484C1.xml")
    
