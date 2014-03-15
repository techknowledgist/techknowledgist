"""

Simple tool to take a file with terms and contexts, display the term in
context and sollicit whether the term is a technology. Usage:

% python term_annotator.py <SOURCE_FILE>

The SOURCE_FILE has to be named *.context.txt. The first time you open
SOURCE_FILE, a new file will be created with the name *.labels.txt. Initially
this labels file is empty except for a header copied from SOURCE_FILE. The label
file will be opened on subsequent visits to the file. SOURCE_FILE is only read
and never written to.

The annotator sees one term with its instances and then either hits 'y', 'n' or
'c', followed by a return, where 'y' indicates that the term is a technology,
'n' indicates that the term is not a technology and 'c' indicates that the term
is corrupted. The tool appends a line to the labels file with a label and the
term. The default is to use 'n' for the label so simply hitting the return will
add the 'n' label. Hitting 'q' followed by return terminates annotation and
closes the files. The tool remembers where it stopped last time and will not
simply start at the beginning when a file is reopened.

The SOURCE_FILE contains a list of terms where each term is printed as follows:

term
     year term_instance_id1 term_loc left_context term right_context
     year term_instance_id2 term_loc left_context term right_context
     ...

That is, the term on a line by itself, followed by one or more term instances
with their context. Each term instance line starts with a tab and all field are
tab-separated. See annotate.terms.context.txt for an example, this file was
created by the technology annotation code in step3_annotation.py.

This script was originally called technology_annotator_v2.py.

"""

import os, sys, codecs, textwrap

BOLD = '\033[1m'
GREEN = '\033[32m'
BLUE = '\033[34m'
INV = '\033[97;100m'
END = '\033[0m'


LEADING_TEXT = 'Technology?'

LABELS = [('y', 'yes'),
          ('n', 'no'),
          ('c', 'crap/corrupted'),
          ('q', 'quit')]

LABEL_IDX = dict.fromkeys([l1 for (l1,l2) in LABELS])


def read_annotated_terms(out_file):
    annotated_terms = {}
    if os.path.exists(out_file):
        fh = codecs.open(out_file, encoding='utf-8')
        for line in fh:
            if line.startswith('#'):
                continue
            (label, term) = line.rstrip("\n\r").split("\t")
            annotated_terms[term] = True
        fh.close()
    return annotated_terms

def read_terms_with_contexts(fh_contexts):
    terms = []
    info = ''
    for line in fh_contexts:
        if line.startswith('#'):
            info += line
        # context lines start with a tab
        elif line[0] == "\t":
            term.add_context(line)            
        # this is when we find a new term
        elif line.strip():
            term = Term(line)
            terms.append(term)
        else:
            print "WARNING:", line,
    return info, terms


class Term(object):

    def __init__(self, line):
        self.name = line.strip()
        self.contexts = []

    def __str__(self):
        return "<Term freq=%02d name='%s'>" % (len(self.contexts), self.name)

    def add_context(self, line):
        fields = line.strip().split("\t")
        self.contexts.append(fields)

    def write_stdout(self, contexts=5):
        print "\n%s%s%s\n" % (BOLD, self.name, END)
        for year, id, loc, left, t, right in self.contexts[:contexts]:
            print "   %s%s %s %s%s" % (GREEN, year, id, loc, END)
            lines = textwrap.wrap("%s %s%s%s %s\n" % (left, BLUE + BOLD, t, END, right), width=80)
            for l in lines: print '  ', l
            print


def make_query():
    return ">>> %s %s\n? " % (LEADING_TEXT,
                              ", ".join(["%s (%s)" % (l2, l1) for (l1, l2) in LABELS]))

def print_info(contexts_file, labels_file, terms, annotated_terms):
    print "\n### Contexts file  -  %s" % contexts_file
    print "### Labels file    -  %s" % labels_file
    print "###"
    print "### Terms in contexts file   -  %3d" % len(terms)
    print "### Terms already annotated  -  %3d\n" % len(annotated_terms)


def ask_for_label(term, fh_contexts, fh_labels):
    got_answer = False
    contexts = term.contexts
    term.write_stdout(contexts=5)
    while not got_answer:
        answer = raw_input(make_query())
        if answer in LABEL_IDX:
            got_answer = True
        else:
            print ">>> Not a valid answer, try again..."
            continue
        process_answer(term, answer, fh_contexts, fh_labels)

def process_answer(term, answer, fh_contexts, fh_labels):
    if answer == 'q':
        fh_contexts.close()
        fh_labels.close()
        exit("\n")
    else:
        fh_labels.write("%s\t%s\n" % (answer, term.name))
        fh_labels.flush()




if __name__ == '__main__':

    contexts_file = sys.argv[1]
    if not contexts_file.endswith('.context.txt'):
        exit('ERROR: annotation file needs to end in ".context.txt".')
    labels_file = contexts_file.replace('.context.txt', '.labels.txt')

    annotated_terms = read_annotated_terms(labels_file)
    fh_contexts = codecs.open(contexts_file, encoding='utf-8')
    info, terms = read_terms_with_contexts(fh_contexts)

    add_preface = False if os.path.exists(labels_file) else True
    fh_labels = codecs.open(labels_file, 'a', encoding='utf-8')
    if add_preface:
        fh_labels.write(info)
        fh_labels.flush()
        
    print_info(contexts_file, labels_file, terms, annotated_terms)

    for term in terms:
        if term.name in annotated_terms:
            continue
        ask_for_label(term, fh_contexts, fh_labels)
