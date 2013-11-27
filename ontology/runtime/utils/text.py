import sys


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

