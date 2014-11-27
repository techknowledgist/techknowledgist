"""

A standalone utility to take a bunch of files from a list, parse the files using
an xml parser or string matching and extract the application date and the
publication date.

Usage:

    $ python create-date-idx.py INFILE OUTFILE WARNINGS START END

    Parses INFILE and creates OUTFILE which has three fields for each file, an
    application date, a publicaiton date and the filepath. Writes warnings to
    WARNINGS. If START and END are given, limits the number of files processed,
    starting the file after START and finishing at END.

Expects each line of the input to start like this:

    1997    /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/1997/004/US5675817A.xml

That is, a year followed by a path. There can be more information after the long
path (for example a short path as often used in the corpus config files).

Alternatively, it allows this kind of input:

    4577022A    /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/1986/004/US4577022A.xml

This is the format as used in ln_uspto.all.shuffled.txt and its ordered version
in the lists in /home/j/corpuswork/fuse/FUSEData/lists/.

Here is an example on how to do the entire list of US patents using three
processors:

    $ python create-date-idx.py /home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.shuffled.txt ln-uspto-1.txt warnings-1.txt 0 2500000
    $ python create-date-idx.py /home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.shuffled.txt ln-uspto-2.txt warnings-2.txt 2500000 5000000
    $ python create-date-idx.py /home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.shuffled.txt ln-uspto-3.txt warnings-3.txt 5000000 7500000

On the CS machines, this takes about 2-3 days.

"""

import sys, time
from xml.dom.minidom import parse

SKIP = 0
COUNT = 999999999999999999999
if len(sys.argv) > 4: SKIP = int(sys.argv[4])
if len(sys.argv) > 5: COUNT = int(sys.argv[5])
fh = open(sys.argv[1])
fh_results = open(sys.argv[2], 'w')
fh_warnings = open(sys.argv[3], 'w')
sys.stderr.write("Processing files %s through %s from %s\n" % (SKIP, COUNT, fh.name))


def find_dates():

    count = 0
    for line in fh:
        count += 1
        if count <= SKIP:
            continue
        if count > COUNT: break
        if count % 100 == 0: sys.stderr.write("%d\n" % count)
        fields = line.strip().split("\t")
        if len(fields) > 1: fname = fields[1]
        if len(fields) == 1: fname = fields[0]
        if fname == '':
            continue
        #find_dates_using_xml(fname)
        find_dates_using_grep(fname)


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

    t1 = time.time()
    find_dates()
    print "Time elapsed: %d seconds" % (time.time() - t1)
