"""view-patent-dates.py

Write a table of application dates and publication dates to the standard output,
using the date index ln_uspto.all.index.date2path.txt.

"""

DATE_INDEX_FILE = '/home/j/corpuswork/fuse/FUSEData/lists/ln_uspto.all.index.date2path.txt'

DATES = {}

for i in range(1980, 2012):
    DATES[i] = { 0:0 }
    for j in range(1980, 2012):
        DATES[i][j] = 0

def print_dates():
    print '    ',
    for j in sorted(DATES[1980].keys()):
        if j == 0: continue
        print j,
    print
    for i in sorted(DATES.keys()):
        print i,
        for j in sorted(DATES[i].keys()):
            if j == 0: continue
            if not DATES[i][j]:
                print '    ',
            else:
                print "%4d" % (DATES[i][j] * 100 / DATES[i][0]),
        print
        
count = 0
skipped_patents = 0
for line in open(DATE_INDEX_FILE):
    count += 1
    if count > 100000:
        break
    (app_date, pub_date, path) = line.strip().split()
    app_date = int(app_date[:4])
    pub_date = int(pub_date[:4])
    if pub_date < app_date:
        print "WEIRD DATES:", app_date, pub_date, path
    if pub_date < 1980 or app_date < 1980:
        skipped_patents += 1
        #print app_date, pub_date
    else:
        DATES[app_date][pub_date] += 1
        DATES[app_date][0] += 1

print
print "Patents plotted  %6d" % (count-1)
print "Patents skipped  %6d\n" % (skipped_patents)
print "Application dates are on the y-axis, publication dates are on the x-axis."
print "The numbers in the cells are percentages over the total number applied for in a year."
print "No number means there were no patents, 0 means there were some but less than 1 percent."
print "Patents were skipped if application date or publication date was before 1980."
print
print_dates()
