"""

Scripts to build an index over files with document features.

Most work on the batches is done in memory and therefore the batches are limited to a
certain size.

OPTIONS

    -l LANG     --  provides the language, one of ('en, 'de', 'cn'), default is 'en'
    -t PATH     --  target directory, default is data/patents
    -n INTEGER  --  number of documents to process

    --collect-data  --  run in batch mode to collect data from a set of documents
    --build-index   --  combine the results from available batches

    --dataset STRING   --  dataset to collect data from, taken from a t2_classify dataset
    --version STRING   --  identifier for the combined build, probably not needed
    --config FILENAME  --  file with pipeline configuration
    --files FILENAME   --  contains files to process, either for training or testing

    --verbose         --  set verbose printing to stdout
    --track-memory    --  use this to track memory usage
    --show-data       --  print available datasets, then exits
    --show-pipelines  --  print defined pipelines, then exits


Example for --batch:
$ python step6_index.py -t data/patents -l en --collect-data --dataset standard.batch-001-030 --verbose

Example for --build:
$

"""

import os, sys, shutil, getopt, subprocess, codecs, resource, glob

script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)
os.chdir('../..')
sys.path.insert(0, os.getcwd())
os.chdir(script_dir)

from ontology.utils.batch import GlobalConfig
from ontology.utils.file import ensure_path
from ontology.utils.git import get_git_commit
from step2_document_processing import show_datasets, show_pipelines


def measure_memory_use(fun):
    """Print thee increased memory use after the wrapped function exits."""
    def wrapper(*args):
        m1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result = fun(*args)
        m2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if track_memory:
            print "[%s] increase in memory use: %d" % (fun.__name__, m2 - m1)
        return result
    return wrapper


def run_collect_data(config, dataset):
    """Data collections proceeds off of a classify dataset, using the
    classify.features.doc_feats.txt and classify.features.phr_feats.txt files (or the file
    list and then get the files from the doc_feats and phr_feats datasets)."""
    data_dir = os.path.join(config.target_path, config.language, 'data')
    classify_dir = os.path.join(data_dir, 't2_classify', dataset)
    index_dir = os.path.join(data_dir, 'o1_index', dataset)
    generate_info_files(config, dataset, index_dir, classify_dir)
    collect_statistics(classify_dir, index_dir)


def generate_info_files(config, dataset, index_dir, classify_dir):
    """Copy statistics from t2_classify to o1_index data sets. In some cases the
    statistics can be different, overwrite the classifier values with the indexer values
    (for example for the git commit)."""
    ensure_path(index_dir)
    fh = open(os.path.join(index_dir, 'index.info.general.txt'), 'w')
    fh.write("$ python %s\n\n" % ' '.join(sys.argv))
    fh.write("dataset=%s\n" % dataset)
    fh.write("config_file=%s\n" % os.path.basename(config.pipeline_config_file))
    fh.write("git_commit=%s" % get_git_commit())
    for info_file in ('info.config.txt', 'info.filelist.txt'):
        shutil.copyfile(os.path.join(classify_dir, 'classify.' + info_file),
                        os.path.join(index_dir, 'index.' + info_file))


def collect_statistics(classify_dir, index_dir):
    """Collect statistics from the phr_feats file(s) and the scores file and write them to
    files in the index directory."""
    statistics = {}
    feats_fh = codecs.open(os.path.join(classify_dir, 'classify.features.phr_feats.txt'))
    scores_fh = codecs.open(os.path.join(classify_dir, 'classify.MaxEnt.out.s2.y.nr'))
    summary_fh = codecs.open(os.path.join(index_dir, 'index.count.summary.txt'), 'w')
    expanded_fh = codecs.open(os.path.join(index_dir, 'index.count.expanded.txt'), 'w')
    print "[collect_statistics] reading scores"
    scores = load_scores(scores_fh)
    print "[collect_statistics] reading phr_feats"
    process_phr_feats_lines(statistics, scores, feats_fh, expanded_fh)
    print_summary_statistics(statistics, scores, summary_fh)


@measure_memory_use
def load_scores(scores_fh):
    scores = {}
    for line in scores_fh:
        identifier, score = line.strip().split("\t")
        (year, docid, term) = identifier.split('|', 2)
        term = term.replace('_', ' ')
        scores.setdefault(term, {})
        scores[term].setdefault(year, {})
        if scores[term][year].has_key(docid):
            print "[load scores] WARNING: duplicate scores for '%s' in year %s for document %s" % (term, year, docid)
        scores[term][year][docid] = score
    return scores


@measure_memory_use
def process_phr_feats_lines(statistics, scores, feats_fh, expanded_fh):
    for line in feats_fh:
        vector = line.strip().split("\t")
        (docid, year, term) = vector[0:3]
        docid = docid.rstrip('0123456789')[:-1]
        feats = vector[3:]
        loc_feats = [f[12:] for f in feats if f.startswith('section_loc=')]
        loc_feat = loc_feats[0] if loc_feats else None
        loc_feats = ' '.join(loc_feats)
        update_summary_statistics(statistics, docid, year, term, loc_feats)
        print_to_expanded_statistics(docid, year, term, loc_feats, scores, expanded_fh)


def update_summary_statistics(statistics, docid, year, term, loc_feat):
    statistics.setdefault(term,{})
    statistics[term].setdefault(year,{'scores': [], 'documents': {}, 'instances': 0, 'section_counts': {}})
    statistics[term][year]['documents'][docid] = True
    statistics[term][year]['instances'] += 1
    statistics[term][year]['section_counts'].setdefault(loc_feat, 0)
    statistics[term][year]['section_counts'][loc_feat] += 1


def print_summary_statistics(statistics, scores, fh):
    for term in sorted(statistics.keys()):
        for year in statistics[term]:
            data = statistics[term][year]
            try:
                term_scores = scores[term][year].values()
                average_score = sum([float(s) for s in term_scores]) / len(term_scores)
                average_score = "%.4f" % average_score
            except KeyError:
                average_score = 'None'
            except ZeroDivisionError:
                average_score = 'None'
            fh.write("%s\t%s\t%s\t%d\t%d" % (term, year, average_score, len(data['documents']), data['instances']))
            for section, count in data['section_counts'].items():
                fh.write("\t%s %d" % (section, count))
            fh.write("\n")


def print_to_expanded_statistics(docid, year, term, loc_feats, scores, fh):
    global TMP
    try:
        score = scores[term][year][docid]
        score = "%.4f" % float(score)
    except KeyError:
        score = 'None'
    fh.write("%s\t%s\t%s\t%s\t%s\n" % (term, year, docid, score, loc_feats))



def build_index(config, dataset):
    """In this case, dataset is actually a regular expression that can match many
    datasets, or a comma-separated list of regular expressions"""
    pass



def read_opts():
    longopts = ['config=', 'collect-data', 'build-index', 'version=', 'dataset=', 
                'track-memory', 'verbose', 'show-data', 'show-pipelines']
    try:
        return getopt.getopt(sys.argv[1:], 'l:t:n:', longopts)
    except getopt.GetoptError as e:
        sys.exit("ERROR: " + str(e))



if __name__ == '__main__':

    # default values of options
    target_path, language = 'data/patents', 'en'
    dataset = None
    collect_data = False
    build_index = False
    pipeline_config = 'pipeline-default.txt'
    verbose, track_memory = False, False
    show_data_p, show_pipelines_p = False, False

    (opts, args) = read_opts()
    for opt, val in opts:
        if opt == '-l': language = val
        if opt == '-t': target_path = val
        if opt == '--dataset': dataset = val
        if opt == '--collect-data': collect_data = True
        if opt == '--build-index': build_index = True
        if opt == '--show-data': show_data_p = True
        if opt == '--show-pipelines': show_pipelines_p = True
        if opt == '--verbose': verbose = True
        if opt == '--track-memory': track_memory = True

    config = GlobalConfig(target_path, language, pipeline_config)
    if verbose:
        config.pp()

    if show_data_p:
        show_datasets(target_path, language, config)
    elif show_pipelines_p:
        show_pipelines(target_path, language)

    elif collect_data:
        run_collect_data(config, dataset)

    elif build_index:
        run_build_index(config, dataset)
