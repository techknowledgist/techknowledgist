
"""

Script that bundles all processing on patents, starting with a external directory of
patents for English, German or Chinese. Paths to filenames in these directories are
expected to look like '<year>/<xmlfile>'.

Processing steps include:
    - copying the external xml files
    - applying the document structure parser
    - tagging (includes segmentation for Chinese)
    - creating chunks in contexts
    - creating summary files for all years with all terms

Usage:
    
    % python patent_analyzer.py [OPTIONS]

    -l LANG     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -s PATH     --  external source directory with XML files, see below for the default
    -t PATH     --  target directory, default is data/patents
    --init      --  initialize directory structure in target path (non-destructive)
    --populate  --  populate directory in target path with files from source path
    --xml2txt   --  document structure parsing
    --txt2tag   --  tagging
    --tag2chk   --  creating chunks in context
    --summary   --  create summary lists
    --all       --  all processing steps

    All long options require a target path and a language (via the -l and -t options or
    their defaults). The long options --init, --populate and --all also require a source
    path (via -s or its default).
    
The final results of these steps are in:

    TARGET_PATH/LANGUAGE/phr_occ
    TARGET_PATH/LANGUAGE/phr_feat
    TARGET_PATH/LANGUAGE/ws

"""


import os, sys, getopt, subprocess

import putils
import xml2txt
import txt2tag
import tag2chunk
import cn_txt2seg
import cn_seg2tag


source_path = "/home/j/clp/chinese/corpora/fuse-patents/" + \
              "500-patents/DATA/Lexis-Nexis/US/Xml"
target_path = "data/patents"
language = "en"



if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:',
        ['init', 'populate', 'xml2txt', 'txt2tag', 'tag2chk', 'summary', 'all'])
    
    init = False
    populate = False
    xml_to_txt = False
    txt_to_seg = False
    txt_to_tag = False
    tag_to_chk = False
    summary = False
    all = False
    
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '--init': init = True
        if opt == '--populate': populate = True
        if opt == '--xml2txt': xml_to_txt = True
        if opt == '--txt2tag': txt_to_tag = True
        if opt == '--tag2chk': tag_to_chk = True
        if opt == '--summary': summary = True
        if opt == '--all': all = True


    if init:
        # creates a directory inside data/patents, using a hard-code range of years
        # suitable to the 500 patents sample, needs to be generalized
        l_year = os.listdir(source_path)
        putils.make_patent_dir(language, target_path, l_year)
 
    elif populate:
        # populates target xml directory from the external source
        l_year = os.listdir(source_path)
        putils.populate_patent_xml_dir(language, source_path, target_path, l_year)

    elif xml_to_txt:
        # takes xml files and runs the document structure parser in onto mode
        # populates language/txt directory and ds_* directories with intermediate
        # document structure parser results
        xml2txt.patents_xml2txt(target_path, language)

    elif txt_to_tag:
        # populates language/tag directory
        # works on pasiphae but not on chalciope
        if language == 'cn':
            cn_txt2seg.patent_txt2seg_dir(target_path, language)
            cn_seg2tag.patent_txt2tag_dir(target_path, language)
        else:
            txt2tag.patent_txt2tag_dir(target_path, language)

    elif tag_to_chk:
        # populates language/phr_occ and language/phr_feat
        tag2chunk.patent_tag2chunk_dir(target_path, language)

    elif summary:
        command = "sh ./cat_phr.sh %s/%s/phr_occ %s/%s/ws" % \
                  (target_path, language, target_path, language)
        subprocess.call(command, shell=True)
        
    elif all:
        l_year = os.listdir(source_path)
        putils.make_patent_dir(language, target_path, l_year)
        putils.populate_patent_xml_dir(language, source_path, target_path, l_year)
        xml2txt.patents_xml2txt(target_path, language)
        if language == 'cn':
            cn_txt2seg.patent_txt2seg_dir(target_path, language)
            cn_seg2tag.patent_txt2tag_dir(target_path, language)
        else:
            txt2tag.patent_txt2tag_dir(target_path, language)
        tag2chunk.patent_tag2chunk_dir(target_path, language)
