"""

Takes the file list in files-1M.txt and creates separate ones for each year.

"""

FILELIST = 'files-1M.txt'

years = range(1994, 2011+1)

print years

fhs = {}
for year in years:
    fhs[str(year)] = open("%d.txt" % year, 'w')

for line in open(FILELIST):
    year = line.split("\t")[0]
    fhs[year].write(line)
