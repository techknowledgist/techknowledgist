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


class InfoDatabase(Database):

    """Wrapper around the info database, which for now only keeps track of the
    batches loaded."""

    def __init__(self, dir, db_file):
        """Open the db_file database and create connection and cursor
        objects. Create the years table if db_file did not exist."""
        self.db_file = os.path.join(dir, db_file)
        db_existed = os.path.exists(self.db_file)
        self.connect()
        if not db_existed:
            q1 = "CREATE TABLE datasets(dataset TEXT)"
            self.cursor.execute(q1)
        print "[InfoDatabase] Opened database in %s" % self.db_file

    def add_dataset(self, dataset):
        query = "INSERT INTO datasets VALUES(?)"
        self.execute('InfoDatabase', query, (dataset,))

    def list_datasets(self):
        q = "SELECT dataset from datasets"
        self.cursor.execute(q)
        return [r[0] for r in self.cursor.fetchall()]


class YearsDatabase(Database):

    """This database holds document counts for each year."""

    def __init__(self, dir, db_file):
        """Open the db_file database and create connection and cursor
        objects. Create the years table if db_file did not exist."""
        self.db_file = os.path.join(dir, db_file)
        db_existed = os.path.exists(self.db_file)
        self.connect()
        if not db_existed:
            q1 = "CREATE TABLE years(year TEXT, doc_count INT)"
            q2 = "CREATE UNIQUE INDEX idx_year ON years(year)"
            self.cursor.execute(q1)
            self.cursor.execute(q2)
        print "[YearsDatabase] Opened database in %s" % self.db_file

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


class TermsDatabase(Database):

    """Wrapper around the terms database."""

    def __init__(self, dir, db_file):
        """Open the db_file database and create connection and cursor objects. Create the
        years table if db_file did not exist."""
        self.db_file = os.path.join(dir, db_file)
        db_existed = os.path.exists(self.db_file)
        self.connect()
        if not db_existed:
            fields = ['term TEXT', 'year TEXT', 'score FLOAT', 'doc_count INT',
                      'v0 INT', 'v1 INT', 'v2 INT', 'v3 INT', 'v4 INT',
                      'v5 INT', 'v6 INT', 'v7 INT', 'v8 INT', 'v9 INT' ]
            q1 = "CREATE TABLE terms(%s)" % ', '.join(fields)
            q2 = "CREATE UNIQUE INDEX idx_term_year ON terms(term, year)"
            self.cursor.execute(q1)
            self.cursor.execute(q2)
        print "[TermsDatabase] Opened database in %s" % self.db_file

    def add(self, term, year, score, doc_count, bins):
        result = self.get_term(term, year)
        if result is None:
            self.execute(
                'TermsDatabase.add',
                "INSERT INTO terms VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [term, year, score, doc_count,
                 bins[0], bins[1], bins[2], bins[3], bins[4],
                 bins[5], bins[6], bins[7], bins[8], bins[9]])
        else:
            #print term, year, score, doc_count, bins
            #print '  ', result
            (old_score, old_doc_count, v0, v1, v2, v3, v4, v5, v6, v7, v8, v9) = result[2:]
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
            #result = self.get_term(term, year)
            #print '  ', result
            #exit("No thanks")

    def get_term(self, term, year):
        query = "SELECT * FROM terms WHERE term=? AND year=?"
        self.execute('TermsDatabase.get_term', query, (term, year))
        return self.cursor.fetchone()

    def select_terms(self, doc_count, score):
        query = "SELECT * FROM terms WHERE doc_count >= ? AND score >= ?"
        self.execute('TermsDatabase.select_terms', query, (doc_count, score))
        return self.cursor.fetchall()



class OLD_TermsDatabase(Database):

    """Wrapper around the terms database."""

    def __init__(self, db_file):
        """Open the db_file database and create connection and cursor objects. Create the
        years table if db_file did not exist."""
        self.db_file = os.path.join(dir, db_file)
        db_existed = os.path.exists(self.db_file)
        self.connect()
        if not db_existed:
            q1 = "CREATE TABLE terms(term TEXT, score FLOAT, doc_count INT, term_count INT)"
            q2 = "CREATE UNIQUE INDEX idx_term ON terms(term)"
            self.cursor.execute(q1)
            self.cursor.execute(q2)
        print "[TermsDatabase] Opened database in %s" % self.db_file

    def add(self, term, score, doc_count, instance_count):
        result = self.get_term(term)
        if result is None:
            query = "INSERT INTO terms VALUES(?,?,?,?)"
            values = (term, score, doc_count, instance_count)
            self.execute('TermsDatabase', query, values)
        else:
            (old_score, old_doc_count, old_instance_count) = result[1:4]
            new_doc_count = old_doc_count + doc_count
            new_instance_count = old_instance_count + instance_count
            new_score = ((old_score * old_doc_count) + (score * doc_count)) / new_doc_count
            query = "UPDATE terms SET score=?, doc_count=?, term_count=? " + \
                    "WHERE term=?"
            values = (new_score, new_doc_count, new_instance_count, term)
            self.execute('TermsDatabase', query, values)

    def get_term(self, term):
        query = "SELECT * FROM terms WHERE term=?"
        self.execute('TermsDatabase.get_term', query, (term,))
        return self.cursor.fetchone()

    def select_terms(self, doc_count, score):
        query = "SELECT * FROM terms WHERE doc_count >= ? AND score >= ?"
        self.execute('TermsDatabase.select_terms', query, (doc_count, score))
        return self.cursor.fetchall()



class SummaryDatabase(Database):

    """Wrapper around the summary and years databases."""

    def __init__(self, db_file):
        """Open the db_file database and create connection and cursor objects. Create the
        summary table if db_file did not exist."""
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
                "CREATE TABLE sections(%s)" % ', '.join(fields2),
                "CREATE UNIQUE INDEX idx_summary ON summary(term, year)",
                "CREATE UNIQUE INDEX idx_sections ON sections(term, year)" ]
            for query in queries:
                print "[SummaryDatabase]", query
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
        self.execute('SummaryDatabase.get_summary_row', query, (term, year))
        return self.cursor.fetchone()

    def get_term_data(self, term):
        query = "SELECT * from summary where term=?"
        #print term
        self.execute('SummaryDatabase.get_term_data', query, (term,))
        return self.cursor.fetchall()


def test_years(db_file):
    db = YearsDatabase(db_file)
    years = [('1998', 18, 0.065), ('2001', 218, 0.765),('2008', 78, 0.132)]
    for year, count, ratio in years:
        db.add(year, count, ratio)
    db.commit_and_close()


if __name__ == '__main__':
    import sys
    test_years(sys.argv[1])
