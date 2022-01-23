
from __future__ import print_function, unicode_literals





# ------------------------------------------------------------------------------

class LatexParserBase(object):
    def __init__(self):
        super(LatexParserBase, self).__init__()

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):
        raise RuntimeError("LatexParserBase subclasses must reimplement __call__()")



