# putils.py
# utility functions for processing documents
# Directory structure supporting the text analysis pipline:
# <root_path>/<lang>/<step>/<year>
# where <step> is one of ["xml", "txt", "seg", "tag", "chunk", "pickle", "annot", "ds_text", "ds_tags", "ds_sect", "ds_fact"]
# steps preceded by ds_ are created by Marc's xml analysis pipeline
# To create a patent directory structure and populate the xml files from some external source:
# modify the following function with root path (for target) and source path of xml files:
# putils.init_patent_dir("en") 
# putils.init_patent_dir("de") 
# putils.init_patent_dir("cn") 
# To only make the directory structure but not populate it, use
# putils.make_patent_dir("en")
# putils.make_patent_dir("de")
# putils.make_patent_dir("cn")


import fxml
import sdp
import os
import errno
import sys
import shutil

import xml2txt
import txt2tag
import tag2chunk

# putils.sent_patent_dir("/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml/1980", "/home/j/anick/fuse/data/patents/en/sent/1980")

# putils.tag_sent_dir( "/home/j/anick/fuse/data/patents/en/sent/1980",  "/home/j/anick/fuse/data/patents/en/tag/1980")

# If path already exists, print a message and continue
def make_sure_path_exists(path, msg=True):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno == errno.EEXIST:
            if msg == True:
                print "[maks_sure_path_exists]MSG: %s already exists." % (path)
            pass
        else:
            raise

# l_subdir is a list of subdirectory names to be created under the target_path
# l_year is a list of year names to be created under each subdir path
def create_patent_dir(target_path, l_year):
    l_subdir = ["xml", "txt", "tag", "seg", "chunk", "ds_text", "ds_tags", "ds_sect", "ds_fact", "phr_occ", "phr_feats", "doc_feats_lab", "doc_feats_unl", "doc_feats"]
    for subdir in l_subdir:
        subdir_path = target_path + "/" + subdir
        make_sure_path_exists(subdir_path)
        for year in l_year:
            year_path = subdir_path + "/" + year
            make_sure_path_exists(year_path)

# copy xml files from some external place into the target_path
# assume the source path has a set of year subdirectories below it, listed in l_year
def populate_patent_xml_dir(xml_source_path, target_path, l_year):
    # populate the xml subdir
    print "l_year: %s, xml_source_path: %s" % (l_year, xml_source_path)
    for year in l_year:
        source_path = xml_source_path + "/" + year
        print "[populate_xml]source path for xml files: %s" % source_path
        for file in os.listdir(source_path):
            source_file = source_path + "/" + file
            target_file = target_path + "/xml/" + year + "/" + file
            print "[populate_xml]Copying %s to %s" % (source_file, target_file)
            shutil.copyfile(source_file, target_file)

    print "[populate_xml]done"

# create directory structure and populate xml portion
def create_patent_dir_wrapper(xml_source_path, target_path, l_year):
    # create the directory structure
    create_patent_dir(target_path, l_year)
    # populate the xml files
    populate_patent_xml_dir(xml_source_path, target_path, l_year)

# high level including the source paths for each language
# putils.init_patent_dir("en")
def init_patent_dir(lang):
    xml_source_path = ""
    #create the list of years, lang dependently since the range of years differs from language to language in
    # the source dir
    l_year = [] 

    if lang == "en":
        xml_source_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml"

        for year in range(1980, 2012):
            l_year.append(str(year))

    elif lang == "de":
        xml_source_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/DE/Xml"
        for year in range(1982, 2008):
            l_year.append(str(year))

    elif lang == "cn":
        xml_source_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/CN/Xml"
        for year in range(1987, 2012):
            l_year.append(str(year))


    patent_lang_path = "/home/j/anick/fuse/data/patents" + "/" + lang
    create_patent_dir_wrapper(xml_source_path, patent_lang_path, l_year)

# putils.make_patent_dir("en")
# putils.make_patent_dir("de")
# putils.make_patent_dir("cn")
# Just make the directory structure but do not populate (per language)
def make_patent_dir(lang):
    xml_source_path = ""
    #create the list of years, lang dependently since the range of years differs from language to language in
    # the source dir
    l_year = [] 

    if lang == "en":
        xml_source_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml"

        for year in range(1980, 2012):
            l_year.append(str(year))

    elif lang == "de":
        xml_source_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/DE/Xml"
        for year in range(1982, 2008):
            l_year.append(str(year))

    elif lang == "cn":
        xml_source_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/CN/Xml"
        for year in range(1987, 2012):
            l_year.append(str(year))


    patent_lang_path = "/home/j/anick/fuse/data/patents" + "/" + lang
    create_patent_dir(patent_lang_path, l_year)

# create directory structure for processing xml docs and load the xml docs from a source path.
def populate_xml_en():
    xml_source_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml"
    target_path = "/home/j/anick/fuse/data/patents/en"
    l_subdir = ["xml", "txt", "tag", "chunk", "pickle", "annot", "ds_text", "ds_tags", "ds_sect", "ds_fact"]
    l_year = [] 
    for subdir in l_subdir:
        subdir_path = target_path + "/" + subdir
        os.makedirs(subdir_path)
        print "[populate_xml]created subdir path: %s" % subdir_path
        for year in range(1980, 2012):
            year_path = subdir_path + "/" + str(year)
            l_year.append(str(year))
            os.makedirs(year_path)
            print "[populate_xml]created year path: %s" % year_path
    # populate the xml subdir
    print "l_year: %s, xml_source_path: %s" % (l_year, xml_source_path)
    for year in l_year:
        source_path = xml_source_path + "/" + year
        print "[populate_xml]source path for xml files: %s" % source_path
        for file in os.listdir(source_path):
            source_file = source_path + "/" + file
            target_file = target_path + "/xml/" + year + "/" + file
            print "[populate_xml]Copying %s to %s" % (source_file, target_file)
            shutil.copyfile(source_file, target_file)

    print "[populate_xml]done"

# putils.xml2txt_years_en()
def xml2txt_years_en():
    source_path = "/home/j/anick/fuse/data/patents/en/xml"
    target_path = "/home/j/anick/fuse/data/patents/en/txt"
    for year in range(1980, 2012):
        source_year_path = source_path + "/" + str(year)
        target_year_path = target_path + "/" + str(year)
        xml2txt.xml2txt_dir(source_year_path, target_year_path)
    print "[xml2txt_years_en]done"

# putils.txt2tag_years_en()
def txt2tag_years_en():
    source_path = "/home/j/anick/fuse/data/patents/en/txt"
    target_path = "/home/j/anick/fuse/data/patents/en/tag"
    tagger = sdp.STagger("english-caseless-left3words-distsim.tagger")
    for year in range(1980, 2012):
        source_year_path = source_path + "/" + str(year)
        target_year_path = target_path + "/" + str(year)
        txt2tag.txt2tag_dir(source_year_path, target_year_path, tagger)
    print "[txt2tag_years_en]done"

def tag2chunk_years_en():
    source_path = "/home/j/anick/fuse/data/patents/en/tag"
    chunk_path = "/home/j/anick/fuse/data/patents/en/chunk"
    pickle_path = "/home/j/anick/fuse/data/patents/en/pickle"
    tagger = sdp.STagger("english-caseless-left3words-distsim.tagger")
    chunk_schema = tag2chunk.chunk_schema_en()
    for year in range(1980, 2012):
        source_year_path = source_path + "/" + str(year)
        chunk_year_path = chunk_path + "/" + str(year)
        pickle_year_path = pickle_path + "/" + str(year)
        tag2chunk.tag2chunk_dir(chunk_schema, source_year_path, chunk_year_path, pickle_year_path)
    print "[tag2chunk_years_en]done"




############################


# obsolete, replaced by sent_patent_dir and tag_sent_dir 
def tag_patent_dir(patent_dir, sent_dir, tag_dir):
    # create output directories if they don't already exist
    make_sure_path_exists(sent_dir)
    make_sure_path_exists(tag_dir)

    # path names should not contain the end slash
    patent_dir = patent_dir.rstrip("/")
    sent_dir = sent_dir.rstrip("/")
    tag_dir = tag_dir.rstrip("/")

    # initiate the stanford parser process
    sw = sdp.sdpWrapper("wordsAndTags")

    # iterate over input files
    for file in os.listdir(patent_dir):
        print "[tag_patent_dir]Processing file: %s" % file
        full_sent_path = sent_dir + "/" + file
        full_tag_path = tag_dir + "/" + file

        # write out the sent file
        pat = fxml.Patent(patent_dir, file)
        pat.output_lines(full_sent_path)
        print "[tag_patent_dir]Created: %s" % full_sent_path

        # write out the tag file
        sw.tag_file(full_sent_path, full_tag_path)
        print "[tag_patent_dir]Created: %s" % full_tag_path


# create a dir of tagged files given a directory of sent files
def tag_sent_dir(sent_dir, tag_dir):
    # create output directories if they don't already exist
    make_sure_path_exists(tag_dir)

    # path names should not contain the end slash
    sent_dir = sent_dir.rstrip("/")
    tag_dir = tag_dir.rstrip("/")

    # initiate the stanford parser process
    sw = sdp.sdpWrapper("wordsAndTags")

    # iterate over input files
    for file in os.listdir(sent_dir):
        print "[tag_sent_dir]Processing file: %s" % file
        full_sent_path = sent_dir + "/" + file
        full_tag_path = tag_dir + "/" + file

        # write out the tag file
        sw.tag_file(full_sent_path, full_tag_path)
        print "[tag_patent_dir]Created: %s" % full_tag_path


# just create the sentence files
def sent_patent_dir(patent_dir, sent_dir):
    # create output directories if they don't already exist
    make_sure_path_exists(sent_dir)

    # path names should not contain the end slash
    patent_dir = patent_dir.rstrip("/")
    sent_dir = sent_dir.rstrip("/")

    # iterate over input files
    for file in os.listdir(patent_dir):
        print "[tag_patent_dir]Processing file: %s" % file
        full_sent_path = sent_dir + "/" + file

        # write out the sent file
        pat = fxml.Patent(patent_dir, file)
        pat.output_lines(full_sent_path)
        print "[sent_patent_dir]Created: %s" % full_sent_path


def test():
    tag_patent_dir("/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml/1980", "/home/j/anick/fuse/data/patents/en/1980/sent",  "/home/j/anick/fuse/data/patents/en/1980/tag")


# reverse all phrases in a file containing a list of space separated words (each making up a phrase)
# useful for finding lexical hierarchies
def reverse_words():
    print "[reverse_words]starting..."
    for line in sys.stdin:

        line = line.strip("\n")
        #print "line is: %s" % line
        l_words = line.split(" ")
        #print "l_words after split is: %s" % l_words
        l_words.reverse()
        #print "r_words after reverse is: %s" % l_words
        r_string = " ".join(l_words)
        print "%s" % r_string

if __name__ == '__main__':
    reverse_words()
