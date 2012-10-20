import os, sys

#BASE_DIR = '/Users/marc/Documents/fuse/patent-classifier/data/patents'
#BASE_DIR = '/Users/marc/Desktop/FUSE/ontology_creation/data/patents'

script_name = os.path.abspath(sys.argv[0])

if script_name.startswith('/home/j/marc/'):
    BASE_DIR = '/home/j/marc/Desktop/FUSE/code/patent-classifier/' + \
               'ontology/creation/data/patents'

elif script_name.startswith('/home/fuse'):
    BASE_DIR = '/shared/home/marc/batch'

else:
    BASE_DIR = '/home/j/corpuswork/fuse/code/patent-classifier/' + \
               'ontology/creation/data/patents'
