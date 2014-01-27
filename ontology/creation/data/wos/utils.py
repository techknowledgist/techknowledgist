"""

Utilities for processing WOS documents.

"""


import gzip, codecs


def get_filehandle(filename):
    gzipfile = gzip.open(filename, 'rb')
    reader = codecs.getreader('utf-8')
    fh = reader(gzipfile) 
    return fh


class WosDoc(object):

    def __init__(self):
        self.issue = None
        self.issn = None
        self.bibvol = None
        self.bibdate = None
        self.title = None
        self.subject = None
        self.subjects = []
        self.abstract = ''

    def is_okay(self):
        """Only documents with a title and abstract are okay."""
        return self.title and self.abstract
    
    def is_cs_document(self):
        """Return True if one of the subject lines has the string 
        'COMPUTER SCIENCE' in it."""
        search_str = 'COMPUTER SCIENCE'
        return any([l for l in self.subjects if l.find(search_str) > -1])

    def write_to_file(self, fh, id=None):
        id_str = '' if id is None else " id=%s" % id
        fh.write("<wos-item%s>\n" % id_str)
        if self.issue is not None: fh.write(self.issue)
        if self.issn is not None: fh.write(self.issn)
        if self.bibvol is not None: fh.write(self.bibvol)
        if self.bibdate is not None: fh.write(self.bibdate)
        for line in sorted(list(set(self.subjects))): fh.write(line)
        fh.write(self.title)
        fh.write("<abstract>\n")
        fh.write(self.abstract)
        fh.write("</abstract>\n")
        fh.write("</wos-item>\n\n")


class WosReader(object):

    def __init__(self, infile):
        self.infile = infile
        self.fh_in = get_filehandle(self.infile)
        self.documents = 0
        self.cs_documents = 0
        self.wosdoc = WosDoc()
        self.in_abstract = False


    def read(self):

        for line in self.fh_in:

            if line.startswith('<REC>'):
                self.documents += 1
                self.wosdoc = WosDoc()
                self.in_abstract = False
            elif line.startswith('<item_title'):
                self.wosdoc.title = line
            elif line.startswith('<issue_title'):
                self.wosdoc.issue = line
            elif line.startswith('<bib_vol '):
                self.wosdoc.bibvol = line
            elif line.startswith('<bib_date '):
                self.wosdoc.bibdate = line
            elif line.startswith('<issn>'):
                self.wosdoc.issn = line
            elif line.startswith('<abstract avail="Y"'):
                self.in_abstract = True
            elif line.startswith('<subject '):
                self.wosdoc.subjects.append(line)
            elif line.startswith('</abstract>'):
                self.in_abstract = False
            elif line.startswith('</REC>'):
                return self.wosdoc
            elif self.in_abstract:
                self.wosdoc.abstract += line

        return None
