"""

Scans the source data directory with Web of Science data in WOS_DIR and selects
the computer science abstracts from all years in YEARS.

Usage:

    $ python read_cs_docs.py

Input files to the WosReader are gzipped files like WoS.out.1998000001.gz. For
each of these, a file WoS.out.1998000001 is created in the cs subdirectory, that
file has all cs abstracts separated by white lines.

A follow up script would takes these files and create individual files for each
abstract, grouped in directories for years.

"""


import os, sys, glob, gzip, codecs


WOS_DIR = '/home/j/corpuswork/fuse/FUSEData/2013-04/WoS_2012_Aug/'
YEARS = [1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007]



def get_filehandle(filename):
    gzipfile = gzip.open(filename, 'rb')
    reader = codecs.getreader('utf-8')
    fh = reader(gzipfile) 
    return fh


class WosReader(object):

    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile
        self.fh_in = get_filehandle(self.infile)
        self.fh_out = codecs.open(self.outfile, 'w')
        self.documents = 0
        self.cs_documents = 0
        self.issue = None
        self.issn = None
        self.bibvol = None
        self.bibdate = None
        self.title = None
        self.subject = None
        self.abstract = ''
        self.in_abstract = False
        self.is_cs_document = False


    def read(self):
        c = 0
        for line in self.fh_in:
            c += 1
            #if c > 100000: break
            if c % 1000000 == 0: print c

            if line.startswith('<item_title'):
                self.documents += 1
                self.title = line
            elif line.startswith('<issue_title'):
                self.issue = line
            elif line.startswith('<bib_vol '):
                self.bibvol = line
            elif line.startswith('<bib_date '):
                self.bibdate = line
            elif line.startswith('<issn>'):
                self.issn = line
            elif line.startswith('<abstract avail="Y"'):
                self.in_abstract = True
            
            elif line.startswith('<subject '):
                if line.find('COMPUTER SCIENCE') > -1:
                    self.subject = line
                    self.cs_documents += 1
                    self.is_cs_document = True
            
            elif line.startswith('</abstract>'):
                if self.is_cs_document:
                    self.print_wos_item()
                self.reset()
                    
            elif self.in_abstract:
                self.abstract += line

        print "ALL DOCUMENTS: %5d" % self.documents
        print "CS DOCUMENTS:  %5d" % self.cs_documents


    def reset(self):
        self.issue = None
        self.issn = None
        self.bibvol = None
        self.bibdate = None
        self.subject = None
        self.title = None
        self.in_abstract = False
        self.is_cs_document = False
        self.abstract = ''
                

    def print_wos_item(self):
        if self.title and self.abstract:
            self.fh_out.write("<wos-item>\n")
            if self.issue is not None: self.fh_out.write(self.issue)
            if self.issn is not None: self.fh_out.write(self.issn)
            if self.bibvol is not None: self.fh_out.write(self.bibvol)
            if self.bibdate is not None: self.fh_out.write(self.bibdate)
            if self.subject is not None: self.fh_out.write(self.subject)
            self.fh_out.write(self.title)
            self.fh_out.write("<abstract>\n")
            self.fh_out.write(self.abstract)
            self.fh_out.write("</abstract>\n")
            self.fh_out.write("</wos-item>\n")
            self.fh_out.write("\n")


if __name__ == '__main__':
    
    #infile = sys.argv[1]
    #outfile = sys.argv[2]
    #WosReader(infile, outfile).read()
    #exit()
    
    for year in YEARS:
        files = glob.glob("%s/WoS.out.%d*" % (WOS_DIR, year))
        for infile in files:
            outfile = 'cs/' + os.path.basename(infile)[:-3]
            print infile, outfile
            WosReader(infile, outfile).read()
