"""merge-patent-indexes.py

Merge the two indexes in /home/j/corpuswork/fuse/FUSEData/lists and create an
index will all information.

The first index is ln_uspto.all.index.id2path.txt, which maps patent identifiers
to relative paths:

    BASE_DIR = /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto
    20010000001 2001/028/US20010000001A1.xml
    20010000002 2001/028/US20010000002A1.xml

The second index is ln_uspto.all.index.date2path.txt, which contains application
dates, publication dates and full paths:

    19830621 19860318 /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/1986/004/US4577022A.xml
    20090203 20110705 /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto/2011/067/US7973447B2.xml

Results are written to:

    tmp.merged.index.out.txt
    tmp.merged.index.warnings.txt

The format of the first file is:

    BASE_DIR = /home/j/corpuswork/fuse/FUSEData/2013-04/ln_uspto
    20010000001 20001129 20010315 2001/028/US20010000001A1.xml
    20010000002 20001201 20010315 2001/028/US20010000002A1.xml

The second file contains the merge failures. This should be all due to files
where we were not able to find an application date or publication date.

"""

ID_INDEX = '/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.id2path.txt'
DATE_INDEX = '/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.date2path.txt'

COMBINED_INDEX = 'tmp.merged.index.out.txt'
COMBINED_INDEX_WARNINGS = 'tmp.merged.index.warnings.txt'

ID2PATH = {}
PATH2DATE = {}
BASE_DIR = None

print "Reading", ID_INDEX
count = 0
for line in open(ID_INDEX):
    count += 1
    if count % 1000000 == 0: print '  ', count
    #if count > 1000: break
    if line.startswith('BASE_DIR'):
        BASE_DIR = line.split()[2]
    elif not line.strip():
        continue
    else:
        (id, relative_path) = line.split()
        ID2PATH[id] = relative_path

print "Reading", DATE_INDEX
count = 0
for line in open(DATE_INDEX):
    count += 1
    if count % 1000000 == 0: print '  ', count
    #if count > 100000: break
    (app_date, pub_date, full_path) = line.split()
    relative_path = full_path[len(BASE_DIR)+1:]
    #print (app_date, pub_date, relative_path)
    PATH2DATE[relative_path] = (app_date, pub_date)

out = open(COMBINED_INDEX, 'w')
out.write("BASE_DIR = %s\n" % BASE_DIR)
warnings = open(COMBINED_INDEX_WARNINGS, 'w')

print "Merging items"
count = 0
path_has_dates = 0
path_has_no_dates = 0
for id in sorted(ID2PATH.keys()):
    count += 1
    if count % 1000000 == 0: print '  ', count
    path = ID2PATH[id]
    if PATH2DATE.has_key(path):
        (app_date, pub_date) = PATH2DATE[path]
        out.write("%s\t%s\t%s\t%s\n" % (id, app_date, pub_date, path))
        path_has_dates += 1
    else:
        warnings.write("No dates for %s %s\n" % (id, path))
        path_has_no_dates += 1

print "Merged items   %7d" % path_has_dates
print "Merged failed  %7d" % path_has_no_dates
