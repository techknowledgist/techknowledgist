# xml2txt
# module to create a fielded text file from an xml (patent) file
# top level call: patents_xml2txt(patent_path, lang)

import os
import pdb
import sys

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from utils.docstructure.main import Parser, create_fact_file, open_write_file
from utils.docstructure.main import load_data, restore_sentences


def xml2txt(xml_parser, source_file, target_file, workspace):
    """Create a target_file in the txt directory from a source_file in the xml directory,
    using a Parser() object. This method is called from batch.py and does not depend on
    the hard-coded path above."""
    basename = os.path.basename(target_file)
    ds_text_file = os.path.join(workspace, "%s.text" % basename)
    ds_tags_file = os.path.join(workspace, "%s.tags" % basename)
    ds_fact_file = os.path.join(workspace, "%s.fact" % basename)
    ds_sect_file = os.path.join(workspace, "%s.sect" % basename)

    #print "\n".join((source_file, ds_text_file, ds_tags_file, ds_fact_file, ds_sect_file))
    create_fact_file(source_file, ds_text_file, ds_tags_file, ds_fact_file)
    xml_parser.collection = 'LEXISNEXIS'
    xml_parser.process_file(ds_text_file, ds_fact_file, ds_sect_file, fact_type='BASIC')
    (text, section_tags) = load_data(ds_text_file, ds_sect_file)
    TARGET_FIELDS = ['FH_TITLE', 'FH_DATE', 'FH_ABSTRACT', 'FH_SUMMARY',
                     'FH_TECHNICAL_FIELD', 'FH_BACKGROUND_ART',
                     'FH_DESC_REST', 'FH_FIRST_CLAIM']
    USED_FIELDS = TARGET_FIELDS + ['FH_DESCRIPTION']
    FH_DATA = {}
    for f in USED_FIELDS:
        FH_DATA[f] = None
    _add_usable_sections(xml_parser, section_tags, text, FH_DATA)
    ONTO_FH = open_write_file(target_file)
    for f in TARGET_FIELDS:
        if FH_DATA.has_key(f) and FH_DATA[f] is not None:
            ONTO_FH.write("%s:\n" % f)
            data_to_write = FH_DATA[f][2]
            if xml_parser.language == 'CHINESE':
                data_to_write = restore_sentences(f, data_to_write)
            ONTO_FH.write(data_to_write)
            ONTO_FH.write("\n")
    ONTO_FH.write("END\n")
    for fname in (ds_text_file, ds_tags_file, ds_fact_file, ds_sect_file):
        os.remove(fname)

    
def _add_usable_sections(xml_paser, section_tags, text, FH_DATA):
    mappings = { 'META-TITLE': 'FH_TITLE', 'META-DATE': 'FH_DATE',
                 'ABSTRACT': 'FH_ABSTRACT', 'SUMMARY': 'FH_SUMMARY',
                 'DESCRIPTION': 'FH_DESCRIPTION',
                 'TECHNICAL_FIELD': 'FH_TECHNICAL_FIELD',
                 'BACKGROUND_ART': 'FH_BACKGROUND_ART'
                 }
    for tag in section_tags:
        (p1, p2, tagtype) = (tag.start_index, tag.end_index, tag.attr('TYPE'))
        if mappings.get(tagtype) is not None:
            mapped_type = mappings[tagtype]
            # skip the title or abstract if it is in English and the language set is
            # German or Chinese
            # TODO: needs to be generalized to all languages
            if xml_paser.language != 'ENGLISH' and tagtype in ('META-TITLE', 'ABSTRACT'):
                if tag.attr('LANGUAGE') == 'eng':
                    continue
            # only add the content if there wasn't any already, this is a bit ad hoc
            # but will have a preference for the first occurrence of the same content
            if FH_DATA.has_key(mapped_type) and FH_DATA[mapped_type] is None:
                section_text = text[int(p1):int(p2)].strip()
                if mapped_type == 'FH_TITLE' and xml_paser.language == 'GERMAN':
                    section_text = restore_proper_capitalization(section_text)
                FH_DATA[mapped_type] = (p1, p2, section_text)
        elif tagtype == 'CLAIM':
            if tag.attr('CLAIM_NUMBER') == '1':
                FH_DATA['FH_FIRST_CLAIM'] = (p1, p2, text[int(p1):int(p2)].strip())
    desc = FH_DATA['FH_DESCRIPTION']
    summ = FH_DATA['FH_SUMMARY']
    tech = FH_DATA['FH_TECHNICAL_FIELD']
    back = FH_DATA['FH_BACKGROUND_ART']
    if desc and summ:
        FH_DATA['FH_DESC_REST'] = (summ[1], desc[1], text[summ[1]:desc[1]].strip())
    elif desc and tech and back:
        FH_DATA['FH_DESC_REST'] = (back[1], desc[1], text[back[1]:desc[1]].strip())
    elif desc and  back:
        FH_DATA['FH_DESC_REST'] = (back[1], desc[1], text[back[1]:desc[1]].strip())
    elif desc and tech:
        FH_DATA['FH_DESC_REST'] = (tech[1], desc[1], text[tech[1]:desc[1]].strip())
    elif desc:
        FH_DATA['FH_DESC_REST'] = (desc[0], desc[1], text[desc[0]:desc[1]].strip())



def xml2txt_dir(xml_parser, source_path, target_path,
                ds_text_path, ds_tags_path , ds_fact_path, ds_sect_path):
    # TODO: this does not work anymore and should be fixed, but only if it is going to be
    # used again (which it isn't as of April 14, 2013)
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
