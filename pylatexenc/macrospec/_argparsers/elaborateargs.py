# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2021 Philippe Faist
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


import sys


if sys.version_info.major > 2:
    # Py3
    def unicode(s): return s
    _basestring = str
    _str_from_unicode = lambda x: x
    _unicode_from_str = lambda x: x
else:
    # Py2
    _basestring = basestring
    _str_from_unicode = lambda x: unicode(x).encode('utf-8')
    _unicode_from_str = lambda x: x.decode('utf-8')

#


from .macroargsbase import ParsedMacroArgs, MacroStandardArgsParser




class ParsedElaborateMacroArgs(ParsedMacroArgs):
    def __init__(self, argument_spec_list, argnlist, **kwargs):
        super(ParsedElaborateMacroArgs, self).__init__(
            argspec=None,
            argnlist=argnlist,
            **kwargs
        )
        self.argument_spec_list = argument_spec_list


class ElaborateArgumentBase(object):
    def __init__(self, optional=False, argument_is_in_math_mode=None, **kwargs):
        super(ElaborateArgumentBase, self).__init__(**kwargs)
        self.optional = optional
        self.argument_is_in_math_mode = argument_is_in_math_mode # None, True or False

    def description(self):
        return "<MISSING DESCRIPTION>"

    def get_parsing_state_for_argument(self, parsing_state):
        if self.argument_is_in_math_mode is None:
            return parsing_state
        if self.argument_is_in_math_mode == parsing_state.in_math_mode: # True or False
            return parsing_state # already in correct mode
        return parsing_state.sub_context(in_math_mode=self.argument_is_in_math_mode)

    def parse_argument(self, w, pos, parsing_state):
        raise RuntimeError("Subclasses need to reimplement parse_argument()")


class ElaborateExpressionArgument(ElaborateArgumentBase):
    def __init__(self, **kwargs):
        super(ElaborateExpressionArgument, self).__init__(
            optional=False, # cannot be optional
            **kwargs
        )

    def description(self):
        return "expression = macro or braced group"

    def parse_argument(self, w, pos, parsing_state):
        (node, np, nl) = w.get_latex_expression(
            pos,
            strict_braces=False,
            parsing_state=self.get_parsing_state_for_argument(parsing_state),
        )
        return (node, np, nl)


class ElaborateNestableDelimitedArgument(ElaborateArgumentBase):
    def __init__(self, delimiters=('{', '}'), **kwargs):
        super(ElaborateNestableDelimitedArgument, self).__init__(**kwargs)
        self.delimiters = tuple(delimiters)

    def description(self):
        return "expression delimited by ‘{}’ and ‘{}’".format(*self.delimiters)

    def parse_argument(self, w, pos, parsing_state):

        from ... import latexwalker

        # if the argument is optional, check to see if it was provided or not
        if self.optional:
            try:
                tok = w.get_token(pos,
                                  include_brace_chars=[self.delimiters],
                                  environments=False,
                                  parsing_state=parsing_state)
            except latexwalker.LatexWalkerEndOfStream:
                # we're at end of stream, simply report no optional arg and let
                # parents re-detect end of stream when they call again get_token().
                return (None, pos, 0)

            if tok.tok != 'brace_open' or tok.arg != self.delimiters[0]:
                # optional argument not present
                return (None, pos, 0)

        (node, np, nl) = w.get_latex_braced_group(
            pos,
            brace_type=self.delimiters,
            parsing_state=self.get_parsing_state_for_argument(parsing_state),
        )
        return (node, np, nl)


class ElaborateNestableDelimitedSimpleTokensArgument(ElaborateArgumentBase):
    def __init__(self, delimiters=('{', '}'), **kwargs):
        super(ElaborateNestableDelimitedSimpleTokensArgument, self).__init__(**kwargs)
        self.delimiters = tuple(delimiters)

    def description(self):
        return "tokens delimited by ‘{}’ and ‘{}’".format(*self.delimiters)

    def parse_argument(self, w, pos, parsing_state):

        from ... import latexwalker

        # if the argument is optional, check to see if it was provided or not
        if self.optional:
            try:
                tok = w.get_token(pos,
                                  include_brace_chars=[self.delimiters],
                                  environments=False,
                                  parsing_state=parsing_state)
            except latexwalker.LatexWalkerEndOfStream:
                # we're at end of stream, simply report no optional arg and let
                # parents re-detect end of stream when they call again get_token().
                return (None, pos, 0)

            if tok.tok != 'brace_open' or tok.arg != self.delimiters[0]:
                # optional argument not present
                return (None, pos, 0)

        # read token by token
        inner_parsing_state = self.get_parsing_state_for_argument(parsing_state)

        (node, nodepos, nodelen) = \
            w.get_delimited_group_token_chars(pos,
                                              delimiters=[self.delimiters],
                                              start_with_delimiter=self.delimiters[0],
                                              wrap_in_group_node=True,
                                              parsing_state=inner_parsing_state)

        return (node, nodepos, nodelen)


class MacroElaborateArgsParser(MacroStandardArgsParser):
    def __init__(self, argument_spec_list, **kwargs):
        super(MacroElaborateArgsParser, self).__init__(**kwargs)
        self.argument_spec_list = tuple(argument_spec_list)
        
    def parse_args(self, w, pos, parsing_state=None):

        from ... import latexwalker

        if parsing_state is None:
            parsing_state = w.make_parsing_state()

        pos_start = None
        argnlist = []

        for j_arg, argument_spec in enumerate(self.argument_spec_list):

            try:
                (node, npos, nlen) = argument_spec.parse_argument(w, pos, parsing_state)
            except (latexwalker.LatexWalkerEndOfStream,
                    latexwalker.LatexWalkerParseError) as e:
                if hasattr(e, 'open_contexts'):
                    lineno, colno = w.pos_to_lineno_colno(pos)
                    e.open_contexts.append(
                        ("Argument #{} (expected: {})".format(j_arg,
                                                              argument_spec.description()),
                         pos,
                         lineno,
                         colno)
                    )
                raise

            if node is not None and pos_start is None:
                pos_start = npos
            argnlist.append( node )
            pos = npos + nlen

        pos_end = pos

        return (
            ParsedElaborateMacroArgs(
                argument_spec_list=self.argument_spec_list,
                argnlist=argnlist
            ),
            pos_start,
            pos_end - pos_start
        )
            

