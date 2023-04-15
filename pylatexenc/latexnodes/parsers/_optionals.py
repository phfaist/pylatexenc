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
from ._delimited import (
    LatexDelimitedGroupParser,
)
from ..nodes import (
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
                 return_none_instead_of_empty=True,
                 allow_pre_space=True,
                 return_full_node_list=True,
                 **kwargs):
        super(LatexOptionalCharsMarkerParser, self).__init__(**kwargs)

        self.chars = " ".join(chars.strip().split())
        self.following_arg_parser = following_arg_parser
        self.include_chars_node_before_following_arg = \
            include_chars_node_before_following_arg
        self.return_none_instead_of_empty = return_none_instead_of_empty
        self.allow_pre_space = allow_pre_space
        self.return_full_node_list = return_full_node_list

        if not self.chars:
            raise ValueError(("Invalid chars={!r}, needs to be non-empty "
                              "string (after stripping whitespce)").format(chars))


    def contents_can_be_empty(self):
        return True

    def get_following_arg_parser(self, chars):
        return self.following_arg_parser

    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        def _return_none(pos):
            if self.return_none_instead_of_empty:
                return None, None
            emptynl = latex_walker.make_nodelist(
                [],
                pos=pos,
                pos_end=pos,
                parsing_state=parsing_state,
            )
            return emptynl, None

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
                    if len(first_token.pre_space) and not self.allow_pre_space:
                        # no pre-space allowed, the optional marker was not provided.
                        return _return_none(first_token.pos)
                if tok.tok != 'char':
                    break
                if read_s and len(tok.pre_space):
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
            return _return_none(orig_pos_tok.pos)

        following_arg_parser = self.get_following_arg_parser(read_s)

        nodes = []
        if (self.include_chars_node_before_following_arg or
            (following_arg_parser is None and not self.return_full_node_list)):
            nodes += [
                latex_walker.make_node(
                    LatexCharsNode,
                    parsing_state=parsing_state,
                    chars=self.chars,
                    pos=orig_pos_tok.pos,
                    pos_end=pos_end,
                )
            ]

        parsing_state_delta = None

        if following_arg_parser is not None:
            following_nodes, parsing_state_delta = latex_walker.parse_content(
                following_arg_parser,
                token_reader=token_reader,
                parsing_state=parsing_state,
            )

            if not self.return_full_node_list:
                return following_nodes, parsing_state_delta

            nodes += following_nodes

        else:
            if not self.return_full_node_list:
                return nodes[-1], parsing_state_delta

        nodes = latex_walker.make_nodelist(
            nodes, 
            parsing_state=parsing_state,
        )

        return nodes, parsing_state_delta
        
