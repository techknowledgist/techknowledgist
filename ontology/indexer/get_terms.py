"""


Usage:
    $ python get_terms.py OPTIONS

Options:
    --corpus   -  the corpus to run the matcher on
    --batch    -  directory in data/o2_index to read from and write to

Example:
    $ python get_terms.py \
      --corpus data/patents/201306-computer-science \
      --batch standard \
      --verbose

"""

import os, sys, getopt, sqlite3

# number of locations actually returned
LIMIT = 100

get_term_data_query = "SELECT * FROM terms WHERE term = ?;"
get_locations_query = "SELECT doc, lines FROM locations WHERE term = ? LIMIT %d;" % LIMIT
get_locations_count_query = "SELECT count(*) FROM locations WHERE term = ?;"


def get(corpus, batch, term):
    batch_dir = os.path.join(corpus, 'data', 'o1_index', batch)
    term_db = os.path.join(batch_dir, 'db.terms.sqlite')
    location_db = os.path.join(batch_dir, 'db.locations.sqlite')
    db = Terms(term_db, location_db)
    return db.get(term)

    
class Terms(object):

    def __init__(self, term_db, location_db):
        self.tdb = term_db
        self.ldb = location_db
        self.tconnection = sqlite3.connect(self.tdb)
        self.lconnection = sqlite3.connect(self.ldb)
        self.tcursor = self.tconnection.cursor()
        self.lcursor = self.lconnection.cursor()
            
    def get(self, term):
        term = Term(term, self.tcursor, self.lcursor)
        return term

    def close(self):
        self.tconnection.close()
        self.lconnection.close()


class Term(object):
    
    def __init__(self, term, tcursor, lcursor):
        self.name = term
        self.frequency = None
        self.technology_score = None
        self.maturity_score = None
        self.init_term_data(tcursor)
        self.init_locations(lcursor)

    def init_term_data(self, tcursor):
        tcursor.execute(get_term_data_query, (self.name,))
        row = tcursor.fetchone()
        if row is not None:
            self.frequency = row[1]
            self.technology_score = row[2]
            self.maturity_score = row[3]

    def init_locations(self, lcursor):
        lcursor.execute(get_locations_count_query, (self.name,))
        row = lcursor.fetchone()
        self.locations_count = row[0]
        lcursor.execute(get_locations_query, (self.name,))
        rows = lcursor.fetchall()
        self.locations = [Location(row) for row in rows]

    def __str__(self):
        return "<Term '%s'" % self.name + \
               " freq=%d" % self.frequency + \
               " tscore=%f" % self.technology_score + \
               " mscore=%f" % self.maturity_score + \
               " locations=%d>" % self.locations_count
    
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
    longopts = ['corpus=', 'batch=', 'verbose' ]
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))



if __name__ == '__main__':

    corpus = None
    batch = None

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--corpus': corpus = val
        elif opt == '--batch': batch = val
        elif opt == '--verbose': VERBOSE = True

    term = get(corpus, batch, 'laser device')
    print term
    term.pp_locations()
