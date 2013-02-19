"""

Scripts that wraps evaluaiton code.

OPTIONS

    -l LANG     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -t PATH     --  target directory, default is data/patents
    
    --gold-standard
    --system-file
    --logfile
    --threshold

    --verbose         --  set verbose printing to stdout
    --show-data       --  print available datasets, then exits
    --show-pipelines  --  print defined pipelines, then exits

Example:
$ python step5_evaluate.py -t data/patents -l en --system-file data/patents/en/data/t2_classify/standard.eval.batch1/classify.standard.eval.batch1.MaxEnt.out.s5.scores.sum.nr --gold-standard ../annotation/en/phr_occ.eval.lab --logfile xxxx.txt

"""

import os, sys, shutil, getopt, subprocess, codecs

#script_path = os.path.abspath(sys.argv[0])
#script_dir = os.path.dirname(script_path)
#os.chdir(script_dir)
#os.chdir('../..')
#sys.path.insert(0, os.getcwd())
#os.chdir(script_dir)

import evaluation


def run_test(system_file, gold_standard, threshold, log_file):
    evaluation.test(gold_standard, system_file, threshold, log_file)

def read_opts():
    longopts = ['system-file=', 'gold-standard=', 'threshold=', 'logfile=']
    try:
        return getopt.getopt(sys.argv[1:], 'l:t:', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))


if __name__ == '__main__':

    # default values of options
    target_path, language = 'data/patents', 'en'
    system_file = None
    gold_standard = None
    threshold = 0.9
    logfile = None
    
    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '--verbose': verbose = True
        if opt == '--gold-standard': gold_standard = val
        if opt == '--system-file': system_file = val
        if opt == '--threshold': threshold = float(val)
        if opt == '--logfile': logfile = val

    run_test(system_file, gold_standard, threshold, logfile)
