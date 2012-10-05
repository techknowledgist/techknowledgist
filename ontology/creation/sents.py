# top level python script for using stanford dep parser to 
# extract sentences from patent docs.

# args:
# 1: patent_dir  -  a full path (without final slash) containing
# lexis-nexis patents in xml format
# 2: sent_dir  - a full path in which selected sentences from each patent will
# be written.  If the directory does not exist, it will be created.  There should be
# one file created for each file in the patent_dir.

if __name__ == "__main__":
    import putils
    import os
    import sys

    code_dir = "/home/j/anick/fuse"
    #current_dir = os.getcwd()

    #os.chdir(code_dir)

    patent_dir = sys.argv[1]
    sent_dir = sys.argv[2]
    putils.sent_patent_dir(patent_dir, sent_dir)

    #os.chdir(current_dir)
