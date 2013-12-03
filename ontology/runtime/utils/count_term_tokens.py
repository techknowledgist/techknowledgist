"""

Create two lists of all tokens in all terms, ordered alphabetically and ordered
on frequency.

$ python count_term_tokens ../workspace/terms/source/all_terms.txt


"""


import sys, codecs

fh_in = codecs.open(sys.argv[1], encoding='utf-8')
fh_out_alpha = codecs.open("all_terms.tokens.az.txt", 'w', encoding='utf-8')
fh_out_nr = codecs.open("all_terms.tokens.nr.txt", 'w', encoding='utf-8')

tokens = {}

print "\nReading terms...\n"

count = 0
for line in fh_in:
    count += 1
    if count % 100000 == 0: print count
    #if count > 1000000: break
    for token in line.split():
        tokens[token] = tokens.get(token, 0) + 1

print "\nNumber of unique tokens: %s\n" % len(tokens)

print "Sorting lists...\n"

pairs_az = tokens.items()
pairs_nr = [(c,t) for (t,c) in pairs_az]
pairs_az.sort()
pairs_nr.sort()
pairs_nr.reverse()

print "Writing lists...\n"

for t, c in pairs_az:
    fh_out_alpha.write("%s\t%s\n" % (t, c))
for c, t in pairs_nr:
    fh_out_nr.write("%s\t%s\n" % (c, t))

