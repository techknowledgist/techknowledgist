
import sys, codecs, textwrap

BOLD = '\033[1m'
RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
INV = '\033[97;100m'
END = '\033[0m'



class TermContexts(object):
    """Stores the contents of a context file, optionally filter to only contain the
    terms in a specific list."""

    def __init__(self, contexts_file, allowed_terms_file=None):
        self.info = ''    # the preface at the beginning of the file
        self.terms = []   # a list of Term instances
        self.allowed_terms = {}
        self.filter_terms = False
        self.contexts_file = contexts_file
        self.allowed_terms_file = allowed_terms_file
        self.read_allowed_terms()
        self.read_contexts()
        self.filter()

    def read_allowed_terms(self):
        if self.allowed_terms_file is not None:
            self.filter_terms = True
            fh = codecs.open(self.allowed_terms_file, encoding='utf-8')
            for line in fh:
                self.allowed_terms[line.strip().split("\t")[0]] = True

    def read_contexts(self):
        self.fh_contexts = codecs.open(self.contexts_file, encoding='utf-8')
        for line in self.fh_contexts:
            if line.startswith('#'):
                self.info += line
            elif line[0] == "\t":
                # context lines start with a tab
                term.add_context(line)
            elif line.strip():
                # this is when we find a new term
                term = Term(line)
                self.terms.append(term)
            else:
                print "WARNING:", line,

    def filter(self):
        if self.filter_terms:
            self.terms = [t for t in self.terms if self.allowed_terms.has_key(t.name)]

    def pp(self):
        for t in self.terms: print t


class Term(object):

    def __init__(self, line):
        self.name = line.strip()
        self.contexts = []

    def __str__(self):
        return "<Term freq=%02d name='%s'>" % (len(self.contexts), self.name)

    def add_context(self, line):
        fields = line.lstrip("\t").rstrip("\n\r").split("\t")
        self.contexts.append(fields)

    def write_as_raw_data(self, fh=sys.stdout):
        fh.write("%s\n" % self.name)
        for c in self.contexts:
            try:
                year, id, loc, left, t, right = c
                fh.write("\t%s\t%s\t%s\t%s\t%s\t%s\n" % (year, id, loc, left, t, right))
            except ValueError:
                print "CONTEXT WARNING:", self.name, c

    def write_as_annotation_context(self, contexts=5):
        print "\n%sTERM: %s%s (%d contexts)\n" % (BOLD, self.name, END, len(self.contexts))
        for year, id, loc, left, t, right in self.contexts[:contexts]:
            print "   %s%s %s %s%s" % (GREEN, year, id, loc, END)
            highlighted_term = "%s%s%s" % (BLUE + BOLD, t, END)
            context = "%s %s %s" % (left[-200:], highlighted_term, right[:200])
            lines = textwrap.wrap("%s\n" % context, width=80)
            for l in lines:
                try:
                    print '  ', l
                except UnicodeEncodeError:
                    # TODO: this is a rather blunt way of dealing with this
                    pass
            print
