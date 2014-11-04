To create an index, do the following:


1. run collect_frequencies.py

This collects frequencies and locations from d3_phr_feats file in a corpus. It
creates a file index.locs.txt with four columns: document, term, number of
occurrences in document, lines in document.


2. Run summarize_frequencies.py

This takes the output of the previous step and creates a corpus-wide summary of
the frequencies for each term. Creates index.locs.summ.az.txt.


3. Run combine_scores.py

Takes the output of the previous step as well as the technology and maturity
time series and creates a combined file with term, frequency, technology score
and maturity score. This creates a file named index.terms.txt.


4. Create db.terms.sqlite

This can be done as follows:

$ sqlite3 db.terms.sqlite < FILE_WITH_THE_FOLLOWING

.echo ON
PRAGMA cache_size = 500000;
PRAGMA synchronous = OFF;
PRAGMA journal_mode = OFF;
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA count_changes = OFF;
PRAGMA temp_store = MEMORY;
PRAGMA auto_vacuum = NONE;
.separator "\t"

CREATE TABLE terms(term TEXT, frequency INT, technology_score FLOAT, maturity_score FLOAT);

.import index.terms.txt terms

CREATE UNIQUE INDEX terms_term ON terms(term);
CREATE INDEX terms_frequency ON terms(frequency);
CREATE INDEX terms_technology ON terms(technology_score);
CREATE INDEX terms_maturity ON terms(maturity_score);

.exit


5. Create db.locations.sqlite

$ sqlite3 db.locations.sqlite < FILE_WITH_THE_FOLLOWING

.echo ON
PRAGMA cache_size = 500000;
PRAGMA synchronous = OFF;
PRAGMA journal_mode = OFF;
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA count_changes = OFF;
PRAGMA temp_store = MEMORY;
PRAGMA auto_vacuum = NONE;
.separator "\t"

CREATE TABLE locations(doc TEXT, term TEXT, count INT, lines TEXT);

.import index.locs.txt locations

-- Now do one of the following. I have not yet tested the second. It is not
-- needed now, but it has two advantages: it checks integrity of the data and
-- you can then search for documents and there terms
CREATE INDEX locations_term on locations(term);
CREATE UNIQUE INDEX locations_idx on locations(doc, term);

.exit
