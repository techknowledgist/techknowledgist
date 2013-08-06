file1='en/technology/annot.ts10.nc.lo.er.20130611.lab'
file2='en/technology/annot.ts10.nc.lo.mv.20130424.lab'
file3='en/technology/annot.ts10.nc.lo.pa.20130415.lab'

python iaa.py $file1 $file2 iaa-er-mv-ALL.txt
python iaa.py $file1 $file2 1 100 iaa-er-mv-0001-0100.txt
python iaa.py $file1 $file2 101 200 iaa-er-mv-0101-0200.txt
python iaa.py $file1 $file2 201 300 iaa-er-mv-0201-0300.txt
python iaa.py $file1 $file2 301 400 iaa-er-mv-0301-0400.txt
python iaa.py $file1 $file2 801 900 iaa-er-mv-0801-0900.txt
python iaa.py $file1 $file2 1301 1400 iaa-er-mv-1301-1400.txt

python iaa.py $file2 $file3 iaa-mv-pa-ALL.txt
python iaa.py $file2 $file3 1 100 iaa-mv-pa-0001-0100.txt
python iaa.py $file2 $file3 101 200 iaa-mv-pa-0101-0200.txt
python iaa.py $file2 $file3 201 300 iaa-mv-pa-0201-0300.txt
python iaa.py $file2 $file3 301 400 iaa-mv-pa-0301-0400.txt
python iaa.py $file2 $file3 801 900 iaa-mv-pa-0801-0900.txt
python iaa.py $file2 $file3 1301 1400 iaa-mv-pa-1301-1400.txt

python iaa.py $file3 $file1 iaa-pa-er-ALL.txt
python iaa.py $file3 $file1 1 100 iaa-pa-er-0001-0100.txt
python iaa.py $file3 $file1 101 200 iaa-pa-er-0101-0200.txt
python iaa.py $file3 $file1 201 300 iaa-pa-er-0201-0300.txt
python iaa.py $file3 $file1 301 400 iaa-pa-er-0301-0400.txt
python iaa.py $file3 $file1 801 900 iaa-pa-er-0801-0900.txt
python iaa.py $file3 $file1 1301 1400 iaa-pa-er-1301-1400.txt


