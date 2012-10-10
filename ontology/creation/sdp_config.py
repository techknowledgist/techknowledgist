# configuration defaults for sdp in sdpWrapper

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

# tagger location
#stag_dir="/home/j/anick/fuse/share/stanford-postagger-full-2012-07-09"
stag_dir="/home/j/corpuswork/fuse/code/patent-classifier/tools/stanford/stanford-postagger-full-2012-07-09" 

# segmenter location
#seg_dir="/home/j/anick/fuse/share/stanford-segmenter-2012-07-09"
seg_dir="/home/j/corpuswork/fuse/code/patent-classifier/tools/stanford/stanford-segmenter-2012-07-09"

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
#tag_separator = ""
tag_separator = "_"
tokenized = 0
#output_format = "wordsAndTags,penn,typedDependenciesCollapsed"
output_format = "wordsAndTags"



