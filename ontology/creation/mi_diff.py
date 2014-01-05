# Postprocessing of the mi files

# filter out 
#    pairs that are variants (e.g. share the same prefix)
#    pairs that have some word in common  (e.g. java application|java applet)
#    
# For the rest:
#
# add the year as a field
# compute the diff in value from last year for mi*freq, mi, doc_freq
# (if term pair did not exist in previous year, assume its values were all 0)

# write out 
# term1 term2 year mif_diff, mi_diff, doc_freq_diff, mif, mi, doc_freq, term1_freq, term2_freq

import codecs
import math

# populate the d_mi dictionaries, given last year
def mi_diff(path, last_year, file_type="mi"):
    # dicts to store last year, current year and output data
    d_mi_last = {}
    d_mi_current = {}
    d_mi_diff = {}

    current_year = last_year + 1
    last_year = str(last_year)
    current_year = str(current_year)
    
    current_year_path = path + "/" + current_year + "." + file_type
    last_year_path = path + "/" + last_year + "." + file_type

    diff_output_path = path + "/" + current_year + "." + file_type + ".diff"

    s_last = codecs.open(last_year_path, encoding='utf-8')
    s_current = codecs.open(current_year_path, encoding='utf-8')
    s_diff = codecs.open(diff_output_path, "w", encoding='utf-8')

    # store data in dictionaries indexed by the pair and with value = list of all fields 
    last_count = 0
    for line in s_last:
        line = line.strip("\n")
        l_field = line.split("\t")
        term1 = l_field[0]
        term2 = l_field[1]
        pair = term1 + "|" + term2
        d_mi_last[pair] = l_field
        last_count += 1
        #print "loading line: %s" % l_field

    print "loaded %i pairs from year: %s" % (last_count, last_year)
    current_count = 0
    for line in s_current:
        line = line.strip("\n")
        l_field = line.split("\t")
        term1 = l_field[0]
        term2 = l_field[1]
        pair = term1 + "|" + term2
        d_mi_current[pair] = l_field
        current_count += 1

        #print "loading line: %s" % l_field
    s_last.close()
    s_current.close()


    print "loaded %i pairs from year: %s" % (current_count, current_year)

    # Now for each pair in current_year, compute the diffs from last_year
    for pair in d_mi_current.keys():
        # extract the current fields needed to compute diffs
        current = d_mi_current[pair]
        term1 = current[0]
        term2 = current[1]
        c_mif = float(current[2])
        c_mi = float(current[3])
        c_freq = int(current[4])
        t1_freq = current[5]
        t2_freq = current[6]

        # initialize default last values, in case pair did not occur in last_year
        last_mif = 0.0
        last_mi = 0.0
        last_freq = 0
        diff_mif = 0.0
        diff_mi = 0.0
        diff_freq = 0
        if d_mi_last.has_key(pair):
            last = d_mi_last[pair]
            last_mif = float(last[2])
            last_mi = float(last[3])
            last_freq = int(last[4])

        diff_freq = c_freq - last_freq
        diff_mi = c_mi - last_mi
        diff_mif = c_mif - last_mif
        change = (c_freq + 1.0) / (last_freq + 1.0)
        log_diff = math.log((abs(diff_freq) + 1), 2)
        adj_change = math.copysign(log_diff, diff_freq) * change

        #print "list: %s" % ([term1, term2, current_year, str(diff_mif), str(diff_mi), str(diff_freq), str(c_mif), str(c_mi), str(c_freq), t1_freq, t2_freq])
        #print "join: %s" % "\t".join([term1, term2, current_year, str(diff_mif), str(diff_mi), str(diff_freq), str(c_mif), str(c_mi), str(c_freq), t1_freq, t2_freq, str(change), str(adj_change)] )
   
        # write out the full set of fields
        # adj_change is col 7 (for sorting)
        # c_freq is col 5
        diff_line = "\t".join([term1, term2, current_year, str(last_freq), str(c_freq),  str(change), str(adj_change), str(diff_mif), str(diff_mi), str(diff_freq), str(c_mif), str(c_mi), str(c_freq), t1_freq, t2_freq] )
        #print "diff_line: %s" % str(diff_line)
        s_diff.write("%s\n" % diff_line)

    s_diff.close()



# diff for files containing freq and category
# populate the d_mi dictionaries, given last year
def tfc_diff(path, last_year, file_type="tfc"):
    # dicts to store last year, current year and output data
    d_mi_last = {}
    d_mi_current = {}
    d_mi_diff = {}

    current_year = last_year + 1
    last_year = str(last_year)
    current_year = str(current_year)
    
    current_year_path = path + "/" + current_year + "." + file_type
    last_year_path = path + "/" + last_year + "." + file_type

    diff_output_path = path + "/" + current_year + "." + file_type + ".diff"

    s_last = codecs.open(last_year_path, encoding='utf-8')
    s_current = codecs.open(current_year_path, encoding='utf-8')
    s_diff = codecs.open(diff_output_path, "w", encoding='utf-8')

    # store data in dictionaries indexed by the term and with value = list of all fields 
    last_count = 0
    for line in s_last:
        line = line.strip("\n")
        l_field = line.split("\t")
        term = l_field[0]
        d_mi_last[term] = l_field
        last_count += 1
        #print "loading line: %s" % l_field

    print "loaded %i terms from year: %s" % (last_count, last_year)
    current_count = 0
    for line in s_current:
        line = line.strip("\n")
        l_field = line.split("\t")
        term = l_field[0]
        d_mi_current[term] = l_field
        current_count += 1

        #print "loading line: %s" % l_field
    s_last.close()
    s_current.close()


    print "loaded %i terms from year: %s" % (current_count, current_year)

    # Now for each term in current_year, compute the diffs from last_year
    for term in d_mi_current.keys():
        # extract the current fields needed to compute diffs
        current = d_mi_current[term]
        term = current[0]
        c_cat = current[1]
        c_freq = int(current[2])
        c_cat_freq = int(current[3])

        # initialize default last values, in case pair did not occur in last_year
        last_freq = 0
        last_cat_freq = 0
        diff_freq = 0
        last_cat = "u"
        cat_change = "n"
        if d_mi_last.has_key(term):
            last = d_mi_last[term]
            last_cat = last[1]
            last_freq = int(last[2])
            last_cat_freq = int(last[3])
            # Has the primary category for this term changed?  Don't count "u" for changes.
            if c_cat != last_cat and not (last_cat == "u" or c_cat == "u"):
                cat_change = "y"

        diff_freq = c_freq - last_freq
        change = (c_freq + 1.0) / (last_freq + 1.0)
        log_diff = math.log((abs(diff_freq) + 1), 2)
        adj_change = math.copysign(log_diff, diff_freq) * change

        # write out the full set of fields

        # create a grep searchable cat symbol: |<c_cat>
        cat_symbol = "|" + c_cat
        diff_line = "\t".join([term, current_year, cat_symbol, str(last_freq), str(c_freq),  str(change), str(adj_change), str(diff_freq), cat_change, last_cat, str(last_cat_freq), c_cat, str(c_cat_freq)])
        #print "diff_line: %s" % str(diff_line)
        s_diff.write("%s\n" % diff_line)

    s_diff.close()

# run diff on term cooccurrence pairs
def run_mi_diff():
    last_year = 1995
    # to run a small test:
    #last_year = 9998
    #path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_mi"
    path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_mi_tas"
    mi_diff(path, last_year)

# run diff on term/verb pairs
# (difference is in the path where the input and output go)
# mi_diff.run_tv_diff()
def run_tv_diff():
    #last_year = 1995
    # to run a small test:
    #last_year = 9998
    path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"

    file_type = "tcmi"
    #end_range = 2007
    end_range = 1996
    for last_year in range(1995, end_range):
        print "[run_tv_diff] last_year: %i" % last_year
        mi_diff(path, last_year, file_type)

    print "[run_tv_diff] Completed for year: %s, file: %s" % (str(last_year), file_type)

# mi_diff.run_tfc_diff()
def run_tfc_diff():
    #last_year = 1995
    # to run a small test:
    #last_year = 9998
    path = "/home/j/anick/patent-classifier/ontology/creation/data/patents/cs_500k/data/m2_tv"

    file_type = "tfc"
    end_range = 2007
    #end_range = 1996
    for last_year in range(1995, end_range):
        print "[run_tfc_diff] last_year: %i" % last_year
        tfc_diff(path, last_year, file_type)

    print "[run_tfc_diff] Completed for year: %s, file: %s" % (str(last_year), file_type)

