import sys, types



def parse_fact_line(fields):
    """Retrieve the type, start and end features from a fact file line."""
    fact_class = fields.pop(0)
    fact_type, start, end = None, None, None
    for keyval in fields:
        try:
            key, val = keyval.split('=')
            val = val.strip('"')
            if key == 'TYPE': fact_type = val
            if key == 'START': start = int(val)
            if key == 'END': end = int(val)
        except ValueError:
            # this happens when more complicated fact lines have spaces in the
            # values, for example for title strings
            pass
    return (fact_class, fact_type, start, end)




class DocNode(object):

    """A DocNode is an element of a document structure tree. It can be build
    from a section triple with start offset, end offset and type. The label is
    TOP for the topnode and the section type for other nodes. Leaves have an
    empty self.elements list."""

    def __init__(self, section=None):
        self.elements = []
        self.start = 0
        self.end = sys.maxint
        self.label = 'TOP'
        if section is not None:
            self.start = section[0]
            self.end = section[1]
            self.label = section[2]

    def add_element(self, section):
        if not self.elements:
            self.elements.append(DocNode(section))
        else:
            last = self.elements[-1]
            if last.start <= section[0] and last.end >= section[1]:
                last.add_element(section)
            else:
                self.elements.append(DocNode(section))

    def pp(self, indent=''):
        print "%s%s %s %s" % (indent, self.label, self.start, self.end)
        for e in self.elements:
            e.pp(indent+'   ')


def build_section_tree(sections):
    """Build a tree of DocNodes from the list of sections. Each section is a
    triple of start offset, end offset and type."""
    tree = DocNode()
    for section in sections:
        tree.add_element(section)
    return tree



class SentenceSplitter(object):

    """Performs minimal tokenization by isolating periods, question marks,
    exclamation marks, colons, semi-colons and commas. Splits a text into
    sentences on the EOS markers."""

    def __init__(self):
        self.EOS = { '.': True, '?': True, '!': True }
        self.EOC = { ',': True, ':': True, ';': True }

    def split(self, text):
        self.sentences = []
        self.current_sentence = []
        for t in text.split():
            if t[-1] in self.EOS:
                self.current_sentence.append(t[:-1])
                self.current_sentence.append(t[-1])
                self.sentences.append(self.current_sentence)
                self.current_sentence = []
            elif t[-1] in self.EOC:
                self.current_sentence.append(t[:-1])
                self.current_sentence.append(t[-1])
            else:
                self.current_sentence.append(t)
        if self.current_sentence:
            self.sentences.append(self.current_sentence)
        return self.sentences


class Chunker(object):

    """Very simplistic chunker that uses a few sets of closed classes to
    identify items that are not in a chunk and that assumes that any sequency of
    non-function words and non-punctuation marks is a chunk."""

    CC = ['and', 'both', 'but', 'either', 'or']

    DT = [u'a', u'all', u'an', u'another', u'any', u'both', u'each', u'either',
          u'no', u'some', u'that', u'the', u'these', u'this', u'those']

    IN = [u'about', u'above', u'across', u'after', u'against', u'along',
          u'although', u'among', u'amongst', u'as', u'at', u'because',
          u'before', u'below', u'beneath', u'between', u'beyond', u'by',
          u'during', u'except', u'for', u'from', u'if', u'in', u'inside',
          u'into', u'near', u'next', u'of', u'off', u'on', u'onto', u'out',
          u'outside', u'over', u'per', u'since', u'so', u'than', u'that',
          u'though', u'through', u'toward', u'under', u'unless', u'until',
          u'up', u'upon', u'via', u'whether', u'while', u'with', u'within',
          u'without']

    RP = [u'down', u'in', u'off', u'on', u'out', u'over']

    TO = [u'to']

    # other words that never occur inside a chunk
    NIC = [u'is', u'are', u'which', u'then', u'has', u'have', u'', u'', ]
    
    PUNCT = ['.', '?', '!', ',', ':', ';']

    def __init__(self):
        self.CC = dict.fromkeys(Chunker.CC, True)
        self.DT = dict.fromkeys(Chunker.DT, True)
        self.IN = dict.fromkeys(Chunker.IN, True)
        self.RP = dict.fromkeys(Chunker.RP, True)
        self.TO = dict.fromkeys(Chunker.TO, True)
        self.NIC = dict.fromkeys(Chunker.NIC, True)
        self.PUNCT = dict.fromkeys(Chunker.PUNCT, True)
        self.chunked_sentences = []

    def chunk(self, sentences, text_size=None):
        self.text_size = text_size
        self.chunked_sentences = [self._chunk_sentence(s) for s in sentences]

    def get_chunks(self):
        """Returns a list of all the chunks in the chunked sentences list."""
        chunks = []
        for s in self.chunked_sentences:
            for c in s:
                if type(c) == types.ListType:
                    chunks.append(c)
        return chunks

    def pp_chunks(self):
        print "\n>>> TEXT len=%s" % str(self.text_size)
        for s in self.chunked_sentences:
            print
            for c in s:
                pstring = c if type(c) is types.UnicodeType else '['+' '.join(c)+']'
                print pstring

    def _chunk_sentence(self, sentence):
        self.chunked_sentence = []
        self.current_chunk = []
        for t in sentence:
            # stand-alone pucntuations are not in chunk
            if t in self.PUNCT:
                self._add_to_current_sentence(t)
            # determiners are not in chunk (may want to chane this to make them
            # the first element
            elif t in self.DT:
                self._add_to_current_sentence(t)
            # other function words not in chunks
            elif t in self.CC or t in self.IN or t in self.RP or t in self.TO:
                self._add_to_current_sentence(t)
            # add all others to the current chunk
            else:
                self.current_chunk.append(t)
        if self.current_chunk:
            self.chunked_sentence.append(self.current_chunk)
        return self.chunked_sentence

    def _add_to_current_sentence(self, t):
        if self.current_chunk:
            self.chunked_sentence.append(self.current_chunk)
            self.current_chunk = []
        self.chunked_sentence.append(t)


def chunk_text(text):
    splitter = SentenceSplitter()
    sentences = splitter.split(text)
    chunker = Chunker()
    chunker.chunk(sentences, len(text))
    #chunker.pp_chunks()
    return chunker.get_chunks()
