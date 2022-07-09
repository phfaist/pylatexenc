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

import logging
logger = logging.getLogger(__name__)

from .._exctypes import *
from .. import nodes
from .._parsingstatedelta import (
    ParsingStateDeltaEnterMathMode,
    get_updated_parsing_state_from_delta,
)

from ._delimited import (
    LatexDelimitedExpressionParserInfo,
    LatexDelimitedExpressionParser,
)



# for Py3
_basestring = str

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _basestring = basestring
### END_PYTHON2_SUPPORT_CODE





class LatexMathParserInfo(LatexDelimitedExpressionParserInfo):
    r"""
    Reimplementation of the :py:class:`LatexDelimitedExpressionParserInfo` class
    for math environments, for :py:class:`LatexMathParser`.
    """

    @classmethod
    def is_opening_delimiter(cls, delimiters, first_token, group_parsing_state,
                             delimited_expression_parser, latex_walker, **kwargs):

        if first_token.tok not in ('mathmode_inline', 'mathmode_display'):
            return False

        if not cls.check_opening_delimiter(
                delimiters=delimiters,
                parsed_opening_delimiter=first_token.arg,
                latex_walker=latex_walker
        ):
            return False

        return True

    @classmethod
    def get_acceptable_open_delimiter_list(cls, delimiters, group_parsing_state,
                                           delimited_expression_parser, latex_walker,
                                           **kwargs):
        if delimiters is not None:
            if isinstance(delimiters, _basestring):
                return [delimiters]
            else:
                return [delimiters[0]]
            
        return [
            od
            for (od, cd) in (
                    group_parsing_state.latex_inline_math_delimiters
                    + group_parsing_state.latex_display_math_delimiters
            )
        ]


    # ---

    def initialize(self):
        # set up all the relevant fields manually:

        self.math_mode_type = self.first_token.tok
        self.math_mode_delimiter = self.first_token.arg

        # enter math mode !
        self.math_parsing_state = get_updated_parsing_state_from_delta(
            self.parsing_state,
            ParsingStateDeltaEnterMathMode(
                math_mode_delimiter=self.math_mode_delimiter,
                trigger_token=self.first_token
            ),
            self.latex_walker,
        )

        self.contents_parsing_state = self.math_parsing_state
        self.parsed_delimiters = self.get_parsed_delimiters()

    def stop_token_condition(self, token):
        if token.tok == self.math_mode_type and token.arg == self.parsed_delimiters[1]:
            return True
        return False

    def get_matching_delimiter(self, opening_delimiter):
        return self.math_parsing_state._math_expecting_close_delim_info['close_delim']


    def make_group_node_and_parsing_state_delta(self, latex_walker, token_reader,
                                                nodelist, parsing_state_delta):

        # As for the delimited group parser, use cur_pos() so that it includes
        # the closing math mode delimiter.
        pos_end = token_reader.cur_pos()

        # note that nodelist can be None in case of a parse error

        if self.math_mode_type == 'mathmode_inline':
            displaytype = 'inline'
        elif self.math_mode_type == 'mathmode_display':
            displaytype = 'display'
        else:
            displaytype = '<unknown>'

        math_node = latex_walker.make_node(
            nodes.LatexMathNode,
            displaytype=displaytype,
            nodelist=nodelist,
            parsing_state=self.parsing_state,
            delimiters=self.parsed_delimiters,
            pos=self.first_token.pos,
            pos_end=pos_end,
        )

        return math_node, parsing_state_delta


# ------------------------------------------------------------------------------

class LatexMathParser(LatexDelimitedExpressionParser):
    def __init__(self,
                 math_mode_delimiters,
                 **kwargs):
        super(LatexMathParser, self).__init__(
            delimiters=math_mode_delimiters,
            discard_parsing_state_delta=False,
            delimited_expression_parser_info_class=LatexMathParserInfo,
            **kwargs
        )
