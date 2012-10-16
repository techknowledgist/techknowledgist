import os, sys

BASE_DIR = '/Users/marc/Documents/fuse/patent-classifier/data/patents'
BASE_DIR = '/Users/marc/Desktop/FUSE/ontology_creation/data/patents'

script_name = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_name)

if script_dir == '/home/j/marc/Desktop/FUSE/code/patent-classifier/ontology/selector':
    BASE_DIR = '/home/j/marc/Desktop/FUSE/code/patent-classifier/ontology/creation/data/patents'
else:
    BASE_DIR = '/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data/patents'
