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


from .._exctypes import (
    LatexWalkerParseError, LatexWalkerTokenParseError, LatexWalkerEndOfStream
)
from .._nodetypes import *
from .._nodetypes import _update_poslen_from_nodelist

from ._base import LatexParserBase
from ._generalnodes import LatexDelimitedGroupParser



# --------------------------------------



class _TryAgainWithSkippedCommentNodes(Exception):
    def __init__(self, skipped_comment_nodes, pos):
        super(_TryAgainWithSkippedCommentNodes, self).__init__("<internal>")
        self.skipped_comment_nodes = skipped_comment_nodes
        self.pos = pos



class LatexExpressionParser(LatexParserBase):
    def __init__(self,
                 include_skipped_comments=True,
                 single_token_requiring_arg_is_error=True,
                 **kwargs
                 ):
        super(LatexExpressionParser, self).__init__(**kwargs)
        self.include_skipped_comments = include_skipped_comments
        self.single_token_requiring_arg_is_error = single_token_requiring_arg_is_error


    def contents_can_be_empty(self):
        return False


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        expr_parsing_state = parsing_state.sub_context(enable_environments=False)
        
        exprnodes = []
        # p = None
        # l = None
        while True:
            try:
                moreexprnodes = \
                    self._parse_single_token(latex_walker,
                                             token_reader,
                                             expr_parsing_state,
                                             parsing_state=parsing_state,
                                             **kwargs)
            except _TryAgainWithSkippedCommentNodes as e:
                exprnodes += e.skipped_comment_nodes
                # if p is None:
                #     p = e.pos
                continue

            exprnodes += moreexprnodes

            # if len(moreexprnodes) > 0:
            #     lastnode = moreexprnodes[len(moreexprnodes)-1]
            #     pp, ll = lastnode.pos, lastnode.len
            #     if p is None and pp is not None:
            #         p = pp
            #     if p is not None and pp is not None and ll is not None:
            #         l = pp + ll - p

            if len(exprnodes) == 1:
                thenodelist = exprnodes[0]
            else:
                # determine (pos,len) automatically please...
                pos, len_ = _update_poslen_from_nodelist(pos=None, len=None,
                                                         nodelist=exprnodes)

                thenodelist = latex_walker.make_node(
                    LatexGroupNode,
                    nodelist=exprnodes,
                    delimiters=('',''),
                    pos=pos,
                    len=len_,
                )

            return thenodelist, None


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
                    pos=token_reader.cur_pos()
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
                        pos=tok.pos
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
                        nodeoptarg=None,
                        nodeargs=None,
                        pos=tok.pos,
                        len=tok.len
                    )
                ]

            mspec = parsing_state.latex_context.get_macro_spec(macroname)

            self._check_if_requires_args(latex_walker, mspec, tok,
                                         r"a single macro ‘\{}’".format(macroname))

            return [
                latex_walker.make_node(
                    LatexMacroNode,
                    parsing_state=parsing_state,
                    macroname=tok.arg,
                    spec=mspec,
                    nodeargd=None,
                    macro_post_space=tok.post_space,
                    nodeoptarg=None,
                    nodeargs=None,
                    pos=tok.pos,
                    len=tok.len
                )
            ]

        if tok.tok == 'specials':

            specialsspec = tok.arg

            self._check_if_requires_args(latex_walker, specialsspec, tok,
                                         r"specials ‘{}’".format(specialsspec.specials_chars))

            return [
                latex_walker.make_node(
                    LatexSpecialsNode,
                    parsing_state=parsing_state,
                    specials_chars=specialsspec.specials_chars,
                    spec=specialsspec,
                    nodeargd=None,
                    pos=tok.pos,
                    len=tok.len
                )
            ]

        if tok.tok == 'comment':

            if self.include_skipped_comments:
                cnodes = [
                    latex_walker.make_node(LatexCommentNode,
                                           parsing_state=parsing_state,
                                           comment=tok.arg,
                                           comment_post_space=tok.post_space,
                                           pos=tok.pos,
                                           len=tok.len)
                ]
            else:
                cnodes = []

            raise _TryAgainWithSkippedCommentNodes(cnodes, tok.pos)


        if tok.tok == 'brace_open':

            # put the token back so that it can be found again by the
            # LatexDelimitedGroupParser
            token_reader.move_to_token(tok)

            groupnode, carryover_info = latex_walker.parse_content(
                LatexDelimitedGroupParser(
                    require_brace_type=tok.arg
                ),
                token_reader=token_reader,
                parsing_state=parsing_state,
            )

            if carryover_info is not None:
                logger.warning("Ignoring carryover_info after parsing an expression group!")

            return [ groupnode ]

        if tok.tok == 'brace_close':

            raise LatexWalkerNodesParseError(
                msg="Expected LaTeX expression, got closing brace ‘{}’".format(tok.arg),
                pos=tok.pos,
                recovery_nodes=latex_walker.make_node(LatexCharsNode,
                                                      parsing_state=parsing_state,
                                                      chars='',
                                                      pos=tok.pos,
                                                      len=0),
                # don't consume the closing brace if we're trying to recover
                # from the parse error
                recovery_at_token=tok
            )

        if tok.tok == 'char':

            return [ latex_walker.make_node(LatexCharsNode,
                                            parsing_state=parsing_state,
                                            chars=tok.arg,
                                            pos=tok.pos,
                                            len=tok.len) ]

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
                                                        nodeoptarg=None,
                                                        nodeargs=None,
                                                        macro_post_space=tok.post_space,
                                                        pos=tok.pos,
                                                        len=tok.len)
            else:
                recovery_nodes = latex_walker.make_node(LatexCharsNode,
                                                        parsing_state=parsing_state,
                                                        chars=tok.arg,
                                                        pos=tok.pos,
                                                        len=tok.len)
                
            raise LatexWalkerNodesParseError(
                "Unexpected math mode delimiter ‘{}’, was expecting a LaTeX expression"
                .format(tok.arg),
                pos=tok.pos,
                recovery_nodes=recovery_nodes,
                recovery_past_token=tok,
            )

        raise LatexWalkerParseError(
            "Unknown token type: ‘{}’".format(tok.tok),
            pos=tok.pos
        )


    def _check_if_requires_args(self, latex_walker, spec, got_token, what_we_got):

        print("**** Checking if macro ‘\\", got_token.arg, "’ requires an arg ...", sep='')

        if self.single_token_requiring_arg_is_error \
           and not spec.get_node_parser(got_token).contents_can_be_empty():
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    (r"Expected a LaTeX expression but got {} which "
                     r"expects arguments; did you mean to provide an expression "
                     r"in {{curly braces}} ?").format(what_we_got),
                )
            )
            if exc is not None:
                raise exc

