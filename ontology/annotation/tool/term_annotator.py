"""

Simple tool to take a file with terms and contexts, display the term in
context and sollicit a label for the term.

Usage:

    $ python term_annotator.py --technology <SOURCE_FILE>
    $ python term_annotator.py --category <SOURCE_FILE>
    $ python term_annotator.py --polarity <SOURCE_FILE>

The tool has three modes: technology annotation (labels: yes, no, not-a-term),
category annotation (labels: attribute, task, component, other, not-a-term) and
polarity annotation (labels: yes, no, unknown, not-an-attribute).

The SOURCE_FILE has to be named *.context.txt. The first time you open
SOURCE_FILE, a new file will be created with the name *.labels.txt. This file
contains the labels for the terms that were annotated. Initially this labels
file is empty except for a header copied from SOURCE_FILE. The label file will
be opened on subsequent visits to the file. SOURCE_FILE is only read and never
written to.

When the tool is started, the annotator sees one term in context with its
instances and a line with a query and then some options. In technology mode,
these options are 'y','n' and 'c', where 'y' indicates that the term is a
technology, 'n' indicates that the term is not a technology and 'c' indicates
that the term is corrupted. Type one of these, followed by a return, to save the
label. The tool appends a line to the labels file with a label and the term. The
labels are different for the other modes.

For all modes, hitting 'm' followed by a return directs the tool to show all
available contexts. Hitting 'q' followed by return terminates annotation and
closes the files. The tool remembers where it stopped last time and will not
simply start at the beginning when a file is reopened.

This tool only allows you to add labels to terms that were not annotated before,
it does not allow the user to revisit annotations (this would have to be done
maually by opening the labels file, or better, to avoid potential trouble, by
making a note in a separate file).

The SOURCE_FILE contains a list of terms where each term is printed as follows:

    term
       year term_instance_id1 term_loc left_context term right_context
       year term_instance_id2 term_loc left_context term right_context
       ...

That is, the term on a line by itself, followed by one or more term instances
with their context. Each term instance line starts with a tab and all field are
tab-separated. See annotate.terms.context.txt for an example, this file was
created by the technology annotation code in step3_annotation.py.

This script was originally a copy of technology_annotator_v2.py.

"""

import os, sys, codecs
from utils import TermContexts, INV, RED, END


class AnnotationTask(object):

    def __init__(self):
        self.leading_text = None
        self.labels = None
        self.label_idx = None
        self.quit = ('q', 'quit')
        self.more = ('m', 'more-contexts')

    def technology_mode(self):
        self.leading_text = 'Is this term a technology?'
        self.labels = [('y', 'yes'), ('n', 'no'), ('c', 'crap/corrupted')]
        self.index_labels()

    def category_mode(self):
        self.leading_text = 'What is the term\'s category?'
        self.labels = [('c', 'component'), ('a', 'attribute'), ('t', 'task'),
                       ('u', 'unknown'), ('x', 'not-a-term')]
        self.index_labels()

    def polarity_mode(self):
        self.leading_text = 'What is the term\'s polarity?'
        self.labels = [('p', 'positive'), ('n', 'negative'), ('u', 'unknown'),
                       ('x', 'not-an-attribute')]
        self.index_labels()

    def index_labels(self):
        self.label_idx = dict.fromkeys([l1 for (l1,l2) in self.labels])

    def make_query(self):
        labels = ", ".join(["%s (%s)" % (l2, l1) for (l1, l2) in self.labels])
        more_and_quit = "%s (%s), %s (%s)" % (self.more[1], self.more[0],
                                              self.quit[1], self.quit[0])
        return "%s\n\n" % self.leading_text \
               + "%s%s, %s%s\n\n" % (INV, labels, more_and_quit, END) \
               + ">>> "


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

def print_info(contexts_file, labels_file, terms, annotated_terms):
    print "\n### Contexts file  -  %s" % contexts_file
    print "### Labels file    -  %s" % labels_file
    print "###"
    print "### Terms in contexts file   -  %3d" % len(terms)
    print "### Terms already annotated  -  %3d\n" % len(annotated_terms)

def ask_for_label(task, term, fh_contexts, fh_labels):
    got_answer = False
    contexts = term.contexts
    term.write_as_annotation_context(contexts=5)
    while not got_answer:
        answer = raw_input(task.make_query())
        if answer == 'q':
            msg = "\nDone, saved labels in %s\n" % fh_labels.name
            fh_contexts.close()
            fh_labels.close()
            exit(msg)
        if answer == 'm':
            term.write_as_annotation_context(contexts=sys.maxint)
            continue
        if answer in task.label_idx:
            got_answer = True
        else:
            print "\n%sWARNING: not a valid answer, try again...%s\n" % (RED, END)
            continue
        process_answer(term, answer, fh_contexts, fh_labels)

def process_answer(term, answer, fh_contexts, fh_labels):
    fh_labels.write("%s\t%s\n" % (answer, term.name))
    fh_labels.flush()



if __name__ == '__main__':

    #import platform
    #print platform.system()
    #exit()
    task = AnnotationTask()
    if sys.argv[1] == '--technology':
        task.technology_mode()
    elif sys.argv[1] == '--category':
        task.category_mode()
    elif sys.argv[1] == '--polarity':
        task.polarity_mode()
    else:
        exit("No valid annotation mode specified")
    contexts_file = sys.argv[2]

    if not contexts_file.endswith('.context.txt'):
        exit('ERROR: annotation file needs to end in ".context.txt".')
    labels_file = contexts_file.replace('.context.txt', '.labels.txt')
    allowed_terms_file = sys.argv[2] if len(sys.argv) > 2 else None

    annotated_terms = read_annotated_terms(labels_file)
    contexts = TermContexts(contexts_file, allowed_terms_file)

    add_preface = False if os.path.exists(labels_file) else True
    fh_labels = codecs.open(labels_file, 'a', encoding='utf-8')
    if add_preface:
        fh_labels.write(contexts.info)
        fh_labels.flush()
        
    print_info(contexts_file, labels_file, contexts.terms, annotated_terms)

    for term in contexts.terms:
        if term.name in annotated_terms:
            continue
        ask_for_label(task, term, contexts.fh_contexts, fh_labels)
