# configuration for mallet path on local machine

# last mallet release on pasiphae as of July 2012: 2.0.7

import os, sys

# no final "/" 
#mallet_dir = "/home/j/anick/mallet/mallet-2.0.7/bin"

script_path = os.path.abspath(sys.argv[0])
if script_path.startswith('/home/fuse'):
    mallet_dir = "/home/fuse/tools/mallet/mallet-2.0.7/bin"
elif script_path.startswith('/Users/marc/Documents/fuse/git/patent-classifier'):
    mallet_dir = '/Applications/ADDED/NLP/mallet/mallet-2.0.7/bin'
else:
    mallet_dir = "/home/j/corpuswork/fuse/code/patent-classifier/tools/mallet/mallet-2.0.7/bin"
