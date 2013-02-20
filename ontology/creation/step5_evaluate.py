"""

Scripts that simply wraps evaluation code.

OPTIONS

    --gold-standard   -- file with labeled terms
    --system-file     -- file with system output, this is the *.s5.scores.sum.nr file
    --logfile         -- logfile, default is ../evaluation/logs/tmp.log
    --threshold       -- classifier threshold, if none specified, a ragne from 0.0-0.9 is used

Example:
$ python step5_evaluate.py --system-file data/patents/en/data/t2_classify/standard.eval.batch1/classify.standard.eval.batch1.MaxEnt.out.s5.scores.sum.nr --gold-standard ../annotation/en/phr_occ.eval.lab --logfile xxxx.txt --threshold 0.9

"""

import os, sys, getopt
import evaluation

def run_test(system_file, gold_standard, threshold, log_file, command):
    if threshold is not None:
        evaluation.test(gold_standard, system_file, threshold, log_file,
                        debug_c=True, command=command)
    else:
        # this requires that the version can be extracted as below
        version = os.path.basename(os.path.dirname(system_file))
        log_file = os.path.join('..', 'evaluation', 'logs', "%s-%s.log" % (version, "0.90"))
        evaluation.test(gold_standard, system_file, 0.9, log_file,
                        debug_c=True, command=command)
        for threshold in (0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0):
            log_file = os.path.join('..', 'evaluation', 'logs',
                                    "%s-%s.log" % (version, "%.2f" % threshold))
            evaluation.test(gold_standard, system_file, threshold, log_file,
                            debug_c=False, command=command)

def read_opts():
    longopts = ['system-file=', 'gold-standard=', 'threshold=', 'logfile=']
    try:
        return getopt.getopt(sys.argv[1:], '', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))


if __name__ == '__main__':

    # default values of options
    system_file = None
    gold_standard = None
    threshold = None
    logfile = '../evaluation/logs/tmp.log'

    command = "python %s" % ' '.join(sys.argv)
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '--gold-standard': gold_standard = val
        if opt == '--system-file': system_file = val
        if opt == '--threshold': threshold = float(val)
        if opt == '--logfile': logfile = val

    run_test(system_file, gold_standard, threshold, logfile, command)
