# create two training sets for the sample 500, one for all of them and one with the 10 test files held out

python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-sample-500 --model-dir data/models/technologies-500 --annotation-file ../annotation/en/technology/phr_occ.lab --filelist files.txt --verbose
python create_mallet_file.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-sample-500 --model-dir data/models/technologies-490 --annotation-file ../annotation/en/technology/phr_occ.lab --filelist files-training.txt --verbose

python select_features.py --source-mallet-file data/models/technologies-500/train.mallet --features all --verbose
python select_features.py --source-mallet-file data/models/technologies-490/train.mallet --features all --verbose

python create_model.py --mallet-file data/models/technologies-500/train.all.mallet
python create_model.py --mallet-file data/models/technologies-490/train.all.mallet

python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-sample-500 --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-sample-500/config/files-testing.txt --model data/models/technologies-500/train.all.model --batch data/classifications/eval-sample-500-all-500 --gold-standard ../annotation/en/technology/phr_occ.eval.lab --verbose
python run_tclassify.py --corpus /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-sample-500 --filelist /home/j/corpuswork/fuse/FUSEData/corpora/ln-us-sample-500/config/files-testing.txt --model data/models/technologies-490/train.all.model --batch data/classifications/eval-sample-500-all-490 --gold-standard ../annotation/en/technology/phr_occ.eval.lab --verbose
