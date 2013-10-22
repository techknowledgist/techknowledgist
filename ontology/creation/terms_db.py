"""
terms_db.py

Classes that act as an interface to the index database for terms

It may be better to use apsw to interface with sqlite.  apsw promises to handle unicode correctly
and allow greater control over transactions.

We should populate the database before creating indexes and do it in large transactions, rather than
committing after each row update.  It appears that explicit commits are required for data to stay 
in db.

Note that pysqlite is the same as sqlite3

Based on np_db.py in which Marc comments:
Based on an older version by PGA (from 10/25/12), but transformed to such an
extent that the original is not recognizable anymore. See discarded/np_db.py for
the first version. One of the reasons for all the changes was that the original
code would not scale to large data sets.

To test:
>>>  tdb = terms_db.TermsDB("/home/j/anick/temp/fuse/", "terms_db")
>>>  tdb.add("first term", "1990", "file1.xml")
>>>  tdb.cursor.execute("select doc,term,year from terms where term = 'test'").fetchall()
>>>  tdb.cursor.execute("select * from terms where term = 'test'").fetchall()
>>>   l_3 = ['test', '1990', 'file5.xml', 0, 0, 0, 0, 0]
>>>   l_2 = ['test', '1990', 'file4.xml', 0, 0, 0, 0, 0]
>>>   l_1 = ['testy', '1990', 'file5.xml', 0, 0, 0, 0, 0]
>>>   tdb.addmany([l_1, l_2, l_3])
>>>   tdb.cursor.execute("select doc,term,year from terms where term = 'test'").fetchall()
[(u'file4.xml', u'test', u'1990'), (u'file5.xml', u'test', u'1990')]
>>>   tdb.cursor.execute("select doc,term,year from terms where term = 'testy'").fetchall()
[(u'file5.xml', u'testy', u'1990')]
>>>  tdb.commit()

# testing commit after cntl-c after 1000 + files
# >>> tdb.cursor.execute("select count(distinct doc) from terms").fetchall()
# [(1000,)]


NOTE:  Some terms containing / will have \\/ in their strings.  This could cause a problem if we are looking for
the string without the escape chars.  We might want to remove the \\ from all terms before loading into the db.

"""
import collections
import pdb
import os
import sys
import codecs
import apsw
import re
import config
import log
import math
from collections import defaultdict
from ontology.utils.file import get_year_and_docid, open_input_file
from operator import itemgetter, attrgetter

debug_p = False

#global dictionary mapping year to # docs
# created by querying the cs_terms_db terms table:
# select count(distinct(doc)) from terms where year = 2002; 
d_corpus_size = {2003: 32106, 2002: 28188, 2001: 12918, 2000: 8354, 1999: 8769, 1998: 8534, 1997: 4974} 

class Database(object):

    """Abstract class that contains some basic code for database
    connectivity.

    For a schema with a key constraint use:
    CREATE TABLE name (column defs, UNIQUE (col_name1, col_name2) ON CONFLICT REPLACE);
    Working example:
    CREATE TABLE a (i INT, j INT, UNIQUE(i, j) ON CONFLICT REPLACE);
    """

    def __init__(self, dir, db_file, schema):
        """Open the db_file database and create a cursor object. Create the
        schema if db_file did not exist."""
        self.db_file = os.path.join(dir, db_file)
        self.inserts = 0
        self.updates = 0
        db_existed = os.path.exists(self.db_file)
        self.connect()
        if not db_existed:
            for q in schema:
                print "Database__init__: Create command: %s" % q
                self.cursor.execute(q)

    def connect(self):
        self.connection = apsw.Connection(self.db_file)
        self.cursor = self.connection.cursor()

    def execute(self, caller, query, values):
        try:
            self.cursor.execute(query, values)
        except apsw.ConstraintError:
            print "[%s] WARNING: ignored duplicate value: %s" % (caller, values)
        except apsw.ProgrammingError:
            print "[%s] WARNING: %s" % (caller, sys.exc_value)

    def executemany(self, caller, query, l_tuple):
        try:
            self.cursor.executemany(query, l_tuple)
        except apsw.ConstraintError:
            print "[%s] WARNING: Detected duplicate value in tuple list and exited" % (caller)
        except apsw.Error:
            print "[%s] WARNING: %s" % (caller, sys.exc_value)



    def commit_and_close(self):
        self.commit()
        self.close()

    def begin(self):
        self.cursor.execute('BEGIN')

    def commit(self):
        self.cursor.execute('COMMIT')

    def close(self):
        self.cursor.close()
        self.connection.close()

    def reset_counts(self):
        self.inserts = 0
        self.updates = 0



# Optimization notes:
# Remove the UNIQUE constraint after testing code to avoid the overhead of a supporting index we don't 
# otherwise need during database population.
# Add the term_year_index after the database is fully populated to avoid overhead.
# Drop the term_year_index if there is a need to add more entries to the terms table and then recreate it.
# To avoid commit transaction overhead, put as many rows into the addmany list as possible for each call.
# Adding some PRAGMA statements may help.
class TermsDB(Database):
    # test dups, transactions, etc.  
    # the term and doc together should uniquely define a record.
    TERMS_TABLE = "CREATE TABLE terms(term TEXT, doc TEXT, year INT, total INT, title INT, abstract INT, summary INT, desc INT, first INT, other INT, s_total INT, s_title INT, s_abstract INT, s_summary INT, s_desc INT, s_first INT, s_other INT, UNIQUE(term, doc))"
    SCHEMA = [TERMS_TABLE]

    def __init__(self, dir, db_file):
        """Open the terms database, creating it if needed."""
        Database.__init__(self, dir, db_file, TermsDB.SCHEMA)
        #print "[TermsDB] Opened database in %s" % self.db_file

    def add(self, term, doc, year=9999, total=0, title=0, abstract=0, summary=0, desc=0, first=0, other=0, s_total=0, s_title=0, s_abstract=0, s_summary=0, s_desc=0, s_first=0, s_other=0):
        query = "INSERT INTO terms VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        self.execute('TermsDB.add', query, (term, doc, year, title, abstract, summary, desc, first, other, s_total, s_title, s_abstract, s_summary, s_desc, s_first, s_other))

    def addmany(self, l_tuple):
        query = "INSERT INTO terms VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        self.executemany('TermsDB.addmany', query, l_tuple)

    # convert phr_feats term information into tuples and add them to db
    def add_phr_feats_file(self, phr_feats_file, year, transaction_p=False):
        l_tuples = phr_feats2tuples(phr_feats_file, year)
        if transaction_p: 
            self.begin()
        self.addmany(l_tuples)
        if transaction_p:
            self.commit()

    def add_term_year_index(self):
        query = "CREATE INDEX term_year_index ON terms (term, year)"
        self.execute('TermsDB.add_term_year_index', query, ())

    def drop_term_year_index(self):
        query = "DROP INDEX term_year_index"
        self.execute('TermsDB.drop_term_year_index', query, ())

# Given a phr_feats file, return a list of tuples compatible with terms_db rows.

class Tcounts:
    def __init__(self, total=0, title=0, abstract=0, summary=0, desc=0, first=0, other=0, s_total=0, s_title=0, s_abstract=0, s_summary=0, s_desc=0,s_first=0, s_other=0):
        self.total = total
        self.title = title
        self.abstract = abstract
        self.summary = summary
        self.desc = desc
        self.first = first
        self.other = other

        self.s_total = s_total
        self.s_title = s_title
        self.s_abstract = s_abstract
        self.s_summary = s_summary
        self.s_desc = s_desc
        self.s_first = s_first
        self.s_other = s_other



    # increment phrase count for section in which it is found
    def incr(self, section, subphrase_match_p=False):
        if subphrase_match_p:
            # update the fields corresponing to subphrase occurrence counts

            self.s_total += 1
            if section == "TITLE":
                self.s_title += 1
            elif section == "ABSTRACT":
                self.s_abstract += 1
            elif section == "SUMMARY":
                self.s_summary += 1
            elif section == "DESC":
                self.s_desc += 1
            elif section == "FIRST":
                self.s_first += 1
            elif section == "OTHER":
                self.s_other += 1

        else:
            # update the fields corresponding to standalone phrase match counts    

            self.total += 1
            if section == "TITLE":
                self.title += 1
            elif section == "ABSTRACT":
                self.abstract += 1
            elif section == "SUMMARY":
                self.summary += 1
            elif section == "DESC":
                self.desc += 1
            elif section == "FIRST":
                self.first += 1
            elif section == "OTHER":
                self.other += 1

    # given a phr_feats line, increment the counts for the section
    def incr_section(self, line):
        self.incr(find_section(line))

    def make_row(self, term, doc, year):
        return([term, doc, int(year), self.total, self.title, self.abstract, self.summary, self.desc, self.first, self.other, self.s_total, self.s_title, self.s_abstract, self.s_summary, self.s_desc, self.s_first, self.s_other])

# example of a phr_feats line:  
# US20020002483A1.xml_6   2002    apparatus       doc_loc=2       section_loc=ABSTRACT_sent1      sent_loc=3-4    suffix3=tus


def find_section(line):
    #print("line is: %s" % line)
    matchObj = re.search(r'(section_loc=)([^_]*)', line)
    #print("match is: %s" % matchObj.group(2))
    return(matchObj.group(2))

# terms_db.phr_feats2tuples("...
def phr_feats2tuples(phr_feats_file, year):
    doc = os.path.basename(phr_feats_file).split(".")[0]
    #print "[phr_feats2tuples]loading doc: %s, basename: %s" % (phr_feats_file, doc)
    d_terms = defaultdict(Tcounts)
    l_tuples = []
    # handle compressed or uncompressed files
    
    s_phr_feats = open_input_file(phr_feats_file)
    line_no = 1

    # For each line in phr_feats file, 
    for line in s_phr_feats:
        term = line.split("\t")[2]

        # skip lines containing quotes.  These are bad terms and will cause
        # the sqlite3 shell trouble parsing the data.
        if term.find('"') < 0:
            #print "term is: %s" % term
            section = find_section(line)

            counts = d_terms[term]
            counts.incr(section, subphrase_match_p=False)

            # Now update subphrase counts for all subphrases of the term
            # (including the term itself)
            for subphrase in subphrases(term, d_subphrases):
                sp_counts = d_terms[subphrase]
                sp_counts.incr(section, subphrase_match_p=True)

            #print "processed line: %i" % line_no
            line_no += 1

    #print "[phr_feats2tuples]processed %i lines. " % line_no
    s_phr_feats.close()

    for key in d_terms.keys():
        l_tuples.append(d_terms[key].make_row(key, doc, year))
        #print "l_tuples: %s" % l_tuples

    return(l_tuples)


d_subphrases = {}
# keep an external subphrase dict, to avoid need to recompute
# return all subphrases (including the original phrase)
def subphrases(phrase, d_subphrases):
    l_subphrases = []
    
    if d_subphrases.has_key(phrase):
        return d_subphrases[phrase]
    else:
        l_phrase = phrase.split(" ")
        plen = len(l_phrase)

        if plen == 1:
            return([phrase])
        else:

            for start in range(0, plen):
                for end in range(start + 1, plen + 1):
                    # turn list back into a string and add to the list of subphrases
                    l_subphrases.append(" ".join(l_phrase[start:end]))
                
        d_subphrases[phrase] = l_subphrases
        return(l_subphrases)


# db_dir should be full path ending in slash
# root dir is location of phr_feats files, typically the path up to the year
# specify a year in year_filter to limit files to process to a given year
def load_terms_db(root_dir, filelist_file, db_dir, transaction_length=1000, year_filter=0):
    # get database handle (and create db if it doesn't yet exist)
    tdb = TermsDB(db_dir, "terms_db")
    logfile = db_dir + "terms_db.log"
    s_log = open(logfile, "w")
    file_count = 1
    filename = ""
    # start a transaction
    tdb.begin()
    start_time = log.log_current_time(s_log, "start", True)
    s_filelist = codecs.open(filelist_file, encoding='utf-8')
    for line in s_filelist:
        line = line.strip("\n")
        l_line = line.split("\t")
        year = int(l_line[0])
        if year == 0 or year == year_filter:
            filename = l_line[2]
            phr_feats_file = root_dir + filename
            #pdb.set_trace()
            tdb.add_phr_feats_file(phr_feats_file, year, transaction_p=False)

            if file_count%transaction_length == 0:
                tdb.commit()
                tdb.begin()
                log_message = "file " + str(file_count) +  ": " + filename
                log.log_time_diff(start_time, s_log, log_message, True)
            file_count += 1

    log_message = "file " + str(file_count) +  ": " + filename
    log.log_time_diff(start_time, s_log, log_message, True)

    s_filelist.close()
    s_log.close()
    tdb.commit_and_close()

# create a tab separated string from a list of items
def list2tsv(l_items):
    return '\t'.join(unicode(item) for item in l_items)

# create a tab separated string from a list of floating point items.
# floating point numbers in list to be truncated to 2 decimal digits
def flist2tsv(l_items):
    return '\t'.join(unicode('%.2f' % item) for item in l_items)


# Generator for files in a corpus, given a file_type and year
# root_dir = "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files/"
# terms_db.patent_filelist_iter("/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/", "phr_feats", 1998)
def patent_filelist_iter(corpus_dir, file_type, year_filter):
    #print "filelist_file: %s" % filelist_file
    f_year = 0
    f_filename = 2

    if file_type == "phr_feats":
        target_subpath = "/data/d3_phr_feats/01/files/"
    else:
        print "[patent_filelist_iter]Error: unknown file_type: %s" % file_type
        exit()

    # locate the files.txt filelist in the corpus_dir
    corpus_dir = corpus_dir.rstrip("/")
    filelist_file = corpus_dir + "/config/files.txt"
    s_filelist = codecs.open(filelist_file, encoding='utf-8')
    for line in s_filelist:
        line = line.strip("\n")
        l_field = line.split("\t")
        year = int(l_field[f_year])
        #print "year is: %i" % year
        if year_filter == 0 or year_filter == year:

            filename = l_field[f_filename]
            target_file = corpus_dir + target_subpath + filename
            yield(target_file)
    s_filelist.close()

# output a csv file suitable for bulk loading into a database
# separator is a tab rather than comma
def create_csv_file(root_dir, filelist_file, db_dir, csv_file_prefix, transaction_length=1000, year_filter=0):
    csv_file = db_dir + csv_file_prefix + ".csv"
    s_csv = codecs.open(csv_file, "w", encoding='utf-8')
    logfile = db_dir + "terms_csv.log"
    s_log = open(logfile, "w")
    file_count = 1
    filename = ""
    # start a transaction
    start_time = log.log_current_time(s_log, "start", True)
    s_filelist = codecs.open(filelist_file, encoding='utf-8')
    #print "filelist_file: %s" % filelist_file
    for line in s_filelist:
        line = line.strip("\n")
        l_line = line.split("\t")
        year = int(l_line[0])
        #print "year is: %i" % year
        if year_filter == 0 or year_filter == year:

            filename = l_line[2]
            phr_feats_file = root_dir + filename
            #print "[create_csv_file]file: %s, year: %i" % (phr_feats_file, year)
            #pdb.set_trace()
            #tdb.add_phr_feats_file(phr_feats_file, year, transaction_p=False)
            l_tuples = phr_feats2tuples(phr_feats_file, year)
            for tuple in l_tuples:
                s_csv.write("%s\n" % list2tsv(tuple))
            if file_count%transaction_length == 0:
                log_message = "file " + str(file_count) +  ": " + filename
                log.log_time_diff(start_time, s_log, log_message, True)
            file_count += 1
    
    log.log_time_diff(start_time, s_log, "Completed csv file creation", True)

    s_filelist.close()
    s_log.close()
    s_csv.close()



# tdb = terms_db.test1()
# tdb.cursor.execute("select doc,term,year from terms where term = 'test'").fetchall()
def test1():
    root_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/"
    # NOTE: the file extension should not include .gz here even if it is .gz in the files directory.
    #rel_file = "US20020002483A1.xml"
    #rel_file = "US6499121B1.xml"
    rel_file = "US6470395B1.xml"
    phr_feats_file = root_dir + "data/d3_phr_feats/01/files/2002/" + rel_file
    #file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/d3_phr_feats/01/files/2002/US20020002483A1.xml.gz"

    year = "2002"
    #l_rows = phr_feats2tuples(phr_feats_file, year) 
    #return(l_rows)

    # open db and insert tuples for phr_feats file
    
    tdb = TermsDB("/home/j/anick/temp/fuse/", "terms_db")
    tdb.add_phr_feats_file(phr_feats_file, year, transaction_p=True)
    return(tdb)

# terms_db.test2_csv()
def test2_csv():
    filelist_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt"
    root_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/d3_phr_feats/01/files/"
    db_dir = "/home/j/anick/temp/fuse/"
    csv_file_prefix = "cs_2002_subset"

    create_csv_file(root_dir, filelist_file, db_dir, csv_file_prefix, transaction_length=20, year_filter=0)


# terms_db.test2()
def test2():
    filelist_file = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/config/files.txt"
    root_dir = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_2002_subset/data/d3_phr_feats/01/files/"
    db_dir = "/home/j/anick/temp/fuse/"
    load_terms_db(root_dir, filelist_file, db_dir, transaction_length=20, year_filter=2002)
    print "loaded terms"

# terms_db.load_cs(1998)
def load_cs(year):
    filelist_file = "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/config/files.txt"
    root_dir = "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files/"
    db_dir = "/home/j/anick/temp/fuse/"
    load_terms_db(root_dir, filelist_file, db_dir, transaction_length=1000, year_filter=year)
    print "loaded terms"

# terms_db.load_cs_csv(2003)
def load_cs_csv(year):
    filelist_file = "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/config/files.txt"
    root_dir = "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files/"
    db_dir = "/home/j/anick/temp/fuse/"
    csv_file_prefix = "cs" + str(year)

    create_csv_file(root_dir, filelist_file, db_dir, csv_file_prefix, transaction_length=1000, year_filter=year)
    print "Finished creating csv file"

# tdb = terms_db.handle()
def handle():

    return(TermsDB("/home/j/anick/temp/fuse/", "terms_db"))


# terms_db.term_year("/home/j/anick/temp/fuse/zero_9798_to50.annot", "/home/j/anick/temp/fuse/zero_9798_to50.annot.out")
# terms_db.term_year("/home/j/anick/temp/fuse/zero_9798_2_to_lt5.filtered.500.annot", "/home/j/anick/temp/fuse/zero_9798_2_to_lt5.filtered.500.annot.out")

# outputs each year's documents' section counts for the term

# input is of the form:
# y       active server page      0       0       1       2       24      100     83
# i.e. second column in input_file is the term

# NOTE: To intepret the data, the input file is based on terms for which at least one
# document in the year contains the exact chunk (not just as a subphrase).  Thus, the 
# subphrase counts are limited to those years in which the chunk by itself occurs somewhere.
# This explains why some records do not have a chunk count > 0.  They are there because
# the subphrase count > 0.  As a result, when we compute the probability of a section containing
# a term, we need to base it on the number of docs containing the chunk (for chunks) or the 
# number of docs containing a subphrase (for subphrases).  Subphrases include the chunk in the counts.

# start_year is the first year in which the chunk count >= 1
# currently we don't use this.  But we need to know what was the start year.  This
# could be establish by the sql query that we ran to generate the term list.
def term_year_old(input_file, output_file, start_year=1999):
    s_in = codecs.open(input_file, encoding='utf-8')
    s_totals_out = codecs.open(output_file, encoding='utf-8', mode="w")
    s_prob_out = codecs.open(output_file + ".prob", encoding='utf-8', mode="w")

    db = Database("/home/j/anick/temp/fuse/", "cs_terms_db", "") 
    #db.cursor.execute(".mode tabs")
    #l_term = ["border gateway protocol", "apache web server"]
    for line in s_in:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[1]

        #print "line: %s" % line
        for year in [1997, 1998, 1999, 2000, 2001, 2002, 2003]:
            # save up the rows per year to compute summary data
            l_rows = []
            for row in db.cursor.execute("select * from terms where term = ? and year = ?", ([term, year])):
                s_totals_out.write("%s\n" % list2tsv(row) )
                l_rows.append(row)
            # compute the summary
            # this records the number of docs for which a term shows up in a section.
            
            summary_row = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]

            for row in l_rows:
                for i in range(3,17):
                    j = i - 3
                    if row[i] > 0:
                        summary_row[j] += 1
          
            # prepare list for output
            # Verify whether there was data for the given year
            if len(l_rows) > 0:
                term = l_rows[0][0]
                year = unicode(l_rows[0][2])
                # compute prob of term showing up in section
                # as num section occurrences/num docs
                num_docs_with_chunk = float(summary_row[0])
                num_docs_with_subphrase = float(summary_row[7])
                for j in range(0,7):
                    # it is possible that there are no docs with chunks in this year.  
                    # Make the probs 0 in this case.
                    if num_docs_with_chunk == 0.0:
                        summary_row[j] = unicode('%.2f' % 0.0 )
                    else:
                        prob = summary_row[j] / num_docs_with_chunk
                        summary_row[j] = unicode('%.2f' % prob )

                for j in range(7,14):
                    prob = summary_row[j] / num_docs_with_subphrase
                    summary_row[j] = unicode('%.2f' % prob )

                summary_line = term + "\t" + year + "\t" + list2tsv(summary_row)
                s_prob_out.write("%s\n" % summary_line)

    s_totals_out.close()
    s_prob_out.close()

#####################################################################
# term_idx is the index of the term in whatever input file you use
def term_year(input_file, output_file, term_idx=1):
    s_in = codecs.open(input_file, encoding='utf-8')
    s_totals_out = codecs.open(output_file, encoding='utf-8', mode="w")
    s_prob_out = codecs.open(output_file + ".prob", encoding='utf-8', mode="w")
    db = Database("/home/j/anick/temp/fuse/", "cs_terms_db", "") 
    #db.cursor.execute(".mode tabs")
    #l_term = ["border gateway protocol", "apache web server"]
    for line in s_in:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[1]
        
        summary_line = term_loc_by_year(term, db)
        if summary_line != "":
            s_prob_out.write("%s\n" % summary_line)

    s_totals_out.close()
    s_prob_out.close()

# terms_db.term_loc_by_year("entitlement management", db, "count")
def term_loc_by_year(term, db, output_type="prob"):
    #print "line: %s" % line
    l_summary_line = []
    for year in [1997, 1998, 1999, 2000, 2001, 2002, 2003]:
        # save up the rows per year to compute summary data
        l_rows = []
        cmd = "select * from terms where term = \"" + term + "\" and year = " + str(year) 
        print "cmd: %s" % cmd
        
        for row in db.cursor.execute( cmd ):
            #s_totals_out.write("%s\n" % list2tsv(row) )
            #print "%s\n" % list2tsv(row)
            l_rows.append(row)
        # compute the summary
        # this records the number of docs for which a term shows up in a section.

        summary_row = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        for row in l_rows:
            for i in range(3,17):
                j = i - 3
                if row[i] > 0:
                    summary_row[j] += 1

        # prepare list for output
        # Verify whether there was data for the given year
        if len(l_rows) > 0:
            term = l_rows[0][0]
            year = unicode(l_rows[0][2])
            # compute prob of term showing up in section
            # as num section occurrences/num docs
            num_docs_with_chunk = float(summary_row[0])
            num_docs_with_subphrase = float(summary_row[7])
            for j in range(0,7):
                # it is possible that there are no docs with chunks in this year.  
                # Make the probs 0 in this case.
                if num_docs_with_chunk == 0.0:
                    summary_row[j] = unicode('%.2f' % 0.0 )
                else:
                    prob = summary_row[j] / num_docs_with_chunk
                    summary_row[j] = unicode('%.2f' % prob )

            for j in range(7,14):
                prob = summary_row[j] / num_docs_with_subphrase
                summary_row[j] = unicode('%.2f' % prob )

            summary_line = term + "\t" + year + "\t" + list2tsv(summary_row)
            l_summary_line.append(summary_row)
    return(l_summary_line)


    
# computes average value of each column for the key
# key is first item in tab separated file                                         
# number of columns must be the same for each line (and num_cols should not include the key field)

# create a list with num_cols 0's.
def zero_sum_list(num_cols, num_type="f"):
    l_init = []
    for i in range(0,num_cols):
        if num_type == "f":
            l_init.append(0.0)
        elif num_type == "i":
            l_init.append(0)
    return l_init

# terms_db.average_key_tsv("/home/j/anick/temp/fuse/zero_9798_to50.annot.10.out.prob.year_probs", "none", 14) 
# terms_db.average_key_tsv("/home/j/anick/temp/fuse/zero_9798_to50.annot.out.prob.year_probs", "none", 14) 
# terms_db.average_key_tsv("/home/j/anick/temp/fuse/zero_9798_2_to_lt5.filtered.500.annot.out.prob.year_probs", "none", 14) 
def average_key_tsv(input_file, output_file, num_cols):
    l_init = zero_sum_list(num_cols)
    def zsfactory ():
        # return a <new copy> of the zero_sum_list
        return list(l_init)
    d_key2count = collections.defaultdict(int)
    d_key2sums = collections.defaultdict(zsfactory)
    s_input = codecs.open(input_file, encoding='utf-8')
    for line in s_input:
        #print "line: %s" % line
        line = line.strip()
        line_fields = line.split("\t") 
        key = line_fields[0]
        l_cols = line_fields[1:]
        
        # add to count for this key
        d_key2count[key] += 1
        for i in range(0,num_cols):
            #print "i: %i, val: %s" % (i, l_cols[i])
            # add to sum for the column
            d_key2sums[key][i] += float(l_cols[i])
            
        #print "d_key2sums[%s]: %s" % (key, d_key2sums[key])
            
    # compute the average for each key
    for key in sorted(d_key2count.keys()):
        count = d_key2count[key]
        l_sums = d_key2sums[key]
        #print "key: %s, count: %i, l_sums: %s" % (key, count, l_sums)
        l_avg = []
        for i in range(0,num_cols):
            l_avg.append(l_sums[i] / count)
        key_avg_line = key + "\t" + flist2tsv(l_avg)
        print key_avg_line


"""
For each term in term_file, get the sets of phrases containing the term and compute:
For each term and year, compute dispersion at 1 and dispersion at 2.
Dispersion at n means the number of phrases which appear in n docs.
Head dispersion = # of different head terms dominating the term
Modifier dispersion = # of different modifiers modifying the term

Ideally we could also have a Dispersion at A where A is number of different assignees.

Dh1
Dh2
Dm1
Dm2
"""
# terms_db.dispersion_by_year(""...)
def dispersion_by_year(term, s_out, num_years, db):
    l_init = zero_sum_list(num_years, "i")
    def zsfactory ():
        # return a <new copy> of the zero_sum_list
        return list(l_init)

    # initialize year lists for each kind of dispersion 
    l_dh1 = list(l_init)
    l_dh2 = list(l_init)
    l_dm1 = list(l_init)
    l_dm2 = list(l_init)

    cmd = "select * from chunk_counts where term = \"" + term + "\""
    result = db.cursor.execute(cmd).fetchall()

    if len(result) > 0:
        l_res = result[0][1:]
        print "chunk counts: %s" % (result[0][1:],)

    cmd = "select * from counts where term = \"" + term + "\""
    result = db.cursor.execute(cmd).fetchall()

    if len(result) > 0:
        l_res = result[0][1:]
        #print "all context counts tuple: %s" % (list2tsv(result[0][1:]),)
        print "all context counts: %s" % (result[0][1:],)



    # run query for dispersion of head terms
    # the db row will contain term, then a column for each year
    end_of_row_range = num_years + 1
    #term_with_variable_head = "\'" + term + " %\'"
    term_with_variable_head = term + " %"
    #print "term: %s" % term_with_variable_head

    cmd = "select * from chunk_counts where term like \"" + term + " %\""
    #print "cmd: %s" % cmd
    #for row in db.cursor.execute("select * from chunk_counts where term like ? ", ([term_with_variable_head])):
    for row in db.cursor.execute(cmd):
        #print "head row: %s" % list2tsv(row)
        for year_idx in range(1, end_of_row_range):
            disp_idx = year_idx - 1
            # increment appropriate dispersion counts if phrase exists with count == 1 or >1
            if row[year_idx] >= 2:
                l_dh1[disp_idx] += 1
                l_dh2[disp_idx] += 1
            elif row[year_idx] == 1:
                l_dh1[disp_idx] += 1

    print "dh1: %s" % l_dh1
    print "dh2: %s" % l_dh2

    """
    term_with_variable_mod = "\"% " + term + "\""
    #print "term: %s" % term_with_variable_mod
    cmd = "select * from chunk_counts where term like \"% " + term + "\""
    for row in db.cursor.execute(cmd):
        #print "mod row: %s" % list2tsv(row)
        for year_idx in range(1, end_of_row_range):
            disp_idx = year_idx - 1
            # increment appropriate dispersion counts if phrase exists with count == 1 or >1
            if row[year_idx] >= 2:
                l_dm1[disp_idx] += 1
                l_dm2[disp_idx] += 1
            elif row[year_idx] == 1:
                l_dm1[disp_idx] += 1
    
    print "dm1: %s" % l_dm1
    print "dm2: %s" % l_dm2
    """

# terms_db.test_disp("internet search engine")
# terms_db.test_disp("")
def test_disp(term):
    db = Database("/home/j/anick/temp/fuse/", "cs_terms_db", "") 
    num_years = 7
    disp_file = "disp.tsv"
    s_out = codecs.open(disp_file, "w", encoding='utf-8')
    dispersion_by_year(term, s_out, num_years, db)
    s_out.close()

# assign floating point numbers in range 1 to -1 into 10 bins.                                                       
# We will use the bins to generate a balanced random sample of training and test instances                           
def bin_num(num):
    bin = 0
    if num > .9:
        bin = 9
    elif num > .8:
        bin = 8
    elif num > .7:
        bin = 7
    elif num > .6:
        bin = 6
    elif num > .5:
        bin = 5
    elif num > .4:
        bin = 4
    elif num > .3:
        bin = 3
    elif num > .2:
        bin = 2
    elif num > .1:
        bin = 1
    else:
        bin = 0
    return(bin)

# generate a file with counts and chunk_counts for the years 2002, 2003
# run this over a file containing a list of terms
# cat terms_br_nyu_mitre.sorted.keep.uniq | cut -f1 > terms_br_nyu_mitre.terms
# terms_db.term_file_counts("/home/j/anick/temp/fuse/terms_br_nyu_mitre.terms", "/home/j/anick/temp/fuse/terms_br_nyu_mitre.brprom")
# outputs binned terms with their brandeis prominence for 2003 (from 2002)
def term_file_counts(term_file, out_file):
    db = Database("/home/j/anick/temp/fuse/", "cs_terms_db", "") 
    s_term = codecs.open(term_file, encoding='utf-8')
    s_out = codecs.open(out_file, "w", encoding='utf-8')
    for line in s_term:
        term = line.strip()
        output_line = term_counts(term, db)
        s_out.write("%s\n" % output_line)

    s_out.close()
    s_term.close()

# terms_db.term_counts("vsat", db, 2002, 2003)
def term_counts(term, db, ref_year=2002, pred_year=2003):
    # convert years to db field names
    ref_field = "c" + str(ref_year)
    pred_field = "c" + str(pred_year)

    cmd1 = "select " + ref_field + "," + pred_field + " from chunk_counts where term = \"" + term + "\""
    cmd2 = "select " + ref_field + "," + pred_field + " from counts where term = \"" + term + "\""

    print "cmd1: %s" % cmd1
    print "cmd2: %s" % cmd2
    result1 = db.cursor.execute(cmd1).fetchall()
    result2 = db.cursor.execute(cmd2).fetchall()
    # handle empty results by replacing with (0,0) tuples
    # If term exists, it should result in a list of one tuple
    if result1 == []:
        result1 = (0,0)
    else:
        result1 = result1[0]

    if result2 == []:
        result2 = (0,0)
    else:
        result2 = result2[0]

    # compute "prominence" as 2003-2002/2003+2002
    prom1 = (result1[1] - result1[0])/(result1[1] + result1[0] + .000001)
    prom2 = (result2[1] - result2[0])/(result2[1] + result2[0] + .000001)
    avg = (prom1 + prom2) / 2

    bin = bin_num(avg)
    # create the output line
    # term prom1 prom2 #chunk_2002 #chunks_2003 #subphrases_2002 #subphrases_2003
    output_line = list2tsv([bin, term, ('%.2f' % avg), ('%.2f' % prom1), ('%.2f' % prom2), result1[0], result1[1], result2[0], result2[1]])
    #print "output_list: %s" % output_line
    return(output_line)
    
# Takes the output of term_file_counts() and modifies the prominence score by multiplying by the 
# factor:  (count of docs containing subphrase in abstract / count of docs containing subphrase) in year 2003 (prediction year).
# It also removes any terms which don't appear as chunks in 2002 (reference year)
# terms_db.term_count_w_abstracts("/home/j/anick/temp/fuse/terms_br_nyu_mitre.brprom", "/home/j/anick/temp/fuse/terms_br_nyu_mitre.brprom.abs")

# test with
# terms_db.term_count_w_abstracts("/home/j/anick/temp/fuse/terms_br_nyu_mitre.brprom.5", "/home/j/anick/temp/fuse/terms_br_nyu_mitre.brprom.abs", 2003)
# terms_br_nyu_mitre.brprom.5
def term_count_w_abstracts(binned_term_file, modified_term_file, year):
    db = Database("/home/j/anick/temp/fuse/", "cs_terms_db", "") 
    s_term = codecs.open(binned_term_file, encoding='utf-8')
    s_out = codecs.open(modified_term_file, "w", encoding='utf-8')
    for line in s_term:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[1]
        avg_change = float(l_fields[2])
        # how many docs contained chunk in 2002?
        ref_chunk_count = int(l_fields[5])
        ref_subphrase_count = int(l_fields[6])
        pred_chunk_count = int(l_fields[7])
        pred_subphrase_count = int(l_fields[8])
        
        if ref_chunk_count > 0:
            abstract_count = abstract_subphrase_count(term, year, db)
            abstract_percent = abstract_count / (pred_subphrase_count + .00001)
            score = avg_change * abstract_percent
            bin = bin_num(score)
            output_list = [bin, term, ('%.2f' % score), avg_change, abstract_count, ref_chunk_count, ref_subphrase_count, pred_chunk_count, pred_subphrase_count]
        
            output_line = list2tsv(output_list)
            s_out.write("%s\n" % output_line)

    s_out.close()
    s_term.close()

# terms_db.abstract_subphrase_count("rfid readers", 2003, db)
def abstract_subphrase_count(term, year, db):
    #cmd = "select count(*) from terms where s_abstract > 0 and year = " + str(year) + "  and term = \"" + term + "\""
    cmd = "select c" + str(year) + " from abstract_scounts where term = \"" + term + "\""
    if debug_p:
        print "[abstract_subphrase_count]cmd: %s" % cmd
    result = db.cursor.execute(cmd).fetchall()
    if result == []:
        result = 0
    else:
        result = result[0][0]
    return(result)

# terms_db.growth("web site", 2000, db)
def growth1(term, year, db, dist=1):
    # growth is based on substring counts for docs and abstracts
    # return raw counts and growth (computed as year-year-change / (prev_year + 1))
    prev_year = year - dist
    cmd_doc_counts = "select c" + str(prev_year) + ", c" + str(year) + " from counts where term = \"" + term + "\""
    cmd_abstract_counts = "select c" + str(prev_year) + ", c" + str(year) + " from abstract_scounts where term = \"" + term + "\""
    doc_counts = db.cursor.execute(cmd_doc_counts).fetchall()
    if doc_counts == []:
        doc_counts = 0
    else:
        doc_counts = doc_counts[0]

    abs_counts = db.cursor.execute(cmd_abstract_counts).fetchall()
    if abs_counts == []:
        abs_counts = 0
    else:
        abs_counts = abs_counts[0]

    abs_growth = (abs_counts[1] - abs_counts[0]) / (abs_counts[0] + 1.0)
    doc_growth = (doc_counts[1] - doc_counts[0]) / (doc_counts[0] + 1.0)
    print "[growth] doc_counts: %s, abs_counts: %s, doc_growth: %.2f, abs_growth: %.2f" % (doc_counts, abs_counts, doc_growth, abs_growth)


# terms_db.growth("web site", 2000, db)
def growth(term, year, db, dist=1):
    
    # growth is based on substring counts for docs and abstracts
    # return raw counts and growth (computed as year-year-change / (prev_year + 1))
    prev_year = year - 1
    cmd_doc_counts = "select c" + str(prev_year) + ", c" + str(year) + " from counts where term = \"" + term + "\""
    cmd_abstract_counts = "select c" + str(prev_year) + ", c" + str(year) + " from abstract_scounts where term = \"" + term + "\""
    doc_counts = db.cursor.execute(cmd_doc_counts).fetchall()
    if doc_counts == []:
        doc_counts = 0
    else:
        doc_counts = doc_counts[0]

    abs_counts = db.cursor.execute(cmd_abstract_counts).fetchall()
    if abs_counts == []:
        abs_counts = 0
    else:
        abs_counts = abs_counts[0]

    abs_growth = (abs_counts[1] - abs_counts[0]) / (abs_counts[0] + 1.0)
    doc_growth = (doc_counts[1] - doc_counts[0]) / (doc_counts[0] + 1.0)
    print "[growth] doc_counts: %s, abs_counts: %s, doc_growth: %.2f, abs_growth: %.2f" % (doc_counts, abs_counts, doc_growth, abs_growth)

    


# Let's try using log of the abstract count divided by log of total docs 
# (rather than docs containing the term) as our term importance metric
# terms_br_nyu_mitre.brprom.abs
# terms_db.abstract_count_mod("/home/j/anick/temp/fuse/terms_br_nyu_mitre.brprom.abs", "/home/j/anick/temp/fuse/terms_br_nyu_mitre.brprom.mod", 32091)
def abstract_count_mod(abs_file, out_file, pred_year_doc_count):
    denom = math.log(pred_year_doc_count, 2)
    s_in = codecs.open(abs_file, encoding='utf-8')
    s_out = codecs.open(out_file, "w", encoding='utf-8')
    for line in s_in:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[1]
        mult_score = float(l_fields[2])
        avg_change = float(l_fields[3])
        pred_abstract_count = int(l_fields[4])
        # how many docs contained chunk in 2002?
        ref_chunk_count = int(l_fields[5])
        ref_subphrase_count = int(l_fields[6])
        pred_chunk_count = int(l_fields[7])
        pred_subphrase_count = int(l_fields[8])
    
        log_ac = math.log((pred_abstract_count + 2), 2)
        log_dc = math.log((pred_subphrase_count + 2), 2)
        #importance_score = log_ac / denom
        #importance_score = log_ac 
        importance_score = log_ac / log_dc
        score = avg_change * importance_score
        
        bin = bin_num(score)
        output_list = [bin, term, ('%.2f' % score), ('%.2f' % importance_score), avg_change, pred_abstract_count, ref_chunk_count, ref_subphrase_count, pred_chunk_count, pred_subphrase_count]
        
        output_line = list2tsv(output_list)
        s_out.write("%s\n" % output_line)

    s_out.close()
    s_in.close()
    

# To create a file for generating train/test data:
# cat terms_br_nyu_mitre.brprom.mod | egrep -v '        1       '| sort -nr -k3,3 -t"   " > terms_br_nyu_mitre.brprom.mod.no1.nr
# Now randomize the file
# sort -R terms_br_nyu_mitre.brprom.mod.no1.nr > terms_br_nyu_mitre.brprom.mod.no1.random


# take a randomized binned_terms_file and extract sets of terms for training and testing
# 

def create_train_test(binned_terms_file, max_terms_per_bin, percent_train, train_out_file, test_out_file):
    d_bin = collections.defaultdict(list)
    d_bin_len = collections.defaultdict(int)
    s_bin = codecs.open(binned_terms_file, encoding='utf-8')
    s_train_out = codecs.open(train_out_file, "w", encoding='utf-8')
    s_test_out = codecs.open(test_out_file, "w", encoding='utf-8')
    for line in s_bin:
        line = line.strip()
        l_fields = line.split("\t")
        bin = int(l_fields[0])

        if d_bin_len[bin] < max_terms_per_bin:
            d_bin[bin].append(line)
            #print "d_bin[%i]: %s" % (bin, line)
            d_bin_len[bin] += 1
            #print "bin_len: %i" % (d_bin_len[bin])

    # allocate the selected terms to train and test
    for bin in range(0,10):
        bin_len = d_bin_len[bin]
        train_len = int(percent_train * bin_len)
        #print "train len for bin %i: %i" % (bin, train_len)
        #print "training lines:"
        for line in d_bin[bin][0:train_len]:
            s_train_out.write("%s\n" % line)

        #print "test lines:"
        for line in d_bin[bin][train_len:]:
            s_test_out.write("%s\n" % line)

        
    s_bin.close()
    s_train_out.close()
    s_test_out.close()

# terms_db.run_bin()
def run_bin():
    db_dir = "/home/j/anick/temp/fuse/"
    #inp = db_dir + "terms.2003.random"
    inp = db_dir + "terms_br_nyu_mitre.brprom.mod.no1.random"
    train = db_dir + "terms.mod.2003.train"
    test = db_dir + "terms.mod.2003.test"
    max_terms = 50
    percent_train = .7
    create_train_test(inp, max_terms, percent_train, train, test)

def run_2003():
    db_dir = "/home/j/anick/temp/fuse/"
    inp = db_dir + "terms_br_nyu_mitre.sorted.keep.uniq"
    out = db_dir + "terms.2003"
    rej = db_dir + "terms.2003.rejected"
    filter_2003(inp, out, rej)

# features for regresssion
# disp/head/mod for ref year and ref -1
# section locs for ref year and year -1

#----------------------------------------------------------------------

# terms_db.db_term_year2docs(db, "vsat", 2002, "s_abstract")
# return a list of doc names for which a term occurs within the section
def db_term_year2docs(db, term, year, section):
    cmd = "select doc from terms where term = \"" + term + "\" and year = " + str(year) + " and " + section + " > 0"
    print "cmd: %s" % cmd
    l_docid = []
    for docid in db.cursor.execute( cmd ):
        l_docid.append(docid)
        #print "docid: %s" % docid

    return(l_docid)



# WARNING: this function has dependencies on the year to directory mapping!!!
# return the terms in the abstracts of patents in the l_docid list
# This assumes that we know the file location, given the year and the root directory.
# However this will not be the case for the next CS database, in which application date
# and the year in the directory path (publication date) may differ.
# We should create a db table mapping docid to app_year pub_year directory?

"""
# For now root: /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files
def db_docs2cohort_old(l_docid, year, phr_feats_root):


    dir_path = os.path.join(phr_feats_root, str(year))
    section = ""
    # cohort is a set of related terms, defined here as terms that
    # appear in the title or abstract of a patent in which the term also occurs.
    d_cohort = collections.defaultdict(int)

    for docid in l_docid:
        # keep the set of cohort terms found in this doc's abstract/title
        l_cohort = set()        
        # don't include the .gz as part of the file name, since open_input_file does not expect it.
        filename = docid[0]  + ".xml"
        #print "processing doc: %s" % filename
        phr_feats_file = os.path.join(dir_path, filename)

        # handle compressed or uncompressed files
        s_phr_feats = open_input_file(phr_feats_file)
        #line_no = 1

        # For each line in phr_feats file, 
        # Keep the term if it is in abstract or title section
        for line in s_phr_feats:
            #print "line: %s" % line
            term = line.split("\t")[2]

            # skip lines containing quotes.  These are bad terms and will cause
            # the sqlite3 shell trouble parsing the data.
            if term.find('"') < 0:
                #print "term is: %s" % term
                section = find_section(line)
                if section == "ABSTRACT" or section == "TITLE":
                    l_cohort.add(term)

        # now increment doc counts for any cohort terms found
        for term in l_cohort:
            d_cohort[term] += 1
        s_phr_feats.close()
    return(d_cohort)
"""

def db_docs2cohort(term, l_docid, db, partial_match=True, window_size=5):
    if debug_p:
        print "\n[db_docs2cohort]term: %s" % (term)
    # cohort is a set of related terms, defined here as terms that
    # appear in the title or abstract of a patent in which the term also occurs.
    # store doc counts and overall term counts separately
    d_cohort_dc = collections.defaultdict(int)
    d_cohort_tc = collections.defaultdict(int)

    for docid in l_docid:
        # keep the set of cohort terms found in this doc's abstract/title
        #print "[db_docs2cohort]docid: %s" % str(docid)
        l_cohort = set()
        # retrieve the vector of abstract terms for a document
        cmd = "select abstract from abstract where doc = \"" + docid[0] +"\""
        abs_tsv_str = db.cursor.execute( cmd ).fetchall()[0][0]
        abs_tsv = abs_tsv_str.split("\t")
        if debug_p:
            print "[db_docs2cohort]Calling window with term: %s, tsv: %s" % (term, abs_tsv) 
        # extract the terms that fall within the window
        l_window = window(term, abs_tsv, partial_match=True, window_size=5)
        u_window = set().union(l_window)
        if debug_p:
            print "[db_docs2cohort] l_window: %s" % (l_window)

        #pdb.set_trace()

        # now increment doc counts for any cohort terms found
        for wterm in u_window:
            d_cohort_dc[wterm] += 1
        # increment term counts
        for wterm in l_window:
            d_cohort_tc[wterm] += 1

    return([d_cohort_dc, d_cohort_tc])




# /// todo
# Create a tab separated file suitable for loading into sqlite
# In order to allow us to generate a window of terms around a given term, we keep all phrases in order (even if duplicates)
# fields are docid abstract_tsv
# For now root: /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files
# terms_db.abstract_tsv(l_docid, 2001, "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files") 

#Given a file spec, return a tab separated vector (string) of terms
def file2abstract_terms(phr_feats_file):
    section = ""
    l_terms = []

    # handle compressed or uncompressed files
    s_phr_feats = open_input_file(phr_feats_file)
    #line_no = 1

    # For each line in phr_feats file, 
    # Keep the term if it is in abstract or title section
    for line in s_phr_feats:
        #print "line: %s" % line
        term = line.split("\t")[2]

        # skip lines containing quotes.  These are bad terms and will cause
        # the sqlite3 shell trouble parsing the data.
        if term.find('"') < 0:
            #print "term is: %s" % term
            section = find_section(line)
            if section == "ABSTRACT" or section == "TITLE":
                l_terms.append(term)

    s_phr_feats.close()
    return(list2tsv(l_terms))

def doc_year2filespec(docid, year, root="/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files"):
    dir_path = os.path.join(root, str(year))
    # don't include the .gz as part of the file name, since open_input_file does not expect it.
    filename = docid + ".xml"
    phr_feats_file = os.path.join(dir_path, filename)
    return(phr_feats_file)

# used in populating db cohort table (abstract)
# i1 = terms_db.create_doc_year_tsv("/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/", "phr_feats", 1997, 2003)
def doc_years2tsv_iter(corpus_dir, file_type, start_year, end_year):
    count = 0
    for year in range(start_year, end_year + 1):
        print "[doc_years2tsv_iter]Starting year: %i, total count: %i" % (year, count)
        patent_iter = patent_filelist_iter(corpus_dir, file_type, year)
        for phr_feats_file in patent_iter:
            docid = filename2docid(phr_feats_file)
            tsv = file2abstract_terms(phr_feats_file)
            db_row = docid + "\t\"" + tsv + "\""
            yield(db_row)
            count += 1

# split off path and qualifiers from filename to extract docid
def filename2docid(filename):
    return(filename.rpartition("/")[2].split(".")[0])

# top level call to create the abstract file for 280k cs corpus
# terms_db.run_create_doc_year_tsv()
def run_create_doc_year_tsv():
    tsv_iter = doc_years2tsv_iter("/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/", "phr_feats", 1997, 2003)
    #///
    db_dir = "/home/j/anick/temp/fuse"
    tsv_file = db_dir + "/doc_abstract.tsv"
    s_tsv = codecs.open(tsv_file, "w", encoding='utf-8')
    i = 0
    for tsv in tsv_iter:
        s_tsv.write("%s\n" % tsv)
        i += 1

    s_tsv.close()
    print "[run_create_doc_year_tsv]Wrote %i lines to %s" % (i, tsv_file)

# tsv contains ordered terms (without docid)
def doc_year2tsv(docid, year):
    phr_feats_file = doc_year2filespec(docid, year)
    tsv_str = file2abstract_terms(phr_feats_file)
    #tsv_list = tsv_str.split("\t")
    return(tsv_str)

def term_tsv2indices(term, tsv, partial_match=True):
    #pdb.set_trace()
    if partial_match:
        l_index = [i for i, s in enumerate(tsv) if term in s]
    else:
        l_index = [i for i, s in enumerate(tsv) if term == s]
    return(l_index)

def window(term, tsv, partial_match=True, window_size=3):
    l_index = term_tsv2indices(term, tsv, partial_match)
    #pdb.set_trace()
    l_window = []
    u_window = []
    for i in l_index:
        lower_bound = 1
        if (i - 5) > 1:
            lower_bound = i - window_size
        upper_bound = i + window_size + 1
        l_window.extend(tsv[lower_bound:upper_bound])
        if debug_p:
            print "[window]windows: %s" % l_window
        # take the union of terms

    return(l_window)

"""
# Given a term and year, return its abstract cohort.
# terms_db.term_year2cohort("entitlement management", 2000, db)
def term_year2cohort_old(term, year, db):
    phr_feats_root = "/home/j/marc/Desktop/fuse/code/patent-classifier/ontology/creation/data/patents/201306-computer-science/data/d3_phr_feats/01/files"
    # section is the name of the database field for the term count in terms table
    section = "s_abstract"
    l_docid = db_term_year2docs(db, term, year, section)
    print "term_year2cohort: found %i docs." % len(l_docid)
    d_cohort = db_docs2cohort(l_docid, year, phr_feats_root)
    return(d_cohort)
"""

# d_cohort maps from a cohort term into number of shared abstracts
def term_year2cohort(term, year, db):
    section = "s_abstract"
    if debug_p:
        print "[term_year2cohort]term: %s, year: %i" % (term, year)
    l_docid = db_term_year2docs(db, term, year, section)
    if debug_p:
        print "term_year2cohort: found %i docs." % len(l_docid)
    l_d_cohort = db_docs2cohort(term, l_docid, db)
    return(l_d_cohort)


# ratio of subphrases in abstract / total for year 
# terms_db.abstract_total_counts("web site", 1998, db)
# returns term, abstract count, total count in prev year and given year for term as subphrase
# freq is the number of abstracts the cohort term occurs in
def abstract_total_counts(term, year, db):
    prev_year = year - 1
    str_prev_year = str(prev_year)
    str_year = str(year)
    total_year = "c" + str_year
    total_prev_year = "c" + str_prev_year
    total_cmd = "select " + total_prev_year + "," + total_year + " from counts where term = \"" + term + "\""

    abs_count = abstract_subphrase_count(term, year, db)
    #print "cmd: %s, %i" % (total_cmd, abs_count)
    result = db.cursor.execute(total_cmd).fetchall()

    # get document counts for prev_year and year
    total_prev_count = 0;
    if result != []:
        total_prev_count = result[0][0]
        total_count = result[0][1]

    else:
        # This should not be necessary, but some terms (e.g. "default home page web site setting")
        # don't seem to yield a result in the counts table.  So we default the result to 0.
        total_count = 0
    diff_ratio = 0
    diff = (total_count - total_prev_count) + 1
    if diff > 0:
        log_diff = math.log(diff, 2)
        total = total_count + total_prev_count + 1
        log_total = math.log(total, 2)
        #diff_ratio = log_diff / log_total
        diff_ratio = diff / (total + .00001)
    else:
        log_diff = 0
    prominence_score = log_diff * diff_ratio
    return([ term, abs_count, total_prev_count, total_count, prominence_score, diff, diff_ratio])

# terms_db.tfidf(2, 2394, 2002, terms_db.d_corpus_size)
def tfidf(tf, doc_freq, year, d_corpus_size):
    corpus_size = d_corpus_size[year]
    return(tf * math.log((corpus_size / (doc_freq + 1)), 2))

# for now, assume there is a global dictionary mapping year to # docs
# called d_corpus_size
# terms_db.cohort_info("web site", 1999, db)
# returns:
# [ term, abs_count, total_prev_count, total_count, prominence_score, diff, diff_ratio, tf, tfidf]
def cohort_info(term, year, db):
    print "[cohort_info]term: %s, year: %i" % (term, year)
    f_abstract_count = 1
    f_doc_prev_count = 2
    f_doc_count = 3
    f_diff_ratio = 4
    f_dfidf = 9
    f_tfidf = 10
    count_info = abstract_total_counts(term,year,db)
    abs_count = count_info[f_abstract_count]
    doc_prev_count = count_info[f_doc_prev_count]
    doc_count = count_info[f_doc_count]
    diff_ratio = count_info[f_diff_ratio]
    diff_ratio = ('%.2f' % diff_ratio)
    # info on the query term
    print "stats: %s\t%i\t%i\t%i\t%s" % (term, abs_count, doc_prev_count, doc_count, diff_ratio)
    l_cohort = []
    l_cohort_data = []
    #pdb.set_trace()
    #if abs_count > 0:
    # find all terms in windows within abstracts containing the query term
    l_d_cohort = term_year2cohort(term, year, db)
    # count of doc abstracts containing term
    d_cohort_dc = l_d_cohort[0]
    # count of total occurrences of term within abstracts
    d_cohort_tc = l_d_cohort[1]
    print "cohort_info: found cohort. size: %i" % len(d_cohort_dc.keys())
    for cohort in d_cohort_dc.keys():
        #pdb.set_trace()
        df = d_cohort_dc[cohort]
        tf = d_cohort_tc[cohort]
        cohort_data = abstract_total_counts(cohort,year,db)
        # compute tf/idf and add it to the data
        doc_freq = cohort_data[f_doc_count]
        cohort_dfidf = tfidf(df, doc_freq, year, d_corpus_size)
        cohort_tfidf = tfidf(tf, doc_freq, year, d_corpus_size)
        cohort_data.extend([df, tf, cohort_dfidf, cohort_tfidf])
        l_cohort_data.append(cohort_data)

        #print "%s" % l_cohort_data
    #l_cohort_data.sort(key=itemgetter(4), reverse=True)
    # sort by tfidf
    l_cohort_data.sort(key=itemgetter(f_tfidf), reverse=True)
    return(l_cohort_data)

# terms_db.print_cohort_data("applet", 2001, db)
def print_cohort_data(term, year, db):
    l_cohort_data = cohort_info(term, year, db)
    for cohort_data in l_cohort_data:
        print "%s" % cohort_data

# Create db tables storing counts in title/abstract by year for terms/subphrases
# input is the output of the query:
# select term, year, title, abstract, s_title, s_abstract from terms where s_title > 0 or s_abstract > 0;
# This was further filtered to reduce bogus terms, using
# cd /home/j/anick/temp/fuse
# sh cs_csv/filter_abstract_counts_file.sh
# Then sorted: sort title_abstract_from_terms.filtered > title_abstract_from_terms.sorted
# output are two tsv files with a row for each term and a count for each year in range of years
# terms_db.create_abstract_counts_tables()
def create_abstract_counts_tables():
    # subhrase and chunk dictionaries
    d_scounts = collections.defaultdict(int)
    d_ccounts = collections.defaultdict(int)
    # keep a list of all terms encountered
    d_terms = collections.defaultdict(bool)

    # indexes into input file fields
    f_term = 0
    f_year = 1
    f_ctitle = 2
    f_cabstract = 3
    f_stitle = 4
    f_sabstract = 5

    #input_file = "/home/j/anick/temp/fuse/title_abstract_from_terms.sorted.100"
    input_file = "/home/j/anick/temp/fuse/title_abstract_from_terms.sorted"
    scounts_out = "/home/j/anick/temp/fuse/abs_scounts.tsv"
    ccounts_out = "/home/j/anick/temp/fuse/abs_ccounts.tsv"
    s_input = codecs.open(input_file, encoding='utf-8')
    s_scounts = codecs.open(scounts_out, "w", encoding='utf-8')
    s_ccounts = codecs.open(ccounts_out, "w", encoding='utf-8')

    for line in s_input:
        line = line.strip()
        l_field = line.split("\t")
        term = l_field[f_term]
        year = int(l_field[f_year])
        # use the tuple of term and year as key to the count data
        key = (term, year)
        c_title_abstract_count = int(l_field[f_ctitle]) + int(l_field[f_cabstract])
        s_title_abstract_count = int(l_field[f_stitle]) + int(l_field[f_sabstract])

        d_terms[term] = True

        if c_title_abstract_count != 0:
            d_ccounts[key] += 1

        if s_title_abstract_count != 0:
            d_scounts[key] += 1

    # now create the tsv files from the dictionary data
    i = 0
    for term in d_terms.keys():
        # initialize rows for term
        crow = [term]
        srow = [term]

        for year in range(1997,2004):
            key = (term, year)
            ccount = d_ccounts[key]
            scount = d_scounts[key]
            crow.append(ccount)
            srow.append(scount)

        # write out the records
        s_ccounts.write("%s\n" % list2tsv(crow))
        s_scounts.write("%s\n" % list2tsv(srow))
        i += 1

    print "%i rows created" % i

    s_input.close()
    s_scounts.close()
    s_ccounts.close()

# functions to extract raw data and construct features from db given a term
# db = terms_db.Database("/home/j/anick/temp/fuse/", "cs_terms_db", "") 
# tc = terms_db.TermCache(1997, 2003, db)
# r1 = tc.get_count("web site", "s", "a", 2002, "count")
# r2 = tc.get_cohort("web site", 2002, "list")
# return a table of data for a term
class TermCache():
    def __init__(self, start_year, end_year, db):
        self.d_counts = {}
        self.d_cohorts = {}
        self.start_year_range = start_year
        self.end_year_range = end_year + 1
        self.number_years = end_year - start_year
        self.db = db

    def get_count(self, term_str, status, loc, year, attr):
        key = (term_str, status, loc, year, attr)
        if self.d_counts.has_key(key):
            return(self.d_counts[key])
        else:
            # do the appropriate db fetch to load data into cache
            # status -
            # p: phrase
            # s: subphrase
            # loc -
            # a: abstract
            # d: full document
            # attr -
            # count
            row = []
            if attr == "count":
                if status == "p" and loc == "a":
                    table = "abstract_ccounts"
                elif status == "s" and loc == "a":
                    table = "abstract_scounts"
                elif status == "p" and loc == "d":
                    table = "chunk_counts"
                elif status == "s" and loc == "d":
                    table = "counts"
                else:
                    print "TermCache get: illegal argument(s). Exiting"
                    exit()
                # populate cache for all years
                cmd = "select * from " + table + " where term = \"" + term_str + "\""
                l_row = self.db.cursor.execute( cmd ).fetchall()
                #return(l_row)
                if len(l_row) == 1:
                    row = l_row[0]
                    print "TermCache get: db row found: %s" % str(row)
                else:
                    # the requested info is not in the database
                    # create a default row of 0 counts for use in cache.  Note the
                    # first entry, reserved for the term, will be ignored, so we 
                    # can set this to 0 as well.  Hence adding 2 to number of years to create
                    # a row of the necessary length.
                    row = [0] * (self.number_years + 2)
                    print "TermCache get: db data not found. Creating empty row: %s" % (row)
                    
                # field_number is index into the db row for the year in the range
                field_number = 1
                for update_year in range(self.start_year_range, self.end_year_range):
                    update_key = (term_str, status, loc, update_year, attr)
                    self.d_counts[update_key] = row[field_number]
                    field_number += 1
                 
        # at this point, the cache should be populated            
        return(self.d_counts[key])

    def get_ratio(self, term_str, year, attr):
        l_ratio = []
        ratio = 0.0
        if attr == "as_ds":
            if year == 0:
                for year in range(self.start_year_range, self.end_year_range):
                    
                    abs_s = self.get_count(term_str, "s", "a", year, "count")
                    doc_s = self.get_count(term_str, "s", "d", year, "count")
                    ratio = abs_s / (doc_s + .00001)
                    l_ratio.append(ratio)
        elif attr == "as_ds_cum":
            if year == 0:
                cum_abs_s = 0
                cum_doc_s = 0
                    #print " in get_ratio as_ds_cum"
                for year in range(self.start_year_range, self.end_year_range):
                    
                    abs_s = self.get_count(term_str, "s", "a", year, "count")
                    cum_abs_s = cum_abs_s + abs_s                                  
                    
                    doc_s = self.get_count(term_str, "s", "d", year, "count")
                    cum_doc_s = cum_doc_s + doc_s
                    ratio = cum_abs_s / (cum_doc_s + .00001)
                    l_ratio.append(ratio)


        return(l_ratio)

    # cohort is all terms appearing wihtin a window in any abstract in which term_str
    # also occurs, along with the freq (ie. number of abstracts in which terms co-occur)
    # d_cohort maps from cohort term (in a given year) to its frequency.
    def get_cohort(self, term_str, year, attr):
        print "[get_cohort]term_str: %s, year: %i" % (term_str, year)
        key = (term_str, year)
        if self.d_cohorts.has_key(key):
            d_cohort = self.d_cohorts[key]
        else:
            d_cohort = term_year2cohort(term_str, year, self.db)
            self.d_cohorts[key] = d_cohort
        if attr == "list":
            l_cohort = d_cohort.keys()
            return(l_cohort)
        if attr == "dict":
            return(d_cohort)


# g = terms_db.GrowthInfo("applet", db)
class GrowthInfo:
    
    def __init__(self, term, db, start_year=1997, end_year=2003):
        self.num_cols = (end_year - start_year) + 1
        self.d_data = {}

        cmd_doc_counts = "select * from counts where term = \"" + term + "\""
        cmd_abstract_counts = "select * from abstract_scounts where term = \"" + term + "\""
        counts_row = db.cursor.execute(cmd_doc_counts).fetchall()
        abstract_scounts_row = db.cursor.execute(cmd_abstract_counts).fetchall()

        if counts_row == []:
            counts_row = zero_sum_list(self.num_cols, num_type="i")
        else:
            # remove term from list of counts
            counts_row = counts_row[0][1:]

        abstract_scounts_row = db.cursor.execute(cmd_abstract_counts).fetchall()
        if abstract_scounts_row == []:
            abstract_scounts_row = zero_sum_list(self.num_cols, num_type="i")
        else:
            # remove term from list of counts
            abstract_scounts_row = abstract_scounts_row[0][1:]


        index = 0

        # variables used to find the index (of year) of first non-0 count
        # Let -1 indicate that the first occurrence preceded the earliest year in our range
        self.first_doc_index = -1
        self.first_abs_index = -1
        # We don't start looking for a first occurrence unless the first year has count = 0
        seeking_first_doc_occurrence_p = False
        seeking_first_abs_occurrence_p = False

        print "[growth] year_index, abs_doc_ratio, doc_counts, abstract_scounts, doc_prom, abs_prom"

        for year in range(start_year, end_year + 1):
            #print "Entering year loop with year = %i, index = %i" % (year, index)
            prev_index = index - 1
            # store the count info by year index
            key = ("doc_counts", index)
            self.d_data[key] = counts_row[index]

            if seeking_first_doc_occurrence_p and counts_row[index] != 0:
                self.first_doc_index = index
                seeking_first_doc_occurrence_p = False

            if index == 0:
                if counts_row[index] == 0:
                    # start looking for the first occurrence
                    seeking_first_doc_occurrence_p = True

            key = ("doc_prob", index)
            self.d_data[key] = (float(counts_row[index] + .000001)) / d_corpus_size[year]
            key = ("abs_counts", index)
            self.d_data[key] = abstract_scounts_row[index]

            if seeking_first_abs_occurrence_p and abstract_scounts_row[index] != 0:
                self.first_abs_index = index
                seeking_first_abs_occurrence_p = False

            if index == 0:
                if abstract_scounts_row[index] == 0:
                    # start looking for the first occurrence
                    seeking_first_abs_occurrence_p = True

            key = ("abs_prob", index)
            self.d_data[key] = (float(abstract_scounts_row[index]) + .000001) / d_corpus_size[year]
            key = ("abs_doc_ratio", index)
            self.d_data[key] = abstract_scounts_row[index] / (counts_row[index] + .000001)
            
            key = ("doc_growth", index)
            if prev_index >= 0:
                #self.d_data[key] = ( self.d_data[("doc_prob", index)] - self.d_data[("doc_prob", prev_index)] )/ (self.d_data[("doc_prob", prev_index)] + (1.0 / d_corpus_size[year -1]) )
                #self.d_data[key] = self.d_data[("doc_prob", index)] - self.d_data[("doc_prob", prev_index)] 
                self.d_data[key] = ( self.d_data[("doc_counts", index)] - self.d_data[("doc_counts", prev_index)] )/ (self.d_data[("doc_counts", prev_index)] + 1.0 )
            else:
                self.d_data[key] = 0.00000001
            key = ("abs_growth", index)
            if prev_index >= 0:
                #self.d_data[key] = ( self.d_data[("abs_prob", index)] - self.d_data[("abs_prob", prev_index)] )/ (self.d_data[("abs_prob", prev_index)] + (1.0 / d_corpus_size[year -1]) )
                #self.d_data[key] = self.d_data[("abs_prob", index)] - self.d_data[("abs_prob", prev_index)] 
                self.d_data[key] = ( self.d_data[("abs_counts", index)] - self.d_data[("abs_counts", prev_index)] )/ (self.d_data[("abs_counts", prev_index)] + 1.0 )
            else:
                self.d_data[key] = 0.00000001

            key = ("doc_prom", index)
            if prev_index >= 0:
                if self.d_data[("doc_counts", prev_index)] < self.d_data[("doc_counts", index)] :
                    self.d_data[key] = (1 - (self.d_data[("doc_counts", prev_index)] / float(self.d_data[("doc_counts", index)]) )) * (1 - (1.0 / (self.d_data[("doc_counts", index)] )))
                else:
                    self.d_data[key] = 0.000001
            else:
                self.d_data[key] = 0.00000001

            key = ("abs_prom", index)
            if prev_index >= 0:
                if self.d_data[("abs_counts", prev_index)] < self.d_data[("abs_counts", index)] :
                    self.d_data[key] = (1 - (self.d_data[("abs_counts", prev_index)] / float(self.d_data[("abs_counts", index)]) )) * (1 - (1.0 / (self.d_data[("abs_counts", index)] )))
                else:
                    self.d_data[key] = 0.000001
            else:
                self.d_data[key] = 0.00000001

                

            #print "[growth] year_index: %i, counts_row: %s, abstract_scounts_row: %s, doc_growth: %.5f, abs_growth: %.5f" % (index, counts_row[index], abstract_scounts_row[index], self.d_data[("doc_growth", index)], self.d_data[("abs_growth", index)] )
            #print "[growth] year_index: %i, counts_row: %s, abstract_scounts_row: %s, doc_prom: %.5f, abs_prom: %.5f" % (index, counts_row[index], abstract_scounts_row[index], self.d_data[("doc_prom", index)], self.d_data[("abs_prom", index)] )

            print "[growth] %i, %i, %.5f, %s, %s, %.5f, %.5f" % (index, year, self.d_data[("abs_doc_ratio", index)], counts_row[index], abstract_scounts_row[index], self.d_data[("doc_prom", index)], self.d_data[("abs_prom", index)] )

            index += 1
        print "[growth]first_doc_index: %i, first_abs_index: %i" % (self.first_doc_index, self.first_abs_index)


