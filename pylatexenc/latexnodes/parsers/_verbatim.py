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


from .._exctypes import *
from .._nodetypes import *

from ._base import LatexParserBase


class LatexVerbatimBaseParser(LatexParserBase):
    r"""
    Note: this parser requires the token reader to provide character-level
    access to the input string.
    """
    
    def __init__(self, **kwargs):
        super(LatexVerbatimParser, self).__init__(**kwargs)

    def new_char_check_stop_condition(self, char, verbatim_string):
        r"""
        The default implementation in this base class is to read a single verbatim
        char.  Reimplement this method in a subclass for more advanced behavior.
        """
        if verbatim_string:
            return True
        return False

    def error_end_of_stream(self, pos, recovery_nodes, latex_walker):
        raise LatexWalkerNodesParseError(
            msg="End of stream reached while reading verbatim content",
            pos=pos,
            recovery_nodes=recovery_nodes
        )
        

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        return self.read_verbatim_content(latex_walker, token_reader, parsing_state, **kwargs)


    def read_verbatim_content(self, latex_walker, token_reader, parsing_state, **kwargs):
        r"""
        ....
        
        The `token_reader` is left *after* the character that caused the
        processing to stop.
        """

        verbatim_string = ''
        stop_condition_met = False

        orig_pos = token_reader.cur_pos()

        ended_with_eos = False

        try:
            while not stop_condition_met:
                char = token_readers.next_chars(1, parsing_state=parsing_state)

                if self.new_char_check_stop_condition(char, verbatim_string):
                    # stop condition met
                    stop_condition_met = True
                else:
                    verbatim_string += char

        except LatexWalkerEndOfStream:
            ended_with_eos = True

        pos_end = token_reader.cur_pos()
        nodes = latex_walker.make_node(
            LatexCharsNode,
            chars=verbatim_string,
            pos=orig_pos,
            pos_end=pos_end,
            parsing_state=parsing_state,
        )

        if ended_with_eos:
            return self.error_end_of_stream( pos=pos_end,
                                             recovery_nodes=nodes,
                                             latex_walker=latex_walker )
        
        return nodes, None



class LatexVerbatimDelimParser(LatexVerbatimBaseParser):
    def __init__(self,
                 delimiter_chars=None,
                 auto_delimiter_chars=None,
                 **kwargs):
        super(LatexVerbatimDelimParser, self).__init__(**kwargs)

        self.delimiter_chars = delimiter_chars

        if auto_delimiter_chars is not None:
            self.auto_delimiter_chars = dict(auto_delimiter_chars)
        else:
            self.auto_delimiter_chars = {
                '{': '}',
                '[': ']',
                '<': '>',
                '(': ')',
            }

        self.depth_counter = 1


    def new_char_check_stop_condition(self, char, verbatim_string):
        r"""
        The default implementation in this base class is to read a single verbatim
        char.  Reimplement this method in a subclass for more advanced behavior.
        """
        if char == self.delimiter_chars[1]:
            # closing delimiter
            self.depth_counter -= 1
            if self.depth_counter <= 0:
                # final closing delimiter
                return True
        elif char == self.delimiter_chars[0]:
            # opening delimiter, if not the same as the closing delimiter
            self.depth_counter += 1

        return False


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        token_reader.skip_space_chars()

        orig_pos = token_reader.cur_pos()

        if self.delimiter_chars is None:
            # read the delimiter character

            open_delim_char = token_reader.next_chars(1, parsing_state=parsing_state)
            
            close_delim_char = self.auto_delimiter_chars.get(open_delim_char, open_delim_char)

            self.delimiter_chars = (open_delim_char, close_delim_char)

        else:

            first_char = token_reader.next_chars(1, parsing_state=parsing_state)
            if first_char != self.delimiter_chars[0]:
                raise LatexWalkerParseError(
                    msg="Expected opening delimiter ‘{}’ for verbatim content".format(
                        self.delimiter_chars[0]
                    ),
                    pos=pos,
                )
            
        verbatim_node, _ = \
            self.read_verbatim_content(latex_walker, token_reader, parsing_state, **kwargs)

        nodes = latex_walker.make_node(
            LatexGroupNode,
            delimiters=self.delimiter_chars,
            nodelist=LatexNodeList(verbatim_node),
            pos=orig_pos,
            pos_end=verbatim_node.pos_end + 1, # +1 for closing delimiter
            parsing_state=parsing_state
        )

        return nodes, None



# class LatexVerbatimEnvironmentParser(LatexVerbatimBaseParser):
#     def __init__(self,
#                  environment_name=None,
#                  **kwargs):
#         super(LatexVerbatimDelimParser, self).__init__(**kwargs)

#     ........................

#     # TODO
