# txt2tag.py
# tag text files
# formatted as follows:
# field headers of the form    FH_<name>:
# each followed by one or more lines of text (without any empty lines)
# A line can consist of multiple sentences, which will be split by the tagger
# Last line must be     END:

import sdp
import os
import codecs

debug_p = False
#debug_p = True

def tag(input, output, tagger):
    s_input = codecs.open(input, encoding='utf-8')
    s_output = open(output, "w")
    section = ""
    sent_no_in_section = 0
    for line in s_input:
        # skip very long lines since these typically contain non-tectual crut like gene
        # sequences; skip them because some of them break the tagger
        # TODO: now we just lose them, write them to the output but mark them somehow
        if len(line) > 10000:
            continue
        line = line.strip("\n")
        # TODO: this is hack to make the tagger work, but it loses information
        # TODO: could replace with &tilde;
        # TODO: or find the real solution
        line = line.replace('~','')
        if debug_p == True:
            print "[tag]Processing line: %s\n" % line
        if line != "":

            if line[0:3] == "FH_":
                # we are at a section header
                # write it back out as is
                line_out = line.encode('utf-8')
                s_output.write("%s\n" % line_out)
            else:
                if debug_p:
                    print "[tag]line: %s" % line
                # process the sentences in the section
                l_tag_string = tagger.tag(line)
                if debug_p:
                    print "[tag]line2: %s" % line
                for tag_string in l_tag_string:
                    tag_string = tag_string.encode('utf-8')
                    if debug_p:
                        print "[tag]tag_string: %s" % tag_string
                    s_output.write("%s\n" % tag_string)

    s_input.close()
    s_output.close()

    
def test_tag_en():
    input = "/home/j/anick/fuse/data/patents/en_test/txt/US20110052365A1.xml"
    output = "/home/j/anick/fuse/data/patents/en_test/tag/US20110052365A1.xml"
    tagger = sdp.STagger("english-caseless-left3words-distsim.tagger")
    tag(input, output, tagger)

# txt2tag.test_tag_de
def test_tag_de():
    tagger = sdp.STagger("german-fast.tagger")
    dir = "/home/j/anick/fuse/data/tmp"
    file_list = ["DE3102424A1_all_caps", "DE3102424A1_all_lower", "DE3102424A1_first_cap"]
    for file in file_list:
        full_inpath = dir + "/" + file + ".xml"
        full_outpath = dir + "/" + file + ".tag"
        tag(full_inpath, full_outpath, tagger)
        print "Created %s" % full_outpath


def txt2tag_file(txt_file, tag_file, tagger):
    tag(txt_file, tag_file, tagger)


# tag all txts in source and place results in target dir
def txt2tag_dir(source_path, target_path, tagger):
    for file in os.listdir(source_path):
        source_file = source_path + "/" + file
        target_file = target_path + "/" + file
        print "[txt2tag_dir]from %s to %s" % (source_file, target_file)
        #txt2tag_file(source_file, target_file, tagger)
        tag(source_file, target_file, tagger)
    print "[txt2tag_dir]done"


"""
Stanford tagger options:
(info here: http://ufallab.ms.mff.cuni.cz/tectomt/share/data/models/tagger/stanford/README-Models.txt)
chinese7.tagger
chinese7.tagger.props
chinese.tagger
chinese.tagger.props
english-bidirectional-distsim.tagger
english-bidirectional-distsim.tagger.props
english-caseless-left3words-distsim.tagger
english-caseless-left3words-distsim.tagger.props
english-left3words-distsim.tagger
english-left3words-distsim.tagger.props
french.tagger
french.tagger.props
german-dewac.tagger
german-dewac.tagger.props
german-fast.tagger
german-fast.tagger.props
german-hgc.tagger
german-hgc.tagger.props
"""

# language is en, de, cn
# lang_path (above year_dir)
# e.g. patent_txt2tag_dir("/home/j/anick/fuse/data/patents", "de")
def patent_txt2tag_dir(lang_path, language):
    # choose tagger for language
    if language == "en":
        tagger = sdp.STagger("english-caseless-left3words-distsim.tagger")
    elif language == "de":
        # note: german-fast is much faster than german-dewac although 4% poorer in dealing
        # with unknown words.
        tagger = sdp.STagger("german-fast.tagger")
    elif language == "cn":
        tagger = sdp.STagger("chinese.tagger")
    
    txt_path = lang_path + "/" + language + "/txt"
    tag_path = lang_path + "/" + language + "/tag"
    for year in os.listdir(txt_path):
        txt_year_dir = txt_path + "/" + year
        tag_year_dir = tag_path + "/" + year
        print "[patent_txt2tag_dir]calling txt2tag for dir: %s" % txt_year_dir
        txt2tag_dir(txt_year_dir, tag_year_dir, tagger)
    print "[patent_txt2tag_dir]finished writing tagged data to %s" % tag_path

# top level call to tag txt data dir in a language
# txt2tag.tag_lang("en")
# txt2tag.tag_lang("de")
# txt2tag.tag_lang("cn")
def tag_lang(lang):
    patent_path = "/home/j/anick/fuse/data/patents"
    patent_txt2tag_dir("/home/j/anick/fuse/data/patents", lang)

### added by PGA 10/8

def pipeline_txt2tag_dir(root, language):
    source_path = os.path.join(root, "txt")
    target_path = os.path.join(root, "tag")

    # choose tagger for language
    if language == "en":
        tagger = sdp.STagger("english-caseless-left3words-distsim.tagger")
    elif language == "de":
        # note: german-fast is much faster than german-dewac although 4% poorer in dealing
        # with unknown words.
        tagger = sdp.STagger("german-fast.tagger")
    elif language == "cn":
        tagger = sdp.STagger("chinese.tagger")

    for file in os.listdir(source_path):
        source_file = source_path + "/" + file
        target_file = target_path + "/" + file
        print "[txt2tag_dir]from %s to %s" % (source_file, target_file)
        #txt2tag_file(source_file, target_file, tagger)
        tag(source_file, target_file, tagger)
    print "[txt2tag_dir]done"


### Added MV 10/15

def get_tagger(language):
    """Used by batch.py."""
    if language == "en":
        return sdp.STagger("english-caseless-left3words-distsim.tagger")
    elif language == "de":
        return sdp.STagger("german-fast.tagger")
    elif language == "cn":
        return sdp.STagger("chinese.tagger")
