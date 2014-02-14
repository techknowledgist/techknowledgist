"""This script prints most of the  commands needed for processing data. It prints the following:

1. example commands for creating a date index
2. example commands for processing a single corpus
3. example commands for processing a composite corpus

All three can be switched on and off by setting the SHOW_ globals below. Both 2
and 3 can be parametrized, thatis, made specific for a specific source. Edit the
globals below to do that.

The third one is not quite finished, the merging and time series part is hard-wired for just one corpus.

"""

SHOW_CREATE_DATE_INDEX = False
SHOW_SINGLE = False
SHOW_COMPOSITE = True

SINGLE_CORPUS = 'data/patents/en-500'
SINGLE_LANGUAGE = 'en'
SINCLE_FILELIST = 'data/patents/sample-500-en-full-scrambled.txt'
SINGLE_DOWNSAMPLE = 50
SINGLE_FEATURES = 'all'

COMPOSITE_CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-cs-500k'
COMPOSITE_CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/wos-cs-520k'
COMPOSITE_CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-12-chemical'
COMPOSITE_CORPUS = '/home/j/corpuswork/fuse/FUSEData/corpora/ln-us-14-health'
COMPOSITE_LANGUAGE = 'en'
COMPOSITE_FILELIST = 'files.txt'
COMPOSITE_DOWNSAMPLE1 = 200
COMPOSITE_DOWNSAMPLE2 = 1000
COMPOSITE_FEATURES = 'all'




import os, sys



def create_date_idx(language='en'):

    """Write the commands to create a data index. We can use this to create an index
    on the first 600k documents of the ln_uspto (the default) or ln_cn
    corpora. Use 'language=cn' for the latter.

    """
    
    list_dir = '/home//j/corpuswork/fuse/FUSEData/lists'
    list_file = os.path.join(list_dir, 'ln_uspto.all.shuffled.txt')
    if language == 'cn':
        list_file = os.path.join(list_dir, 'ln_cn.all.shuffled.txt')
    print "\n##### CREATING A DATE INDEX\n"
    print "# Creating the date index for 600K CN patents"
    print "# run this from patent-classifier/utils"
    print "python create_date_idxs.py %s data_idx_cn_000000-100000.txt warnings_cn_1.txt 0 100000 &" % list_file
    print "python create_date_idxs.py %s data_idx_cn_100000-200000.txt warnings_cn_2.txt 100000 200000 &" % list_file
    print "python create_date_idxs.py %s data_idx_cn_200000-300000.txt warnings_cn_3.txt 200000 300000 &" % list_file
    print "python create_date_idxs.py %s data_idx_cn_300000-400000.txt warnings_cn_4.txt 300000 400000 &" % list_file
    print "python create_date_idxs.py %s data_idx_cn_400000-500000.txt warnings_cn_5.txt 400000 500000 &" % list_file
    print "python create_date_idxs.py %s data_idx_cn_500000-600000.txt warnings_cn_6.txt 500000 600000 &" % list_file
    print


def process_single_corpus(
        corpus='data/patents/cn-500',
        language='cn',
        filelist='data/patents/sample-500-cn-full-scrambled.txt',
        downsample=100,
        features='all-cn'):

    corpus_size = get_corpus_size(filelist)
    annotation_file = '../annotation/cn/phr_occ.lab'
    print "\n##### PROCESSING A SINGLE CORPUS (%s)\n" % corpus
    print_step2_commands(filelist, corpus, language, corpus_size)
    print_training_commands(corpus, annotation_file, features, downsample)
    print_classify_command(corpus, downsample, features)


def print_step2_commands(filelist, corpus, language, corpus_size):
    print "# initialize and process"
    print "# run this from patent-classifier/ontology/creation"
    print "# assumes an expanded file list as created by patent-classifier/creation/data/patents/create_file_list.py"
    print "# you may need to edit the value of -n if it is set to 1 below"
    print "python step1_initialize.py --language %s --corpus %s --filelist %s" % (corpus, language, filelist)
    print_step2_command_initialize(filelist, corpus, language)
    print_step2_command(corpus, language, corpus_size, '--populate')
    print_step2_command(corpus, language, corpus_size, '--xml2txt')
    print_step2_command(corpus, language, corpus_size, '--txt2seg')
    print_step2_command(corpus, language, corpus_size, '--seg2tag')
    print_step2_command(corpus, language, corpus_size, '--tag2chk')
    print

def print_step2_command_initialize(filelist, corpus, language):
    print "python step1_initialize.py --corpus %s --language %s --filelist %s" % (corpus, language, filelist)

def print_step2_command(corpus, language, corpus_size, stage):
    print "python step2_document_processing.py --corpus %s -l %s --verbose -n %d %s &" % (corpus, language, corpus_size, stage)

    
def print_training_commands(corpus, annotation_file, features, downsample):
    print "# training"
    print "# run this from patent-classifier/ontology/classifier"
    print "# creates and uses model in local data/models directory," + \
        " using features in %s.features and downsample threshold of %d" % (features, downsample)
    print "# creating the model, takes about 30 minutes, needs 8GB in bin/mallet file"
    print "python create_mallet_file.py --corpus ../creation/%s --model-dir data/models/%s --annotation-file %s" \
        % (corpus, os.path.basename(corpus), annotation_file)
    print "python downsample.py --source-mallet-file data/models/%s/train.mallet --threshold %d --verbose" \
        % (os.path.basename(corpus), downsample)
    print "python select_features.py --source-mallet-file data/models/%s/train.ds%04d.mallet --features %s" \
        % (os.path.basename(corpus), downsample, features)
    print "python create_model.py --mallet-file data/models/%s/train.ds%04d.%s.mallet --verbose" \
        % (os.path.basename(corpus), downsample, features)
    print

def print_classify_command(corpus, downsample, features):
    print "# classifying"
    print "# creates classification in local data/classifications directory and uses a local model in data/models"
    print "# needs only 2GB in bin/mallet file"
    print "python run_tclassify.py --corpus ../creation/%s" % corpus + \
        " --model data/models/%s/train.ds%04d.%s.model" % (os.path.basename(corpus), downsample, features) + \
        " --batch data/classifications/%s --verbose" % os.path.basename(corpus)
    print


def get_corpus_size(filelist):
    pdir = '/Users/marc/Documents/fuse/patent-classifier/ontology/creation'
    if not filelist.startswith(os.sep):
        filelist = os.path.join(pdir, filelist)
    try:
        return len([l for l in open(filelist) if l.strip()])
    except IOError:
        return 1



def process_composite_corpus(corpus, language):

    years = [1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007]
    sizes = {}
    corpora = {}
    for year in years:
        sizes[year] = get_corpus_size(os.path.join(corpus, 'sublists', "%d.txt" % year))
        corpora[year] = os.path.join(corpus, 'subcorpora', str(year))

    print "\n##### PROCESSING A COMPOSITE CORPUS (%s)\n" % corpus

    print "# initialize"
    for year in years:
        print_step2_command_initialize(os.path.join(corpus, 'sublists', "%d.txt" % year),
                                       corpora[year], language)
    print "\n# populate"
    for year in years: print_step2_command(corpora[year], language, sizes[year], '--populate')
    print "\n# xml2txt"
    for year in years: print_step2_command(corpora[year], language, sizes[year], '--xml2txt')
    if language == 'cn':
        print "\n# txt2seg"
        for year in years: print_step2_command(corpora[year], language, sizes[year], '--txt2seg')
        print "\n# seg2tag"
        for year in years: print_step2_command(corpora[year], language, sizes[year], '--seg2tag')
    else:
        print "\n# txt2tag"
        for year in years: print_step2_command(corpora[year], language, sizes[year], '--txt2tag')
    print "\n# tag2chk"
    for year in years: print_step2_command(corpora[year], language, sizes[year], '--tag2chk')
    print "\n# pattern matching"
    for year in years:
        print "python run_matcher.py --corpus %s" % corpora[year] + \
            "--filelist files.txt --language %s --patterns MATURITY --batch maturity --verbose &"  % language
    print


def model_creation_on_composite_corpus(corpus, filelist, ds1, ds2, features):

    print "\n##### CREATING MODEL FOR COMPOSITE CORPUS\n"
    print "# corpus = %s" % corpus
    print "# downsample on subcorpora = %d" % ds1
    print "# downsample on composite corpus = %d" % ds2
    print "# feature set = %s\n" % features

    years = [1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007]
    corpora = {}
    models = {}
    for year in years:
        corpora[year] = os.path.join(corpus, 'subcorpora', str(year))
        models[year] = os.path.join(corpus, 'models', 'technologies', 'pubyears-2007', str(year))
    annotation_file = '../annotation/cn/phr_occ.lab'

    print "# training - create mallet file"
    print "# may need to edit the model path\n"
    for year in years:
        print "python create_mallet_file.py --corpus %s --filelist %s --model-dir %s --annotation-file %s --verbose &\n" \
            % (corpora[year], filelist, models[year], annotation_file)

    print "\n# downsampling subcorpora to %d" % ds1
    for year in years:
        print "python downsample.py --source-mallet-file %s/train.mallet --threshold %d --verbose &" % (models[year], ds1)
        #/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/1997/

    print MERGING_AND_SUCH

    print "\n##### CLASSIFYING FOR COMPOSITE CORPUS (%s)\n" % corpus
    for year in years:
        print "python run_tclassify.py --corpus %s" % corpora[year] + \
            " --filelist %s" % filelist + \
            " --model %s/models/technologies/pubyears-2007/merged-97-07/train.ds%04d.%s.model" % (corpus, ds2, features) + \
            " --batch %s/classifications/phase2-eval/technologies-ds%04d-%s-1997 --verbose &\n" % (corpus, ds2, features)

    print TIME_SERIES
    

MERGING_AND_SUCH = """

##### TRAINING - MERGING MODELS, DOWNSAMPLING AGAIN, FEATURE SELECTION, MODEL CREATION, TESTING

# merging
python merge_mallet_files.py /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07 '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/[0-9]*/train.ds0200.mallet' &

# downsampling again on merged model
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.mallet --threshold 1000 --verbose &

# feature selection (perhaps not needed if you use all features, depending on where the classifier gets its features)
python select_features.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.mallet --features all-cn --verbose &

# creating the model, takes about 30 minutes, needs 8GB in bin/mallet file
python create_model.py --mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.mallet --verbose &

# testing the model (2GB in mallet file should suffice)
python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/201401-en-500 --filelist /home/j/corpuswork/fuse/FUSEData/corpora/201401-en-500/config/files-testing.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-all-600k/models/merged-97-07/train.ds1000.all.model --batch data/classifications/eval-320k-all --gold-standard ../annotation/en/technology/phr_occ.eval.lab --verbose &
"""


TIME_SERIES = """

##### TECHNOLOGY SCORE TIME SERIES

# run these from the ln-us-all-600k/time-series/technology-scores directory
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-1997/classify.MaxEnt.out.s3.scores.sum > 1997.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-1998/classify.MaxEnt.out.s3.scores.sum > 1998.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-1999/classify.MaxEnt.out.s3.scores.sum > 1999.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2000/classify.MaxEnt.out.s3.scores.sum > 2000.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2001/classify.MaxEnt.out.s3.scores.sum > 2001.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2002/classify.MaxEnt.out.s3.scores.sum > 2002.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2003/classify.MaxEnt.out.s3.scores.sum > 2003.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2004/classify.MaxEnt.out.s3.scores.sum > 2004.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2005/classify.MaxEnt.out.s3.scores.sum > 2005.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2006/classify.MaxEnt.out.s3.scores.sum > 2006.tab
cut -f1,2 ../../classifications/phase2-eval/technologies-ds1000-all-2007/classify.MaxEnt.out.s3.scores.sum > 2007.tab


##### MATURITY SCORE TIME SERIES

# splitting terms into good terms and bad terms
# from ontology/classifier/utils
# edit settings in filter.py
python filter.py 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007

# merging all terms and sort them into frequency bins
# from ontology/classifier/utils
# edit settings in merge.py
python merge.py 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007
python split_terms_on_frequency

# move the files to the classifications directory
mv all_terms.* /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval

# create and split maturity scores
# from ontology/matcher
# edit settings in maturity.py and split-maturity-scores.py
python maturity.py
python split-maturity-scores.py
"""



if __name__ == '__main__':

    if SHOW_CREATE_DATE_INDEX:
        create_date_idx()

    if SHOW_SINGLE:
        process_single_corpus(corpus=SINGLE_CORPUS, language=SINGLE_LANGUAGE,
                              filelist=SINCLE_FILELIST,
                              downsample=SINGLE_DOWNSAMPLE, features=SINGLE_FEATURES)

    if SHOW_COMPOSITE:
        process_composite_corpus(corpus=COMPOSITE_CORPUS, language=COMPOSITE_LANGUAGE)
        model_creation_on_composite_corpus(corpus=COMPOSITE_CORPUS, filelist=COMPOSITE_FILELIST,
                                           ds1=COMPOSITE_DOWNSAMPLE1, ds2=COMPOSITE_DOWNSAMPLE2,
                                           features=COMPOSITE_FEATURES)
