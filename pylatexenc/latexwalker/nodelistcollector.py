
class LatexNodeListCollector(object):
    r"""
    .. versionadded:: 3.0

       The `LatexNodeListCollector` class was added in `pylatexenc 3`.
    """
    def __init__(self, tokenreader, w):

        self._tokenreader = tokenreader
        self._w = w

        self._token_stream_pos = 0
        self._new_node_pos = 0

        self._nodelist = []
        self._pending_chars = ''

    def get_nodelist(self):
        # push final chars 
        if self._pending_chars:
            ......
        return self._nodelist

    def next_token(self):
        tok, p, l = self.w.get_token(self.pos)
        self._token_stream_pos = p + l
        return tok

    def next_node(self):
        

    ...
