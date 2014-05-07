import os, codecs


DIR = '.'

candidates_file = os.path.join(DIR, 'terms-candidates.txt')
annotation_results_file = os.path.join(DIR, 'annotate.maturity.en.labels.txt')
merged_file = os.path.join(DIR, 'terms-merged.txt')


terms = {}
fh = codecs.open(candidates_file, encoding='utf8')
for line in fh:
    if line.find("\t") > -1:
        term, maturity_score = line.strip().split("\t")
        terms[term] = maturity_score

annotations = {}
fh = codecs.open(annotation_results_file, encoding='utf8')
for line in fh:
    if line.find("\t") > -1:
        label, term = line.strip().split("\t")
        term, suffix = term.split(' - ')
        annotations.setdefault(term,[]).append(label)

for term, labels in annotations.items():
    count = len([l for l in labels if l == 'y'])
    total = len([l for l in labels if l in ('y', 'n')])
    annotations[term] = float(count) / total

out = codecs.open(merged_file, 'w', encoding='utf8')
print
for term, count in annotations.items():
    print "%s\t%.4f\t%s" % (term, count, terms[term])
    out.write("%s\t%.4f\t%s\n" % (term, count, terms[term]))

#exit()
keys = annotations.keys()
print
for t in keys:
    print "%.4f" % annotations[t]
print
for t in keys:
    print terms[t]
