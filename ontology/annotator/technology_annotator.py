"""

Very simple tool to take a file with a vector, display the term in context and sollicit
whether the term is a technology. Usage:

% python technology_annotator.py <SOURCE_FILE> <ANNOTATION_FILE>

SOURCE_FILE is expected to have at least nine tab-separated columns and the ninth column
has the term in context. The annotator sees one sentence and then either hits 'y' or 'n'
followed by a return, where 'y' indicates that the term is a technology. The tool then
appends a line to ANNOTATION_FILE with a + or - prepended, depending on the answer. The
default is 'n' so simply hitting the return will count as no-technology. Hitting 'q'
followed by return closes the files and saves the work. The tool remembers where it
stopped last time and will not simply start at the beginning when a file is reopened.

"""

import os, sys

BOLD = '\033[1m'
BLUE = '\033[34m'
INV = '\033[97;100m'
END = '\033[0m'

in_file = sys.argv[1]
out_file = sys.argv[2]
fh_in = open(in_file)

new_file = True
done = 0
if os.path.exists(out_file):
    new_file = False
    fh_out = open(out_file)
    done = len(fh_out.readlines())
    fh_out.close()
fh_out = open(out_file, 'a')

if new_file:
    print "\n%sStarting annotation of file '%s'%s\n" % (BOLD, in_file, END)
else:
    print "\n%sContinuing annotation of file '%s', %d lines done%s\n" % (BOLD, in_file, done, END)

for i in range(done):
    fh_in.readline()

for line in fh_in:
    context = line.split("\t")[8]
    p1 = context.find('[')
    p2 = context.find(']')
    term = context[p1:p2+1]
    print "\n%s%s%s%s%s" % (context[:p1], BLUE, term, END, context[p2+1:])
    query = "%s Technology? (y) yes, (n) no, (q) quit %s " % (INV, END)
    answer = raw_input(query)

    if answer == 'q':
        print
        fh_in.close()
        fh_out.close()
        break
    elif answer == 'y':
        fh_out.write("+\t%s" % line)
    else:
        fh_out.write("-\t%s" % line)
