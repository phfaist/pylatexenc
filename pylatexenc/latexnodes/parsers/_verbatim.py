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
from ..nodes import *

from ._base import LatexParserBase


class LatexVerbatimBaseParser(LatexParserBase):
    r"""
    Note: this parser requires the token reader to provide character-level
    access to the input string.
    """
    
    def __init__(self, **kwargs):
        super(LatexVerbatimBaseParser, self).__init__(**kwargs)

    class VerbatimInfo(object):
        def __init__(self):
            super(LatexVerbatimBaseParser.VerbatimInfo, self).__init__()
            self.parsed_delimiters = (None, None)

    def new_char_check_stop_condition(self, char, verbatim_string, verbatim_info,
                                      parsing_state):
        r"""
        The default implementation in this base class is to read a single verbatim
        char.  Reimplement this method in a subclass for more advanced behavior.
        """
        if verbatim_string:
            return True # or dict like { 'put_back_char': True }
        return False

    def error_end_of_stream(self, pos, recovery_nodes, latex_walker, verbatim_info):
        raise LatexWalkerNodesParseError(
            msg="End of stream reached while reading verbatim content",
            pos=pos,
            recovery_nodes=recovery_nodes,
            error_type_info={
                'what': 'verbatim_unexpected_end_of_stream',
                'verbatim_delimiters': verbatim_info.parsed_delimiters,
            },
        )
        

    def finalize_verbatim_string(self, verbatim_string, verbatim_info):
        r"""
        Return the string to include in the verbatim chars node.

        Also, this method should assign the fields `pos_start` and `pos_end` in
        `verbatim_info` to set the start and the end positions of the node.
        """
        verbatim_info.pos_start = verbatim_info.content_pos_start
        verbatim_info.pos_end = verbatim_info.content_pos_start + len(verbatim_string)
        return verbatim_string


    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):

        verbatim_info = LatexVerbatimBaseParser.VerbatimInfo()
        verbatim_info.original_pos = token_reader.cur_pos()

        return self.read_verbatim_content(latex_walker, token_reader, parsing_state,
                                          verbatim_info=verbatim_info, **kwargs)


    def read_verbatim_content(self, latex_walker, token_reader, parsing_state,
                              verbatim_info, **kwargs):
        r"""
        Doc ...........
        
        The `token_reader` is left *after* the character that caused the
        processing to stop.
        """

        verbatim_string = ''
        stop_condition_met = False

        ended_with_eos = False
        
        verbatim_info.content_pos_start = token_reader.cur_pos()

        while not stop_condition_met:
            try:
                char = token_reader.next_chars(1, parsing_state=parsing_state)
            except LatexWalkerEndOfStream:
                char = None
                ended_with_eos = True

            stopinfo = \
                self.new_char_check_stop_condition(char, verbatim_string, verbatim_info,
                                                   parsing_state)
            if stopinfo:
                # stop condition met
                stop_condition_met = True
                if stopinfo is not True and char is not None and stopinfo['put_back_char']:
                    token_reader.move_to_pos_chars( token_reader.cur_pos() - 1 )
            else:
                if char is None:
                    break
                verbatim_string += char


        verbatim_string = \
            self.finalize_verbatim_string(verbatim_string, verbatim_info)

        pos_start = verbatim_info.pos_start
        pos_end = verbatim_info.pos_end

        nodes = latex_walker.make_node(
            LatexCharsNode,
            chars=verbatim_string,
            pos=pos_start,
            pos_end=pos_end,
            parsing_state=parsing_state,
        )

        if not stop_condition_met and ended_with_eos:
            return self.error_end_of_stream( pos=pos_end,
                                             recovery_nodes=nodes,
                                             latex_walker=latex_walker,
                                             verbatim_info=verbatim_info )
        
        return nodes, None



class LatexDelimitedVerbatimParser(LatexVerbatimBaseParser):
    r"""
    Parse verbatim content specified between token delimiters (e.g.,
    ``\verb|...|``).

    Doc..................
    """

    def __init__(self,
                 delimiters=None,
                 auto_delimiters=None,
                 **kwargs):
        super(LatexDelimitedVerbatimParser, self).__init__(**kwargs)

        self.delimiters = delimiters

        if auto_delimiters is not None:
            self.auto_delimiters = dict(auto_delimiters)
        else:
            self.auto_delimiters = {
                '{': '}',
                '[': ']',
                '<': '>',
                '(': ')',
            }

        self.depth_counter = 1

        # will be determined upon encountering the open delimiter
        self.parsed_delimiters = None


    def new_char_check_stop_condition(self, char, verbatim_string, verbatim_info,
                                      parsing_state):
        r"""
        The default implementation in this base class is to read a single verbatim
        char.  Reimplement this method in a subclass for more advanced behavior.
        """
        if char is None:
            return False

        if char == verbatim_info.parsed_delimiters[1]:
            # closing delimiter
            self.depth_counter -= 1
            if self.depth_counter <= 0:
                # final closing delimiter
                return True
        elif char == verbatim_info.parsed_delimiters[0]:
            # opening delimiter, if not the same as the closing delimiter
            self.depth_counter += 1

        return False


    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        verbatim_info = LatexVerbatimBaseParser.VerbatimInfo()

        token_reader.skip_space_chars(parsing_state)

        verbatim_info.original_pos = token_reader.cur_pos()

        if self.delimiters is None:
            # read the delimiter character

            open_delim_char = token_reader.next_chars(1, parsing_state=parsing_state)
            
            close_delim_char = self.auto_delimiters.get(open_delim_char, open_delim_char)

            verbatim_info.parsed_delimiters = (open_delim_char, close_delim_char)

        else:
            
            verbatim_info.parsed_delimiters = self.delimiters

            first_char = token_reader.next_chars(1, parsing_state=parsing_state)
            if first_char != verbatim_info.parsed_delimiters[0]:
                raise LatexWalkerParseError(
                    msg="Expected opening delimiter ‘{}’ for verbatim content".format(
                        verbatim_info.parsed_delimiters[0]
                    ),
                    pos=pos,
                    error_type_info={
                        'what': 'verbatim_expected_opening_delimiter_not_found',
                        'expected_delimiters': verbatim_info.parsed_delimiters,
                    },
                )
            
        verbatim_node, _ = \
            self.read_verbatim_content(latex_walker, token_reader, parsing_state,
                                       verbatim_info=verbatim_info, **kwargs)

        nodes = latex_walker.make_node(
            LatexGroupNode,
            delimiters=verbatim_info.parsed_delimiters,
            nodelist=latex_walker.make_nodelist(
                [ verbatim_node ],
                parsing_state=parsing_state,
            ),
            pos=verbatim_info.original_pos,
            pos_end=verbatim_node.pos_end + len(verbatim_info.parsed_delimiters[1]),
            parsing_state=parsing_state
        )

        return nodes, None



class LatexVerbatimEnvironmentContentsParser(LatexVerbatimBaseParser):
    r"""
    Parse verbatim content given as an environment body contents.

    Doc.......................
    """
    def __init__(self, environment_name='verbatim', **kwargs):
        super(LatexVerbatimEnvironmentContentsParser, self).__init__(**kwargs)
        self.environment_name = environment_name

    def new_char_check_stop_condition(self, char, verbatim_string, verbatim_info,
                                      parsing_state):

        if verbatim_string.endswith( verbatim_info.end_environment_code ):
            return {'put_back_char': True}
        return False

    def finalize_verbatim_string(self, verbatim_string, verbatim_info):

        end_environment_code = verbatim_info.end_environment_code
        assert( verbatim_string.endswith(end_environment_code) )

        verbatim_string = verbatim_string[:-len(end_environment_code)]

        pos_start = verbatim_info.original_pos

        if verbatim_string.startswith('\n'):
            # gobble a single newline at the beginning of the verbatim content,
            # i.e., the newline that immediately follows \begin{verbatim}
            verbatim_string = verbatim_string[1:]
            pos_start += 1

        verbatim_info.pos_start = pos_start
        verbatim_info.pos_end = pos_start + len(verbatim_string)
        return verbatim_string

    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):

        verbatim_info = LatexVerbatimBaseParser.VerbatimInfo()
        verbatim_info.original_pos = token_reader.cur_pos()

        verbatim_info.end_environment_code = \
            parsing_state.macro_escape_char + 'end{'+self.environment_name+'}'


        verbatim_chars_node, _ = \
            self.read_verbatim_content(latex_walker, token_reader, parsing_state,
                                       verbatim_info, **kwargs)

        nodes = latex_walker.make_nodelist(
            [ verbatim_chars_node ],
            parsing_state=parsing_state,
        )

        # the pos_end of the environment node itself will use the current
        # token_reader position, which is set correctly at this point.

        return nodes, None
