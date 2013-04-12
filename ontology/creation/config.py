"""

File with configuration settings. Intended to replace all previous configuration files,
which were named inconsistently and which duplicated some code. Used all caps for all
variables that are intended to be consumed by other scripts, which makes it easier to
recognize when variables from this file are used.

Configuration settings in this file:
- mallet location
- stanford tool locations and settings

"""

import os, sys


# First some code to determine what machine we are running this on, will be used to
# determine locations

script_path = os.path.abspath(sys.argv[0])
if script_path.startswith('/home/fuse'):
    location = 'FUSENET'
elif script_path.startswith('/home/j/'):
    location = 'BRANDEIS'
elif script_path.startswith('/Users/'): 
    location = 'MAC'
else:
    print "WARNING: could not determine the location"
    location = None



### MALLET settings
### -----------------------------------------------------------------------

MALLET_RELEASE = '2.0.7'

# mallet directory, note that there should be no trailing slash in the directory name
if location == 'FUSENET':
    # location on the fuse VM
    MALLET_DIR = "/home/fuse/tools/mallet/mallet-2.0.7/bin"
elif location == 'MAC':
    # assumed location on any Mac
    MALLET_DIR = '/Applications/ADDED/nlp/mallet/mallet-2.0.7/bin'
else:
    # location on the department machines
    MALLET_DIR = "/home/j/corpuswork/fuse/code/patent-classifier/tools/mallet/mallet-2.0.7/bin"


### Stanford parser/segmenter settings
### -----------------------------------------------------------------------

STANFORD_TAGGER_RELEASE = "2012-07-09"
STANFORD_SEGMENTER_RELEASE = "2012-07-09"

# tagger and segmenter location
if location == 'BRANDEIS':
    base_dir = "/home/j/corpuswork/fuse/code/patent-classifier/tools/stanford/"
    STANFORD_TAGGER_DIR = base_dir + "stanford-postagger-full-2012-07-09" 
    STANFORD_SEGMENTER_DIR = base_dir + "stanford-segmenter-2012-07-09"
elif location == 'FUSENET':
    STANFORD_TAGGER_DIR = "/home/fuse/tools/stanford-postagger-full-2012-07-09" 
    STANFORD_SEGMENTER_DIR = "/home/fuse/tools/stanford-segmenter-2012-07-09"
elif location == 'MAC':
    base_dir = '/Applications/ADDED/nlp/stanford/'
    STANFORD_TAGGER_DIR = base_dir + "stanford-postagger-full-2012-07-09"
    STANFORD_SEGMENTER_DIR = base_dir + "stanford-segmenter-2012-07-09"
else:
    # cobbel together a path local to the repository
    tools_path = os.path.join(script_path, '..', '..', 'tools')
    tools_path = os.path.abspath(tools_path)
    STANFORD_TAGGER_DIR = os.path.join(tools_path, "stanford-postagger-full-2012-07-09" )
    STANFORD_SEGMENTER_DIR = os.path.join(tools_path, "stanford-segmenter-2012-07-09")


# memory use for any of the stanford tools, may need to define separate values for tagger,
# segmenter and parser
STANFORD_MX = "3000m"

STANFORD_DEBUG_P = 1

STANFORD_SENTENCES = "newline"

# parameters for 3 kinds of output, the output format variable does not appear to be used
STANFORD_TAG_SEPARATOR = "_"
STANFORD_TOKENIZED = 0
STANFORD_OUTPUT_FORMAT = "wordsAndTags"
#STANFORD_OUTPUT_FORMAT = "wordsAndTags,penn,typedDependenciesCollapsed"

### use these parameters to test handling of pre-tagged input
# if tokenized = 1 and tag_separator = "/"
# then parser should use tags provided in input line
# tag_separator = "/"
# tokenized = 1
# output_format = "penn,typedDependenciesCollapsed"

# See discarded/sdp_config for Some older settings that are not used anymore



### configuration for data used by patent_analysis.py and pipeline.py
### -----------------------------------------------------------------------

DATA_ROOT = "data"

# for patent_analysis.py

# directory of patent xml files arranged into yearly subdirectories
EXTERNAL_PATENT_PATH = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml"

# location where patents are copied to local directory for processing steps.  The directory structure 
# arranges files by language/step/year
# The .xml qualifier is expected on file names in all subdirectories, so that the file
# names within the step subdirectories are identical.
WORKING_PATENT_PATH = os.path.join(DATA_ROOT, "patents")

# default language
LANGUAGE = "en"

# for training annotations
ANNOT_LANG_PATH = "../annotation/" + LANGUAGE

# another version that is less language specific (the above always uses 'en')
ANNOTATION_DIRECTORY = "../annotation"

# for pipeline.py

# For each RDG (related document group), there must be a filelist containing
# doc_id year external_file_path
EXTERNAL_RDG_FILELIST = os.path.join(DATA_ROOT, "external/en1.txt")

# For each RDG, create a local working directory
WORKING_RDG_PATH = os.path.join(DATA_ROOT, "working/rdg/en1")
