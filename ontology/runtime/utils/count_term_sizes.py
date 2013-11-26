import codecs

TOKENS = {}

c = 0
for line in codecs.open('all_terms.txt'):
    c += 1
    if c % 1000000 == 0: print c
    #if c > 1000000: break
    char_count = len(line)
    tok_count = len(line.split())
    TOKENS[tok_count] = TOKENS.get(tok_count, 0) + 1
    #if tok_count > 15:
    #    print "%3d %2d  %s" % (char_count, tok_count, line),

for key in sorted(TOKENS.keys()):
    print key, TOKENS[key]


"""

0 1
1 3620993
2 10855390
3 11221684
4 4156741
5 1164429
6 312982
7 82398
8 24333
9 7747
10 3063
11 1684
12 717
13 440
14 389
15 175
16 181
17 92
18 91
19 33
20 24
21 21
22 12
23 14
24 6
25 5
26 2
27 1
28 2
29 5
32 1
35 1


"""

