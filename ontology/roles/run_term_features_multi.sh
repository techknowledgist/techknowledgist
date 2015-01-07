# run run_term_features for multiple corpora/years

CORPUS_LIST='ln-us-10-agriculture ln-us-11-construction'
YEAR_LIST='1997 2002'

for CORPUS in $CORPUS_LIST; do
   echo "[run_term_features_multi]Processing corpus: $CORPUS"

   for YEAR in $YEAR_LIST; do 
      sh run_term_features.sh $CORPUS $YEAR $YEAR
      echo "[run_term_features_multi]Completed $CORPUS for year $YEAR"
   done
done