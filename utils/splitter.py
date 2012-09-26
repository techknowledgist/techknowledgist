
import codecs

default_split_chars = ['.', '!', '?']
chinese_split_chars = [',', '.', ':', ';', '!', '?']
chinese_split_chars = [u'\uff0c', u'\u3002'] # comma and period

(tab, cr, lf) = ("\t", "\n", "\f")


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

        """Split a text, taking into account the language it is in. Simply scans for split
        characters, using two different sets, one for Chinese and one for English and
        German, the latter is actually the default. Always splits on end of line
        punctuation marks, tabs and sequences of line feeds and carriage returns longer than
        one. For Chinese, also splits on spaces and some other punctuation marks."""

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


if __name__ == '__main__':

    splitter = Splitter('ENGLISH')
    print '-' * 100
    for s in ("end of line. new line ",
              "before tab \t after tab",
              "before whitelines \n\f\n\n after whitelines"):
        print repr(s), '==>', splitter.split(s)
    print '-' * 100

    # run the script from this directory to make this work
    splitter.change_language('CHINESE')
    for l in codecs.open('examples/CN1159155A-short.txt', encoding='utf-8'):
        if not l.strip():
            continue
        print '[', l.strip(), ']'
        fragments = splitter.split(l)
        for f in fragments: print '  ', f
        print '-' * 100

