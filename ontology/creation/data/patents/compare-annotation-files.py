"""

Script to compare the terms in an old-style annotation file to a new style
annotation file. Creates:

    1- file with the old terms with a +/- prefix depending on whether the old
       term is amongst the new terms

    2- file with the new terms with a +/- prefix depending on whether the new
       term is amongst the old terms

"""

import codecs

old_file = '../../../annotation/en/technology/annot.ts10.nc.lo.pa.20130415.lab'
new_file = '201305-en/data/t0_annotate/technologies/test1/annotate.terms.counts.txt'

old_terms_idx = {}
old_terms = []
for line in codecs.open(old_file, encoding='utf-8'):
    (label, term) = line.strip().split("\t")
    old_terms_idx[term] = True
    old_terms.append([label, term])

new_terms_idx = {}
new_terms = []
for line in codecs.open(new_file, encoding='utf-8'):
    (rank, freq, cumulative, term) = line.strip().split("\t")
    new_terms_idx[term] = True
    new_terms.append([rank, freq, cumulative, term])

# print the new terms, adding a + in front if they occur in the old terms and a
# - if they do not occur in the old terms
fh1 = codecs.open("terms-new.txt", 'w', encoding='utf-8')
plus, minus = 0, 0
for (rank, freq, cumulative, term) in new_terms:
    marker = '+' if old_terms_idx.has_key(term) else '-'
    if marker == '+': plus += 1
    if marker == '-': minus += 1
    fh1.write("%s\t%s\t%s\t%s\t%s\n" %
              (marker, rank, freq, cumulative, term))
print 'New terms:', plus, 'out of', plus + minus, 'occur in old terms'

# print the old terms, adding a + in front if they occur in the new terms and a
# - if they do not occur in the new terms
fh1 = codecs.open("terms-old.txt", 'w', encoding='utf-8')
plus, minus = 0, 0
for (label, term) in old_terms:
    marker = '+' if new_terms_idx.has_key(term) else '-'
    if marker == '+': plus += 1
    if marker == '-': minus += 1
    fh1.write("%s\t%s\t%s\n" %
              (marker, label, term))
print 'Old terms:', plus, 'out of', plus + minus, 'occur in new terms'
