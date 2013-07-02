"""
np_db.py

Classes that act as an interface to the index databases.

Based on an older version by PGA (from 10/25/12), but transformed to such an
extent that the original is not recognizable anymore. See discarded/np_db.py for
the first version. One of the reasons for all the changes was that the original
code would not scale to large data sets.

"""


import os
import sys
import sqlite3



class Database(object):

    """Abstract class that contains some basic code for database
    connectivity."""

    def __init__(self, dir, db_file, schema):
        """Open the db_file database and create a cursor objects. Create the
        schema if db_file did not exist."""
        self.db_file = os.path.join(dir, db_file)
        self.inserts = 0
        self.updates = 0
        db_existed = os.path.exists(self.db_file)
        self.connect()
        if not db_existed:
            for q in schema:
                self.cursor.execute(q)

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

    def reset_counts(self):
        self.inserts = 0
        self.updates = 0


class InfoDatabase(Database):

    """Wrapper around the info database, which for now only keeps track of the
    datasets loaded."""

    DATASETS_TABLE = "CREATE TABLE datasets(dataset TEXT)"
    SCHEMA = [DATASETS_TABLE]

    def __init__(self, dir, db_file):
        """Open the info database, creating it if needed."""
        Database.__init__(self, dir, db_file, InfoDatabase.SCHEMA)
        #print "[InfoDatabase] Opened database in %s" % self.db_file

    def add_dataset(self, dataset):
        query = "INSERT INTO datasets VALUES(?)"
        self.execute('InfoDatabase', query, (dataset,))

    def list_datasets(self):
        q = "SELECT dataset from datasets"
        self.cursor.execute(q)
        return [r[0] for r in self.cursor.fetchall()]


class YearsDatabase(Database):

    """This database holds document counts for each year."""

    YEARS_TABLE = "CREATE TABLE years(year TEXT, doc_count INT)"
    YEARS_INDEX = "CREATE UNIQUE INDEX idx_year ON years(year)"
    SCHEMA = [YEARS_TABLE, YEARS_INDEX]

    def __init__(self, dir, db_file):
        """Open the years database, creating it if needed."""
        Database.__init__(self, dir, db_file, YearsDatabase.SCHEMA)
        #print "[YearsDatabase] Opened database in %s" % self.db_file

    def add(self, year, count):
        query = "INSERT INTO years VALUES(?,?)"
        self.execute('YearsDatabase.add', query, (year, count))

    def update(self, year, count):
        query = "UPDATE years SET doc_count=? WHERE year=?"
        self.execute('YearsDatabase.update', query, (year, count))

    def get_count(self, year):
        query = "SELECT doc_count FROM years WHERE year=?"
        self.execute('YearsDatabase.get_count', query, (year,))
        result = [r[0] for r in self.cursor.fetchall()]
        return result[0] if result else 0


class OLD_TermsDatabase(Database):

    """Wrapper around the terms database. Version with a years column"""

    TERMS_TABLE = "CREATE TABLE terms(" + \
                  'term TEXT, year TEXT, score FLOAT, doc_count INT, ' + \
                  'v0 INT, v1 INT, v2 INT, v3 INT, v4 INT, ' + \
                  'v5 INT, v6 INT, v7 INT, v8 INT, v9 INT)'
    TERMS_INDEX = "CREATE UNIQUE INDEX idx_term_year ON terms(term, year)"
    SCHEMA = [TERMS_TABLE, TERMS_INDEX]

    def __init__(self, dir, db_file):
        """Open the terms database, creating it if needed."""
        Database.__init__(self, dir, db_file, TermsDatabase.SCHEMA)
        #print "[TermsDatabase] Opened database in %s" % self.db_file

    def add(self, term, year, score, doc_count, bins):
        """Add term data by either inserting a row or updating an existing row."""
        result = self.get_term(term, year)
        if result is None:
            self._insert(term, year, score, doc_count, bins)
        else:
            self._update(result, term, year, score, doc_count, bins)

    def _insert(self, term, year, score, doc_count, bins):
        self.execute(
            'TermsDatabase.add',
            "INSERT INTO terms VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [term, year, score, doc_count] + bins)

    def _update(self, old_row, term, year, score, doc_count, bins):
        (old_score, old_doc_count, v0, v1, v2, v3, v4, v5, v6, v7, v8, v9) = old_row[2:]
        new_doc_count = old_doc_count + doc_count
        new_score = ((old_score * old_doc_count) + (score * doc_count)) / new_doc_count
        self.execute(
            'TermsDatabase.add',
            "UPDATE terms SET score=?, doc_count=?, " +
            "v0=?, v1=?, v2=?, v3=?, v4=?, v5=?, v6=?, v7=?, v8=?, v9=? " +
            "WHERE term=? AND year=?",
            [new_score, new_doc_count,
             bins[0] + v0, bins[1] + v1, bins[2] + v2, bins[3] + v3, bins[4] + v4,
             bins[5] + v5, bins[6] + v6, bins[7] + v7, bins[8] + v8, bins[9] + v9,
             term, year])

    def get_term(self, term, year):
        query = "SELECT * FROM terms WHERE term=? AND year=?"
        self.execute('TermsDatabase.get_term', query, (term, year))
        return self.cursor.fetchone()

    def select_terms(self, doc_count, score):
        query = "SELECT * FROM terms WHERE doc_count >= ? AND score >= ?"
        self.execute('TermsDatabase.select_terms', query, (doc_count, score))
        return self.cursor.fetchall()



class TermsDatabase(Database):

    """Wrapper around a term database. Similar as TermDatabase, but specific to
    a year. This will make scaling up a bit easier."""

    TERMS_TABLE = "CREATE TABLE terms(" + \
                  'term TEXT, score FLOAT, doc_count INT, ' + \
                  'v0 INT, v1 INT, v2 INT, v3 INT, v4 INT, ' + \
                  'v5 INT, v6 INT, v7 INT, v8 INT, v9 INT)'
    TERMS_INDEX = "CREATE UNIQUE INDEX idx_term ON terms(term)"
    SCHEMA = [TERMS_TABLE, TERMS_INDEX]

    def __init__(self, dir, db_file):
        """Open the terms database, creating it if needed."""
        Database.__init__(self, dir, db_file, self.__class__.SCHEMA)
        #print "[TermsDatabase] Opened database in %s" % self.db_file

    def add(self, term, score, doc_count, bins):
        """Add term data by either inserting a row or updating an existing row."""
        result = self.get_term(term)
        if result is None:
            self._insert(term, score, doc_count, bins)
        else:
            self._update(result, term, score, doc_count, bins)

    def _insert(self, term, score, doc_count, bins):
        self.inserts += 1
        self.execute(
            'TermsDatabase.add',
            "INSERT INTO terms VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [term, score, doc_count] + bins)

    def _update(self, old_row, term, score, doc_count, bins):
        self.updates += 1
        (old_score, old_doc_count, v0, v1, v2, v3, v4, v5, v6, v7, v8, v9) = old_row[1:]
        new_doc_count = old_doc_count + doc_count
        new_score = ((old_score * old_doc_count) + (score * doc_count)) / new_doc_count
        self.execute(
            'TermsDatabase.add',
            "UPDATE terms SET score=?, doc_count=?, " +
            "v0=?, v1=?, v2=?, v3=?, v4=?, v5=?, v6=?, v7=?, v8=?, v9=? " +
            "WHERE term=?",
            [new_score, new_doc_count,
             bins[0] + v0, bins[1] + v1, bins[2] + v2, bins[3] + v3, bins[4] + v4,
             bins[5] + v5, bins[6] + v6, bins[7] + v7, bins[8] + v8, bins[9] + v9,
             term])

    def get_term(self, term):
        query = "SELECT * FROM terms WHERE term=?"
        self.execute('TermsDatabase.get_term', query, (term,))
        return self.cursor.fetchone()

    def select_terms(self, doc_count, score):
        query = "SELECT * FROM terms WHERE doc_count >= ? AND score >= ?"
        self.execute('TermsDatabase.select_terms', query, (doc_count, score))
        return self.cursor.fetchall()

