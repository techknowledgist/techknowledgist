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

    """Wrapper around the summary and years databases."""

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
            (old_score, old_doc_count, old_instance_count) = result[2:5]
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



def test_years(db_file):
    db = YearsDatabase(db_file)
    years = [('1998', 18, 0.065), ('2001', 218, 0.765),('2008', 78, 0.132)]
    for year, count, ratio in years:
        db.add(year, count, ratio)
    db.commit_and_close()


if __name__ == '__main__':
    import sys
    test_years(sys.argv[1])
