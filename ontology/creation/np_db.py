"""
np_db.py

PGA 10/25/12 
Functions for managing an sqlite3 database of noun phrase information
with fields:
   np (noun phrase)
   docid (filename w/o qualifier)
   date (year of document in whih np occurs)
We use two keys: 
   np (to give fast lookup by phrase)
   np_docid (to enforce uniqueness for np/docid combinations)

MV 2/28/2013
This is nice, but I am not sure whether it will scale nicely to the number of documents we
need to run this over. Running this on 10 patents created a database with 4000+
records. Since the number of records will scale linearly with increased number of
documents, running this on 500,000 patents will result in 200,000,000+ records. And a
query to extract the number of documents a term occurs in may be slowish for frequent
terms. It might be better to have a database as follows:

   CREATE TABLE NP(np TEXT, year INT, doc_count INT, instance_count INT)
   CREATE INDEX idx_np ON NP(np)
   CREATE UNIQUE INDEX idx_np_year ON NP(np, year)

Top-level functions used by the indexer:

   np_db_open(db_file) - opens db_file and returns a connection and a cursor
   np_db_create_years() - 

"""


import os
import sys
import sqlite3

# create a database in location <path>
# There should be one database for each language.
# Suggested path is the workspace directory:
# e.g. .../patent-classifier/ontology/creation/data/patents/en/ws/np.db
def np_db_create(db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE NP(np TEXT, docid TEXT, date INT)")
        cursor.execute("CREATE INDEX idx_np ON NP(np)")
        cursor.execute("CREATE UNIQUE INDEX idx_np_docid ON NP(np, docid)")
        np_db_commit_and_close(conn, cursor)
        print "[np_db_create] Created database in %s" % db_file
    except:
        print "[np_db_create] ERROR: Failed to create database %s" % db_file
        print "[np_db_create] ERROR: Error: %s" % str(sys.exc_info())
        sys.exit()



class Database(object):

    def connect(self):
        self.connection = sqlite3.connect(self.db_file)
        self.cursor = self.connection.cursor()

    def execute(self, caller, query, values):
        try:
            self.cursor.execute(query, values)
        except sqlite3.IntegrityError:
            print "[%s] WARNING: ignored duplicate value: %s" % (caller, values)
        except sqlite3.ProgrammingError:
            print "[%s] WARNING: %s" % (caller, sys.exc_value)

    def commit_and_close(self):
        self.commit()
        self.close()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()


class YearsDatabase(Database):

    """Wrapper around the years database."""

    def __init__(self, db_file):
        """Open the db_file database and create connection and cursor
        objects. Create the years table if db_file did not exist."""
        db_existed = os.path.exists(db_file)
        self.db_file = db_file
        self.connect()
        if not db_existed:
            q1 = "CREATE TABLE years(year TEXT, doc_count INT, ratio FLOAT)"
            q2 = "CREATE UNIQUE INDEX idx_year ON years(year)"
            self.cursor.execute(q1)
            self.cursor.execute(q2)
        print "[YearsDatabase] Opened database in %s" % self.db_file

    def add(self, year, count, ratio):
        """Add a row with year, count and ratio values."""
        query = "INSERT INTO years VALUES(?,?,?)"
        self.execute('YearsDatabase', query, (year, count, ratio))


class SummaryDatabase(Database):

    """Wrapper around the years database."""

    def __init__(self, db_file):
        """Open the db_file database and create connection and cursor
        objects. Create the summary table if db_file did not exist."""

        db_existed = os.path.exists(db_file)
        self.db_file = db_file
        self.connect()
        if not db_existed:
            fields1 = ['term TEXT', 'year TEXT', 'score FLOAT',
                       'doc_count INT', 'term_count INT',
                       'v0 INT', 'v1 INT', 'v2 INT', 'v3 INT', 'v4 INT',
                       'v5 INT', 'v6 INT', 'v7 INT', 'v8 INT', 'v9 INT' ]
            fields2 = ['term TEXT', 'year TEXT', 'section TEXT', 'count INT']
            queries = [
                "CREATE TABLE summary(%s)" % ', '.join(fields1),
                "CREATE TABLE sections(%s)" % ', '.join(fields1),
                "CREATE UNIQUE INDEX idx_summary ON summary(term, year)",
                "CREATE UNIQUE INDEX idx_sections ON sections(term, year)" ]
            for query in queries:
                print query
                self.cursor.execute(query)
        print "[SummaryDatabase] Opened database in %s" % self.db_file


    def add_to_summary(self, term, year, score, doc_count, instance_count):
        result = self.get_summary_row(term, year)
        if result is None:
            query = "INSERT INTO summary VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            values = (term, year, score, doc_count, instance_count,
                      0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            self.execute('SummaryDatabase', query, values)
        else:
            (old_score, old_doc_count, old_instance_count) = result[2:]
            new_doc_count = old_doc_count + doc_count
            new_instance_count = old_instance_count + instance_count
            new_score = ((old_score * old_doc_count) + (score * doc_count)) / new_doc_count
            query = "UPDATE summary SET score=?, doc_count=?, term_count=? " + \
                    "WHERE term=? and year=?"
            values = (new_score, new_doc_count, new_instance_count, term, year)
            self.execute('SummaryDatabase', query, values)


    def add_to_sections(self, term, year, section_counts):
        # TODO: add/update rows in the sections table
        pass

    def add_scores(self, term, year, scores):
        result = self.get_summary_row(term, year)
        if result is None:
            print "[add_scores] WARNING: cannot add scores to", (year, term)
        else:
            current_scores = list(result[5:])
            for score_range, value in scores.items():
                score_range = int(score_range)
                current_scores[score_range] += value
            query = \
                "UPDATE summary " + \
                "SET v0=?, v1=?, v2=?, v3=?, v4=?, v5=?, v6=?, v7=?, v8=?, v9=? " + \
                "WHERE term=? and year=?"
            self.execute('SummaryDatabase.add_scores', query, current_scores + [term, year])

    def get_summary_row(self, term, year):
        query = "SELECT * FROM summary WHERE term=? and year=?"
        self.execute('YearsDatabase', query, (term, year))
        return self.cursor.fetchone()



# format of doc_feats.all is
# position of this element        1980|US4236596A|position_of_this_element ...  


# np_db.np_db_insert_doc_feats("/home/j/anick/patent-classifier/ontology/creation/data/patents/en/ws", "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/ws/doc_feats.all")

def np_db_insert_doc_feats(db_path, doc_feats_file):
    (conn, cursor) = np_db_open(db_file)
    # insert entries into db
    with open(doc_feats_file) as s_df:
        lines = 0
        for line in s_df:
            # extract np, date, docid
            fields = line.split("\t")
            np = fields[0]
            (date, docid, symbol) = fields[1].split("|")
            np_db_insert_np(cursor, np, docid, date)
            lines += 1
        print "[np_db_insert_doc_feats] Added %i NP's to database in %s" % (lines, db_file)
    np_db_commit_and_close(conn, cursor)


def np_db_insert_np(c, np, docid, date):
    try:
        c.execute("INSERT INTO NP VALUES(?, ?, ?)", (np, docid, date))
    except sqlite3.IntegrityError:
        # This is ok - preventing duplicate np/doc_id entries from being inserted.
        print "[np_db_insert_np] WARNING: not adding duplicate NP (%s, %s, %s)" \
              % (np, docid, date)
    except:
        print "[np_db_insert_np] WARNING: could not add (%s, %s, %s)" % (np, docid, date)
        print "[np_db_insert_np] WARNING: %s" % str(sys.exc_info())


def np_db_open(db_file):
    """Open the db_file database, create a cursor and return the conenction and cursor
    objects."""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print "[np_db.open_db] Opened database in %s" % db_file
        return (conn, cursor)
    except:
        e = sys.exc_info()
        sys.exit("[np_db.open_db] ERROR: Failed to open database in %s, Error: %s" \
                 % (db_file, e))


def np_db_commit_and_close(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()


# Example of creating an np_db.  Needs to be done only once per language
# np_db.test_create()
def np_db_test_create():
    lang_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/ws"    
    np_db_create(lang_path)

def np_db_test_create_cn():
    lang_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cn/ws"    
    np_db_create(lang_path)

# Example of inserting a file of doc_feats records into the np_db
#np_db.np_db_test_insert()
def np_db_test_insert():
    ws_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/ws"
    doc_feats_file = os.path.join(ws_path, "doc_feats.all")
    # Note: No other processes should have the database open when you are trying to do updates
    # unless they have opened it in readonly mode.
    np_db_insert_doc_feats(ws_path, doc_feats_file)

def np_db_test_insert_cn():
    ws_path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cn/ws"
    doc_feats_file = os.path.join(ws_path, "doc_feats.all")
    # Note: No other processes should have the database open when you are trying to do updates
    # unless they have opened it in readonly mode.
    np_db_insert_doc_feats(ws_path, doc_feats_file)



# Example of getting a (readonly) connection for doing database queries
# Readonly mode isn't actually supported but you should be allowed to have 
# concurrent readers provided no one is doing a write transaction.
def np_db_conn(db_filename):
    try:
        conn = sqlite3.connect(db_filename)
        return(conn)
    except:
        e = sys.exc_info()
        print "[np_db_create] ERROR: %s" % e

def np_db_close(conn):
    conn.close()

# select the counts for a given np for each date in a list of dates and 
# return a list of the form [[date, count], [date, count], ...]
def np_db_counts(conn, np, date_list):
    count_list = []
    c = conn.cursor()
    sql_main = 'select count(*) from np where np = "' + np + '" and date = '
    for date in date_list:
        sql = sql_main + str(date)
        print "[np_db_counts]query: %s" % sql
        count_list.append([date, c.execute(sql).fetchall()[0][0]])
    return(count_list)

# Example of computing counts for np's and dates.
# Assumes database has been populated and not locked by another process doing updates.
# It opens a connection, does some queries and closes the connection.
def np_db_counts_test():
    db_filename = "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/ws/np.db"
    conn = np_db_conn(db_filename)
    res = np_db_counts(conn, "link", [2008, 2009, 2010, 2011])
    print "Counts for phrase link: %s" % res
    res = np_db_counts(conn, "invention", [2001, 2002, 2003])
    print "Counts for phrase invention: %s" % res
    np_db_close(conn)


def np_db_counts_test_cn():
    # NOTE: a comment following this method reported on an error on CHinese processing, it
    # was removed because it broke the script, see discarded/np_db.py for the comment
    db_filename = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cn/ws/np.db"
    conn = np_db_conn(db_filename)
    res = np_db_counts(conn, "link", [2008, 2009, 2010, 2011])
    print "Counts for phrase link: %s" % res
    res = np_db_counts(conn, "invention", [2001, 2002, 2003])
    print "Counts for phrase invention: %s" % res
    np_db_close(conn)


def test_doc_feats():
    db_file = sys.argv[1]
    doc_feats_file = sys.argv[2]
    np_db_create(db_file)
    np_db_insert_doc_feats(db_file, doc_feats_file)

def test_years(db_file):
    db = YearsDatabase(db_file)
    years = [('1998', 18, 0.065), ('2001', 218, 0.765),('2008', 78, 0.132)]
    for year, count, ratio in years:
        db.add(year, count, ratio)
    db.commit_and_close()


if __name__ == '__main__':
    import sys
    test_years(sys.argv[1])
