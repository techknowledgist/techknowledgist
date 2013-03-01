# np_db.py

# PGA 10/25/12 
# Functions for managing an sqlite3 database of noun phrase information
# with fields:
# np (noun phrase)
# docid (filename w/o qualifier)
# date (year of document in whih np occurs)
# We use two keys: 
# np (to give fast lookup by phrase)
# np_docid (to enforce uniqueness for np/docid combinations)

# MV 2/28/2013
# This is nice, but I am not sure whether it will scale nicely to the number of documents
# we need to run this over. Running this on 10 patents created a database with 4000+
# records. Since the number of records will scale linearly with increased number of
# documents, running this on 500,000 patents will result in 200,000,000+ records. And a
# query to extract the number of documents a term occurs in may be slowish for frequent
# terms. It might be better to have a database as follows:
#    CREATE TABLE NP(np TEXT, year INT, doc_count INT, instance_count INT)
#    CREATE INDEX idx_np ON NP(np)
#    CREATE UNIQUE INDEX idx_np_year ON NP(np, year)


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



if __name__ == '__main__':

    import sys
    db_file = sys.argv[1]
    doc_feats_file = sys.argv[2]
    np_db_create(db_file)
    np_db_insert_doc_feats(db_file, doc_feats_file)
