# prom.py
# support functions for ML of promise features using 
# Mitre's prominence data.

# convert prominence file to annotation format
# prominence file: terms_br_nyu_mitre.sorted.keep.ch.nr
# Created by joining brandeis chunks, NYU filter file, and Mitre's prominence scores for
# patents granted in 2002.
# term chunk_count mitre_abstract_count pe1 pe2 pe3 pe4 pe5
# pe is the prominence from 2002 to 1-5 years out
# remote connection       94      0       0.944444444     0.87    0.729916898     0.588477366     0.397959184

# When this data is used to create mallet training instances, the number of instances per category will depend on
# both the number of terms in the category and the number of docs each term occurs in.  Thus, balancing the 
# number of instances should be done on the mallet file rather than earlier in the process.


import sys

# pass in a list of ranges and labels and a prominence distance value (1-5)
# ranges should be disjoint, with the most common range occurring first
# [[label, high, low][label, high, low],...]
def prom2annot(l_range, prom_distance):
    #print "[prom2annot] %s, %i" % (l_range, prom_distance)
    # get the index in the line for the pe value to be used
    prom_field = prom_distance + 2
    min_doc_count = 1
    for line in sys.stdin:
        line = line.strip()
        l_fields = line.split("\t")
        term = l_fields[0]
        doc_count = int(l_fields[1])
        if doc_count >= min_doc_count:
            prom = float(l_fields[prom_field])
            #print "term: %s, prom: %s" % (term, prom)
            for range in l_range:
                high = range[1]
                low = range[2]
                #print "high: %f, low: %f" % (high , low)
                if prom >= low and prom <= high:
                    print "%s\t%s\t%f\t%i" % (range[0], term, prom, doc_count)
                    break

# prom.prom1()
def prom1():
    l_range = [["y", 1.0, 0.6], ["n", 0.2, 0.0]]
    prom_distance = 1
    prom2annot(l_range, prom_distance)
    
        
# python prom.py < /home/j/anick/temp/fuse/terms_br_nyu_mitre.sorted.keep.ch.nr > /home/j/anick/temp/fuse/prom1.annot
if __name__ == '__main__':
    prom1()
        


