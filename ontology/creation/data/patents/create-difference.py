"""

% python create-difference.py FILE1 FILE2

Prints all lines to stdout that occur in FILE1 but not in FILE2.

"""


import sys

file1 = open(sys.argv[1])
file2 = open(sys.argv[2])

subtract = {}
for line in file2:
    subtract[line] = True

for line in file1:
    if not subtract.has_key(line):
        print line,

