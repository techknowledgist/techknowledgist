file1='en/technology/annot.20130212.ts10.nc.lo.lab'
file2='en/technology/annot.20130212.ts10.nc.lo.mv.lab'

python iaa.py $file1 $file2 > iaa-ALL.txt
python iaa.py $file1 $file2 1 100 > iaa-0001-0100.txt
python iaa.py $file1 $file2 101 200 > iaa-0101-0200.txt
python iaa.py $file1 $file2 201 300 > iaa-0201-0300.txt
python iaa.py $file1 $file2 301 400 > iaa-0301-0400.txt
python iaa.py $file1 $file2 801 900 > iaa-0801-0900.txt
python iaa.py $file1 $file2 1301 1400 > iaa-1301-1400.txt

