import os, sys

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
code_dir = os.path.split(script_dir)[0]
sys.path.append(code_dir)

import getopt
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
    - calling the Aggregator to calculate year-by-year scores and RDG score
    - calling the Exporter to generate output
    """

    def __init__(self, language, file_list):
        self.language = language
        self.file_list = file_list
        self.files = [l.strip() for l in open(file_list).readlines()]
        
    def __str__(self):
        return "<TechnologyTagger on \"%s\" language=\"%s\">" % (self.file_list, self.language)

    def process_files(self):
        for filename in self.files:
            self.process_file(filename)

    def process_file(self, filename):
        """The workhorse method."""
        
    
class Aggregator(object): pass

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

    ttagger = TechnologyTagger(language, file_list)

    print ttagger
    
    


