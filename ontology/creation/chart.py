
class ChartToken:
    def __init__(self, token, pos, col):
        self.token = token
        self.col = col
        self.pos = pos
        self.chunk = ""
        self.l_chunk = []
        self.chunk_type = ""
        self.start = col
        self.end = col
        self.lc1 = ""
        self.lc2 = ""
        self.lc3 = ""
        self.rc1 = ""

class Chart:

    def init(self, tagged_sent):
        self.tokens = []
        self.len = len(tagged_sent)
        col = 0
        for word in tagged_sent:
            (token, pos) = word.split("/")
            ctoken = ChartToken(token, pos, col)
            self.tokens.append(ctoken)
            col += 1

class FieldDoc:
    
    def __init__(self, file):
        s_doc = open(file, "r")
        
        s_doc.close()
    
