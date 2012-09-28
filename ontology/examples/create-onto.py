import os, sys

saved_dir = os.getcwd()
os.chdir('../..')
sys.path.append(os.getcwd())
os.chdir(saved_dir)

from utils.docstructure.main import Parser

f = 'DE4214475A1.xml'
(source_file, ds_text_file, ds_tags_file , ds_fact_file, ds_sect_file, target_file) = \
    (f, f+".txt", f+".tags", f+".fact", f+".sect", f+".onto")

parser = Parser()

parser.create_ontology_creation_input(
    source_file, ds_text_file, ds_tags_file , ds_fact_file, ds_sect_file, target_file)
