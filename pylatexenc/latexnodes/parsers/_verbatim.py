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
    Base class for parsers that read verbatim content, i.e., content that is
    taken literally rather than parsed as LaTeX code.

    Instead of reading tokens, these parsers read the input one character at a
    time and hand each character to
    :py:meth:`new_char_check_stop_condition()`, which decides when the verbatim
    content ends.  Subclasses reimplement that method (and possibly
    :py:meth:`finalize_verbatim_string()`) to implement a specific verbatim
    construct; see :py:class:`LatexDelimitedVerbatimParser` and
    :py:class:`LatexVerbatimEnvironmentContentsParser`.

    This base class implementation stops after a single character.

    Note: this parser requires the token reader to provide character-level
    access to the input string.
    """

    def __init__(self, **kwargs):
        super(LatexVerbatimBaseParser, self).__init__(**kwargs)

    class VerbatimInfo(object):
        r"""
        A simple object on which the verbatim parser stores the state associated
        with a single :py:meth:`parse()` call, so that the parser object itself
        can be reused.

        The fields are set by the parser as it goes along and include
        `parsed_delimiters` (the opening and closing delimiters of this verbatim
        construct, if applicable), `original_pos` (the position at which parsing
        started), `content_pos_start` (the position at which the verbatim
        content itself starts), and `pos_start`/`pos_end` (the span of the
        resulting chars node, set by
        :py:meth:`~LatexVerbatimBaseParser.finalize_verbatim_string()`).
        """
        def __init__(self):
            super(LatexVerbatimBaseParser.VerbatimInfo, self).__init__()
            self.parsed_delimiters = (None, None)

    def new_char_check_stop_condition(self, char, verbatim_string, verbatim_info,
                                      parsing_state):
        r"""
        Called for each character that is read, to decide whether the verbatim
        content ends here.  The `char` is the character that was just read (or
        `None` if the end of the stream was reached), and `verbatim_string` is
        the verbatim content that was accumulated so far, *not* including
        `char`.

        Return a false value to continue reading; `char` is then appended to the
        verbatim content.  Return `True` to stop, in which case `char` is
        consumed and dropped, or return a dictionary
        ``{'put_back_char': True}`` to stop and have `char` put back onto the
        input so that it is read again by whatever parses the following content.

        The default implementation in this base class is to read a single verbatim
        char.  Reimplement this method in a subclass for more advanced behavior.
        """
        if verbatim_string:
            return True # or dict like { 'put_back_char': True }
        return False

    def error_end_of_stream(self, pos, recovery_nodes, latex_walker, verbatim_info):
        r"""
        Called when the end of the stream was reached before the stop condition
        fired.  Raises a
        :py:exc:`~pylatexenc.latexnodes.LatexWalkerNodesParseError` with
        `recovery_nodes` set to the verbatim content that was read so far, so
        that parsing can continue in tolerant parsing mode.

        Subclasses reimplement this method in order to wrap `recovery_nodes`
        into the same node structure that a successful parse would have
        produced.
        """
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
        r"""
        Read the verbatim content at the current position and return it as a chars
        node, with no surrounding delimiters.

        Reimplemented from :py:meth:`LatexParserBase.parse()`.
        """

        verbatim_info = LatexVerbatimBaseParser.VerbatimInfo()
        verbatim_info.original_pos = token_reader.cur_pos()

        return self.read_verbatim_content(latex_walker, token_reader, parsing_state,
                                          verbatim_info=verbatim_info, **kwargs)


    def read_verbatim_content(self, latex_walker, token_reader, parsing_state,
                              verbatim_info, **kwargs):
        r"""
        Read the verbatim content itself, character by character, until
        :py:meth:`new_char_check_stop_condition()` says to stop.

        The accumulated string is then handed to
        :py:meth:`finalize_verbatim_string()`, and the result is returned as a
        single :py:class:`~pylatexenc.latexnodes.nodes.LatexCharsNode`.  That
        node's parsing state has macros, environments, specials, comments,
        groups, math mode and paragraph breaks all disabled, reflecting the fact
        that its contents are not LaTeX code.

        If the end of the stream is reached before the stop condition fires,
        :py:meth:`error_end_of_stream()` is called with the chars node offered as
        recovery nodes.

        Return a tuple `(chars_node, None)`.

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
            parsing_state=parsing_state.sub_context(
                # emulate a parsing state in which "special"/"active" features
                # have been disabled.
                enable_double_newline_paragraphs=False,
                enable_macros=False,
                enable_environments=False,
                enable_specials=False,
                enable_comments=False,
                enable_groups=False,
                enable_math=False,
            ),
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

    Any whitespace before the opening delimiter is skipped.  How the delimiters
    are determined depends on the `delimiters` constructor argument:

      - If `delimiters` is `None` (the default), the delimiters are detected
        automatically, as ``\verb`` does: the first character that follows is
        the opening delimiter, and the closing delimiter is looked up in the
        `auto_delimiters` dictionary, falling back to the opening delimiter
        itself.  The default `auto_delimiters` maps ``{``, ``[``, ``<`` and
        ``(`` to their respective closing counterparts.

      - If `delimiters` is a pair `(open_delimiter, close_delimiter)`, then
        exactly that pair is expected; a
        :py:exc:`~pylatexenc.latexnodes.LatexWalkerParseError` is raised if the
        opening delimiter is not there.

    If the opening and closing delimiters are different characters, then nested
    occurrences of the delimiter pair are tracked, so that ``\verb{a{b}c}``
    yields the verbatim content ``a{b}c``.

    The result is a :py:class:`~pylatexenc.latexnodes.nodes.LatexGroupNode` with
    the parsed delimiters, containing a single chars node with the verbatim
    content.
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


    def error_end_of_stream(self, pos, recovery_nodes, latex_walker, verbatim_info):
        # report the same node structure as a successful parse would, i.e. the
        # verbatim contents wrapped in a group node with the delimiters that we
        # did read, so that recovering from this error in tolerant parsing mode
        # yields a verbatim argument of the usual shape
        return super(LatexDelimitedVerbatimParser, self).error_end_of_stream(
            pos=pos,
            recovery_nodes=latex_walker.make_node(
                LatexGroupNode,
                delimiters=verbatim_info.parsed_delimiters,
                nodelist=latex_walker.make_nodelist(
                    [ recovery_nodes ],
                    parsing_state=recovery_nodes.parsing_state,
                ),
                pos=verbatim_info.original_pos,
                pos_end=recovery_nodes.pos_end,
                parsing_state=recovery_nodes.parsing_state,
            ),
            latex_walker=latex_walker,
            verbatim_info=verbatim_info,
        )


    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):

        # the depth counter is state that only makes sense for the duration of a
        # single parse() call; reset it here so that this parser object can be
        # reused for further verbatim arguments (as happens when the same spec
        # object is used repeatedly while parsing a document)
        self.depth_counter = 1

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
                    pos=verbatim_info.original_pos,
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

    The content is read literally until the string ``\end{environment_name}``
    is encountered (using the parsing state's macro escape character in place of
    the backslash).  That terminator is not part of the verbatim content, but it
    is consumed: the token reader is left immediately after it, so that the
    enclosing environment node spans the closing ``\end{...}`` as usual.

    A single newline character immediately following ``\begin{environment_name}``
    is dropped, as LaTeX does.

    The `environment_name` constructor argument gives the name of the
    environment to look for and defaults to ``'verbatim'``.

    The result is a :py:class:`~pylatexenc.latexnodes.LatexNodeList` containing
    a single chars node with the verbatim content, which is the shape expected
    for an environment body.
    """
    def __init__(self, environment_name='verbatim', **kwargs):
        super(LatexVerbatimEnvironmentContentsParser, self).__init__(**kwargs)
        self.environment_name = environment_name

    def new_char_check_stop_condition(self, char, verbatim_string, verbatim_info,
                                      parsing_state):

        if verbatim_string.endswith( verbatim_info.end_environment_code ):
            return {'put_back_char': True}
        return False

    def error_end_of_stream(self, pos, recovery_nodes, latex_walker, verbatim_info):
        # an environment body is always reported as a node list, including when
        # we recover from this error in tolerant parsing mode
        return super(LatexVerbatimEnvironmentContentsParser, self).error_end_of_stream(
            pos=pos,
            recovery_nodes=latex_walker.make_nodelist(
                [ recovery_nodes ],
                parsing_state=recovery_nodes.parsing_state,
            ),
            latex_walker=latex_walker,
            verbatim_info=verbatim_info,
        )

    def finalize_verbatim_string(self, verbatim_string, verbatim_info):

        end_environment_code = verbatim_info.end_environment_code
        if verbatim_string.endswith(end_environment_code):
            verbatim_string = verbatim_string[:-len(end_environment_code)]
        # If the end environment code is not there, we ran into the end of the
        # stream before finding the closing \end{...}.  Don't fail here; return
        # the content that we did read so that read_verbatim_content() can
        # report the parse error and offer these contents as recovery nodes.

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
