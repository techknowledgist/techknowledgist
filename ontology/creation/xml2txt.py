# xml2txt
# module to create a fielded text file from an xml (patent) file
# top level call: patents_xml2txt(patent_path, lang)

import os
import pdb
import sys

# path to include Marc's code
# MV: added the manipulations with the directory since that works on fusenet
# MV: kept all code for safety (and it doe not hurt on fusenet)
script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)
sys.path.append("/home/j/corpuswork/fuse/code/patent-classifier")
from utils.docstructure.main import Parser


def xml2txt(xml_parser, source_file, target_file, workspace):
    """Create a target_file in the txt directory from a source_file in the xml directory,
    using a Parser() object. This method is called from batch.py and does not depend on
    the hard-coded path above."""
    basename = os.path.basename(target_file)
    ds_text_file = os.path.join(workspace, "%s.text" % basename)
    ds_tags_file = os.path.join(workspace, "%s.tags" % basename)
    ds_fact_file = os.path.join(workspace, "%s.fact" % basename)
    ds_sect_file = os.path.join(workspace, "%s.sect" % basename)
    xml_parser.create_ontology_creation_input(source_file, ds_text_file, ds_tags_file,
                                              ds_fact_file, ds_sect_file, target_file)


def xml2txt_dir(xml_parser, source_path, target_path,
                ds_text_path, ds_tags_path , ds_fact_path, ds_sect_path):
    print "[xml2txt_dir]source_path: %s, target_path: %s" % (source_path, target_path)
    for file in os.listdir(source_path):
        source_file = source_path + "/" + file
        target_file = target_path + "/" + file
        ds_text_file = ds_text_path + "/" + file
        ds_tags_file = ds_tags_path + "/" + file
        ds_fact_file = ds_fact_path + "/" + file
        ds_sect_file = ds_sect_path + "/" + file
        print "[xml2txt_dir]from %s to %s" % (source_file, target_file)
        #p1 = Patent(source_file, target_file)
        # xml_file, text_file, tags_file, fact_file, sect_file, onto_file)
        xml_parser.create_ontology_creation_input(source_file, ds_text_file, ds_tags_file,
                                                  ds_fact_file, ds_sect_file, target_file)

def test():
    xml_parser = Parser()
    parser.language = "ENGLISH" 
    #parser.language = "GERMAN" 
    #parser.language = "CHINESE" 

    source_path = "/home/j/anick/fuse/data/patents/en_test/xml"
    target_path = "/home/j/anick/fuse/data/patents/en_test/pickle"
    ds_text_path = "/home/j/anick/fuse/data/patents/en_test/ds_text"
    ds_tags_path = "/home/j/anick/fuse/data/patents/en_test/ds_tags"
    ds_fact_path = "/home/j/anick/fuse/data/patents/en_test/ds_fact"
    ds_sect_path = "/home/j/anick/fuse/data/patents/en_test/ds_sect"
    xml2txt_dir(xml_parser, source_path, target_path, ds_text_path, ds_tags_path,
                ds_fact_path, ds_sect_path)

# run xml doc analysis for lang (en, de, cn)
# eg. xml2txt.patents_xml2txt("/home/j/anick/fuse/data/patents", "en")
# eg. xml2txt.patents_xml2txt("/home/j/anick/fuse/data/patents", "de")
def patents_xml2txt(patent_path, lang):
    xml_parser = Parser()
    xml_parser.onto_mode = True

    if lang == "en":
        xml_parser.language = "ENGLISH"
        print "[patents_xml2txt]xml_parser.language: %s" % xml_parser.language
    elif lang == "de":
        xml_parser.language = "GERMAN"
        print "[patents_xml2txt]xml_parser.language: %s" % xml_parser.language
    elif lang == "cn":
        xml_parser.language = "CHINESE"
        print "[patents_xml2txt]xml_parser.language: %s" % xml_parser.language

    lang_path = os.path.join(patent_path, lang)
    xml_path = os.path.join(lang_path, "xml") 
    
    # create the year list and process those docs
    for year in os.listdir(xml_path):
        year = str(year)
        source_path = os.path.join(xml_path, year)
        target_path = lang_path + "/txt" + "/" + year
        ds_text_path = lang_path + "/ds_text" + "/" + year
        ds_tags_path = lang_path + "/ds_tags" + "/" + year
        ds_fact_path = lang_path + "/ds_fact" + "/" + year
        ds_sect_path = lang_path + "/ds_sect" + "/" + year
        xml2txt_dir(xml_parser, source_path, target_path, ds_text_path, ds_tags_path,
                    ds_fact_path, ds_sect_path)

# we assume all the work will be done in a single directory
def pipeline_xml2txt(root_dir, lang):
    xml_parser = Parser()
    xml_parser.onto_mode = True
    if lang == "en":
        xml_parser.language = "ENGLISH"
        print "[pipeline_xml2txt]xml_parser.language: %s" % xml_parser.language
        
    elif lang == "de":
        xml_parser.language = "GERMAN"
        print "[pipeline_xml2txt]xml_parser.language: %s" % xml_parser.language

    elif lang == "cn":
        xml_parser.language = "CHINESE"
        print "[pipeline_xml2txt]xml_parser.language: %s" % xml_parser.language

    source_path = root_dir + "/xml"
    target_path = root_dir + "/txt"
    ds_text_path = root_dir + "/ds_text" 
    ds_tags_path = root_dir + "/ds_tags"
    ds_fact_path = root_dir + "/ds_fact"
    ds_sect_path = root_dir + "/ds_sect"
    xml2txt_dir(xml_parser, source_path, target_path, ds_text_path, ds_tags_path, ds_fact_path, ds_sect_path)
        
        
"""
def test_pm():
    dir = "/home/j/anick/fuse/data/pubmed"
    file = "pubmed_lines.txt"
    output_file = "/home/j/anick/fuse/data/pubmed/chunks.txt"
    #file = "pubmed_lines_test_1.txt"
    # create a chunker schema instance
    cs = sdp.chunker_tech()
    # create tagger instance
    tagger = sdp.STagger("english-caseless-left3words-distsim.tagger") 

    process_patent_sent_file(dir, file, tagger, cs, output_file)



# process file generated by Olga from pubmed titles and abstracts
def process_pubmed_lines_file(pubmed_file, tagger, cs):
    s_pm = open(pubmed_file)
    for line in s_pm:
        line= line.strip("\n")
        fields = line.split("\t")
        
    s_pm.close()
"""
