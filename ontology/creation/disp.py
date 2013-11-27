"""
disp.py

Database functions to study dispersion of phrases over time

"""

import collections
import pdb
import os
import sys
import codecs
import apsw
import re
import config
import log
import math
from collections import defaultdict
from ontology.utils.file import get_year_and_docid, open_input_file
from operator import itemgetter, attrgetter
import terms_db
import pickle

debug_p = False

#global dictionary mapping year to # docs
# created by querying the cs_terms_db terms table:
# select count(distinct(doc)) from terms where year = 2002; 
d_corpus_size = {2003: 32106, 2002: 28188, 2001: 12918, 2000: 8354, 1999: 8769, 1998: 8534, 1997: 4974} 


def make_header(l_items):
    return '_'.join(item for item in l_items)

# create an object to hold data
# dd = disp.DispData(db, 1997, 2003)
# populate the object with terms
# dd.process("vsat")
# Compute derived statistics for all populated terms
# dd.store_derived_data()

class DispData():
    def __init__(self, db, start_year, end_year, output_dir="/home/j/anick/temp/fuse/tsv/"):
        # dictionary of term stats
        self.d_term = {}
        # list of terms in dictionary
        self.l_term = []
        self.start_year = start_year
        self.end_year = end_year
        self.num_years = (end_year - start_year) + 1
        self.end_of_row_range = self.num_years + 1
        self.db = db
        # dir where tsv files are written
        self.output_dir = output_dir
        # note that this should not be hard coded!
        self.log_file = "/home/j/anick/temp/fuse/disp.log"

    def  close_log(self):
        self.s_log.close()

    def open_log(self):
        self.s_log = codecs.open(self.log_file, "a", encoding='utf-8')

    def pickle(self, file):
        s_file = open(file, "w")
        pickle.dump([self.d_term, self.l_term])
        s_file.close()


    def process(self, term):
        #self.open_log()
        d_term = self.d_term
        self.l_term.append(term)

        # run query for dispersion of head and mod terms and store in dictionary
        # the db row will contain term, then a column for each year
        end_of_row_range = self.num_years + 1
        for disp_type in ["hd", "md", "ha", "ma"]:
            self.store_count_data(term, disp_type)

        #self.s_log.write("[log]\t%s\t%s\n" % (term, disp_type))
        # compute entropy
        for year in range(1997, 2004):
            for disp_type in ["hd", "md", "ha", "ma"]:
                self.store_disp_data(term, year, disp_type)

            #self.s_log.write("[scounts]\t%s\t%i\t%s\n" % (term, year, d_head[(term, year, "s_counts")]))
            #self.s_log.write("[scores]\t%s\t%i\t%s\t%i\t%i\t%f\n" % (term, year, disp_type, disp, counts_sum, prob_sum) )
            #self.s_log.write("%s\t%i\t%s\t%i\t%i\t%f\t%s\n" % (term, year, disp_type, disp, counts_sum, prob_sum, l_superterms_sorted))
                             

        #self.close_log()
        #print "dh1: %s" % l_dh1
        #print "dh2: %s" % l_dh2

        # retrieve raw counts
        self.store_raw_count_data(term)

    """
    def output_stats():
        # term year
        s_file = codecs.open(file, "w", encoding='utf-8')
        for term in self.l_term:
            for year in range(1997, 2004):
                for disp_type in ["hd", "md", "ha", "ma"]:
        s_file.close()
     """

    def store_disp_data(self, term, year, disp_type):
        d_term = self.d_term
        l_counts = d_term[term, year, disp_type, "s_counts"]
        l_superterms = d_term[(term, year, disp_type, "s2")]

        counts_sum = 0
        prob_sum = 0.0
        disp = 0
        l_superterm_counts = []
        l_superterms_sorted = []

        i = 0
        for count in l_counts:
            counts_sum = counts_sum + count
            disp = disp + 1
            l_superterm_counts.append([l_superterms[i], count])
            #print "l_superterm_counts: %s" % l_superterm_counts
            i += 1

        # sort the superterms by count
        #if counts_sum > 0:
        #    pdb.set_trace()
        l_superterms_sorted = l_superterm_counts
        l_superterms_sorted.sort(key=itemgetter(1), reverse=True)

        # now that we have the counts_sum, we can compute prob for each superterm
        for count in l_counts:
            prob = (1.0 * count) / counts_sum
            log2_prob = math.log(prob, 2)
            prob_sum = prob_sum + prob * log2_prob

        #print "s2 for %s, %i: %s" % (term, year, d_head[(term, year, "s2")])

        if prob_sum < 0:
            entropy = -1 * prob_sum
        else: 
            # avoid -0.0; keep it 0.0
            entropy = prob_sum

        #print "s_counts for %s, %i: %s" % (term, year, d_head[(term, year, "s_counts")])
        #print "year: %i, disp: %i, counts_sum: %f, prob_sum: %f" % (year, disp, counts_sum, entropy) 
        #print "terms_sorted: %s\n" % l_superterms_sorted
        
        d_term[(term, year, disp_type, "disp")] = disp
        d_term[(term, year, disp_type, "counts_sum")] = counts_sum
        d_term[(term, year, disp_type, "entropy")] = entropy
        d_term[(term, year, disp_type, "superterms")] = l_superterms_sorted

    def store_derived_data(self):
        d_term = self.d_term
        # potentially diagnostic ratios
        for term in self.l_term:
            for year in range(1997, 2004):

                # check for 0 denominator first
                # compute ratios (abstract and full document)
                if d_term[(term, year, "ma", "disp")] == 0:
                    d_term[(term, year, "a", "hm_disp_ratio")] = 0
                else:
                    d_term[(term, year, "a", "hm_disp_ratio")] = (1.0 * d_term[(term, year, "ha", "disp")]) / d_term[(term, year, "ma", "disp")]

                if d_term[(term, year, "md", "disp")] == 0:
                    d_term[(term, year, "d", "hm_disp_ratio")] = 0
                else:
                     d_term[(term, year, "d", "hm_disp_ratio")] = (1.0 * d_term[(term, year, "hd", "disp")]) / d_term[(term, year, "md", "disp")] 

                if d_term[(term, year, "ma", "entropy")] == 0:
                    d_term[(term, year, "a", "hm_ent_ratio")] = 0
                else:

                    d_term[(term, year, "a", "hm_ent_ratio")] = (1.0 * d_term[(term, year, "ha", "entropy")]) / d_term[(term, year, "ma", "entropy")] 

                if d_term[(term, year, "md", "entropy")] == 0:
                    d_term[(term, year, "d", "hm_ent_ratio")] = 0
                else:

                    d_term[(term, year, "d", "hm_ent_ratio")] = (1.0 * d_term[(term, year, "hd", "entropy")]) / d_term[(term, year, "md", "entropy")] 

                if d_term[(term, year, "d", "scounts")] == 0:
                    d_term[(term, year, "ad", "scounts_ratio")] = 0
                else:
                    d_term[(term, year, "ad", "scounts_ratio")] = (1.0 * d_term[(term, year, "a", "scounts")] ) / d_term[(term, year, "d", "scounts")]


    # stores count data for all years for a term's superterms, given the disp_type (h or m)
    def store_count_data(self, term, disp_type):
        d_term = self.d_term
        # minimum count per year to include a superterm in calculations
        disp_min = 2

        # initialize our dictionary keys
        year = self.start_year

        for year_idx in range(1, self.end_of_row_range):
            # "s2" means subphrase based dispersion with count >= 2
            d_term[(term, year, disp_type, "s2")] = []
            d_term[(term, year, disp_type, "s_counts")] = []
            year += 1
            
        # construct the relevant database command
        # for entire doc
        if disp_type == "md":
            cmd = "select * from chunk_counts where term like \"% " + term + "\""
        elif disp_type == "hd":
            cmd = "select * from chunk_counts where term like \"" + term + " %\""
        # for abstract/title only
        elif disp_type == "ma":
            cmd = "select * from abstract_ccounts where term like \"% " + term + "\""
        elif disp_type == "ha":
            cmd = "select * from abstract_ccounts where term like \"" + term + " %\""

        # process the rows output by the query
        # row are of the form: <term> <counts by year>
        # e.g. static applet registry class|0|0|0|0|2|5|6
        for row in self.db.cursor.execute(cmd):
            superterm = row[0]

            year = self.start_year
            for year_idx in range(1, self.end_of_row_range):

                # create a list of all superterms with count >= disp_min 
                if row[year_idx] >= disp_min:
                    key_s2 = (term, year, disp_type, "s2")
                    d_term[key_s2].append(superterm)
                    #print "s2 for %s, %i, %s: %s" % (term, year, disp_type, d_term[key_s2])
                                
                    # keep track of counts for each superterm to compute entropy
                    key_counts = (term, year, disp_type, "s_counts")
                    d_term[key_counts].append(row[year_idx])
                    #print "s2 for %s, %i, %s: %s" % (term, year, disp_type, d_term[key_counts])
                    
                year += 1


    def store_raw_count_data(self, term):
        d_term = self.d_term
        d_command = {}

        # initialize our dictionary keys
        year = self.start_year

        for year_idx in range(1, self.end_of_row_range):
            d_term[(term, year, "a", "ccounts")] = 0
            d_term[(term, year, "a", "scounts")] = 0
            d_term[(term, year, "d", "ccounts")] = 0
            d_term[(term, year, "d", "scounts")] = 0
            year += 1
            
        # construct the relevant database command
        # doc/abstract counts and subphrase counts
        d_command["cmd_d_ccounts"] = "select * from chunk_counts where term = \"" + term + "\""
        d_command["cmd_d_scounts"] = "select * from counts where term = \"" + term + "\""
        d_command["cmd_a_ccounts"] = "select * from abstract_ccounts where term = \"" + term + "\""
        d_command["cmd_a_scounts"] = "select * from abstract_scounts where term = \"" + term + "\""
        

        # process the rows output by the query
        # rows are of the form: <term> <counts by year>
        # e.g. static applet registry class|0|0|0|0|2|5|6
        for loc in ["a", "d"]:
            for count_type in ["ccounts", "scounts"]:
                cmd = "cmd_" + loc + "_" + count_type
                #print "cmd: %s, %s" % (cmd, d_command[cmd])
                for row in self.db.cursor.execute(d_command[cmd]):
                    #pdb.set_trace()
                    #print "row: %s" % str(row)

                    year = self.start_year
                    for year_idx in range(1, self.end_of_row_range):

                        key = (term, year, loc, count_type)
                        #print "key: %s" % str(key)

                        d_term[key] = row[year_idx]
                        #print "raw count:%s, %i, %s: %s, %i" % (term, year, loc, count_type, d_term[key])

                        year += 1

    """
    tab separated files with header lines, used for data frames in R.
    http://stat.ethz.ch/R-manual/R-devel/library/utils/html/read.table.html
    """
    
    def write_time_series_tsv(self, loc, attr):
        filename = "df_" + loc + "_" + attr + ".tsv"
        print "Writing to: %s" % filename
        dir = self.output_dir
        if dir != "" and dir[-1] != "/":
            dir = dir + "/"
        filepath = dir + filename
        s_out = codecs.open(filepath, "a", encoding='utf-8')

        # output header line
        l_row = ["term"]
        for year in range(self.start_year, self.end_year + 1):
            l_row.append(str(year))
        s_out.write("%s\n" % terms_db.list2tsv(l_row))

        for term in self.l_term:
            l_row = [term]
            for year in range(self.start_year, self.end_year + 1):
                key = (term, year, loc, attr)
                l_row.append(self.d_term[key])
            s_out.write("%s\n" % terms_db.list2tsv(l_row))
            
        s_out.close() 

    # write out all time series data as separate files by field
    def write_all_ts_tsv(self):
        for loc in ["d", "a"]:
            for attr in [ "ccounts", "scounts", "hm_disp_ratio", "hm_ent_ratio"]:
                write_time_series_tsv(loc, attr)
        
        write_time_series_tsv("ad", "scounts_ratio")

        for disp_type in ["hd", "md", "ha", "ma"]:
            for attr in ["disp", "entropy"]:
                write_time_series_tsv(disp_type, attr)

    def write_yearly_tsv(self, year):
        filename = "df_" + str(year) + ".tsv"

        dir = self.output_dir
        if dir != "" and dir[-1] != "/":
            dir = dir + "/"
        filepath = dir + filename
        print "Writing to: %s" % filepath

        s_out = codecs.open(filepath, "w", encoding='utf-8')

        # create a header line of all field names
        l_row = ["term"]
        for loc in ["d", "a"]:
            for attr in [ "ccounts", "scounts", "hm_disp_ratio", "hm_ent_ratio"]:
                l_row.append(make_header([loc, attr]))
        
        l_row.append(make_header(["ad", "scounts_ratio"]))

        for disp_type in ["hd", "md", "ha", "ma"]:
            for attr in ["disp", "entropy"]:
                l_row.append(make_header([disp_type, attr]))

        header_row = terms_db.list2tsv(l_row)
        #print "header row: %s" % header_row
        s_out.write("%s\n" % terms_db.list2tsv(l_row)) 

        # loop over all terms
        for term in self.l_term:
            l_row = [term]

            for loc in ["d", "a"]:
                for attr in [ "ccounts", "scounts", "hm_disp_ratio", "hm_ent_ratio"]:
                    l_row.append(self.d_term[(term, year, loc, attr)])

            l_row.append(self.d_term[(term, year, "ad", "scounts_ratio")])

            for disp_type in ["hd", "md", "ha", "ma"]:
                for attr in ["disp", "entropy"]:
                    l_row.append(self.d_term[(term, year, disp_type, attr)])
        
            s_out.write("%s\n" % terms_db.list2tsv(l_row)) 

    # process terms from a file
    def process_from_file(self, filespec, ):
        s_input = codecs.open(filespec, encoding='utf-8')
        for line in s_input:
            term = line.strip()
            print "Processing: %s" % term
            self.process(term)
        print "Processing completed"
        s_input.close()

# dd = disp.test(db)

# positive examples (terms whch appear in docs in 1998 and reach abstract count of 10 by 2003)
def test_1(db):
    dd = DispData(db, 1997, 2003,  "/home/j/anick/temp/fuse/tsv/test") 
    #dd.process("usb controller")
    #dd.process("emails")
    dd.process_from_file("/home/j/anick/temp/fuse/growth_97-03_Agt10.from98.train.terms")
    dd.store_derived_data()
    for year in range(1997, 2004):
        dd.write_yearly_tsv(year)
    return(dd)


# negative examples (terms appearing in 1998 with at least abstract count of 4 but that did not become prominent by 2003)
def test_0(db):
    dd = DispData(db, 1997, 2003,  "/home/j/anick/temp/fuse/tsv/test_0") 
    #dd.process("usb controller")
    #dd.process("emails")
    dd.process_from_file("/home/j/anick/temp/fuse/growth_97-03_Alt10.from98.Agt4.random.200.train.terms")
    dd.store_derived_data()
    for year in range(1997, 2004):
        dd.write_yearly_tsv(year)
    return(dd)

# create the output directory before running
# db = terms_db.TermsDB("/home/j/anick/temp/fuse/", "cs_terms_db")
# disp.test_bae_mini(db)
def test_bae_mini(db):
    dd = DispData(db, 1997, 2003,  "/home/j/anick/temp/fuse/tsv/test_bae_mini") 
    #dd.process("usb controller")
    #dd.process("emails")
    dd.process_from_file("/home/j/anick/temp/fuse/bae/join_terms.sorted")
    dd.store_derived_data()
    for year in range(1997, 2004):
        dd.write_yearly_tsv(year)
    return(dd)

def test_bae_mini_3(db):
    dd = DispData(db, 1997, 2003,  "/home/j/anick/temp/fuse/tsv/test_bae_mini_3") 
    #dd.process("usb controller")
    #dd.process("emails")
    dd.process_from_file("/home/j/anick/temp/fuse/bae/join_terms.sorted.3")
    dd.store_derived_data()
    for year in range(1997, 2004):
        dd.write_yearly_tsv(year)
    return(dd)


"""
keys for d_term
list of subsuming terms (superterms) of type disp_type  with count >= 2
(term, year, disp_type, "s2")
This is used to compare superterm sets from one year to another.
md  modifier dispersion for entire (d)oc
hd  head disperson for doc
ma  modifier dispersion for abstract
ha  head dispersion for abstract

list of counts of each subsuming term according to disp_type
this corresponds with the s2 list above.  This is used to compute
entropy of heads and modifiers.
(term, year, disp_type, "scounts")

list of <superterm, frequency> pairs sorted by frequency
(term, year, disp_type, "superterms")

entropy of modifiers and heads for a term
(term, year, disp_type, "entropy")

dispersion of modifiers and heads for a term
(term, year, disp_type, "disp")

ratios
abstract disp/entorpy to doc
(term, year, ["a", "d"], ["hm_disp_ratio", "hm_ent_ratio"])

abstract term count to document term count
(term, year, "ad", "scounts_ratio") 

raw counts for abstract and full doc.  ccounts are bounded chunks, scounts 
include subsuming terms.
(term, year, ["a"|"d"], ["ccounts"|"scounts"])


"""

