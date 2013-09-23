"""

A standalone utility to take a bunch of files from a list, XML-parse the files
and extract some dates.

Expects each line of the input to start like this:

    1997    /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/1997/004/US5675817A.xml

That is, a year followed by a path. There can be more information after the long
path (for example a short path as often used in the corpus config files).

Perhaps belongs in ontology/utils (and perhaps patent_index.py belongs there as
well).


"""

import sys
from xml.dom.minidom import parse

SKIP = 1000
COUNT = 999999999999999999999
if len(sys.argv) > 2: COUNT = int(sys.argv[2])
if len(sys.argv) > 3: SKIP = int(sys.argv[3])
fh = open(sys.argv[1])
fh_results = open('date_idx.txt', 'w')
fh_warnings = open('date_warnings.txt', 'w')
sys.stderr.write("Processing %d files from %s\n" % (COUNT, fh.name))


def find_dates():

    global SKIP
    count = 0
    for line in fh:
        if SKIP > 0:
            SKIP = SKIP -1
            continue
        count += 1
        if count > COUNT: break
        if count % 100 == 0: sys.stderr.write("%d\n" % count)
        fname = line.strip().split("\t")[1]
        find_dates_using_xml(fname)
        #find_dates_using_grep(fname)


def find_dates_using_xml(fname):

    dom = parse(fname)

    apprefdate = None
    pubrefdate = None
    
    pubrefs = dom.getElementsByTagName('publication-reference')
    pubrefdates = pubrefs[0].getElementsByTagName('date')
    if len(pubrefs) != 1 or len(pubrefdates) != 1:
        print "WARNING: funny stuff in", fh.name
    else:
        pubrefdate = pubrefdates[0].firstChild.nodeValue

    apprefs = dom.getElementsByTagName('application-reference')
    apprefdates = apprefs[0].getElementsByTagName('date')
    if len(apprefs) != 1 or len(apprefdates) != 1:
        print "WARNING: funny stuff in", fh.name
    else:
        apprefdate = apprefdates[0].firstChild.nodeValue

    fh_results.write("%s\t%s\t%s\n" % (fname, apprefdate, pubrefdate))


    
def find_dates_using_grep(fname):

    appdate = None
    pubdate = None
    in_appref = False
    in_pubref = False
    lines_read = 0
    for line in open(fname):
        lines_read += 1
        text = line.strip()
        if text.startswith('<application-reference'):
            in_appref = True
            in_pubref = False
            #print line,
        if text.startswith('<publication-reference'):
            in_appref = False
            in_pubref = True
            #print line,
        if text.startswith('<date>'):
            if in_appref: appdate = text[6:14]
            if in_pubref: pubdate = text[6:14]
        if appdate and pubdate:
            fh_results.write("%s\t%s\t%s\n" % (appdate, pubdate, fname))
            #sys.stderr.write("LINES READ: %d\n" % lines_read)
            return
    #sys.stderr.write("LINES READ: %d\n" % lines_read)
    if not appdate and pubdate:
        fh_warnings.write("WARNING: funny stuff in %s\n" % fname)
    
        
        
if __name__ == '__main__':

    find_dates()
