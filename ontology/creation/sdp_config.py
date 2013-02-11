# configuration defaults for sdp in sdpWrapper

import os, sys

script_path = os.path.abspath(sys.argv[0])
if script_path.startswith('/home/fuse'):
    LOCATION = 'FUSENET'
elif script_path.startswith('/home/j'):
    LOCATION = 'BRANDEIS'
elif script_path.startswith('/Users/marc/Documents/fuse/git/patent-classifier'):
    LOCATION = 'MARC_MACAIR'
else:
    LOCATION = ''

# sdp_dir is the location of the stanford-parser executable
# ie. /your full path/ stanford-parser-2010-02-26

#sdp_dir = "/Users/panick/peter/my_documents/brandeis/stanford-parser-2010-02-26"

# for hpc64:
# sdp_dir = "/home/panick/stanford-parser-2010-02-26"
# mx = "400m"

# for themis:
#sdp_dir = "/home/g/grad/anick/ie/stanford-parser-2010-02-26"

# parser location
# not needed for chunking
sdp_dir = "/home/j/anick/fuse/share/stanford-parser-2012-07-09"

# tagger and segmenter location
if LOCATION == 'BRANDEIS':
    stag_dir = "/home/j/corpuswork/fuse/code/patent-classifier/tools/stanford/" + \
               "stanford-postagger-full-2012-07-09" 
    seg_dir = "/home/j/corpuswork/fuse/code/patent-classifier/tools/stanford/" + \
              "stanford-segmenter-2012-07-09"
elif LOCATION == 'FUSENET':
    stag_dir = "/home/fuse/tools/stanford-postagger-full-2012-07-09" 
    seg_dir = "/home/fuse/tools/stanford-segmenter-2012-07-09"
elif LOCATION == 'MARC_MACAIR':
    tools_path = '/Applications/ADDED/NLP'
    stag_dir = os.path.join(tools_path, "stanford-postagger-full-2012-07-09" )
    seg_dir = os.path.join(tools_path, "stanford-segmenter-2012-07-09")
else:
    tools_path = os.path.join(script_path, '..', '..', 'tools')
    tools_path = os.path.abspath(tools_path)
    stag_dir = os.path.join(tools_path, "stanford-postagger-full-2012-07-09" )
    seg_dir = os.path.join(tools_path, "stanford-segmenter-2012-07-09")
    #print '>>', tools_path

mx = "3000m"


debug_p = 1
sentences = "newline"

"""
### use these parameters to test handling of pre-tagged input
# if tokenized = 1 and tag_separator = "/"
# then parser should use tags provided in input line
tag_separator = "/"
tokenized = 1
output_format = "penn,typedDependenciesCollapsed"
"""

# parameters for 3 kinds of output
tag_separator = "_"
tokenized = 0
#output_format = "wordsAndTags,penn,typedDependenciesCollapsed"
output_format = "wordsAndTags"
