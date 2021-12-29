
from ._std import LatexGeneralNodesParser, LatexSingleNodeParser


class LatexOptionalCharsMarkerParser(object):
    
    def __init__(self,
                 chars,
                 following_arg_parser=None,
                 include_chars_node_before_following_arg=True,
                 return_none_instead_of_empty=False,
                 **kwargs):
        super(LatexOptionalCharMarker, self).__init__(**kwargs)

        self.chars = " ".join(chars.strip().split())
        self.following_arg_parser = following_arg_parser
        self.include_chars_node_before_following_arg = \
            include_chars_node_before_following_arg
        self.return_none_instead_of_empty = return_none_instead_of_empty

        if not self.chars:
            raise ValueError(("Invalid chars={!r}, needs to be non-empty "
                              "string (after stripping whitespce)").format(chars))

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        orig_pos_tok = token_reader.peek_token()
        pos_end = None
        read_s = ''
        match_found = False
        try:
            while True:
                tok = token_reader.next_token()
                if tok.tok != 'char':
                    break
                if read_s and tok.pre_space:
                    read_s += " "
                read_s += tok.arg
                if read_s == self.chars:
                    match_found = True
                    pos_end = tok.pos+tok.len
                    break
                if not self.chars.startswith(read_s):
                    # mismatched at this point, will not match
                    break

        finally:
            if not match_found:
                token_reader.move_to_token(orig_pos_tok)
        
        if not match_found:
            # chars marker is simply not present.
            if self.return_none_instead_of_empty:
                return None, None
            return LatexNodeList([]), None

        nodes = []
        if self.include_chars_node_before_following_arg:
            nodes += [
                latex_walker.make_node(
                    LatexCharsNode,
                    parsing_state=parsing_state,
                    chars=self.chars,
                    pos=orig_pos_tok.pos,
                    len=pos_end-orig_pos_tok.pos,
                )
            ]

        carryover_info = None

        if self.following_arg_parser is not None:
            following_nodes, carryover_info = latex_walker.parse_content(
                self.following_arg_parser,
                token_reader=token_reader,
                parsing_state=parsing_state,
            )

            nodes += following_nodes

        nodes = LatexNodeList(nodes)

        return nodes, carryover_info
        
