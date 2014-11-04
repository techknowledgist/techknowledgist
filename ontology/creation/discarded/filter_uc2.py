# filter_uc2.py
# reformat output of unix uniq -c 
# while filtering out any lines with count < $1
# putting the count in the second (tab separated) column
# to <value>\t<count>

import sys
min = int(sys.argv[1])
#print "min: %i" % min

def reformat_uc2():
    for line in sys.stdin:
        line = line.strip("\n")
        line = line.lstrip(" ")
        count = line[0:line.find(" ")]
        int_count = int(count)
        value = line[line.find(" ")+1:]
        #print "count: %s, value %s" % (count, value)                                                                                        
        if int_count >= min:
            newline = value + "\t" + count
            print newline
            

if __name__ == "__main__":
    import os
    import sys

    #patent_dir = sys.argv[1]
    reformat_uc2()

