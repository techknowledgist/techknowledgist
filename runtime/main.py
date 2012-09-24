"""

Main script for the technology tagger.

Usage:

    % python main.py -l LANGUAGE FILE_LIST

    LANGUAGE is one of ENGLISH, CHINESE and GERMAN
    FILE_LIST is a list with paths to XML files
    
"""


import os, sys

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
code_dir = os.path.split(script_dir)[0]
sys.path.append(code_dir)

import sys, getopt, time
from utils.docstructure.main import Parser
#from utils.tries


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

    def __init__(self, language, file_list):
        self.language = language
        self.file_list = file_list
        self.files = [l.strip() for l in open(file_list).readlines()]
        # a simple list of technologies, or perhaps tuples with maturity scores added
        # (note that the maturity score are time stamped)
        # these will be used for the prefix trie lookup
        self.technologies = OntologyReader().technologies()
        # - initialize data collector
        # - initialize Lookup instance
        
    def __str__(self):
        return "<TechnologyTagger on \"%s\" language=\"%s\">" % (self.file_list, self.language)

    def process_files(self):
        count = 0
        for filename in self.files[:10]:  # let's cap it for now
            count += 1
            print "%4d Processing %s" % (count, os.path.basename(filename))
            try:
                self.process_file(filename)
            except Exception, e:
                print e
        # - use Scorer to process data from DataCollector (RDG level and per year)
        # - use Exporter to write html files, one for each year and one for the RDG
        
    def process_file(self, filename):
        """The workhorse method."""
        self.filename = filename
        self.data = self._get_data_from_document()
        #print self.data.keys()
        # 1. figure out what data to use
        # 2. lookup over those data (class Lookup)
        # 3. save in database, for now simply in memory (class DataCollector)
        
    def _get_data_from_document(self):
        docparser = Parser()
        docparser.collection = 'LEXISNEXIS'
        docparser.write_files = False
        docparser.language = self.language
        (text_file, tags_file, fact_file, sect_file) = self._set_output_files()
        docparser.process_xml_file(self.filename, text_file, tags_file, fact_file, sect_file)
        return self._select_data(docparser.factory.sections)
        
    def _set_output_files(self):
        extensions = ('txt', 'tags', 'fact', 'sect')
        basename = os.path.basename(self.filename)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        return ["data/tmp/%s-%s.%s" % (timestamp, basename, ext) for ext in extensions]

    def _select_data(self, sections):
        data = {}
        for s in sections:
            if 'Meta-Date' in s.types: data['DATE'] = s.text
            elif 'Meta-Title' in s.types: data['TITLE'] = s.text
            elif 'Technical_Field' in s.types: data.setdefault('TECHNICAL_FIELD', []).append(s.text)
            elif 'Background_Art' in s.types: data.setdefault('BACKGROUND_ART', []).append(s.text)
            elif 'Abstract' in s.types: data.setdefault('ABSTRACTS', []).append(s.text)
            elif 'Examples' in s.types: data.setdefault('EXAMPLES', []).append(s.text)
            elif 'Summary' in s.types: data.setdefault('SUMMARY', []).append(s.text)
            elif 'claim' in s.types: data.setdefault('CLAIMS', []).append(s.text)
            elif 'Description' in s.types:
                if not data.has_key('DESCRIPTION') or len(s.text) > len(data['DESCRIPTION']):
                    data['DESCRIPTION'] = s.text
        return data



class OntologyReader(object):
    def technologies(self):
        return []

class Lookup(object): pass

class DataCollector(object): pass

class Scorer(object): pass

class Exporter(object): pass




if __name__ == '__main__':

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'l:')
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    language = 'ENGLISH'
    for opt, val in opts:
        if opt == '-l': language = val
    file_list = args[0]

    tagger = TechnologyTagger(language, file_list)
    print tagger
    tagger.process_files()
    #tagger.process_file("data/US4192770A.xml")
    #tagger.process_file("data/DE3539484C1.xml")


    


