# script to make it easy to rerun the tf.py function to recreat the .tf file with
# and extra prob feature added.

# sh run_tf.sh ln-us-A21-computers 

ROOT=/home/j/anick/patent-classifier/ontology/roles/data/patents
CORPUS=$1

python tf.py $ROOT/$CORPUS/data/term_features/ $ROOT/$CORPUS/data/tv/ 1997 2008

