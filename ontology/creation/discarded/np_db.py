### This is a copy of ../np_db.py as of 2/28 2013. It was put here because it has
### non-ascii characters in a comment, which caused the script to fail. I removed those
### characters from the original file but kept them here for reference (MV).


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


import sqlite3
import os
import sys

# create a database in location <path>
# There should be one database (named np.db) for each language.
# Suggested path is the workspace directory:
# e.g. .../patent-classifier/ontology/creation/data/patents/en/ws
def np_db_create(path):
    try:
        db_file = os.path.join(path, "np.db")
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute("CREATE TABLE NP(np TEXT, docid TEXT, date INT)")
        c.execute("CREATE INDEX idx_np ON NP(np)")
        c.execute("CREATE UNIQUE INDEX idx_np_docid ON NP(np, docid)")
        conn.commit()
        c.close()
        conn.close()
        print "[np_db_create] Created database in %s" % db_file
    except:
        e = sys.exc_info()
        print "[np_db_create]ERROR: Failed to create database in %s\nError: %s" % (db_file, e)

# format of doc_feats.all is
# position of this element        1980|US4236596A|position_of_this_element ...


# np_db.np_db_insert_doc_feats("/home/j/anick/patent-classifier/ontology/creation/data/patents/en/ws", "/home/j/anick/patent-classifier/ontology/creation/data/patents/en/ws/doc_feats.all")

def np_db_insert_doc_feats(db_path, doc_feats_file):

    # get a connection and a cursor
    db_file = os.path.join(db_path, "np.db")
    (conn, c) = np_db_open(db_file)

    # insert entries into db
    s_df = open(doc_feats_file)
    try:
        i = 0
        for line in s_df:
            #extract np, date, docid
            fields = line.split("\t")
            np = fields[0]
            (date, docid, symbol) = fields[1].split("|")

            #print "[insert_doc_feats_into_np_db]np: %s, docid: %s, date: %i" % (np, docid, date)
            # use double quotes in the sql command since single quote (apostrophe) can appear in the np.
            # Date field is unquoted so it will be interpreted as an integer.
            # This is useful in case we want to do range queries on dates in sql.
            sql = 'INSERT INTO NP VALUES("' + np + '", "' + docid + '", ' + date + ')'
            print "sql is: %s" % sql
            c.execute(sql)
            i += 1
    except sqlite3.IntegrityError:
        # This is ok - preventing duplicate np/doc_id entries from being inserted.
        pass
    else:
        e = sys.exc_info()
        print "[np_db_insert_doc_feats]ERROR: Failed to update database in %s, Error: %s" % (db_file, e)
        sys.exit()

    print "[np_db_insert_doc_feats] Added %i NP's to database in %s" % (i, db_file)

    conn.commit()
    c.close()
    conn.close()
    s_df.close()


def np_db_open(db_file):
    # open db and create a cursor
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print "[np_db.open_db] Opened database in %s" % db_file
        return (conn, cursor)
    except:
        e = sys.exc_info()
        sys.exit("[np_db.open_db] ERROR: Failed to open database in %s, Error: %s" %  (db_file, e))



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
    db_filename = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cn/ws/np.db"
    conn = np_db_conn(db_filename)
    res = np_db_counts(conn, "link", [2008, 2009, 2010, 2011])
    print "Counts for phrase link: %s" % res
    res = np_db_counts(conn, "invention", [2001, 2002, 2003])
    print "Counts for phrase invention: %s" % res
    np_db_close(conn)

"""
Running the Chinese counts_test_cn gives the following error part way through:
sql is: INSERT INTO NP VALUES("滤波 的 方法", "CN101216894A", 2008)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "np_db.py", line 124, in np_db_test_insert_cn
    np_db_insert_doc_feats(ws_path, doc_feats_file)
  File "np_db.py", line 68, in np_db_insert_doc_feats
    (date, docid, symbol) = fields[1].split("|")
ValueError: too many values to unpack
"""


if __name__ == '__main__':

    import sys
    db_file = sys.argv[1]
    docfeats_file = sys.argv[2]
    np_db_create(db_file)
    np_db_insert_doc_feats(db_path, doc_feats_file)
