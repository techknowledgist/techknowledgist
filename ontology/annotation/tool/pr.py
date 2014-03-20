"""


"""


import codecs


def load_labels(gold_data):
    labels = {}
    for label_file in gold_data:
        try:
            fh = codecs.open(label_file, encoding='utf8')
        except IOError:
            continue
        for line in fh:
            line = line.strip()
            if not line: continue
            if line[0] == '#': continue
            score, term = line.split("\t")
            if labels.has_key(term):
                print term
            labels[term] = [score]
    return labels

def add_system_labels(system_data, labels):
    for line in codecs.open(system_data, encoding='utf8'):
        line = line.rstrip()
        term, label, c, s = line.split("\t")
        if labels.has_key(term):
            labels[term].append(label)

def get_categories(labels):
    cats = {}
    for (l1, l2) in labels.values():
        cats[l1] = True
        cats[l2] = True
    return cats.keys()

def calculate_pr(labels, fh):
    categories =  get_categories(labels)
    for cat in categories:
        if cat == 'x': continue
        if cat == 'u': continue
        tp, tn, fp, fn = 0, 0, 0, 0
        for gold_label, system_label in labels.values():
            if gold_label == cat and system_label == cat:
                tp += 1
            elif gold_label == cat:
                fn += 1
            elif system_label == cat:
                fp += 1
            else:
                tn += 1
        precision = float(tp) / (tp + fp)
        recall = float(tp) / (tp + fn)
        fh.write("%s - precision:%.2f recall:%.2f (tp:%03d fp:%03d fn:%03d tn:%03d)\n" 
                 % (cat, precision, recall, tp, fp, fn, tn))
    fh.write("\ngold\tsystem\tterm\n\n")
    for term in labels.keys():
        gl, sl = labels[term]
        fh.write("%s\t%s\t%s\n" % (gl, sl, term))

def process(gold_data, system_data, outfile):
    print outfile
    for fname in gold_data:
        print "   GOLD LABELS    - ", fname
    print "   SYSTEM LABELS  - ", system_data
    print "   OUTPUT         - ", outfile
    fh = codecs.open(outfile, 'w', encoding='utf8')
    fh.write("SYSTEM_DATA: %s\n\n" % system_data)
    for label_file in gold_data:
        fh.write("LABEL_FILE: %s\n" % label_file)
    fh.write("\n")
    labels = load_labels(gold_data)
    add_system_labels(system_data_health_actux, labels)
    calculate_pr(labels, fh)



def filter_jp(fnames): return [f for f in fnames if f.find('jp.labels') > -1]
def filter_pa(fnames): return [f for f in fnames if f.find('pa.labels') > -1]
def filter_mv(fnames): return [f for f in fnames if f.find('mv.labels') > -1]


if __name__ == '__main__':

    annotators = [(1,'pa'), (2,'mv'), (3,'jp')]
    
    system_data_health_actux = "lists/health_eval_actux_2002.act.cat.w0.0_r10-100000_ds0.05.1000"
    system_data_health_pnux  = "lists/health_eval_pnux_2002.a.pn.cat.w0.0_r10-100000_ds0.05.1000"

    labels_health_actux = ["role_annotation/health.2002.act.%d.%s.labels.txt" % (c, n) for (c, n) in annotators]
    labels_health_pnux  = ["role_annotation/health.2002.pn.%d.%s.labels.txt" % (c, n) for (c, n) in annotators]

    system_data_cs_actux = "lists/cs_eval_actux_2002.act.cat.w0.0_r10-100000_ds1.5.1000"
    system_data_cs_pnux  = "lists/cs_eval_pnux_2002.a.pn.cat.w0.0_r10-100000_ds1.5.1000"

    labels_cs_actux = ["role_annotation/cs.2002.act.%d.%s.labels.txt" % (c, n) for (c, n) in annotators]
    labels_cs_pnux = ["role_annotation/cs.2002.pn.%d.%s.labels.txt" % (c, n) for (c, n) in annotators]

    process(labels_health_actux, system_data_health_actux, 'scores-health-actux-all.txt')
    process(filter_pa(labels_health_actux), system_data_health_actux, 'scores-health-actux-pa.txt')
    process(filter_mv(labels_health_actux), system_data_health_actux, 'scores-health-actux-mv.txt')
    process(filter_jp(labels_health_actux), system_data_health_actux, 'scores-health-actux-jp.txt')

    process(labels_health_pnux, system_data_health_pnux, 'scores-health-pnux-all.txt')
    process(filter_pa(labels_health_pnux), system_data_health_pnux, 'scores-health-pnux-pa.txt')
    process(filter_mv(labels_health_pnux), system_data_health_pnux, 'scores-health-pnux-mv.txt')
    process(filter_jp(labels_health_pnux), system_data_health_pnux, 'scores-health-pnux-jp.txt')

    process(labels_cs_actux, system_data_cs_actux, 'scores-cs-actux-all.txt')
    process(filter_pa(labels_cs_actux), system_data_cs_actux, 'scores-cs-actux-pa.txt')
    process(filter_mv(labels_cs_actux), system_data_cs_actux, 'scores-cs-actux-mv.txt')
    process(filter_jp(labels_cs_actux), system_data_cs_actux, 'scores-cs-actux-jp.txt')

    process(labels_cs_pnux, system_data_cs_pnux, 'scores-cs-pnux-all.txt')
    process(filter_pa(labels_cs_pnux), system_data_cs_pnux, 'scores-cs-pnux-pa.txt')
    process(filter_mv(labels_cs_pnux), system_data_cs_pnux, 'scores-cs-pnux-mv.txt')
    process(filter_jp(labels_cs_pnux), system_data_cs_pnux, 'scores-cs-pnux-jp.txt')

