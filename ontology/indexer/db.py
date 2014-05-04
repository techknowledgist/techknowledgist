"""

Module that provides access (read-only) to sqlite databses with term information.

To use a TermDB you need two sqlite databases, one with corpus-level term scores
and one with term locations:

>>> fuse_corpora = '/home/j/corpuswork/fuse/FUSEData/corpora/'
>>> corpus_all_2000 = os.path.join(fuse_corpora, 'ln-us-all-600k', 'subcorpora', '2000')
>>> index_dir = os.path.join(corpus_all_2000, 'data', 'o1_index', 'standard')
>>> tdb = os.path.join(index_dir, 'db.terms.sqlite')
>>> ldb = os.path.join(index_dir, 'db.locations.sqlite')

Now create the database instance, passing in the location of the two sqlite
databases:

>>> db = TermDB(tdb, ldb)

The get() method takes a list of terms and returns a list of Term objects that
contain the term information:

>>> for t in db.get(['computer', 'protective film']): print t
<Term 'computer' freq=18290 documents=2897 tscore=0.985936 mscore=0.715400>
<Term 'protective film' freq=500 documents=95 tscore=1.000000 mscore=0.436000>

If no term information exists, a Term object will still be returned, but it will
be empty:

>>> for t in db.get(['friction backsheet', 'friction blacksheet']): print t
<Term 'friction backsheet' freq=10 documents=1 tscore=0.622755 mscore=-1.000000>
<Term 'friction blacksheet' NOT_IN_DATABASE>

There is a limit on the number of locations actually returned, this might bring
a bias into what rows are returned. This is not a serious problem for all but
the most frequent terms since at least the files were processed in random order
and as a result the inserts were in random order. However, for very frequent
terms the locations returned could all be from the same file.

To change this limit edit the LIMIT variable.

"""

import os, sqlite3

LIMIT = 200

q_get_term_data = "SELECT * FROM terms WHERE term = ?;"
q_get_locations = "SELECT doc, lines FROM locations WHERE term = ? LIMIT %d;" % LIMIT
q_get_locations_count = "SELECT count(*) FROM locations WHERE term = ?;"


class TermDB(object):

    def __init__(self, term_db, location_db):
        self.tdb = term_db
        self.ldb = location_db
        self.tconnection = sqlite3.connect(self.tdb)
        self.lconnection = sqlite3.connect(self.ldb)
        self.tcursor = self.tconnection.cursor()
        self.lcursor = self.lconnection.cursor()
            
    def get(self, terms):
        """Get a list of Term objects from the database, one for each term."""
        return [Term(t, self.tcursor, self.lcursor) for t in terms]

    def query_terms(self, query):
        """Return the result of a query over the terms database."""
        self.tcursor.execute(query)
        return self.tcursor.fetchall()

    def close(self):
        self.tconnection.close()
        self.lconnection.close()


class Term(object):

    """Object that represents information of terminformation in the database. If
    no information exists in the database, then the self.exists instance
    variable will be set to False."""
    
    def __init__(self, term, tcursor, lcursor):
        self.name = term
        self.exists = False
        self.frequency = None
        self.technology_score = None
        self.maturity_score = None
        self.init_term_data(tcursor)
        self.init_locations(lcursor)

    def init_term_data(self, tcursor):
        tcursor.execute(q_get_term_data, (self.name,))
        row = tcursor.fetchone()
        if row is not None:
            self.exists = True
            self.frequency = row[1]
            self.technology_score = row[2]
            self.maturity_score = row[3]

    def init_locations(self, lcursor):
        lcursor.execute(q_get_locations_count, (self.name,))
        row = lcursor.fetchone()
        self.documents = row[0]
        lcursor.execute(q_get_locations, (self.name,))
        rows = lcursor.fetchall()
        self.locations = [Location(row) for row in rows]

    def __str__(self):
        if self.exists:
            return "<Term '%s'" % self.name + \
                   " freq=%d" % self.frequency + \
                   " documents=%d" % self.documents + \
                   " tscore=%f" % self.technology_score + \
                   " mscore=%f>" % self.maturity_score
        else:
            return "<Term '%s' NOT_IN_DATABASE>" % self.name
            
    def pp_locations(self):
        for l in self.locations:
            print '  ', l

            
class Location(object):

    def __init__(self, row):
        self.doc = row[0]
        self.lines = [int(l) for l in row[1].split(' ')]

    def __str__(self):
        return "%s %s" % (self.doc, self.lines)

        
def read_opts():
    longopts = ['corpus=', 'batch=', 'verbose']
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
