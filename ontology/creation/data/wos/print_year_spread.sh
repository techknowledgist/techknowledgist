
for year in 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007
do
    echo $year
    ls -1 cs-corpora/$year | cut -f3 -d'.' | cut -c1-4 | sort | uniq -c
done
