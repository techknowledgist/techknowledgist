# reformat output of unix uniq -c 
# putting the count in the FIRST (tab separated) column
# to <count>\t<value>
def reformat_uc2():
    for line in sys.stdin:
        line = line.strip("\n")
        line = line.lstrip(" ")
        count = line[0:line.find(" ")]
        value = line[line.find(" ")+1:]
        #print "count: %s, value %s" % (count, value)                                                                                        
        newline = count + "\t" + value
        print newline

if __name__ == "__main__":
    import os
    import sys

    #patent_dir = sys.argv[1]
    reformat_uc2()

