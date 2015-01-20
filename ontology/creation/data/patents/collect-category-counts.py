"""

Collect counts per year and category. Uses category files with BAE-provided
MITRE categories and an sqlite database with application and publication dates,
indexed on patent identifiers.

Usage:

    $ python collect-category-counts.py

All file locations are hard-wired in the global variables below. Using a local
sqlite index speeds up the process by what might be a factor 100. It takes a
couple of minutes to run.

See the end of the file for the results of a run at 1/20/2015.

"""


import os, sys, glob, sqlite3

IDX = "/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.sqlite"
IDX = "/local/chalciope/marc/fuse/data/ln_uspto.all.index.sqlite"
CATEGORY_DIR = "/home/j/corpuswork/fuse/FUSEData/lists/patentsByGtf"
CATEGORIES = ('A21', 'A22', 'A23', 'A24', 'A25', 'A26', 'A27', 'A28', 'A29', 'A30') 
CONNECTION = sqlite3.connect(IDX) 
CURSOR = CONNECTION.cursor()

fh_warnings = open("warnings-categories.txt", 'w')


STATS = {}


def get_patent_data(c, id):
    c.execute('SELECT * FROM data WHERE patent_id=?', (id,))
    return c.fetchone()

def process(cat_file):
    print cat_file
    c, uspto, found, notfound, null = 0, 0, 0, 0, 0
    for line in open(cat_file):
        c += 1
        if c % 100000 == 0: print '  ', c
        #if c > 100000: break
        fields = line.strip().split(',')
        id = fields[0]
        cat = fields[2]
        if cat.startswith('LNCN'): continue
        uspto += 1
        if cat == 'null':
            null += 1
            continue
        try:
            (appdate, pubdate, path) = get_patent_data(CURSOR, id)[1:4]
            found += 1
            appdate = appdate[:4]
        except TypeError:
            notfound += 1
            fh_warnings.write("no index data for %s\n" % id)
            continue
        if int(appdate) < 1990:
            continue
        try:
            cat = cat.split('-')[3]
            if not cat.startswith('A'):
                print "Funny category:", line,
            if not STATS.has_key(appdate):
                STATS[appdate] = {}
            STATS[appdate][cat] = STATS[appdate].get(cat,0) + 1
        except:
            print 'ERROR', c, line,
    #print "\nuspto=%d\nnull=%d\nfound=%dnotfound=%d\n" % (uspto, null, found, notfound)

def print_stats():
    print '      ',
    for c in CATEGORIES:
        print "%7s" % c,
    print "    ALL"
    for year in sorted(STATS.keys()):
        print year, ' ',
        for c in CATEGORIES:
            print "%7d" % STATS[year].get(c,0),
        print "%7d" % sum(STATS[year].values())


if __name__ == '__main__':

    for cat_file in sorted(glob.glob("%s/lnusp-*.csv" % CATEGORY_DIR)):
        process(cat_file)
    print_stats()


"""

Results from 1/20/2015 with

   IDX = '/local/chalciope/marc/fuse/data/ln_uspto.all.index.sqlite'
   CATEGORY_DIR = '/home/j/corpuswork/fuse/FUSEData/lists/patentsByGtf'
   
        A21    A22    A23    A24    A25    A26    A27    A28    A29    A30     ALL
1990    190     43     35     50     91    137    268     15      3     36     868
1991    607    223    156    126    226    329    643     43     14    168    2535
1992   2127    945    604    660    747    962   1783    203     47    970    9048
1993   4268   2946   2181   3134   3339   3751   5485   1537    560   4637   31838
1994   6913   4933   4836   5626   5907   6813   9776   3238   1313   8003   57358
1995   9806   6325   6224   6212   6787   9132  15087   3170   1494   8662   72899
1996  11680   7649   7061   6782   6220   6696   9427   3485   1641   9689   70330
1997  14303   9557   9131   7849   7015   7878  11958   3936   1841  10921   84389
1998  14499  10153   9458   7960   6297   6937  11745   3654   1781  10994   83478
1999  17398  11891  10245   8493   6551   7489  13611   3782   1690  11634   92784
2000  24404  13674  12711  10912   7755   8494  15293   4547   2431  14883  115104
2001  51697  26205  25396  23027  13888  15281  32895   8232   4202  26989  227812
2002  50474  27375  28610  23978  15457  16497  38562   8380   4454  28788  242575
2003  55073  29064  30325  26296  16360  17568  42416   9098   4590  30474  261264
2004  57503  33685  33091  28052  15470  15747  40897   8855   4580  32391  270271
2005  59625  38363  35333  29632  15194  14217  38018   8314   4831  33039  276566
2006  60212  35908  34926  29295  14018  13148  37240   8102   4440  34656  271945
2007  60552  33705  32347  27400  13499  11446  34381   7963   4115  34263  259671
2008  56119  27840  27706  24553  11580   9201  29967   6756   3233  31431  228386
2009  43343  23162  20124  16950   9352   7391  24175   5068   2215  23848  175628
2010  27132  13176  13438  10192   5583   3823  15449   3395   1211  13781  107180
2011   5380   2593   2992   1852   1170    819   2942    626    201   2144   20719

It is peculiar that even with files up to lnusp-patent-documents-2013.csv, there
are no files with publication dates after 2011. The very likely reason for this
is that the index probably does not go to a recent enough date.

"""
