# script to run term_features.sh with set parameters
# 10 domains for the years 1997 through 2007

CORPUS_LIST='ln-us-A21-computers ln-us-A22-communications ln-us-A23-semiconductors ln-us-A24-optical-systems ln-us-A25-chemical-engineering ln-us-A26-organic-chemistry ln-us-A27-molecular-biology ln-us-A28-mechanical-engineering ln-us-A29-thermal-technology ln-us-A30-electrical-circuits'

START_YEAR=1997
END_YEAR=2007

for CORPUS in $CORPUS_LIST; do
   echo "[run_term_features_all]Processing corpus: $CORPUS"

   sh run_term_features.sh $CORPUS $START_YEAR $END_YEAR
   echo "[run_term_features_all]Completed $CORPUS for years $START_YEAR - $END_YEAR"

done
