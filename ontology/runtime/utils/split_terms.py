import codecs

TERMS_FILE = 'all_terms.txt'

SQL_STRING = """
-- sqlite3 all_terms.db < all_terms.sql
.echo ON  
PRAGMA cache_size = 500000; 
PRAGMA synchronous = OFF; 
PRAGMA journal_mode = OFF; 
PRAGMA locking_mode = EXCLUSIVE; 
PRAGMA count_changes = OFF; 
PRAGMA temp_store = MEMORY; 
PRAGMA auto_vacuum = NONE;  
CREATE TABLE terms(term TEXT);
.separator "\t"
.import /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/classifier/terms/terms_%s.txt terms
CREATE INDEX i_term on terms (term);
.exit
"""


def create_shell_file():
    """Generates a shell file that takes all the files created with
    split_on_first_character() and build sqlite databases."""
    fh_shell = open("terms.sh", 'w')
    bins = '0abcdefghijklmnopqrstuvwxyz'
    for s in bins:
        sql_file = "terms/terms_%s.sql" % s
        db_file = "terms/terms_%s.db" % s
        sql_string = SQL_STRING % s
        fh = open(sql_file, 'w')
        fh.write(sql_string)
        fh_shell.write("echo $ sqlite3 %s < %s\n" % (db_file, sql_file))
        fh_shell.write("sqlite3 %s < %s\n" % (db_file, sql_file))
        fh_shell.write("echo\n\n")
    
def split_in_buckets():
    """Split the terms file in buckets of at most 1M tertms."""
    count = 0
    fh = codecs.open('tmp.txt', 'w', encoding='utf-8')
    for line in codecs.open(TERMS_FILE, encoding='utf-8'):
        if count % 1000000 == 0:
            print count
            fh.close()
            fh = codecs.open("all_terms_%08d.txt" % count, 'w', encoding='utf-8')
        fh.write(line)
        count += 1


def split_on_first_character():
    """Split the terms file in buckets where the buckets eac have terms that
    start with the same letter (plus a rest bucket with terms that do not start
    with a letter."""
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    alphabet_idx = {}
    for c in alphabet:
        alphabet_idx[c] = True
    fhs = {}
    for c in '0' + alphabet:
        fhs[c] = codecs.open("terms/terms_%s.txt" % c, 'w', encoding='utf-8')
    count = 0
    for line in codecs.open(TERMS_FILE, encoding='utf-8'):
        count += 1
        if count % 1000000 == 0: print count
        #if count > 1000000: break
        first = line[0]
        fh = fhs[first] if alphabet_idx.has_key(first) else fhs['0']
        fh.write(line)
            

if __name__ == '__main__':

    split_on_first_character()
