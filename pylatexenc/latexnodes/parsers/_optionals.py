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

from ._base import LatexParserBase
from ._delimited import (
    LatexDelimitedGroupParser,
)
from ._expression import LatexExpressionParser
from ..nodes import (
    LatexCharsNode,
    LatexGroupNode,
    LatexNodeList,
)
from .._parsingstatedelta import get_updated_parsing_state_from_delta



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
    r"""
    Doc. .................

    .. py::attribute: return_full_node_list

       Idea: if true, then return a list of nodes that accurately represent the
       nodes that were given as arguments, as they were parsed.  Otherwise,
       we'll attempt to return only a node that is the "target" of the argument
       (the following arg, if a following arg parser is non-None, or the chars
       node itself if the following arg parser is None).

       If `return_full_node_list` is `False`, then we should only have a single
       chars entry in `chars_list` or we need to set `max_num_args=1`.
    """
    
    def __init__(self,
                 chars_list,
                 following_arg_parser=None,
                 include_chars_node_before_following_arg=True,
                 return_none_instead_of_empty=True,
                 allow_pre_space=True,
                 return_full_node_list=True,
                 collect_chars_with_following_arg_as_delimited_group=False,
                 max_num_args=None,
                 **kwargs):
        super(LatexOptionalCharsMarkerParser, self).__init__(**kwargs)

        if isinstance(chars_list, str):
            # if a single string is provided, it is interpreted as a list of
            # individual chars.
            chars_list = [c for c in chars_list]

        self.chars_list = [ " ".join(chars.strip().split()) for chars in chars_list ]
        self.following_arg_parser = following_arg_parser
        self.include_chars_node_before_following_arg = \
            include_chars_node_before_following_arg
        self.return_none_instead_of_empty = return_none_instead_of_empty
        self.allow_pre_space = allow_pre_space
        self.return_full_node_list = return_full_node_list
        self.collect_chars_with_following_arg_as_delimited_group = \
            collect_chars_with_following_arg_as_delimited_group
        self.max_num_args = max_num_args

        if not self.chars_list:
            raise ValueError(("Invalid chars={!r}, needs to be non-empty "
                              "string (after stripping whitespce)").format(chars))

        if (not self.return_full_node_list and
            not (len(self.chars_list) == 1 or self.max_num_args <= 1)
            ):
            raise ValueError("Cannot set return_full_node_list=False if we can have "
                             "multiple given chars marker options "
                             "(len(chars_list) > 1 and max_num_args != 1)")

        if not self.return_full_node_list and \
           self.collect_chars_with_following_arg_as_delimited_group:
            raise ValueError("If collect_chars_with_following_arg_as_delimited_group=True, "
                             "then we must have return_full_node_list=True")


    def contents_can_be_empty(self):
        return True

    def get_following_arg_parser(self, chars):
        return self.following_arg_parser

    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        num_args = 0

        full_nodelist = []
        empty_pos = None

        remaining_chars_list = self.chars_list

        while self.max_num_args is None or num_args < self.max_num_args:
            
            arg_nodes, parsing_state_delta, matched_chars, arg_pos = \
                self._parse_single(remaining_chars_list,
                                   latex_walker, token_reader, parsing_state, **kwargs)

            if empty_pos is None:
                empty_pos = arg_pos

            if parsing_state_delta is not None:
                logger.warning("Parsing state delta ignored after parsing optional "
                               "chars marker: %r", parsing_state_delta)

            if matched_chars is None:
                break

            num_args += 1
            full_nodelist += arg_nodes
            remaining_chars_list = [ chars for chars in remaining_chars_list
                                     if chars != matched_chars ]

        if num_args == 0:
            if self.return_none_instead_of_empty:
                return None, None
            emptynl = latex_walker.make_nodelist(
                [],
                pos=empty_pos,
                pos_end=empty_pos,
                parsing_state=parsing_state,
            )
            return emptynl, None

        if not self.return_full_node_list:
            if len(full_nodelist) != 1:
                logger.error("Internal error, node list here should have length == 1")
            final_node_obj = full_nodelist[0]
        else:
            final_node_obj = latex_walker.make_nodelist(
                full_nodelist, 
                parsing_state=parsing_state,
            )

        return final_node_obj, None




    def _parse_single(self, remaining_chars_list, latex_walker, token_reader,
                      parsing_state, **kwargs):
        
        orig_pos_tok = token_reader.peek_token(parsing_state=parsing_state)
        pos_end = None
        read_s = ''
        match_found = False
        matched_chars = None
        first_token = None
        try:
            while True:
                tok = token_reader.next_token(parsing_state=parsing_state)
                if first_token is None:
                    first_token = tok
                    if len(first_token.pre_space) and not self.allow_pre_space:
                        # no pre-space allowed, the optional marker was not provided.
                        return None, None, None, first_token.pos
                # allow continuing with 'specials' because they can count as
                # chars for markers.
                if tok.tok == 'specials':
                    # pretend it's a char
                    tok.tok = 'char'
                    tok.arg = tok.arg.specials_chars
                if tok.tok != 'char':
                    break
                if read_s and len(tok.pre_space):
                    read_s += " "
                read_s += tok.arg
                if read_s in self.chars_list:
                    match_found = True
                    matched_chars = read_s
                    pos_end = tok.pos_end
                    break
                if len([chars for chars in self.chars_list
                        if chars.startswith(read_s)]) == 0:
                    # mismatched all at this point, will not match
                    break

        finally:
            if not match_found:
                token_reader.move_to_token(orig_pos_tok)

        if not match_found:
            # chars marker is simply not present.
            logger.debug("No chars marker found!",)
            return None, None, None, orig_pos_tok.pos

        logger.debug("Chars marker ‘%s’ found.", matched_chars)

        arg_pos = orig_pos_tok.pos

        following_arg_parser = self.get_following_arg_parser(read_s)

        parsing_state_delta = None
        following_nodes = None

        if following_arg_parser is not None:
            following_nodes, parsing_state_delta = latex_walker.parse_content(
                following_arg_parser,
                token_reader=token_reader,
                parsing_state=parsing_state,
            )

        if self.collect_chars_with_following_arg_as_delimited_group:
            if isinstance(following_nodes, LatexNodeList):
                final_nl = following_nodes
            else:
                final_nl = latex_walker.make_nodelist(
                    [ following_nodes ],
                    parsing_state=parsing_state,
                )
            final_nl_pos_end = final_nl.pos_end
            if final_nl_pos_end is None:
                final_nl_pos_end = arg_pos
            nodes = [
                latex_walker.make_node(
                    LatexGroupNode,
                    parsing_state=parsing_state,
                    delimiters=(matched_chars, ''),
                    nodelist=final_nl,
                    pos=arg_pos,
                    pos_end=final_nl_pos_end,
                ),
            ]
            return nodes, parsing_state_delta, matched_chars, arg_pos

        chars_node = None
        if (not self.return_full_node_list and following_arg_parser is None) \
           or self.include_chars_node_before_following_arg:
            chars_node = latex_walker.make_node(
                        LatexCharsNode,
                        parsing_state=parsing_state,
                        chars=matched_chars,
                        pos=arg_pos,
                        pos_end=pos_end,
                    )

        if not self.return_full_node_list:
            if following_arg_parser is not None:
                return [ following_nodes ], parsing_state_delta, matched_chars, arg_pos
            else:
                assert chars_node is not None
                return [ chars_node ], parsing_state_delta, matched_chars, arg_pos

        nodes = []
        if self.include_chars_node_before_following_arg:
            assert chars_node is not None
            nodes.append( chars_node )

        if following_arg_parser is not None:
            if isinstance(following_nodes, LatexNodeList):
                following_nodes_as_list = following_nodes
            else:
                following_nodes_as_list = [ following_nodes ]

            nodes += following_nodes_as_list

        return nodes, parsing_state_delta, matched_chars, arg_pos
        



# ------------------------------------------------------------------------------

class LatexOptionalEmbellishmentArgsParser(LatexOptionalCharsMarkerParser):
    r"""
    Doc...............

    inspired by xparse's ``e{tokens}`` argument type.....
    """
    def __init__(self, embellishment_chars, allow_pre_space=True, **kwargs):
        super(LatexOptionalEmbellishmentArgsParser, self).__init__(
            chars_list=embellishment_chars,
            following_arg_parser=LatexExpressionParser(
                allow_pre_space=allow_pre_space,
                return_full_node_list=True,
            ),
            allow_pre_space=allow_pre_space,
            collect_chars_with_following_arg_as_delimited_group=True,
            return_full_node_list=True,
            **kwargs
        )
        self.embellishment_chars = embellishment_chars

