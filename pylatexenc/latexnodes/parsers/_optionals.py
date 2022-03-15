# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2022 Philippe Faist
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


# Internal module. Internal API may move, disappear or otherwise change at any
# time and without notice.

from __future__ import print_function, unicode_literals


from ._base import LatexParserBase
from ._generalnodes import (
    LatexGeneralNodesParser, LatexDelimitedGroupParser, LatexSingleNodeParser
)
from ..nodes import (
    LatexNodeList,
    LatexCharsNode,
)




# ------------------------------------------------------------------------------



class LatexOptionalSquareBracketsParser(LatexDelimitedGroupParser):
    r"""
    A shorthand for reading an optional argument placed in square brackets.
    """
    def __init__(self, delimiters=('[',']'), optional=True, **kwargs):
        super(LatexOptionalSquareBracketsParser, self).__init__(
            delimiters=delimiters,
            optional=optional,
            **kwargs
        )




# ------------------------------------------------------------------------------

class LatexOptionalCharsMarkerParser(LatexParserBase):
    
    def __init__(self,
                 chars,
                 following_arg_parser=None,
                 include_chars_node_before_following_arg=True,
                 return_none_instead_of_empty=False,
                 allow_pre_space=True,
                 **kwargs):
        super(LatexOptionalCharsMarkerParser, self).__init__(**kwargs)

        self.chars = " ".join(chars.strip().split())
        self.following_arg_parser = following_arg_parser
        self.include_chars_node_before_following_arg = \
            include_chars_node_before_following_arg
        self.return_none_instead_of_empty = return_none_instead_of_empty
        self.allow_pre_space = allow_pre_space

        if not self.chars:
            raise ValueError(("Invalid chars={!r}, needs to be non-empty "
                              "string (after stripping whitespce)").format(chars))


    def contents_can_be_empty(self):
        return True


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        orig_pos_tok = token_reader.peek_token(parsing_state=parsing_state)
        pos_end = None
        read_s = ''
        match_found = False
        first_token = None
        try:
            while True:
                tok = token_reader.next_token(parsing_state=parsing_state)
                if first_token is None:
                    first_token = tok
                    if first_token.pre_space and not self.allow_pre_space:
                        # no pre-space allowed, the optional marker was not provided.
                        return None, None
                if tok.tok != 'char':
                    break
                if read_s and tok.pre_space:
                    read_s += " "
                read_s += tok.arg
                if read_s == self.chars:
                    match_found = True
                    pos_end = tok.pos_end
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
                    pos_end=pos_end,
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
        
