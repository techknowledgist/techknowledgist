import os

# configuration for data used by patent_analysis.py and pipeline.py

#data_root = "/home/j/corpuswork/fuse/code/patent-classifier/ontology/creation/data"
data_root = "data"

# for patent_analysis.py
# directory of patent xml files arranged into yearly subdirectories
external_patent_path = "/home/j/clp/chinese/corpora/fuse-patents/500-patents/DATA/Lexis-Nexis/US/Xml"

# location where patents are copied to local directory for processing steps.  The directory structure 
# arranges files by language/step/year
# The .xml qualifier is expected on file names in all subdirectories, so that the file
# names within the step subdirectories are identical.
working_patent_path = os.path.join(data_root, "patents")

# default language
language = "en"


# for pipeline.py

# For each RDG (related document group), there must be a filelist containing
# doc_id year external_file_path
external_rdg_filelist = os.path.join(data_root, "external/en1.txt")

# For each RDG, create a local working directory
working_rdg_path = os.path.join(data_root, "working/rdg/en1")


