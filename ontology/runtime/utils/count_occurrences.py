"""

Print the total number of tokens for terms that occur more than N times. The
exact numbers are given in the freqs list below. Prints the number of ocurrences
of terms with an equal or higher frequency than the number in the frequencies
list.

On the 31M terms we had for CS in November 2013, the result of this was:

   100000   31205208
    10000   82125961
     1000  116561637
      500  126139497
      100  147947484
       50  157252131
       25  166547985
       10  179978801
        5  191657037
        2  212126094
        1  232097845


"""

import codecs

total = 0
pp = False

freqs = (100000, 10000, 1000, 500, 100, 50, 25, 10, 5, 2)

freqs_pp = {}

for f in freqs:
    freqs_pp[f] = False
    
for line in codecs.open('all_terms.count.nr.txt'):
    fields = line.split()
    matches = int(fields[0])
    for f in freqs:
        if matches < f and not freqs_pp.get(f, False):
            print "%6d  %9d" % (f, total)
            freqs_pp[f] = True
    total += int(fields[0])

print "%6d  %9d" % (1, total)


