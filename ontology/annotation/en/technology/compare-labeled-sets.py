"""

Compare two sets with labeled data, print the phrases that receive different labels as well
as a count of the overlap.

"""

file1 = 'gold-training.txt'
file2 = 'gold-testing.txt'

stuff = {}


overlap = 0
different = []
file1_phrases = 0
file2_phrases = 0

for line in open(file1):
    file1_phrases += 1
    score_and_phrase = line.strip().split()
    score = score_and_phrase.pop(0)
    phrase = " ".join(score_and_phrase)
    stuff[phrase] = score

for line in open(file2):
    file2_phrases += 1
    score_and_phrase = line.strip().split()
    score = score_and_phrase.pop(0)
    phrase = " ".join(score_and_phrase)
    file1_score = stuff.get(phrase)
    if file1_score is not None:
        overlap += 1
        if file1_score != score:
            different.append((file1_score, score, phrase))


print
print "terms in %s: %d" % (file1, file1_phrases)
print "terms in %s: %d" % (file2, file2_phrases)
print "total overlapping terms:", overlap

print "\ndifferent terms:"
for (file1_score, score, phrase) in different:
    print ' ', file1_score, score, phrase
