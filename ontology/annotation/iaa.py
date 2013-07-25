"""

Creates a confusion matrix and generates an overall agreement score given two labeled
files where each line is of the following format:

   y|n|? TAB term
   
Terms for which there is only one judgement are ignored.

See iaa.sh on how to call this script.

"""

import sys, codecs


TERMS = {}

JUDGEMENTS = { 'y': { 'y': 0, 'n': 0, '?': 0 },
               'n': { 'y': 0, 'n': 0, '?': 0 },
               '?': { 'y': 0, 'n': 0, '?': 0 } }

P_E = { }


def add_line(line):
    fields = line.strip().split("\t")
    if len(fields) == 2:
        (judgement, term) = fields
        TERMS.setdefault(term, []).append(judgement)

def collect_judgements(file1, file2, start, end):
    count = 0
    for line in codecs.open(file1, encoding='utf-8'):
        count += 1
        if count >= start and count <= end:
            add_line(line)
    count = 0
    for line in codecs.open(file2, encoding='utf-8'):
        count += 1
        if count >= start and count <= end:
            add_line(line)
    for term, labels in TERMS.items():
        if len(labels) == 2:
            (l1, l2) = labels
            JUDGEMENTS[l1][l2] += 1
    calculate_pe()

def calculate_pe():
    y1 = sum(JUDGEMENTS['y'].values())
    n1 = sum(JUDGEMENTS['n'].values())
    q1 = sum(JUDGEMENTS['?'].values())
    y2 = sum([JUDGEMENTS[x]['y'] for x in ('y', 'n', '?')])
    n2 = sum([JUDGEMENTS[x]['n'] for x in ('y', 'n', '?')])
    q2 = sum([JUDGEMENTS[x]['?'] for x in ('y', 'n', '?')])
    n = sum([y1, n1, q1])
    p_y1 = y1 / float(n)
    p_n1 = n1 / float(n)
    p_q1 = q1 / float(n)
    p_y2 = y2 / float(n)
    p_n2 = n2 / float(n)
    p_q2 = q2 / float(n)
    #print "%d %d %d  %.4f %.4f %.4f" % (y1, n1, q1, p_y1, p_n1, p_q1)
    #print "%d %d %d  %.4f %.4f %.4f" % (y2, n2, q2, p_y2, p_n2, p_q2)
    global P_E
    P_E = { 'y1': y1, 'y2': y2, 'p_y1': p_y1, 'p_y2': p_y2,
            'n1': n1, 'n2': n2, 'p_n1': p_n1, 'p_n2': p_n2,
            '?1': q1, '?2': q2, 'p_?1': p_q1, 'p_?2': p_q2 }

def print_judgements(fh):
    fh.write("\nConfusion Matrix:\n\n")
    fh.write('      | ')
    for i in ('y', 'n', '?'):
        fh.write("  %s  " % i)
    fh.write(' |')
    fh.write("\n   ---|-----------------|----\n")
    for i in ('y', 'n', '?'):
        fh.write("    %s | " % i)
        for j in ('y', 'n', '?'):
            fh.write("%3d  " % JUDGEMENTS[i][j])
        fh.write(" | %3d " % P_E[i+'1'])
        fh.write("\n")
    fh.write("   ---|-----------------|----\n")
    fh.write('      |')
    for i in ('y', 'n', '?'):
        fh.write(" %3d " % P_E[i+'2'])
    fh.write("  |\n")
    
def print_all():
    print "\nAll labeled terms:\n"
    labeled_terms = []
    for term, labels in sorted(TERMS.items()):
        if len(labels) == 2:
            labeled_terms.append("[%s] %s" % (','.join(labels), term))
    labeled_terms.sort()
    for t in labeled_terms:
        print '  ', t.encode('utf-8')

def print_disagreements(fh):
    fh.write("\nDiagreements on:\n\n")
    for term, labels in sorted(TERMS.items()):
        if len(labels) == 2 and labels[0] != labels[1]:
            fh.write("  [%s] %s\n" % (','.join(labels), term))

def iaa():
    (agree, disagree) = agreement_scores()
    return float(agree) / float(agree + disagree)

def kappa():
    pe_y = P_E['p_y1'] * P_E['p_y2']
    pe_n = P_E['p_n1'] * P_E['p_n2']
    pe_q = P_E['p_?1'] * P_E['p_?2']
    pe = pe_y + pe_n + pe_q
    (agree, disagree) = agreement_scores()
    pa = float(agree) / float(agree + disagree)
    #print pe_y, pe_n, pe_q, pe, pa
    kappa = (pa - pe) / (1 - pe)
    return kappa

def agreement_scores():
    agree = 0
    disagree = 0
    for i in ('y', 'n', '?'):
        for j in ('y', 'n', '?'):
            if i == j:
                agree += JUDGEMENTS[i][j]
            else:
                disagree += JUDGEMENTS[i][j]
    return (agree, disagree)

def print_scores(fh):
    fh.write("\nAgreement:  %.2f\n" % iaa())
    fh.write("Kappa:      %.2f\n\n" % kappa())



if __name__ == '__main__':
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    if len(sys.argv) == 4:
        outfile = sys.argv[3]
        start = 0
        end = 999999999
    elif len(sys.argv) == 6:
        outfile = sys.argv[5]
        start = int(sys.argv[3])
        end = int(sys.argv[4])
    fh = codecs.open(outfile, 'w', encoding='utf-8')
    fh.write("%s\n\n" % outfile)
    fh.write("FILE1: %s\n" % file1)
    fh.write("FILE2: %s\n" % file2)
    collect_judgements(file1, file2, start, end)
    print_judgements(fh)
    print_scores(fh)
    print_disagreements(fh)
    #print_all()
    fh.close()
    if True:
        fh = codecs.open(outfile)
        #for i in range(2): fh.readline(),
        for i in range(15): print fh.readline(),
        for i in range(3): print '  ', fh.readline(),
