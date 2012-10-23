
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
    -v VERSION  --  version number (defaults to 1)
    -f FILTER   --  one of (True, False) to turn chunk filtering on/off in tag2chk step 
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

Example calls:
python2.6 patent_analyzer.py -l cn --tag2chk
python2.6 patent_analyzer.py -l cn --summary
python2.6 patent_analyzer.py -l en --tag2chk
python2.6 patent_analyzer.py -l en --pf2dfeats

python2.6 patent_analyzer.py -l en --init

python2.6 patent_analyzer.py -l en -x 0 -v 4 --utrain
python2.6 patent_analyzer.py -l en -v 1 --utest
python2.6 patent_analyzer.py -l en -v 1 --scores

python2.6 patent_analyzer.py -l en -v 1 --all
python2.6 patent_analyzer.py -l de -v 1 -s /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/DE/Xml --all
python2.6 patent_analyzer.py -l de -s /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/DE/Xml --init
python2.6 patent_analyzer.py -l de -s /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/DE/Xml --populate

python2.6 patent_analyzer.py -l cn -v 1 -s /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/CN/Xml --all

python2.6 patent_analyzer.py -l en --pf2dfeats
python2.6 patent_analyzer.py -l en --summary

python2.6 patent_analyzer.py -l de -v 1 -x 0   --utrain
python2.6 patent_analyzer.py -l de -v 1 --utest
python2.6 patent_analyzer.py -l de -v 1 --scores

python2.6 patent_analyzer.py -l cn -v 1 -x 0   --utrain 
python2.6 patent_analyzer.py -l cn -v 1 --utest 
python2.6 patent_analyzer.py -l cn -v 1 --scores

# 10/14/2012 trying a more annotated .lab file for english
python2.6 patent_analyzer.py -l en -v 2 -x 0   --utrain 
python2.6 patent_analyzer.py -l en -v 2 --utest 
python2.6 patent_analyzer.py -l en -v 2 --scores
# The output seems to be reversed (y <=> n)

# Try again, this time redoing the chunking first.
python2.6 patent_analyzer.py -l en --tag2chk
python2.6 patent_analyzer.py -l en -v 7 --scores

python2.6 patent_analyzer.py -l de -f False --tag2chk
python2.6 patent_analyzer.py -l de --pf2dfeats
python2.6 patent_analyzer.py -l de -v 7 -x 0   --utrain
python2.6 patent_analyzer.py -l de -v 7 --utest 
python2.6 patent_analyzer.py -l de -v 7 --scores  
"""


import os, sys, getopt, subprocess, shutil

import putils
import xml2txt
import txt2tag
import tag2chunk
import cn_txt2seg
import cn_seg2tag
import pf2dfeats
import train
import sum_scores

import config_data

# moved to config_data.py
#source_path = "/home/j/clp/chinese/corpora/fuse-patents/" + \
#              "500-patents/DATA/Lexis-Nexis/US/Xml"
#target_path = "data/patents"
#language = "en"

source_path = config_data.external_patent_path
target_path = config_data.working_patent_path
language = config_data.language
annot_path = config_data.annot_lang_path

if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:v:x:f:',
        ['init', 'populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 'summary',
         'utrain', 'utest', 'scores', 'all'])
    

    version = "1"
    xval = "0"
    filter_p = True
    init = False
    populate = False
    xml_to_txt = False
    txt_to_seg = False
    txt_to_tag = False
    tag_to_chk = False
    pf_to_dfeats = False
    union_train = False
    union_test = False
    tech_scores = False
    summary = False
    all = False
    
    for opt, val in opts:
        
        if opt == '-l': language = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '-v': version = val
        if opt == '-x': xval = val
        if opt == '-f': 
            if val == "True":
                filter_p = True
            elif val == "False":
                filter_p = False
            else:
                print "Illegal value for Boolean option -f: %s" % val
                sys.exit()
                

        if opt == '--init': init = True
        if opt == '--populate': populate = True
        if opt == '--xml2txt': xml_to_txt = True
        if opt == '--txt2tag': txt_to_tag = True
        if opt == '--tag2chk': tag_to_chk = True
        if opt == '--pf2dfeats': pf_to_dfeats = True
        if opt == '--utrain': union_train = True
        if opt == '--utest': union_test = True
        if opt == '--scores': tech_scores = True
        if opt == '--summary': summary = True
        if opt == '--all': all = True


    if init:
        print "[patent_analyzer]source_path: %s, target_path: %s, language: %s" % \
            (source_path, target_path, language)
        # creates a directory inside data/patents, using the language and the range of years
        # as determined by the year range in the external sample's subdirectory
        # clear the directory if it exists first.
        lang_path = os.path.join(target_path, language)
        putils.removeDir(lang_path)
        l_year = os.listdir(source_path)
        putils.make_patent_dir(language, target_path, l_year)
 
    elif populate:
        print "[patent_analyzer]source_path: %s, target_path: %s, language: %s" % \
            (source_path, target_path, language)
        # populates target xml directory from the external source
        l_year = os.listdir(source_path)
        putils.populate_patent_xml_dir(language, source_path, target_path, l_year)

    elif xml_to_txt:
        print "[patent_analyzer]target_path: %s, language: %s" % (target_path, language)
        # takes xml files and runs the document structure parser in onto mode
        # populates language/txt directory and ds_* directories with intermediate
        # document structure parser results
        l_year = os.listdir(source_path)
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
        print "[patent_analyzer] filter_p: %s" % filter_p
        tag2chunk.patent_tag2chunk_dir(target_path, language, filter_p)
    
    elif pf_to_dfeats:
        # creates a union of the features for each chunk in a doc (for training)
        pf2dfeats.patent_pf2dfeats_dir(target_path, language)

    elif summary:
        # create summary data phr_occ and phr_feats across dates, also phrase file suitable for 
        # annotation (phr_occ.unlab) in the ws subdirectory
        command = "sh ./cat_phr.sh %s %s" % (target_path, language)
        subprocess.call(command, shell=True)

    # Note: At this point, user must manually create an annotated file phr_occ.lab and
    # place it in <lang>/ws subdirectory.
        
    elif union_train:
        # copy the latest annotation file for the language into our working directory
        source_annot_lang_file = annot_path + "/phr_occ.lab"
        ws_annot_lang_file = target_path + "/" + language + "/ws/phr_occ.lab"
        shutil.copyfile(source_annot_lang_file, ws_annot_lang_file)

        # creates a mallet training file for labeled data with features as union of all phrase
        # instances within a doc.
        # Creates a model: utrain.<version>.MaxEnt.model in train subdirectory
        train.patent_utraining_data(target_path, language, version, xval)

    elif union_test:
        train.patent_utraining_test_data(target_path, language, version)

    elif tech_scores:
        # use the mallet.out file from union_test to generate a sorted list of 
        # technology terms with their probabilities
        command = "sh ./patent_tech_scores.sh %s %s %s" % (target_path, version, language)
        subprocess.call(command, shell=True)

    elif all:
        print "[patent_analyzer]source_path: %s, target_path: %s, language: %s" % (source_path, target_path, language)
        l_year = os.listdir(source_path)
        putils.make_patent_dir(language, target_path, l_year)
        putils.populate_patent_xml_dir(language, source_path, target_path, l_year)
        xml2txt.patents_xml2txt(target_path, language)
        if language == 'cn':
            cn_txt2seg.patent_txt2seg_dir(target_path, language)
            cn_seg2tag.patent_txt2tag_dir(target_path, language)
        else:
            txt2tag.patent_txt2tag_dir(target_path, language)
        tag2chunk.patent_tag2chunk_dir(target_path, language, filter_p)
        pf2dfeats.patent_pf2dfeats_dir(target_path, language)
        command = "sh ./cat_phr.sh %s %s" % (target_path, language)
        subprocess.call(command, shell=True)
