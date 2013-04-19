import os, sys, glob, time, codecs, textwrap, re

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser
from utils.docstructure.utils.select import SectionReader


file_list = [
    
    ]

class PatentClassifier(object):

    MAPPINGS = {'en': 'ENGLISH', 'de': "GERMAN", 'cn': "CHINESE" }

    def __init__(self):
        self.language = 'en'
        self.parser = Parser()
        self.parser.onto_mode = True
        self.parser.language = PatentClassifier.MAPPINGS[self.language]
        self.parser.collection = 'LEXISNEXIS'
        self.xml_directory = 'data/patents/en-basic/data/d0_xml/01/files'
        self.workspace = 'data/patents/en-basic/data/workspace'
        self.results_file = "%s/results-%s.txt" % (self.workspace, time.strftime("%Y%m%d-%H%M%S"))
        self.results_fh = codecs.open(self.results_file, 'w', encoding='utf-8')
        self.path = os.path.join(self.xml_directory, '*', '*')
        self.xml_files = glob.glob(self.path)

    def process_files(self):
        count = 0
        for xml_file in self.xml_files:
            count += 1
            #if count < 50: continue
            print "%04d %s" % (count, xml_file)
            self.process_file(xml_file)
            #if count > 50: break

    def process_file(self, xml_file):
        basename = os.path.basename(xml_file)[:-4]
        text_file = os.path.join(self.workspace, "%s.text" % basename)
        tags_file = os.path.join(self.workspace, "%s.tags" % basename)
        fact_file = os.path.join(self.workspace, "%s.fact" % basename)
        sect_file = os.path.join(self.workspace, "%s.sect" % basename)
        self.parser.process_xml_file(
            xml_file, text_file, tags_file, fact_file, sect_file, debug=True)
        for fname in (tags_file, fact_file):
            os.remove(fname)
        reader = SectionReader(text_file, sect_file)
        related_apps = reader.get_sections(section_type='RELATED_APPLICATIONS', struct='p')
        if related_apps:
            text = related_apps[0].text
            continuation_type = None
            matches = parse_related_applications(text)
            if matches:
                continuation_type = matches[0]
            self.results_fh.write("FILE: %s\n" % xml_file)
            self.results_fh.write("TYPE: %s\n" % continuation_type)
            self.results_fh.write("MATCHES: %s\n" % matches)
            self.results_fh.write("%s\n\n" % text)
            
def parse_related_applications(text):
    keys = ['division', 'divisional', 'continuation',
            'continuation-in-part', 'Continuation-In-Part', 'Continuation-in-Part']
    pattern_text = "\\b(" + '|'.join(keys) + ")\\b"
    pattern = re.compile(pattern_text)
    matches = re.findall(pattern, text)
    print matches
    return matches

def print_section_types(reader):
    print '   types:'
    for line in  textwrap.wrap(' '.join([str(t) for t in reader.section_types()]), 80):
        print '     ', line

def print_section_structs(reader):
    print '   structs:'
    for line in  textwrap.wrap(' '.join([str(t) for t in reader.section_structs()]), 80):
        print '     ', line


if __name__ == '__main__':

    classifier = PatentClassifier()
    classifier.process_files()
