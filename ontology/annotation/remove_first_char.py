# remove the first char from every line
# used to remove labels from annotation files.

import sys

for line in sys.stdin:
    sys.stdout.write(line[1:])

