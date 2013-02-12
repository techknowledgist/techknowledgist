# putils.py
# PGA
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

# PGA 10/7/2012 added subdirectories for mallet train and test

import os
import errno
import sys
import shutil


# copy xml files from some external place into the target_path
# assume the source path has a set of year subdirectories below it, listed in l_year
def populate_patent_xml_dir(language, xml_source_path, target_path, l_year):
    # populate the xml subdir
    print "l_year: %s, xml_source_path: %s" % (l_year, xml_source_path)
    for year in l_year:
        source_path = xml_source_path + os.sep + year
        print "[populate_xml]source path for xml files: %s" % source_path
        for file in os.listdir(source_path):
            source_file = source_path + os.sep + file
            target_file = os.path.join(target_path, language, 'xml', year, file)
            print "[populate_xml]Copying %s to %s" % (source_file, target_file)
            shutil.copyfile(source_file, target_file)

    print "[populate_xml]done"

# copy xml files from some external place into the target_path
# assume the source path has a set of year subdirectories below it, listed in l_year
def populate_rdg_xml_dir(source_list_file, target_path):
    # populate the xml subdir

    # create a local copy of the file list in file_list.txt
    local_list_file = target_path + os.sep + "file_list.txt"
    shutil.copyfile(source_list_file, local_list_file)
    s_list = open(local_list_file)
    
    for line in s_list:
        line = line.strip("\n")
        (doc_id, year, xml_source_file) = line.split(" ")

        print "[populate_rdg_xml]source path for xml file: %s" % xml_source_file
        xml_file = doc_id + ".xml"
        target_file = os.path.join(target_path, "xml", xml_file)
        print "[populate_rdg_xml]Copying %s to %s" % (xml_source_file, target_file)
        shutil.copyfile(xml_source_file, target_file)
        
    print "[populate_rdg_xml]done"
    s_list.close()



# putils.make_patent_dir("en")
# putils.make_patent_dir("de")
# putils.make_patent_dir("cn")
# Just make the directory structure but do not populate (per language)
def make_patent_dir(lang, patent_lang_path, l_year):
    patent_lang_path = os.path.join(patent_lang_path, lang)
    print "Initializing", patent_lang_path
    create_patent_dir(patent_lang_path, l_year)


# If path already exists, print a message and continue
def make_sure_path_exists(path, msg=False):
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
    l_subdir = ["xml", "txt", "tag", "seg", "ds_text", "ds_tags", "ds_sect", "ds_fact",
                "phr_occ", "phr_feats", "doc_feats"]
    for subdir in l_subdir:
        subdir_path = target_path + os.sep + subdir
        make_sure_path_exists(subdir_path)
        for year in l_year:
            year_path = subdir_path + os.sep + year
            make_sure_path_exists(year_path)
    # directories that are not year specific
    # work space to save data that crosses years
    make_sure_path_exists(target_path + os.sep + 'ws')
    # work space for the indexer
    make_sure_path_exists(target_path + os.sep + 'idx')
    # work space for the technology selector, includes results from the matcher and
    # technology classifier
    make_sure_path_exists(target_path + os.sep + 'selector')
    # directories for mallet training and testing files
    make_sure_path_exists(target_path + os.sep + 'train')
    make_sure_path_exists(target_path + os.sep + 'test')

# l_subdir is a list of subdirectory names to be created under the target_path
# l_year is a list of year names to be created under each subdir path
def create_rdg_dir(target_path):
    l_subdir = ["xml", "txt", "tag", "seg", "ds_text", "ds_tags", "ds_sect", "ds_fact", "phr_occ", "phr_feats", "doc_feats", "ws", "train", "test"]
    for subdir in l_subdir:
        subdir_path = target_path + os.sep + subdir
        make_sure_path_exists(subdir_path)
    #file_list_file = target_path + os.sep + "file_list.txt"
    #make_sure_file_exists(file_list_file)
    
#mallet chokes if it encounters a control character
def strip_control_characters(input):
    
    if input:
        
        import re
              
        # unicode invalid characters
        RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
        u'|' + \
        u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
        (unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
         unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
         unichr(0xd800),unichr(0xdbff),unichr(0xdc00),unichr(0xdfff),
         )
        input = re.sub(RE_XML_ILLEGAL, "", input)
        
        # ascii control characters
        input = re.sub(r"[\x01-\x1F\x7F]", "", input)
        
    return input

def file_strip_control_characters(input, output):
    s_input = open(input)
    s_output = open(output, "w")

    line_no = 0
    for line in s_input:
        line_no += 1
        line = line.strip("\n")

        clean_line = strip_control_characters(line)
        if line != clean_line:
            print "Control char in line %i. CL: %s" % (line_no, clean_line)
            print "Control char in line %i. LI: %s" % (line_no, line)
            break
        s_output.write(clean_line)
        s_output.write("\n")

    s_input.close()
    s_output.close()

# remove a directory and subdirectories after testing if it exists
def removeDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

def make_year_dirs(path):
    for year in range(1980, 2013):
        
        year_path = path + os.sep + str(year)
        make_sure_path_exists(year_path)
