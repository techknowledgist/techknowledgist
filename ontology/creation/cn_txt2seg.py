# cn_txt2seg.py
# create segmented chinese files
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

def seg(input, output, segmenter):
    s_input = codecs.open(input, encoding='utf-8')
    s_output = open(output, "w")
    section = ""
    sent_no_in_section = 0
    for line in s_input:
        line = line.strip("\n")
        if debug_p == True:
            print "[tag]Processing line: %s\n" % line
        if line != "":

            if line[0:3] == "FH_":
                # we are at a section header
                # write it back out as is
                line_out = line.encode('utf-8')
                s_output.write(line_out)
            else:
                if debug_p:
                    print "[tag]line: %s" % line
                # process the sentences in the section
                l_seg_string = segmenter.seg(line)

                for seg_string in l_seg_string:
                    seg_string = seg_string.encode('utf-8')
                    if debug_p:
                        print "[tag]seg_string: %s" % seg_string

                    s_output.write("%s\n" % seg_string)


    s_input.close()
    s_output.close()

def test_tag_en():
    input = "/home/j/anick/fuse/data/patents/en_test/txt/US20110052365A1.xml"
    output = "/home/j/anick/fuse/data/patents/en_test/tag/US20110052365A1.xml"
    tagger = sdp.STagger("chinese.tagger")
    tag(input, output, tagger)


# cn_txt2seg.test_seg_cn()
def test_seg_cn():
    input = "/home/j/anick/fuse/data/patents/tmp/cn/CN1394959A-tf.txt"
    output = "/home/j/anick/fuse/data/patents/tmp/cn/CN1394959A-tf.seg2"
    # segment using Stanford segmenter with chinese tree bank model
    segmenter = sdp.Segmenter()
    #seg(input, output, segmenter)
    segmenter.cn_segment_file(input, output)

###-----------------------------------------------


def txt2tag_file(txt_file, tag_file, tagger):
    tag(txt_file, tag_file, tagger)


def txt2seg_file(txt_file, seg_file, segmenter):
    segmenter.cn_segment_file(txt_file, seg_file, segmenter)



# tag all txts in source and place results in target dir
def txt2tag_dir(source_path, target_path, tagger):
    for file in os.listdir(source_path):
        source_file = source_path + "/" + file
        target_file = target_path + "/" + file
        print "[txt2tag_dir]from %s to %s" % (source_file, target_file)
        #txt2tag_file(source_file, target_file, tagger)
        tag(source_file, target_file, tagger)
    print "[txt2tag_dir]done"


# segment all txts in source and place results in target dir
def txt2seg_dir(source_path, target_path, segmenter):
    for file in os.listdir(source_path):
        source_file = source_path + "/" + file
        target_file = target_path + "/" + file
        print "[txt2seg_dir]from %s to %s" % (source_file, target_file)
        segmenter.cn_segment_file(source_file, target_file)
    print "[txt2seg_dir]done"



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

# lang should be "cn"
def patent_txt2seg_dir(lang_path, language):
    segmenter = sdp.Segmenter()

    txt_path = lang_path + "/" + language + "/txt"
    seg_path = lang_path + "/" + language + "/seg"
    for year in os.listdir(txt_path):
        txt_year_dir = txt_path + "/" + year
        seg_year_dir = seg_path + "/" + year
        print "[patent_txt2seg_dir]calling txt2seg for dir: %s" % txt_year_dir
        txt2seg_dir(txt_year_dir, seg_year_dir, segmenter)
    print "[patent_txt2seg_dir]finished writing segmented data to %s" % seg_path



# top level call to tag txt data dir in a language
# cn_txt2seg.seg_lang("cn")
def seg_lang(lang):
    if lang == "cn":
        # we need to segment before tagging
        patent_path = "/home/j/anick/fuse/data/patents"
        patent_txt2seg_dir("/home/j/anick/fuse/data/patents", lang)
