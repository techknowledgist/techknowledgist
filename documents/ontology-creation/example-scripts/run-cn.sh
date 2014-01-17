# Creating the date index for 600K CN patents
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

python create_date_idxs.py /home//j/corpuswork/fuse/FUSEData/lists/ln_cn.all.shuffled.txt data_idx_cn_000000-100000.txt warnings_cn_1.txt 0 100000 &
python create_date_idxs.py /home//j/corpuswork/fuse/FUSEData/lists/ln_cn.all.shuffled.txt data_idx_cn_100000-200000.txt warnings_cn_2.txt 100000 200000 &
python create_date_idxs.py /home//j/corpuswork/fuse/FUSEData/lists/ln_cn.all.shuffled.txt data_idx_cn_200000-300000.txt warnings_cn_3.txt 200000 300000 &
python create_date_idxs.py /home//j/corpuswork/fuse/FUSEData/lists/ln_cn.all.shuffled.txt data_idx_cn_300000-400000.txt warnings_cn_4.txt 300000 400000 &
python create_date_idxs.py /home//j/corpuswork/fuse/FUSEData/lists/ln_cn.all.shuffled.txt data_idx_cn_400000-500000.txt warnings_cn_5.txt 400000 500000 &
python create_date_idxs.py /home//j/corpuswork/fuse/FUSEData/lists/ln_cn.all.shuffled.txt data_idx_cn_500000-600000.txt warnings_cn_6.txt 500000 600000 &


# Running the code on the 500 CN sample patents - for testing
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# use creation/data/patents/create_file_list.py to get the expanded file lists

# initialize and process
python step1_initialize.py --language cn --corpus data/patents/cn-500 --filelist data/patents/sample-500-cn-full-scrambled.txt
python step2_document_processing.py --corpus data/patents/cn-500 --verbose -n 500 --populate
python step2_document_processing.py --corpus data/patents/cn-500 --verbose -n 500 --xml2txt
python step2_document_processing.py --corpus data/patents/cn-500 --verbose -n 500 --txt2seg
python step2_document_processing.py --corpus data/patents/cn-500 --verbose -n 500 --seg2tag
python step2_document_processing.py --corpus data/patents/cn-500 --verbose -n 500 --tag2chk

# training and classifying
python create_mallet_file.py --corpus ../creation/data/patents/cn-500 --model-dir data/models/cn-500 --annotation-file ../annotation/cn/phr_occ.lab 
python downsample.py --source-mallet-file data/models/cn-500/train.mallet --threshold 100 --verbose
python select_features.py --source-mallet-file data/models/cn-500/train.ds0003.mallet --features all
python run_tclassify.py --corpus ../creation/data/patents/cn-500 --model data/models/cn-500/train.ds0003.all.model --batch data/classifications/cn-500 --verbose

python create_mallet_file.py --corpus ../creation/data/patents/cn-005 --model-dir data/models/cn-005 --annotation-file ../annotation/cn/phr_occ.lab


# Running the code on the 600K
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# INITIALIZATION AND PREPROCESSING

# initialize
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/1997.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/1998.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/1999.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2000.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2001.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2002.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2003.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2004.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2005.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2006.txt
python step1_initialize.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 -l cn --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/sublists/2007.txt
# NOTE: at first I had forgotten the -l option, which causes trouble with the default pipeline, so I manually had to change the pipeline config file and the general config file

# populate
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --populate -n 11230 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --populate -n 12539 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --populate -n 13761 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --populate -n 16989 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --populate -n 20241 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --populate -n 26215 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --populate -n 33010 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --populate -n 37513 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --populate -n 44811 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --populate -n 50348 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --populate -n 54058 --verbose &

# xml2txt
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --xml2txt -l cn -n 11230 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --xml2txt -l cn -n 12539 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --xml2txt -l cn -n 13761 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --xml2txt -l cn -n 16989 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --xml2txt -l cn -n 20241 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --xml2txt -l cn -n 26215 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --xml2txt -l cn -n 33010 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --xml2txt -l cn -n 37513 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --xml2txt -l cn -n 44811 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --xml2txt -l cn -n 50348 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --xml2txt -l cn -n 54058 --verbose &

# txt2seg
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --txt2seg -l cn -n 11230 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --txt2seg -l cn -n 12539 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --txt2seg -l cn -n 13761 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --txt2seg -l cn -n 16989 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --txt2seg -l cn -n 20241 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --txt2seg -l cn -n 26215 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --txt2seg -l cn -n 33010 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --txt2seg -l cn -n 37513 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --txt2seg -l cn -n 44811 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --txt2seg -l cn -n 50348 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --txt2seg -l cn -n 54058 --verbose &

# seg2tag
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --seg2tag -l cn -n 11230 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --seg2tag -l cn -n 12539 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --seg2tag -l cn -n 13761 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --seg2tag -l cn -n 16989 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --seg2tag -l cn -n 20241 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --seg2tag -l cn -n 26215 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --seg2tag -l cn -n 33010 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --seg2tag -l cn -n 37513 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --seg2tag -l cn -n 44811 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --seg2tag -l cn -n 50348 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --seg2tag -l cn -n 54058 --verbose &

# tag2chk
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --tag2chk -l cn -n 11230 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --tag2chk -l cn -n 12539 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --tag2chk -l cn -n 13761 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --tag2chk -l cn -n 16989 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --tag2chk -l cn -n 20241 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --tag2chk -l cn -n 26215 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --tag2chk -l cn -n 33010 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --tag2chk -l cn -n 37513 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --tag2chk -l cn -n 44811 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --tag2chk -l cn -n 50348 --verbose &
python step2_document_processing.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --tag2chk -l cn -n 54058 --verbose &


# MATCHING

python run_matcher.py --corpus ../creation/data/patents/cn-005 --filelist files.txt --language cn --patterns MATURITY --batch maturity --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &
python run_matcher.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --filelist files-2007.txt --language cn --patterns MATURITY --batch maturity-2007 --verbose &


# TRAINING - CREATING MALLET FILE

# using config/files-2007.txt

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/1997 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/1998 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/1999 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2000 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2001 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2002 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2003 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2004 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2005 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2006 --annotation-file ../annotation/cn/phr_occ.lab --verbose &

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --filelist files-2007.txt --model-dir /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2007 --annotation-file ../annotation/cn/phr_occ.lab --verbose &



# TRAINING - DOWNSAMPLING

# files-2007
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/1997/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/1998/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/1999/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2000/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2001/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2002/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2003/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2004/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2005/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2006/train.mallet --threshold 200 --verbose &
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/2007/train.mallet --threshold 200 --verbose &


# TRAINING - MERGING MODELS AND DOWNSAMPLING AGAIN, FEATURE SELECTION

# merging
python merge_mallet_files.py /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07 '/home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/[0-9]*/train.ds0200.mallet' &

# downsampling again on merged model
python downsample.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.mallet --threshold 1000 --verbose &

# feature selection (perhaps not needed if you use all features, depending on where the classifier gets its features)
python select_features.py --source-mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.mallet --features all-cn --verbose &


# TRAINING - CREATING THE MODEL

# creating the model, takes about 30 minutes, needs 8GB in bin/mallet file
python create_model.py --mallet-file /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.mallet --verbose &


# TESTING

# testing the model (2GB in mallet file should suffice)
python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/201401-en-500 --filelist /home/j/corpuswork/fuse/FUSEData/corpora/201401-en-500/config/files-testing.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-all-600k/models/merged-97-07/train.ds1000.all.model --batch data/classifications/eval-320k-all --gold-standard ../annotation/en/technology/phr_occ.eval.lab --verbose &

# running the model (2GB in mallet file should suffice)
python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-all-600k/subcorpora/1997 --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-all-600k/models/merged-97-07/train.ds1000.all.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-all-600k/classifications/technologies-ds1000-all-1997 --verbose &

# creating technology score time-series
# run these from the ln-all-600k/time-series/technology-scores directory
cut -f1,2 ../../classifications/technologies-ds1000-all-1997/classify.MaxEnt.out.s3.scores.sum > 1997.tab


# CLASSIFYING

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1997 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-1997 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1998 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-1998 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/1999 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-1999 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2000 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2000 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2001 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2001 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2002 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2002 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2003 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2003 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2004 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2004 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2005 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2005 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2006 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2006 --verbose &

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/subcorpora/2007 --filelist files-2007.txt --model /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/models/technologies/pubyears-2007/merged-97-07/train.ds1000.all-cn.model --batch /home/j/corpuswork/fuse/FUSEData/corpora/ln-cn-all-600k/classifications/phase2-eval/technologies-ds1000-all-2007 --verbose &



# TECHNOLOGY SCORE TIME SERIES

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


# MATURITY SCORE TIME SERIES

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
