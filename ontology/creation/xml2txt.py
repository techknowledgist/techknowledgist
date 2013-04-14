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

TARGET_FIELDS = ['FH_TITLE', 'FH_DATE', 'FH_ABSTRACT', 'FH_SUMMARY',
                 'FH_TECHNICAL_FIELD', 'FH_BACKGROUND_ART',
                 'FH_DESC_REST', 'FH_FIRST_CLAIM', 'FH_OTHER_CLAIMS']

USED_FIELDS = TARGET_FIELDS + ['FH_DESCRIPTION']

# all the fields that should only have one element in their list
SINGLETON_FIELDS = TARGET_FIELDS[:-1]

MAPPINGS = { 'META-TITLE': 'FH_TITLE',
             'META-DATE': 'FH_DATE',
             'ABSTRACT': 'FH_ABSTRACT',
             'SUMMARY': 'FH_SUMMARY',
             'DESCRIPTION': 'FH_DESCRIPTION',
             'TECHNICAL_FIELD': 'FH_TECHNICAL_FIELD',
             'BACKGROUND_ART': 'FH_BACKGROUND_ART' }

DEBUG = False


def xml2txt(xml_parser, source_file, target_file, workspace):
    """Create a target_file in the d1_txt directory from a source_file in the xml
    directory."""

    basename = os.path.basename(target_file)
    ds_text_file = os.path.join(workspace, "%s.text" % basename)
    ds_tags_file = os.path.join(workspace, "%s.tags" % basename)
    ds_fact_file = os.path.join(workspace, "%s.fact" % basename)
    ds_sect_file = os.path.join(workspace, "%s.sect" % basename)

    create_fact_file(source_file, ds_text_file, ds_tags_file, ds_fact_file)
    xml_parser.collection = 'LEXISNEXIS'
    xml_parser.process_file(ds_text_file, ds_fact_file, ds_sect_file, fact_type='BASIC')

    (text, section_tags) = load_data(ds_text_file, ds_sect_file)
    fh_data = {}
    for f in USED_FIELDS:
        fh_data[f] = []

    add_sections(xml_parser, section_tags, text, fh_data)
    write_sections(xml_parser, target_file, fh_data)
    for fname in (ds_text_file, ds_tags_file, ds_fact_file, ds_sect_file):
        os.remove(fname)


def add_sections(xml_parser, section_tags, text, fh_data):
    """Collect all the tags that have a mapping or that are claims. Then remove embedded
    tags and add content to the FH_DESC_REST section."""
    for stag in section_tags:
        (p1, p2, tagtype) = (stag.start_index, stag.end_index, stag.attr('TYPE'))
        section = (p1, p2, text[int(p1):int(p2)].strip())
        if MAPPINGS.get(tagtype) is not None:
            add_mapped_tagtype(xml_parser, stag, fh_data, p1, p2, tagtype, section)
        elif tagtype == 'CLAIM':
            add_claim(fh_data, stag, section)
    remove_embedded_section(fh_data)
    populate_desc_rest(fh_data, text)

def write_sections(xml_parser, target_file, fh_data):
    """Write the sections as requested by the technology tagger to a file."""
    onto_fh = open_write_file(target_file)
    for f in TARGET_FIELDS:
        if fh_data.has_key(f) and fh_data[f]:
            onto_fh.write(u"%s:\n" % f)
            for sect in fh_data[f]:
                data_to_write = sect[2]
                if xml_parser.language == 'CHINESE':
                    data_to_write = restore_sentences(f, data_to_write)
                onto_fh.write(data_to_write)
                onto_fh.write(u"\n")
    onto_fh.write("END\n")
    
def populate_desc_rest(fh_data, text):
    """Create the content of FH_DESC_REST, which has the parts of the description that are
    not in the summary, technical field or backhruond art. A summary is used for English
    patents. Chinese patents can have the background art and/or technical field
    sections."""
    desc = get_first(fh_data, 'FH_DESCRIPTION')
    summ = get_first(fh_data, 'FH_SUMMARY')
    tech = get_first(fh_data, 'FH_TECHNICAL_FIELD')
    back = get_first(fh_data, 'FH_BACKGROUND_ART')
    if desc and summ:
        fh_data['FH_DESC_REST'].append((summ[1], desc[1], text[summ[1]:desc[1]].strip()))
    elif desc and tech and back:
        fh_data['FH_DESC_REST'].append((back[1], desc[1], text[back[1]:desc[1]].strip()))
    elif desc and back:
        fh_data['FH_DESC_REST'].append((back[1], desc[1], text[back[1]:desc[1]].strip()))
    elif desc and tech:
        fh_data['FH_DESC_REST'].append((tech[1], desc[1], text[tech[1]:desc[1]].strip()))
    elif desc:
        fh_data['FH_DESC_REST'].append((desc[0], desc[1], text[desc[0]:desc[1]].strip()))


def add_mapped_tagtype(xml_parser, section_tag, fh_data, p1, p2, tagtype, section):
    """Add a section tag for those tags whose tagtype are mapped to one of the FH_*
    fields used by the technology tagger."""
    mapped_type = MAPPINGS[tagtype]
    # Skip the title or abstract if it is in English and the language set is
    # German or Chinese. TODO: needs to be generalized to all languages.
    if xml_parser.language != 'ENGLISH' and tagtype in ('META-TITLE', 'ABSTRACT'):
        if section_tag.attr('LANGUAGE') == 'eng':
            return        
    # ad hoc fix for german
    if mapped_type == 'FH_TITLE' and xml_parser.language == 'GERMAN':
        section[2] = restore_proper_capitalization(section[2])
    if DEBUG:
        print_section(section, mapped_type)
    fh_data[mapped_type].append(section)
    
def add_claim(fh_data, section_tag, section):
    """Add a claim section, distinguishing between first claim and other claims."""
    if section_tag.attr('CLAIM_NUMBER') == '1':
        if DEBUG:
            print_section(section, 'FH_FIRST_CLAIM')
        fh_data['FH_FIRST_CLAIM'].append(section)
    else:
        if DEBUG:
            print_section(section, 'FH_OTHER_CLAIMS')
        fh_data['FH_OTHER_CLAIMS'].append(section)

def remove_embedded_section(fh_data):
    """Remove all the embedded tags. For example, it is quite common for tthere to be a
    summary inside of a summary (where there is a summary tag and within it a "Summary of
    the Invention" heading). Rather simplistic way of doing this, just keep the first
    summary and description section. Should really loop over all elements and check
    whether they are embedded in any other element."""
    for tagtype in SINGLETON_FIELDS:
        fh_data[tagtype] = fh_data[tagtype][:1]

def get_first(fh_data, field):
    return fh_data[field][0] if fh_data[field] else None
    
def print_section(section, prefix=''):
    if prefix:
        print prefix,
    print section[0], section[1], section[2][:50]


    
### ALL THE FOLLOWING MAY BE OBSOLETE

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
