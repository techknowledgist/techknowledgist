
"""

Script that bundles the processing of a list of patents (RDG) to the output of technologies.
Input is 
(1) a ws separated file containing a list of patents in the form:
<patent_id> <year> <document_location>

(2) a directory path to the root of an output directory for the RDG
(3) the language of the documents: {en|de|cn}

The system will create under the directory <path>/<RDG_name>  a set of subdirectories for
results of intermediate processing

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
    -v VERSION  -- version number (defaults to 1)
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
    
The final results of these intermediate steps are in:

    TARGET_PATH/LANGUAGE/phr_occ
    TARGET_PATH/LANGUAGE/phr_feat
    TARGET_PATH/LANGUAGE/ws

The main object of this script (e.g. if you run with the option --all) is to generate
a ranked list of technologies for the RDG.  This will be created in a file called

    utest.<version>.MaxEnt.out.scores

in the directory <target_path>/test

The scores file has lines of the form:
<year>|<doc_id>|phrase<tab><score>
e.g.,
1990|US4975845A|transmission_system     0.7731347815504757
Scores are sorted in descending order.  There is one score per chunk per document, so the 
same chunk may appear mulitple times with different scores if it occurs in multiple documents in the RDG.


Example calls:

# testing pipeline
python2.6 pipeline.py -l en --init
python2.6 pipeline.py -l en --populate
python2.6 pipeline.py -l en --xml2txt
python2.6 pipeline.py -l en --utest

python2.6 pipeline.py -l en --all
"""


import os, sys, getopt, subprocess

import putils
import xml2txt
import txt2tag
import tag2chunk
import cn_txt2seg
import cn_seg2tag
import pf2dfeats
import train

# config_data holds default values for the parameters below
import config_data

# The following parameters must be set:
# -p patent_path
# -s source_path
# -t target_path
# -l language

# patent_path is the path to the local patent directory.  We assume that it is 
# populated by running patent_analysis.py before running this script.
patent_dir = config_data.working_patent_path

# target_path is the path to a directory in which information for processing an RDG will be stored.
# It should be a "local" path, such as data/working/rdg/<RDG>
target_path = config_data.working_rdg_path

# source_path is the path to an "external" file containing a list of documents (RDG).  The file should be given a name
# <RDG>.txt
# Each line should contain three whitespace separated fields: doc_id year file_path
# as in 
# US4192770A 1980 /home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml/1980/US4192770A.xml
# 
# This file will be copied into the target_path as file_list.txt
source_path = config_data.external_rdg_filelist

# language should be one of "en", "de", "cn"
language = config_data.language

if __name__ == '__main__':

    (opts, args) = getopt.getopt(
        sys.argv[1:],
        'l:s:t:p:',
        ['init', 'populate', 'xml2txt', 'txt2tag', 'tag2chk', 'pf2dfeats', 'summary', 'utest', 'scores', 'all'])
    
    version = "1"
    xval = "0"
    init = False
    populate = False
    xml_to_txt = False
    txt_to_seg = False
    txt_to_tag = False
    tag_to_chk = False
    pf_to_dfeats = False
    union_test = False
    tech_scores = False
    summary = False
    all = False
    
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-s': source_path = val
        if opt == '-t': target_path = val
        if opt == '-p': patent_path = val

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


    print "[pipeline] After options, union_test = %s, version: %s" % (union_test, version)

    if init:
        # creates a directory inside target_path where results of steps of
        # processing steps will go
        putils.create_rdg_dir(target_path)
 
    elif populate:
        # populates target xml directory from the source file listing
        putils.populate_rdg_xml_dir(source_path, target_path)

    elif xml_to_txt:
        # takes xml files and runs the document structure parser in onto mode
        # populates language/txt directory and ds_* directories with intermediate
        # document structure parser results
        xml2txt.pipeline_xml2txt(target_path, language)

    elif txt_to_tag:
        # populates language/tag directory
        # works on pasiphae but not on chalciope

        ### NOTE: Chinese pipeline functions not implemented yet 10/8 PGA
        if language == 'cn':
            cn_txt2seg.pipeline_txt2seg_dir(target_path, language)
            cn_seg2tag.pipeline_txt2tag_dir(target_path, language)
        else:
            txt2tag.pipeline_txt2tag_dir(target_path, language)

    elif tag_to_chk:
        # populates language/phr_occ and language/phr_feat
        tag2chunk.pipeline_tag2chunk_dir(target_path, language)
    
    elif pf_to_dfeats:
        # creates a union of the features for each chunk in a doc (for training)
        pf2dfeats.pipeline_pf2dfeats_dir(target_path, language)

    elif summary:

        # create summary data phr_occ and phr_feats across dates, also phrase file suitable for 
        # annotation (phr_occ.unlab) in the ws subdirectory
        command = "sh ./cat_phr.sh %s %s" % (target_path, language)
        subprocess.call(command, shell=True)

    elif union_test:
        print "[pipeline]calling for union_test with version: %s" % version
        train.pipeline_utraining_test_data(target_path, language, patent_dir, version)

    elif tech_scores:
        # use the mallet.out file from union_test to generate a sorted list of 
        # technology terms with their probabilities
        command = "sh ./pipeline_tech_scores.sh %s %s" % (target_path, version)
        subprocess.call(command, shell=True)
        
    elif all:
        putils.create_rdg_dir(target_path)
        putils.populate_rdg_xml_dir(source_path, target_path)
        xml2txt.pipeline_xml2txt(target_path, language)

        ### NOTE: Chinese pipeline functions not implemented yet 10/8 PGA
        if language == 'cn':
            cn_txt2seg.pipeline_txt2seg_dir(target_path, language)
            cn_seg2tag.pipeline_txt2tag_dir(target_path, language)
        else:
            txt2tag.pipeline_txt2tag_dir(target_path, language)

        tag2chunk.pipeline_tag2chunk_dir(target_path, language)
        pf2dfeats.pipeline_pf2dfeats_dir(target_path, language)

        command = "sh ./cat_phr.sh %s %s" % (target_path, language)
        subprocess.call(command, shell=True)

        train.pipeline_utraining_test_data(target_path, language, patent_dir, version)

        command = "sh ./pipeline_tech_scores.sh %s %s" % (target_path, version)
        subprocess.call(command, shell=True)
