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


from .._exctypes import (
    LatexWalkerParseError,
    LatexWalkerTokenParseError,
    LatexWalkerNodesParseError,
    LatexWalkerEndOfStream
)
from ..nodes import *

from ._base import LatexParserBase
from .._parsedargs import ParsedArguments
from ._delimited import LatexDelimitedGroupParser



# --------------------------------------



class _TryAgainWithSkippedCommentOrWhitespaceNodes(Exception):
    def __init__(self, skipped_nodes, pos):
        super(_TryAgainWithSkippedCommentOrWhitespaceNodes, self).__init__("<internal>")
        self.skipped_nodes = skipped_nodes
        self.pos = pos



class LatexExpressionParser(LatexParserBase):
    r"""
    The parsed result is a `LatexNodeList`.

    If `return_full_node_list` is `True`, then a :py:class:`LatexNodeList` is
    returned as the content returned by :py:meth:`parse()`.  The node list
    contains all nodes read while parsing the given LaTeX expression (including
    comment nodes and whitespace reported as whitespace-only chars node).

    If `return_full_node_list` is `False`, then only the single node that
    contained the expression we're interested in is returned in the contents
    returned by the :py:meth:`parse()` method.  While you directly get the
    expression you're interested in, you might lose information about how to
    recompose the node into its source LaTeX string.
    """
    def __init__(self,
                 allow_pre_space=True,
                 allow_pre_comments=True,
                 return_full_node_list=True,
                 single_token_requiring_arg_is_error=True,
                 **kwargs
                 ):
        super(LatexExpressionParser, self).__init__(**kwargs)
        self.allow_pre_space = allow_pre_space
        self.allow_pre_comments = allow_pre_comments
        self.return_full_node_list = return_full_node_list
        self.single_token_requiring_arg_is_error = single_token_requiring_arg_is_error


    def contents_can_be_empty(self):
        return False


    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):

        expr_parsing_state = parsing_state.sub_context(enable_environments=False)
        
        exprnodes = []
        while True:
            try:
                moreexprnodes = \
                    self._parse_single_token(latex_walker,
                                             token_reader,
                                             expr_parsing_state,
                                             parsing_state=parsing_state,
                                             **kwargs)
            except _TryAgainWithSkippedCommentOrWhitespaceNodes as e:
                exprnodes += e.skipped_nodes
                continue

            exprnodes += moreexprnodes

            if not len(exprnodes):
                # happens when end of stream is reached
                thenodelist = latex_walker.make_nodelist(
                    [],
                    pos=token_reader.cur_pos(),
                    pos_end=token_reader.cur_pos(),
                    parsing_state=parsing_state,
                )

            else:
                thenodelist = latex_walker.make_nodelist(
                    exprnodes,
                    parsing_state=parsing_state,
                )

                # # determine (pos,len) automatically please...
                # expr_nodelist = latex_walker.make_nodelist(
                #     exprnodes,
                #     parsing_state=parsing_state,
                # )

                # thenodelist = latex_walker.make_node(
                #     LatexGroupNode,
                #     parsing_state=parsing_state,
                #     nodelist=expr_nodelist,
                #     delimiters=('',''),
                #     pos=expr_nodelist.pos,
                #     pos_end=expr_nodelist.pos_end,
                # )

            logger.debug("thenodelist = %r", thenodelist)

            if self.return_full_node_list:
                result = thenodelist
            else:
                result = thenodelist[-1] # last node is the main content node

            return result, None


    def _parse_single_token(self, latex_walker, token_reader, expr_parsing_state,
                            parsing_state, **kwargs):

        try:
            tok = token_reader.next_token( parsing_state=expr_parsing_state )
        except LatexWalkerTokenParseError as e:
            exc = latex_walker.check_tolerant_parsing_ignore_error(e)
            if exc is not None:
                raise exc

            # recover from error and continue.  These recovery fields are
            # specific to LatexWalkerTokenParseError.  They can only be set when
            # the token reader implements move_to_pos_chars(); we cannot use
            # move_past_token() etc. because the token couldn't be parsed
            # successfully!
            tok = exc.recovery_token_placeholder
            token_reader.move_to_pos_chars(exc.recovery_token_at_pos)
        except LatexWalkerEndOfStream as e:
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    r"End of input encountered but we expected an expression",
                    pos=token_reader.cur_pos(),
                    error_type_info={
                        'what': 'expression_required_got_unexpected',
                        'unexpected': 'end_of_stream',
                    },
                )
            )
            if exc is not None:
                raise exc
            return []

        if tok.tok == 'macro':

            macroname = tok.arg

            if self.single_token_requiring_arg_is_error \
               and macroname in ('begin', 'end',):
                # error, we were expecting a single token
                exc = latex_walker.check_tolerant_parsing_ignore_error(
                    LatexWalkerParseError(
                        r"Expected expression, got \{}".format(macroname),
                        pos=tok.pos,
                        error_type_info={
                            'what': 'expression_required_got_unexpected',
                            'unexpected': 'beginend',
                            'beginend': macroname,
                        },
                    )
                )
                if exc is not None:
                    raise exc

                # recover from error ->
                return [
                    latex_walker.make_node(
                        LatexMacroNode,
                        parsing_state=parsing_state,
                        macroname=macroname,
                        spec=None,
                        nodeargd=None,
                        macro_post_space=tok.post_space,
                        pos=tok.pos,
                        pos_end=tok.pos_end
                    )
                ]

            mspec = parsing_state.latex_context.get_macro_spec(macroname)

            parsed_arguments = self._check_if_requires_args(
                latex_walker, mspec, tok,
                r"a single macro ‘\{}’".format(macroname)
            )

            return [
                latex_walker.make_node(
                    LatexMacroNode,
                    parsing_state=parsing_state,
                    macroname=tok.arg,
                    spec=mspec,
                    nodeargd=parsed_arguments,
                    macro_post_space=tok.post_space,
                    pos=tok.pos,
                    pos_end=tok.pos_end
                )
            ]

        if tok.tok == 'specials':

            specialsspec = tok.arg

            parsed_arguments = self._check_if_requires_args(
                latex_walker, specialsspec, tok,
                r"specials ‘{}’".format(specialsspec.specials_chars)
            )

            return [
                latex_walker.make_node(
                    LatexSpecialsNode,
                    parsing_state=parsing_state,
                    specials_chars=specialsspec.specials_chars,
                    spec=specialsspec,
                    nodeargd=parsed_arguments,
                    pos=tok.pos,
                    pos_end=tok.pos_end
                )
            ]

        if len(tok.pre_space):
            if self.allow_pre_space:
                # put the token back so that it can be found again on the next
                # iteration, after we've skipped whitespace
                token_reader.move_to_token(tok, rewind_pre_space=False)

                wspos = tok.pos-len(tok.pre_space)

                # create a dummy whitespace char as we did for comments
                cnodes = [
                    latex_walker.make_node(LatexCharsNode,
                                           parsing_state=parsing_state,
                                           chars=tok.pre_space,
                                           pos=wspos,
                                           pos_end=tok.pos)
                ]
                raise _TryAgainWithSkippedCommentOrWhitespaceNodes(cnodes, wspos)

            # whitespace not allowed -> error
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    r"Expected expression w/o leading whitespace but found whitespace",
                    pos=tok.pos - len(tok.pre_space),
                    error_type_info={
                        'what': 'expression_required_got_unexpected',
                        'unexpected': 'whitespace',
                        'whitespace': tok.pre_space,
                    },
                )
            )
            if exc is not None:
                raise exc

            # recover from error ->
            raise _TryAgainWithSkippedCommentOrWhitespaceNodes([], tok.pos)


        if tok.tok == 'comment':
            if self.allow_pre_comments:
                # test for comments after gulping whitespace and including them in
                # possible char nodes
                cnodes = [
                    latex_walker.make_node(LatexCommentNode,
                                           parsing_state=parsing_state,
                                           comment=tok.arg,
                                           comment_post_space=tok.post_space,
                                           pos=tok.pos,
                                           pos_end=tok.pos_end)
                ]
                raise _TryAgainWithSkippedCommentOrWhitespaceNodes(cnodes, tok.pos)

            # comments not allowed here -> error
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                    LatexWalkerParseError(
                    r"Expected expression w/o leading comments but found comment ‘%{}’"
                    .format(tok.arg),
                    pos=tok.pos,
                    error_type_info={
                        'what': 'expression_required_got_unexpected',
                        'unexpected': 'comment',
                        'comment': tok.arg,
                    },
                )
            )
            if exc is not None:
                raise exc

            # recover from error ->
            raise _TryAgainWithSkippedCommentOrWhitespaceNodes([], tok.pos)


        if tok.tok == 'brace_open':

            # put the token back so that it can be found again by the
            # LatexDelimitedGroupParser
            token_reader.move_to_token(tok)

            groupnode, parsing_state_delta = latex_walker.parse_content(
                LatexDelimitedGroupParser(
                    delimiters=tok.arg
                ),
                token_reader=token_reader,
                parsing_state=parsing_state,
            )

            logger.debug("Got groupnode = %r", groupnode)

            if parsing_state_delta is not None:
                logger.warning(
                    "Ignoring parsing_state_delta after parsing an expression group!"
                )

            return [ groupnode ]

        if tok.tok == 'brace_close':

            # put the token back so that it can be processed by whichever group
            # actually needs it
            token_reader.move_to_token(tok)

            exc = LatexWalkerNodesParseError(
                msg="Expected LaTeX expression, got closing brace ‘{}’".format(tok.arg),
                pos=tok.pos,
                recovery_nodes=latex_walker.make_node(LatexCharsNode,
                                                      parsing_state=parsing_state,
                                                      chars='',
                                                      pos=tok.pos,
                                                      pos_end=tok.pos), # not pos_end
                # don't consume the closing brace if we're trying to recover
                # from the parse error
                recovery_at_token=tok,
                error_type_info={
                    'what': 'expression_required_got_unexpected',
                    'unexpected': 'closing_latex_group',
                    'delimiter': tok.arg,
                },
            )
            # internal, to aid pylatexenc2 compatibility code
            exc._error_was_unexpected_closing_brace_in_expression = True
            raise exc

        if tok.tok == 'char':

            return [ latex_walker.make_node(LatexCharsNode,
                                            parsing_state=parsing_state,
                                            chars=tok.arg,
                                            pos=tok.pos,
                                            pos_end=tok.pos_end) ]

        if tok.tok in ('mathmode_inline', 'mathmode_display'):
            
            # I can't think of a good reason why this shouldn't be an error.  If
            # a macro need to handle very special arguments (such as a single $
            # token), then it should provide its own argument parser for that
            # argument.

            # try to figure out a smart recovery node
            if tok.arg.startswith('\\'):
                recovery_nodes = latex_walker.make_node(LatexMacroNode,
                                                        parsing_state=parsing_state,
                                                        macroname=tok.arg,
                                                        macro_post_space=tok.post_space,
                                                        pos=tok.pos,
                                                        pos_end=tok.pos_end)
            else:
                recovery_nodes = latex_walker.make_node(LatexCharsNode,
                                                        parsing_state=parsing_state,
                                                        chars=tok.arg,
                                                        pos=tok.pos,
                                                        pos_end=tok.pos_end)
                
            raise LatexWalkerNodesParseError(
                "Unexpected math mode delimiter ‘{}’, was expecting a LaTeX expression"
                .format(tok.arg),
                pos=tok.pos,
                recovery_nodes=recovery_nodes,
                recovery_past_token=tok,
                error_type_info={
                    'what': 'expression_required_got_unexpected',
                    'unexpected': 'math_mode_delimiter',
                    'mathmode_type': tok.tok,
                    'delimiter': tok.arg,
                },
            )

        raise LatexWalkerParseError(
            "Unknown token type: ‘{}’".format(tok.tok),
            pos=tok.pos
        )


    def _check_if_requires_args(self, latex_walker, spec, got_token, what_we_got):

        if self.single_token_requiring_arg_is_error:

            arg_contents_empty_ok = spec.get_node_parser(got_token).contents_can_be_empty()
            logger.debug("Checking if %s/‘%s’ requires an arg: %r",
                         got_token.tok, got_token.arg, arg_contents_empty_ok)

            if not arg_contents_empty_ok:
                exc = latex_walker.check_tolerant_parsing_ignore_error(
                    LatexWalkerParseError(
                        (r"Expected a LaTeX expression but got {} which "
                         r"expects arguments; did you mean to provide an expression "
                         r"in {{curly braces}} ?").format(what_we_got),
                        pos=got_token.pos,
                        error_type_info={
                            'what': 'expression_required_got_unexpected',
                            'unexpected': 'callable_with_mandatory_arguments',
                            'callable_token': got_token,
                        },
                    )
                )
                if exc is not None:
                    raise exc

                return None

        return ParsedArguments()
