# term_db.py
# create a database mapping terms and features to sentences
# each database corresponds to a single patent application year


from ontology.utils import file

def process_filelist(f_filelist):
    fh = open(filelist)
    for line in fh:
        line = line.strip()
    
    fh.close()
