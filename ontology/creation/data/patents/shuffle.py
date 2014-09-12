"""

Take one of the FUSEData lists with Lexis-Nexis filenames and shuffle
it, making sure the file is a full path.

This can be used instead of the functionality in batch.py since it is
much faster.

Only works on fusenet.

Usage:

    % python shuffle LANGUAGE

    where LANGUAGE is one of ('CN', 'DE', 'US')

"""

import os, sys, random

language = sys.argv[1]

infile = "/FUSEData/Lexis-Nexis/information/file-names/LN-%s-filenames.txt" % language
outfile = os.path.basename(infile)

fnames = []
for fname in open(infile):
    fnames.append(fname.strip())

    random.shuffle(fnames)

    out = open(outfile, 'w')
    for fname in fnames:
        out.write("/FUSEData/Lexis-Nexis/%s\n" % fname)
                
                
