
"""

Given a list of filenames, get the full path in the ln_uspto directory.

Prints results to tmp_patents_found.txt.


"""

import os, codecs


PATENT_LIST = "/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.txt"


NEEDLES = [ 'US20020096692A1.xml', 'US20030225868A1.xml', 'US20040010413A1.xml', 'US20040042441A1.xml', 
            'US20040154801A1.xml', 'US20040185882A1.xml', 'US20050088723A1.xml', 'US20060007055A1.xml', 
            'US20060177426A1.xml', 'US20070048089A1.xml', 'US20070248714A1.xml', 'US20080119708A1.xml', 
            'US20080189504A1.xml', 'US20100066459A1.xml', 'US20100192390A1.xml', 'US20100271134A1.xml', 
            'US20110115522A1.xml', 'US4422268A.xml', 'US4576211A.xml', 'US4871462A.xml', 
            'US4978116A.xml', 'US5090643A.xml', 'US5114267A.xml', 'US5196711A.xml', 
            'US5441151A.xml', 'US5457345A.xml', 'US5622133A.xml', 'US5790620A.xml', 
            'US5862877A.xml', 'US5876796A.xml', 'US5888642A.xml', 'US5919978A.xml', 
            'US6150894A.xml', 'US6192144B1.xml', 'US6234677B1.xml', 'US6619753B2.xml', 
            'US6675055B1.xml', 'US6753722B1.xml', 'US6910154B1.xml', 'US6953880B2.xml', 
            'US6977247B2.xml', 'US7033893B1.xml', 'US7149010B2.xml', 'US7261898B2.xml', 
            'US7523973B2.xml', 'US7568399B2.xml', 'US7597286B2.xml', 'US7843540B2.xml', 
            'USPP011981P2.xml', 'USPP021257P2.xml', ]


def read_patent_list():

    fh = codecs.open(PATENT_LIST, encoding='utf-8')
    basedir_line = fh.readline()
    basedir = basedir_line.split()[2]
    patent_idx = {}

    count = 0
    for line in fh:
        count += 1
        #if count > 1000000: break
        if count % 100000 == 0: print count
        path = line.rstrip("\n\r").split()[1]
        fname = os.path.basename(path)
        patent_idx[fname] = path
    return basedir, patent_idx



if __name__ == '__main__':

    basedir, patent_idx = read_patent_list()

    out = open('tmp_patents_found.txt', 'w')
    for needle in NEEDLES:
        path = patent_idx.get(needle)
        if path is not None:
            path = os.path.join(basedir, path)
        print path
        out.write(path + "\n")
