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
import re
from time import sleep

debug_p = False
#debug_p = True

#version to work with Popen --YZ
def seg(infile, outfile, segmenter):
    s_input = codecs.open(infile, encoding='utf-8')
    s_output = codecs.open(outfile, "w", encoding='utf-8')
    output = []
    for line in s_input:
        line = re.sub(r'^\s*$', '', line)
        if debug_p == True:
            print "[tag]Processing line: %s\n" % line
        if line != "":
            if is_omitable(line):
                s_output.write(line)
                #print "Omit: %s" %line
            else:
                # this is a hack needed because the segmenter has a normalization error
                # for non-breaking spaces, replace them here with regular spaces.
                line = line.replace(unichr(160),' ')
                l_seg_string = segmenter.seg(line)
                if l_seg_string != '':
                    s_output.write("%s" % l_seg_string)
    s_input.close()        
    s_output.close()

    
def is_omitable(s):
    """Do not segment anything over 500 characters or with ascii-8 only."""
    if len(s) > 500:
        return True
    return all(ord(c) < 256 for c in s)

                 
# cn_txt2seg.test_seg_cn()
def test_seg_cn():
    input = "/home/j/yzhou/patentWork/data/cn/txt/1999/CN1214051A.xml"
    #input = "/home/j/yzhou/patentWork/data/cn/txt/2009/CN101573383A.xml"
    output = "/home/j/yzhou/patentWork/data/cn/seg/1999/CN1214051A.xml"
    #output = "/home/j/yzhou/patentWork/data/cn/seg/2009/CN101573383A.xml"
    # segment using Stanford segmenter with chinese tree bank model
    segmenter = sdp.Segmenter()
    seg(input, output, segmenter)
    #segmenter.cn_segment_file(input, output)

###-----------------------------------------------


def txt2seg_file(txt_file, seg_file, segmenter):
    segmenter.cn_segment_file(txt_file, seg_file, segmenter)




# segment all txts in source and place results in target dir
def txt2seg_dir(source_path, target_path, segmenter):
    for file in os.listdir(source_path):
        source_file = source_path + "/" + file
        target_file = target_path + "/" + file
        print "[txt2seg_dir]from %s to %s" % (source_file, target_file)

        #use seg() instead --YZ
        #segmenter.cn_segment_file(source_file, target_file)
        seg(source_file, target_file, segmenter)

    print "[txt2seg_dir]done"



# lang should be "cn"
def patent_txt2seg_dir(lang_path, language):
    segmenter = sdp.Segmenter()
    print "Allowing 10 seconds for segmenter to load stuff..."
    sleep(10)
    
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
