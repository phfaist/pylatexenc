
from ._types import LatexWalkerParseError, LatexWalkerTokenParseError

from ._std import LatexDelimitedGroupParser



# --------------------------------------



class _TryAgainWithSkippedCommentNodes(Exception):
    def __init__(self, skipped_comment_nodes, pos):
        super(_TryAgainWithSkippedCommentNodes, self).__init__("<internal>")
        self.skipped_comment_nodes = skipped_comment_nodes
        self.pos = pos



class LatexExpressionParser(object):
    def __init__(self,
                 include_skipped_comments=True,
                 single_token_requiring_arg_is_error=True,
                 **kwargs
                 ):
        super(LatexExpressionParser, self).__init__(**kwargs)
        self.include_skipped_comments = include_skipped_comments
        self.single_token_requiring_arg_is_error = single_token_requiring_arg_is_error

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        expr_parsing_state = parsing_state.sub_context(enable_environments=False)
        
        exprnodes = []
        p = None
        l = None
        while True:
            try:
                moreexprnodes = \
                    self._parse_single_token(latex_walker,
                                             token_reader,
                                             expr_parsing_state,
                                             **kwargs)
            except _TryAgainWithSkippedCommentNodes as e:
                exprnodes += e.skipped_comment_nodes
                if p is None:
                    p = e.pos
                continue

            exprnodes += moreexprnodes
            if p is None:
                p = pp
            l = pp + ll - p

            return LatexNodeList(nodelist=exprnodes, pos=p, len=l,)


    def _parse_single_token(self, latex_walker, token_reader, expr_parsing_state, **kwargs):

        try:
            tok = token_reader.next_token(environments=False,
                                          parsing_state=expr_parsing_state)
        except LatexWalkerTokenParseError as e:
            exc = latex_walker.check_tolerant_parsing_ignore_error(e)
            if exc is not None:
                raise exc

            # recover from error and continue.  These recovery fields are
            # specific to LatexWalkerTokenParseError.  They can only be set when
            # the token reader implements jump_to_pos(); we cannot use
            # move_past_token() etc. because the token couldn't be parsed
            # successfully!
            tok = exc.recovery_token_placeholder
            token_reader.jump_to_pos(exc.recovery_token_at_pos)


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
                        parsing_state=expr_parsing_state,
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

            mspec = expr_parsing_state.latex_context.get_macro_spec(macroname)

            self._check_if_requires_args(latex_walker, mspec,
                                         r"a single macro ‘\{}’".format(macroname))

            return [
                latex_walker.make_node(
                    LatexMacroNode,
                    parsing_state=expr_parsing_state,
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

            self._check_if_requires_args(latex_walker, specialsspec,
                                         r"specials ‘{}’".format(specialsspec.specials_chars))

            return [
                latex_walker.make_node(
                    LatexSpecialsNode,
                    parsing_state=expr_parsing_state,
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
                                           parsing_state=expr_parsing_state,
                                           comment=tok.arg,
                                           comment_post_space=tok.post_space,
                                           pos=tok.pos,
                                           len=tok.len)
                ]
            else:
                cnodes = []

            raise _TryAgainWithSkippedCommentNodes(cnodes, tok.pos)


        if tok.tok == 'brace_open':

            groupnode = latex_walker.parse_content(
                LatexDelimitedGroupParser(
                    require_brace_type=tok.arg
                ),
                token_reader=token_reader,
                parsing_state=parsing_state,
            )
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
                
            raise LatexWalkerParseError(
                "Unexpected math mode delimiter ‘{}’, was expecting a LaTeX expression"
                .format(tok.arg),
                pos=tok.pos,
                recovery_nodes=recovery_nodes,
                recovery_past_token=tok.pos+tok.len
            )

        raise LatexWalkerParseError(
            "Unknown token type: ‘{}’".format(tok.tok),
            pos=tok.pos
        )


    def _check_if_requires_args(self, latex_walker, spec, what_we_got):

        if self.single_token_requiring_arg_is_error \
           and spec.needs_arguments():
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    (r"Expected a LaTeX expression but got {} which "
                     r"expects arguments; did you mean to provide an expression "
                     r"in {{curly braces}} ?").format(what_we_got),
                )
            )
            if exc is not None:
                raise exc

