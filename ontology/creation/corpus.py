"""

Module that contains corpus-level processing functionality. The Corpus class is
typically used by scripts that process files in batch.

"""


# TODO
#
# - Filenames like files.txt and general.txt are defined in the code, should be
#   put up front; the same holds for names of processing stages and input and
#   output directories like d2_tag.
#
# - Add option to grow an already initialized corpus. One question to answer here
#   is whether you just add lines to config/files.txt or also add some lines
#   saying that x files were added at time t.



import os, sys, shutil, getopt, errno, random, time

import config
from ontology.utils.file import ensure_path, get_file_paths, read_only
from ontology.utils.git import get_git_commit



class Corpus(object):

    """Class that implements a corpus, where a corpus is understood to include
    all source documents as well as document-level processing on all documents
    in the corpus. This class gives access to corpus initialization as well as
    corpus-level batch processing of the corpus contents."""


    def __init__(self, language, source_file, source_path,
                 target_path, pipeline_config, shuffle_file):

        """Creates a directory named target_path and all subdirectories and
        files in there needed for further processing. See the module docstring
        in step1_initialize.py for more details."""

        self.language = language
        self.source_file = source_file
        self.source_path = source_path
        self.target_path = target_path
        self.pipeline_config = pipeline_config
        self.shuffle_file = shuffle_file

        self.command = "$ python %s\n\n" % ' '.join(sys.argv)
        self._generate_settings()
        
        self._print_init_message()
        
        if os.path.exists(self.target_path):
            sys.exit("[--init] ERROR: %s already exists" % self.target_path)
        self.data_path = os.path.join(self.target_path, 'data')
        self.conf_path = os.path.join(self.target_path, 'config')

        self._create_directories()
        self._create_general_config_file()
        self._create_default_pipeline_config_file()
        self._create_filelist()
        print
        

    def _generate_settings(self):
        self.settings = ["timestamp    =  %s\n" % time.strftime("%x %X"),
                         "language     =  %s\n" % self.language,
                         "source_file  =  %s\n" % self.source_file,
                         "source_path  =  %s\n" % self.source_path,
                         "target_path  =  %s\n" % self.target_path,
                         "shuffle      =  %s\n" % str(self.shuffle_file),
                         "git_commit   =  %s\n" % get_git_commit()]

    def _print_init_message(self):
        print "\n[--init] initializing %s" % (self.target_path)
        print "\n   %s" % ("   ".join(self.settings))
    
    

    def _create_directories(self):
        """Create subdirectory structure in target_path."""
        print "[--init] creating directory structure in %s" % (self.target_path)
        ensure_path(self.conf_path)
        for subdir in config.PROCESSING_AREAS:
            subdir_path = self.data_path + os.sep + subdir
            ensure_path(subdir_path)

    def _create_filelist(self):
        """Create a list of files either by copying a given list or by traversing a
        given directory."""
        print "[--init] creating %s/files.txt" % (self.conf_path)
        file_list = os.path.join(self.conf_path, 'files.txt')
        if self.source_file is not None:
            shutil.copyfile(self.source_file, file_list)
        elif self.source_path is not None:
            filenames = get_file_paths(self.source_path)
            if self.shuffle_file:
                random.shuffle(filenames)
            with open(file_list, 'w') as fh:
                for fname in filenames:
                    fh.write("0000\t" + fname + "\n")
        else:
            sys.exit("[--init] ERROR: " +
                     "need to define input with --filelist or " +
                     "--source-directory option, aborting")
        read_only(file_list)

        
    def _create_general_config_file(self):
        filename = os.path.join(self.conf_path, 'general.txt')
        print "[--init] creating %s" % (filename)
        fh = open(filename, 'w')
        fh.write(self.command)
        fh.write("".join(self.settings))
        read_only(filename)

    def _create_default_pipeline_config_file(self):
        filename = os.path.join(self.conf_path, 'pipeline-default.txt')
        print "[--init] creating %s" % (filename)
        fh = open(filename, 'w')
        fh.write(self.pipeline_config.lstrip())
        read_only(filename)
