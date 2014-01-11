
import sys, codecs, StringIO


(cn_comma, cn_period) = (u'\uff0c', u'\u3002')
(tab, cr, lf) = ("\t", "\n", "\f")

default_split_chars = ['.', '!', '?']
chinese_split_chars = [',', '.', ':', ';', '!', '?']
chinese_split_chars = [cn_comma, cn_period]


class Splitter(object):

    def __init__(self, language='ENGLISH'):
        self.language = language
        self.set_split_chars()
        
    def set_split_chars(self):
        self.split_chars = default_split_chars
        if self.language == 'CHINESE':
            self.split_chars = chinese_split_chars

    def change_language(self, language):
        self.language = language
        self.set_split_chars()


    def split(self, text):

        """Split a text, taking into account the language it is in. Simply scans
        for split characters, using two different sets, one for Chinese and one
        for English and German, the latter is actually the default. Always
        splits on end of line punctuation marks, tabs and sequences of line
        feeds and carriage returns longer than one."""

        def end_sentence(collected):
            collected['fragments'].append(''.join(collected['sentence']).strip())
            collected['sentence'] = []
            collected['splits'] += 1

        collected = { 'fragments': [], 'sentence': [], 'splits': 0 }
        crlf = 0
        for c in text:
            if crlf > 1:
                end_sentence(collected)
                crlf = 0
            collected['sentence'].append(c)
            if c in self.split_chars or c == tab or c == ',':
                end_sentence(collected)
            crlf = crlf + 1 if c in (cr, lf) else 0
        if collected['sentence']:
            end_sentence(collected)
        collected['fragments'] = [f for f in collected['fragments'] if f]
        return collected['fragments']


    def split_cn(self, text):

        """A special split command for Chinese only. It is a rather simplistic
        version that first normalizes all whitespace with single \n characters
        and then splits on the Chinese period only, not using the \n character
        as an EOL marker.

        This method is intended to keep as much together as possible, contrary
        to split(), which is aggressive in splitting, most notably by using
        white space (tabs for example) as an excuse to split, thereby splitting
        up many sentences."""

        fh = StringIO.StringIO()
        text = text.strip()
        # this normalizes all whitespace, used to get rid of linefeeds and other crap
        text = "\n".join(text.split())
        length = len(text)
        for i in range(length):
            c = text[i]
            if c == cn_period:
                fh.write(c + u"\n")
            elif c == cr:
                pass
            else:
                fh.write(c)
        return_string = fh.getvalue()
        fh.close()
        return return_string


def test_en():
    splitter = Splitter('ENGLISH')
    print '-' * 100
    for s in ("end of line. new line ",
              "before tab \t after tab",
              "before whitelines \n\f\n\n after whitelines"):
        print repr(s), '==>', splitter.split(s)
    print '-' * 100

def test_cn():
    splitter = Splitter('CHINESE')
    fh_in = codecs.open('examples/CN1159155A-short.txt', encoding='utf-8')
    text_in = fh_in.read()
    print "\n>>>> SPLITTING:"
    print text_in.strip()
    print "\n>>> RESULT split_cn()"
    text_out = splitter.split_cn(text_in)
    #print len(text_in), '-->', len(text_out)
    print text_out
    print "\n>>> RESULT split()"
    for f in splitter.split(text_in):
        print f


if __name__ == '__main__':
    #test_en()
    test_cn()

