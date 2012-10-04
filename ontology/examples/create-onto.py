import os, sys

saved_dir = os.getcwd()
os.chdir('../..')
sys.path.append(os.getcwd())
os.chdir(saved_dir)

from utils.docstructure.main import Parser

parser = Parser()

if 0:
    parser.language = 'GERMAN'
    f = 'DE4214475A1.xml'
else:
    parser.language = 'CHINESE'
    f = 'CN201693419U.xml'

(source_file, ds_text_file, ds_tags_file , ds_fact_file, ds_sect_file, target_file) = \
    (f, f+".txt", f+".tags", f+".fact", f+".sect", f+".onto")


parser.create_ontology_creation_input(
    source_file, ds_text_file, ds_tags_file , ds_fact_file, ds_sect_file, target_file)
