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
    Parse an optional marker consisting of one or more specific characters, such
    as the star in ``\section*``, optionally along with an argument that follows
    the marker.

    The parser looks for a marker repeatedly, so that several markers can be
    picked up one after the other.  It stops as soon as the next tokens don't
    match any of the markers, or once `max_num_args` markers have been read.  If
    no marker at all was found, the parser reports that the optional argument
    was not provided (see `return_none_instead_of_empty`).

    Constructor arguments:

      - `chars_list` is the list of markers to look for.  Each entry is a string
        of one or more characters.  Whitespace within an entry is normalized,
        and matches any run of whitespace in the source.  If a single string is
        given instead of a list, it is interpreted as the list of its individual
        characters.  A "specials" token counts as its characters here, so that a
        marker can be made of characters that are declared as specials.

      - `following_arg_parser`, if non-`None`, is the parser that is used to
        read an argument that follows the marker.  It is obtained via
        :py:meth:`get_following_arg_parser()`, so that subclasses can pick a
        different parser depending on which marker was matched.

      - `include_chars_node_before_following_arg` determines whether or not the
        marker itself is reported as a chars node before the nodes of the
        following argument.

      - `return_none_instead_of_empty` determines what is returned if no marker
        was found: `None` (the default), or an empty node list.

      - `allow_pre_space` determines whether whitespace is allowed before the
        marker.  If it is `False` and whitespace is encountered, the marker
        counts as not provided.

      - `collect_chars_with_following_arg_as_delimited_group` wraps the marker
        and the following argument into a single
        :py:class:`~pylatexenc.latexnodes.nodes.LatexGroupNode` whose delimiters
        are the marker and an empty string.  This requires
        `return_full_node_list=True`.

      - `max_num_args`, if non-`None`, is the maximum number of markers to read.

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
        r"""
        Return `True`; the marker that this parser reads is always optional.

        Reimplemented from :py:meth:`LatexParserBase.contents_can_be_empty()`.
        """
        return True

    def get_following_arg_parser(self, chars):
        r"""
        Return the parser to use to read the argument that follows the marker
        `chars` that was just matched, or `None` if this marker does not take an
        argument.

        The default implementation returns the `following_arg_parser` that was
        specified to the constructor, regardless of `chars`.  Reimplement this
        method if different markers should take different arguments.
        """
        return self.following_arg_parser

    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):
        r"""
        Read the optional marker(s) and any argument that follows them.  See class
        doc.

        Returns a tuple `(nodes, None)`.  The `nodes` is `None` if no marker was
        found and `return_none_instead_of_empty` is set; otherwise it is a
        :py:class:`~pylatexenc.latexnodes.LatexNodeList`, or a single node if
        `return_full_node_list` is `False`.

        Reimplemented from :py:meth:`LatexParserBase.parse()`.
        """

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
    Parse a sequence of optional "embellishments", i.e., single characters that
    each introduce an argument, such as the ``^`` and ``_`` in ``x^i_j``.

    This parser is inspired by `xparse`'s ``e{tokens}`` argument type.

    The `embellishment_chars` argument lists the characters that can introduce
    an embellishment; it is used as the `chars_list` of the base class
    :py:class:`LatexOptionalCharsMarkerParser`, so a plain string is interpreted
    as the list of its individual characters.  Each embellishment character that
    is encountered is followed by a single expression, which is read with a
    :py:class:`LatexExpressionParser`.

    Each embellishment is reported as a
    :py:class:`~pylatexenc.latexnodes.nodes.LatexGroupNode` whose opening
    delimiter is the embellishment character and whose closing delimiter is an
    empty string; all of them are collected into a single node list.  If no
    embellishment at all is present, the parser reports `None`.
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

