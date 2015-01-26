
CNKI_DIR = '/home/j/corpuswork/fuse/FUSEData/cnki'
LISTS_DIR = CNKI_DIR + '/information/tar-lists/targz-fuse-xml-all/vlist-grep'



def split_hy2():
    VLIST_FILE = LISTS_DIR + '/CNKI-HY2-fuse-xml-all-targz-vlist-grep.txt'
    out1 = open("CNKI-HY2-a-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out2 = open("CNKI-HY2-b-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out3 = open("CNKI-HY2-c-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out4 = open("CNKI-HY2-d-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out5 = open("CNKI-HY2-e-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out6 = open("CNKI-HY2-f-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out7 = open("CNKI-HY2-g-fuse-xml-all-targz-vlist-grep.txt", 'w')
    fh = out1
    c = 0
    for line in open(VLIST_FILE):
        c += 1
        fh.write(line)
        if c == 1100000: fh = out2
        if c == 2200000: fh = out3
        if c == 3300000: fh = out4
        if c == 4400000: fh = out5
        if c == 5500000: fh = out6
        if c == 6600000: fh = out7
        if c % 100000 == 0: print c
        # if c > 77: break
        
def split_hy3():
    VLIST_FILE = LISTS_DIR + '/CNKI-HY3-fuse-xml-all-targz-vlist-grep.txt'
    out1 = open("CNKI-HY3-a-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out2 = open("CNKI-HY3-b-fuse-xml-all-targz-vlist-grep.txt", 'w')
    out3 = open("CNKI-HY3-c-fuse-xml-all-targz-vlist-grep.txt", 'w')
    fh = out1
    c = 0
    for line in open(VLIST_FILE):
        c += 1
        fh.write(line)
        if c == 1100000: fh = out2
        if c == 2200000: fh = out3
        if c % 100000 == 0: print c
        # if c > 30: break


if __name__ == '__main__':

    pass
    #split_hy2()
    #split_hy3()
