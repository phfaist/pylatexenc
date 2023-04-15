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

from ..latexnodes._exctypes import *
#from ..latexnodes import nodes
from ..latexnodes import (
    get_updated_parsing_state_from_delta,
)
from ..latexnodes.parsers import (
    LatexDelimitedExpressionParserInfo,
    LatexDelimitedExpressionParser,
)



class LatexEnvironmentBodyContentsParserInfo(LatexDelimitedExpressionParserInfo):

    @classmethod
    def parse_initial(cls, delimiters, allow_pre_space,
                      latex_walker, token_reader, group_parsing_state,
                      delimited_expression_parser):
        # we're already parsing the contents of the environment, so the "initial
        # delimiter" \begin{environment} was already encountered and parsed
        return []

    # ---

    def initialize(self):
        # set up all the relevant fields manually

        #logger.debug("parsing_state=%r, group_parsing_state = %r",
        #             self.parsing_state, self.group_parsing_state)

        contents_parsing_state_delta = \
            self.delimited_expression_parser.get_contents_parsing_state_delta()

        self.contents_parsing_state = get_updated_parsing_state_from_delta(
            self.group_parsing_state,
            contents_parsing_state_delta,
            self.latex_walker,
        )
        #logger.debug("Contents state = %r, delta was = %r",
        #             self.contents_parsing_state, contents_parsing_state_delta)

        self.child_parsing_state_delta = \
            self.delimited_expression_parser.get_child_parsing_state_delta()

        self.parsed_delimiters = (
            "\\begin{}{}{}".format('{',self.delimited_expression_parser.environmentname,'}'),
            "\\end{}{}{}".format('{',self.delimited_expression_parser.environmentname,'}')
        )

        logger.debug(
            "initializing environment body contents delimited parser: environmentname=%r,"
            "parsing_state=%r, group_parsing_state=%r, contents_parsing_state=%r",
            self.delimited_expression_parser.environmentname,
            self.parsing_state,
            self.group_parsing_state,
            self.contents_parsing_state,
        )

    def get_open_context_description(self):
        # don't report an open context for the body contents, we already have an
        # open context for the body node itself
        return None

    def stop_token_condition(self, token):
        if token.tok == 'end_environment' \
           and token.arg == self.delimited_expression_parser.environmentname:
            return True
        return False

    # Note: The default handle_stop_token_condition handler will move past the
    # end environment token.


    def make_group_node_and_parsing_state_delta(self, latex_walker, token_reader,
                                                nodelist, parsing_state_delta):

        if nodelist is None:
            logger.warning("environment body contents parser: parsed nodelist is None")
            nodelist = latex_walker.make_nodelist(
                nodelist=[],
                parsing_state=self.contents_parsing_state
            )

        # just return the LatexNodeList instance
        return nodelist, parsing_state_delta


# ------------------------------------------------------------------------------

class LatexEnvironmentBodyContentsParser(LatexDelimitedExpressionParser):
    r"""
    Parse an environment body, up to a final ``\end{environmentname}``.

    Use can use the `contents_parsing_state_delta` to influence the parsing
    state used to parse the environment body contents.

    You can also use `child_parsing_state_delta` to influence the parsing state
    used for children encountered in the main body contents.  The child parsing
    state delta is always applied onto the main original parsing state, not onto
    the contents parsing state.

    Either of `contents_parsing_state_delta` and `child_parsing_state_delta` is
    `None`, then the corresponding parsing state is taken to be the main parent
    parsing state.

    You can achieve an effect of locally applying a different parsing state for
    the immediate children of the body contents but not further/deeper children
    by setting `contents_parsing_state_delta` while keeping
    `child_parsing_state_delta=None`.  The rationale to do this is to locally
    enable commands that are meant to provide information about or otherwise
    directly relate to that environment, say, ``\label`` or ``\item``, without
    those commands being active in any further children.  For instance, you can
    achieve the following behavior:

    .. code: latex
    
        % failure, \item command unknown
        \item{...}

        % ok if {enumerate} was defined using the present parser with a content
        % parsing state delta that defines '\item'
        \begin{enumerate}
        \item ...
        \item ...
        \end{enumerate}

        % failure for the inner \item, command unknown.
        \begin{enumerate}
        \item ... % this \item is ok
          \textbf{Hello \item{world}} % fail; \item forbidden within children
        \end{enumerate}
    """
    def __init__(self,
                 environmentname,
                 contents_parsing_state_delta=None,
                 child_parsing_state_delta=None,
                 discard_parsing_state_delta=True,
                 **kwargs):
        super(LatexEnvironmentBodyContentsParser, self).__init__(
            delimiters=None,
            discard_parsing_state_delta=discard_parsing_state_delta,
            delimited_expression_parser_info_class=LatexEnvironmentBodyContentsParserInfo,
            **kwargs
        )
        self.environmentname = environmentname
        self.contents_parsing_state_delta = contents_parsing_state_delta
        self.child_parsing_state_delta = child_parsing_state_delta

    def get_contents_parsing_state_delta(self):
        return self.contents_parsing_state_delta

    def get_child_parsing_state_delta(self):
        return self.child_parsing_state_delta

