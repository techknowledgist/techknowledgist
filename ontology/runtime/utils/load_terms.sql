
-- sqlite3 all_terms.db < all_terms.sql
.echo ON
PRAGMA cache_size = 500000;
PRAGMA synchronous = OFF;
PRAGMA journal_mode = OFF;
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA count_changes = OFF;
PRAGMA temp_store = MEMORY;
PRAGMA auto_vacuum = NONE;
CREATE TABLE terms(term TEXT);
.separator "\t"
.import /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/classifier/all_terms.txt terms
CREATE INDEX i_term on terms (term);
.exit


-- Ran this on Saturday October 26th 2013, took about 15-30 minutes.
-- Ran a select count(*) from terms, took about a minute and returned 31,453,657.

-- However, selects were not using the index and here is why:
--
--   6 aeneas-> ontology/classifier> sqlite3 all_terms.sqlite < all_terms.sql &
--   [1] 8004
--   17 aeneas-> ontology/classifier> PRAGMA cache_size = 500000;
--   PRAGMA synchronous = OFF;
--   PRAGMA journal_mode = OFF;
--   PRAGMA locking_mode = EXCLUSIVE;
--   PRAGMA count_changes = OFF;
--   PRAGMA temp_store = MEMORY;
--   PRAGMA auto_vacuum = NONE;
--   CREATE TABLE terms(term TEXT);
--   .separator "\t"
--   .import /home/j/marc/Desktop/fuse/code/patent-classifier/ontology/classifier/all_terms.txt terms
--   CREATE INDEX i_term on terms (term);
--   SQL error: database disk image is malformed
--   .exit
--
--   [1]    Done                          sqlite3 all_terms.sqlite < all_terms.sql

-- Running the last step separately from inside sqlite3 also fails for the same reason.
--
--   sqlite> PRAGMA integrity_check;
--   *** in database main ***
--   Outstanding page count goes from 3 to 7 during this analysis
--
-- (This appears to be a check of the check)

-- Tried again on chalciope in case there was a bad sector, took 6 minutes, but
-- with same result

-- Tried again (11/25/2013), but now in parts, first splitting all_terms.txt
-- into 31 files of 1M or less terms. This worked fine, which might mean that
-- there is a problem with the size of the all_terms.txt file.

-- Tried also on a file concatenated from the first ten 1M files. No problems
-- there either. Then tried on a file concatenated from the first twenty 1M
-- files. This worked eventually but took a very long time, about 6 hours (and
-- created a 1.3GB file). Then tried on a concatenation of all 1M files. This
-- failed as before, immediately after the table and when the index was to be
-- created.

