"""

Script to create and access a patent index. The index maps USPTO patent numbers
to file paths in a patent directory which is taken from an input file with
patents.

While you can run this on any file list, it makes most sense to run it on

   /home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.shuffled.txt

This script can be run from the command line to create the index:

    $ python patent_index.py --create-index PATENT_LIST TEXT_INDEX MAXCOUNT?

    OPTIONS:
        
        PATENT_LIST - the file above or some similar file
        TEXT_INDEX - an output file where the index is written to
        MAXCOUNT - optional argument that specifies how many lines to take, 
                   the default is to take all lines.

The following is a way to test whether the index can be loaded and will check
whether it can retrieve the path for some numbers:

    $ python patent_index.py --test-index TEXT_INDEX? MAXCOUNT?

    OPTIONS:
        
        TEXT_INDEX - location of the input text index
        MAXCOUNT - optional argument that specifies how many lines to take, 
                   the default is to take the first 100,000 lines.

    The test assumes that the file used was
    /home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.txt, which is the
    default.
   
This was only useful when developing the script, typically this script would be
loaded as a module by another script. Loading the index requires creating an
instance of PatentIndex.

The initialization method can be given the location of the filename, but it will
default to ln_uspto.all.index.txt.

    >>> from patent_index import PatentIndex
    >>> idx = PatentIndex()

You can now use get_path() to get the path for a patent:

   >>> idx.get_path('20010001003')
   /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/2001/028/US20010001003A1.xml

"""


import os, sys, re, time, shelve
from xml.dom.minidom import parse


re_PATENT_NUMBER = re.compile('^(B|D|H|HD|RE|PP|T)?(\d+)(.*)')


class DocumentId(object):

    def __init__(self, element):
        self.country = get_data(element.getElementsByTagName('country')[0])
        self.docnumber = get_data(element.getElementsByTagName('doc-number')[0])
        try:
            self.kind = get_data(element.getElementsByTagName('kind')[0])
        except IndexError:
            self.kind = None
        try:
            self.date = get_data(element.getElementsByTagName('date')[0])
        except IndexError:
            self.date = None

    def __str__(self):
        year = None if self.date is None else self.date[:4]
        return "<document-id country=%s doc-number=%s kind=%s year=%s>" % \
               (self.country, self.docnumber, self.kind, year)

        
def get_data(element):
    return element.firstChild.data


def test_numbers_and_codes(patent_list):
    """Test whether the number in the filename (after 'US' and before the kind
    code) is the same as the doc-number in the publication reference. Also
    collect a list of kind codes."""
    codes = {}
    for line in open(patent_list):
        fname = line.strip()
        year = os.path.basename(os.path.dirname(fname))
        dom = parse(fname)
        pub_ref = dom.getElementsByTagName('publication-reference')[0]
        pub_ref_docid = pub_ref.getElementsByTagName('document-id')[0]
        document_id = DocumentId(pub_ref_docid)
        did_year = None if document_id.date is None else document_id.date[:4]
        s1 = os.path.basename(fname)[2:-4]
        s2 = document_id.docnumber
        code = s1[len(s2):]
        codes[code] = codes.get(code, 0) + 1
        if not s1.startswith(s2):
            print "%s %s" % (s1, s2)
        #print "%s  %-25s  %s  %s" % \
        #     (year, os.path.basename(fname), did_year, document_id.docnumber)
    print codes

def test_patent_family(patent_list):
    """Test whether the document number in the publication reference is in the
    patent family. This was not the case for the 500 sample patents, so the
    patent family could be ignored for the index."""
    print_document_ids = False
    for line in open(patent_list):
        fname = line.strip()
        dom = parse(fname)
        pub_ref = dom.getElementsByTagName('publication-reference')
        main_family = dom.getElementsByTagName('main-family')
        pub_ref_docid = pub_ref[0].getElementsByTagName('document-id')
        mfamily_docid = main_family[0].getElementsByTagName('document-id')
        pubref_docid = DocumentId(pub_ref_docid[0])
        family_docids = [DocumentId(e) for e in mfamily_docid] 
        family_docids = [docid for docid in family_docids if docid.country == 'US']
        if not pubref_docid.docnumber in [did.docnumber for did in family_docids]:
            print fname, "number in publication ref is not in the patent family"
        if print_document_ids:
            print fname
            print "     pubref",  pubref_docid
            for family_docid in family_docids:
                print "     family", family_docid


def index_patents(patent_list, index_file, maxcount=100, fast=False):
    """Create a text index for all the patents in patent_list. Two formats are
    allowed: one with just the filepath and one where the first field is a
    shortname and the second the full path."""
    basepath = None
    index = []
    prefixes, kind_codes, classes = {}, {}, {}
    print "collecting mappings..."
    count = 0
    for line in open(patent_list):
        count += 1
        if count % 100000 == 0: print count
        if count > maxcount: break
        fname = line.strip().split()[-1]
        (base_dir, shortpath) = _get_paths(fname)
        if basepath is None:
            basepath = "BASE_DIR = %s" % base_dir
        (prefix, docnumber, kind_code) = _get_docnumber(fname, fast)
        _update_statistics(prefixes, kind_codes, classes, prefix, kind_code)
        index.append("%s\t%s" % (docnumber, shortpath))
    _print_statistics(prefixes, kind_codes, classes)
    print "sorting index..."
    index.sort()
    print "writing index..."
    fh = open(index_file, 'w')
    fh.write(basepath + "\n")
    for line in index:
        fh.write(line + "\n")
    
def _get_paths(fname):
    path_elements = os.path.dirname(fname).split(os.sep)
    if len(path_elements[-1]) == 4:
        year = os.path.basename(os.path.dirname(fname))
        base_dir = os.path.dirname(os.path.dirname(fname))
        shortpath = os.path.join(year, os.path.basename(fname))
    elif len(path_elements[-2]) == 4:
        base_dir = os.sep.join(path_elements[:-2])
        shortpath = os.path.join(os.sep.join(path_elements[-2:]),
                                 os.path.basename(fname))
    return (base_dir, shortpath)

def _get_docnumber(fname, fast):
    if fast:
        basename = os.path.basename(fname)[2:-4]
        result = re_PATENT_NUMBER.match(basename)
        if result is None:
            print "WARNING: no match on", fname
            return None
        prefix = result.groups()[0]
        kind_code = result.groups()[-1]
        number = ''.join([g for g in result.groups()[:-1] if g is not None])
        return (prefix, number, kind_code)
    else:
        dom = parse(fname)
        pub_ref = dom.getElementsByTagName('publication-reference')[0]
        pub_ref_docid = pub_ref.getElementsByTagName('document-id')[0]
        document_id = DocumentId(pub_ref_docid)
        # don't bother getting the prefix and kind code for the slow version
        return (None, document_id.docnumber, None)

def _update_statistics(prefixes, kind_codes, classes, prefix, kind_code):
    prefixes[prefix] = prefixes.get(prefix, 0) + 1
    kind_codes[kind_code] = kind_codes.get(kind_code, 0) + 1
    pclass = "%s-%s" % (prefix, kind_code)
    classes[pclass] = classes.get(pclass, 0) + 1

def _print_statistics(prefixes, kind_codes, classes):
    print "prefixes:", prefixes
    print "kind_codes:", kind_codes
    print "classes:", classes


def test_index(index_file, maxcount):
    """Load a number of lines from the index test retrieval."""
    idx = PatentIndex(index_file, maxcount)
    print
    print idx
    print "\nTesting existing patent numbers (on sample 500)"
    for n in ['4322557', '4353538']:
        print '  ', [n, idx.get_path(n)]
    print "Testing existing patent numbers (on first 100K of full index)"
    for n in ['20010000983', '20010001003']:
        print '  ', [n, idx.get_path(n)]
    print "Testing non-existing patent numbers"
    for n in ['20010000XXX', '2001000XXXX']:
        print '  ', [n, idx.get_path(n)]
    print




class PatentIndex(object):

    """Initialization loads the index from the index file into memory. The
    instance can then be queried with patent numbers and it will return the
    associated file path or None."""

    def __init__(self, text_index=None, maxcount=999999999):
        """Uses the first line of the text_index to determine the base directory
        and then read the rest."""
        self.index = '/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.txt'
        self.basedir = None
        if text_index is not None:
            self.index = text_index
        self.data = {}
        with open(self.index) as fh:
            self.basedir = fh.readline().strip().split(' = ')[1]
            count = 0
            for line in fh:
                count += 1
                if count > maxcount: break
                if count % 100000 == 0: print count
                (number, path) = line.split()
                self.data[number] = path

    def __str__(self):
        return "<PatentIndex using %s>" % self.index
    
    def get_path(self, patent_number):
        """Return the full path for the patent number or None if the number was
        not in the index."""
        result = self.data.get(patent_number)
        return None if result is None else os.path.join(self.basedir, result)


def example():
    """This takes the list with promince scores from Patrick and writes it to a
    file. It strips leading zeros from the patent number."""
    idx = PatentIndex()
    dirname = "/home/j/marc/Dropbox/fuse/data/patents/"
    fh_in = open(dirname +"0_2003_us_pats_w_mitre_gtf.txt")
    fh_out = open('out.txt', 'w')
    fh_in.readline()
    for line in fh_in:
        fields = line.strip().split(',')
        patent_number = fields[0][1:-1]
        fh_out.write("%s\t%s\n" % (patent_number,
                                   idx.get_path(patent_number.lstrip('0'))))


if __name__ == '__main__':

    # default values for arguments
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)
    dir = os.path.join(script_dir, '../ontology/creation/data/patents')
    fname = 'sample-500-en-basic-scrambled.txt'
    patent_list = os.path.abspath(os.path.join(dir, fname))
    index = "out.txt"
    maxcount = 99999999999

    mode = sys.argv[1]

    if mode == '--create-index':
        if len(sys.argv) > 3:
            patent_list = sys.argv[2]
            index = sys.argv[3]
        if len(sys.argv) > 4:
            maxcount = int(sys.argv[4])
        t1 = time.time()
        for i in range(1):
            index_patents(patent_list, index, maxcount=maxcount, fast=True)
            # index_patents(patent_list, index, maxcount=maxcount, fast=False)
        print "done, elapsed time is %.2f seconds" % (time.time() - t1)

    elif mode == '--test-index':
        maxcount = 100000
        text_index = '/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.txt'
        if len(sys.argv) > 2:
            text_index = sys.argv[2]
        if len(sys.argv) > 3:
            maxcount = int(sys.argv[3])
        t1 = time.time()
        test_index(text_index, maxcount)
        print "done, elapsed time is %.2f seconds" % (time.time() - t1)
        
    else:
        print "WARNING: invalid mode, use --create-index or --test-index"
