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
        source_path = xml_source_path + "/" + year
        print "[populate_xml]source path for xml files: %s" % source_path
        for file in os.listdir(source_path):
            source_file = source_path + "/" + file
            target_file = os.path.join(target_path, language, 'xml', year, file)
            print "[populate_xml]Copying %s to %s" % (source_file, target_file)
            shutil.copyfile(source_file, target_file)

    print "[populate_xml]done"

# putils.make_patent_dir("en")
# putils.make_patent_dir("de")
# putils.make_patent_dir("cn")
# Just make the directory structure but do not populate (per language)
def make_patent_dir(lang, patent_lang_path, l_year):
    patent_lang_path = "data/patents" + "/" + lang
    create_patent_dir(patent_lang_path, l_year)


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
    # work space to save data that crosses years
    make_sure_path_exists(target_path + os.sep + 'ws')
