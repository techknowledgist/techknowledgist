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
        self.children = []
        self.all_nodes = []
        self.start = 0
        self.end = sys.maxint
        self.label = 'TOP'
        if section is not None:
            self.start = section[0]
            self.end = section[1]
            self.label = section[2]

    def __str__(self):
        return "<DocNode %d-%d %s %d>" \
               % (self.start, self.end, self.label, len(self.children))

    def add_element(self, section):
        if not self.children:
            # adding to an empty children list
            self.children.append(DocNode(section))
        else:
            # if there are children, then determine whether to append to the
            # current child list or to add to the last child.
            last = self.children[-1]
            if last.start <= section[0] and last.end >= section[1]:
                last.add_element(section)
            else:
                self.children.append(DocNode(section))

    def get_nodes(self, result=None):
        if result is None:
            result = []
        result.append(self)
        for e in self.children:
            e.get_nodes(result)
        return result

    def pp(self, indent=''):
        print "%s%s %s %s" % (indent, self.label, self.start, self.end)
        for e in self.children:
            e.pp(indent+'   ')


class TopNode(DocNode):

    def __init__(self):
        self.title = None
        self.abstract = None
        self.summary = None
        self.claims = None
        DocNode.__init__(self)

    def __str__(self):
        top_str = "<TopNode> %d-%d>\n" % (self.start, self.end)
        title_str = "  title    = %s\n" % self.title
        abstr_str = "  abstract = %s\n" % self.abstract
        summa_str = "  summary  = %s\n" % self.summary
        claim_str = "  claims   = %s\n" % self.claims
        return top_str + title_str + abstr_str + summa_str + claim_str

    def index(self):
        self.all_nodes = self.get_nodes()
        for node in self.all_nodes:
            if node.label == 'TITLE': self.title = node
            elif node.label == 'ABSTRACT': self.abstract = node
            elif node.label == 'SUMMARY': self.summary = node
            elif node.label == 'CLAIMS': self.claims = node


def build_section_list(fact_file, section_types):
    """Build a sorted list of sections from the contents of the fact file, using
    on ly th especified section types. A section is a triple of a start offset,
    end offset and section type."""
    sections = []
    for line in open(fact_file):
        fields = line.split()
        if fields[0] == 'STRUCTURE':
            fclass, ftype, start, end = parse_fact_line(fields)
            if ftype in section_types:
                sections.append((start, end, ftype))
    sections.sort()
    return sections


def build_section_tree(sections):
    """Build a tree of DocNodes from the list of sections. Each section is a
    triple of start offset, end offset and type."""
    tree = TopNode()
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

    """Simplistic chunker that uses a few sets of closed classes to identify
    items that are not in a chunk. It assumes that any sequency of non-function
    words and non-punctuation marks is a chunk. Use the chunker as follows:

    >>> text = u'a unicode string to be chunked.'
    >>> text = text.lower()
    >>> sentences = splitter.split(text)
    >>> chunker.chunk(sentences, len(text))
    >>> return chunker.get_chunks()

    In the case above, only the chunks are returned, ignoring all tokens outside
    of chunks. Access the chunked_sentences instance variable to get all the
    results."""

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

    MD = [u'can', u'may', u'must', u'will', u'would']

    RP = [u'down', u'in', u'off', u'on', u'out', u'over']

    TO = [u'to']

    RB = [u'about', u'accordingly', u'accurately', u'additionally',
          u'adjustably', u'aesthetically', u'afterwards', u'again', u'also',
          u'alternately', u'alternatively', u'apart', u'arbitrarily',
          u'arcuately', u'as', u'audibly', u'automatically', u'autonomously',
          u'away', u'back', u'better', u'chemically', u'circumferentially',
          u'closely', u'commonly', u'communicatively', u'completely',
          u'conductively', u'consequently', u'considerably', u'constantly',
          u'continually', u'conveniently', u'conversely', u'detachably',
          u'digitally', u'directionally', u'directly', u'dramatically',
          u'easily', u'either', u'electrically', u'electrochemically',
          u'entirely', u'especially', u'essentially', u'even', u'exclusively',
          u'exponentially', u'finally', u'financially', u'first', u'fixedly',
          u'forward', u'freely', u'fully', u'further', u'furthermore',
          u'generally', u'hence', u'herein', u'highly', u'however',
          u'immovably', u'indeed', u'independently', u'individually',
          u'initially', u'instead', u'integrally', u'inwardly', u'longer',
          u'magnetically', u'manually', u'moreover', u'mutually', u'namely',
          u'naturally', u'no', u'normally', u'not', u'off', u'olefinically',
          u'once', u'only', u'operatively', u'optically', u'optionally',
          u'outwardly', u'partially', u'particularly', u'pharmaceutically',
          u'photolithographically', u'pivotably', u'pivotally', u'positively',
          u'preferably', u'presently', u'prior', u'quantitatively', u'radially',
          u'randomly', u'rather', u'readily', u'regardless', u'removably',
          u'repeatedly', u'replaceably', u'respectively', u'rigidly',
          u'rotatably', u'second', u'selectively', u'sequentially', u'serially',
          u'seriously', u'side-by-side', u'simultaneously', u'so',
          u'spectroscopically', u'still', u'subsequently', u'substantially',
          u'then', u'thereafter', u'thereby', u'therefor', u'therefore',
          u'therefrom', u'therein', u'thereof', u'thereto', u'thus', u'tightly',
          u'together', u'too', u'twice', u'two-to-one', u'uniformly',
          u'uniquely', u'up', u'upwardly', u'usefully', u'variously', u'versa',
          u'vertically', u'very', u'visibly', u'well', u'wholly']

    WRB = [u'when', u'whenever', u'where', u'whereby', u'wherein']

    # other words that never occur inside a chunk
    NIC = [u'be', u'is', u'are', u'which', u'then', u'has', u'have', u'',
           u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', 
           u'', u'', u'', u'', u'', u'', u'', u'', u''  ]
    
    PUNCT = ['.', '?', '!', ',', ':', ';']

    def __init__(self):
        self.CC = dict.fromkeys(Chunker.CC, True)
        self.DT = dict.fromkeys(Chunker.DT, True)
        self.IN = dict.fromkeys(Chunker.IN, True)
        self.RP = dict.fromkeys(Chunker.RP, True)
        self.TO = dict.fromkeys(Chunker.TO, True)
        self.WRB = dict.fromkeys(Chunker.WRB, True)
        self.MD = dict.fromkeys(Chunker.MD, True)
        self.RB = dict.fromkeys(Chunker.RB, True)
        self.NIC = dict.fromkeys(Chunker.NIC, True)
        self.PUNCT = dict.fromkeys(Chunker.PUNCT, True)
        self.chunked_sentences = []

    def chunk(self, sentences, text_size=None):
        """Chunk the list of sentences and put the results into the
        chunked_sentences instance variable. A text_size can be handed in for
        debugging and benchmarking purposes."""
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
            # determiners are not in chunk (may want to change this to make them
            # the first element
            elif t in self.DT:
                self._add_to_current_sentence(t)
            # other function words not in chunks
            elif t in self.CC or t in self.IN or t in self.RP or t in self.TO \
                 or t in self.WRB:
                self._add_to_current_sentence(t)
            # some non-function words that do not occur in chunks
            elif t in self.MD or t in self.RB or t in self.NIC:
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

