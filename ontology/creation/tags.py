# top level python script for using stanford dep parser to 
# tag sent dir containing sent files

# args:
# 1: sent_dir  - a full path in which selected sentences from each patent has
# been written.  
# 2: tag_dir  - a full path in which tagged sentences for each patent in sent_dir will
# be written.  If the directory does not exist, it will be created.  There should be
# one .tag file created for each file in the patent_dir.  Additionally, there will be one
# .over file created per input file.   These will be empty unless some sentence in the 
# input exceeds the length that can be handled by the Stanford parser.  Any such
# sentences will be output here.

if __name__ == "__main__":
    import putils
    import os
    import sys

    code_dir = "/home/j/anick/fuse"
    #current_dir = os.getcwd()

    #os.chdir(code_dir)

    sent_dir = sys.argv[1]
    tag_dir = sys.argv[2]
    putils.tag_sent_dir(sent_dir, tag_dir)

    #os.chdir(current_dir)
