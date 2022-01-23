# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2019 Philippe Faist
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


from ..latexnodes import CallableSpecBase

from ._argumentsparser import LatexArgumentsParser
from ._macrocallparser import (
    LatexMacroCallParser, LatexEnvironmentCallParser, LatexSpecialsCallParser
)


# for Py3
_basestring = str

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
## End Py2 support code




class _SpecBase(CallableSpecBase):
    def __init__(self, arguments_spec_list=None, make_carryover_info=None, **kwargs):
        self.arguments_spec_list = arguments_spec_list
        self.arguments_parser = LatexArgumentsParser(arguments_spec_list)

        self._make_carryover_info_fn = make_carryover_info

        _li = getattr(self, '_legacy_pyltxenc2_init_from_args_parser', None)
        if _li is not None:
            _li(kwargs)

        if kwargs:
            raise ValueError("Unknown argument(s): {!r}".format(kwargs))
    
    def make_carryover_info(self, parsed_node):
        if self._make_carryover_info_fn is not None:
            return self._make_carryover_info_fn(parsed_node)
        return None



class MacroSpec(_SpecBase):
    r"""
    Stores the specification of a macro.

    This stores the macro name and instructions on how to parse the macro
    arguments.

    .. py:attribute:: macroname

       The name of the macro, without the leading backslash.

    .. py:attribute:: args_parser

       The parser instance that can understand this macro's arguments.  For
       standard LaTeX macros this is usually a
       :py:class:`MacroStandardArgsParser` instance.

       If you specify a string, then for convenience this is interpreted as an
       argspec argument for :py:class:`MacroStandardArgsParser` and such an
       instance is automatically created.
    """
    def __init__(self, macroname, arguments_spec_list=None, **kwargs):
        super(MacroSpec, self).__init__(arguments_spec_list=arguments_spec_list, **kwargs)

        self.macroname = macroname

    def __repr__(self):
        return 'MacroSpec(macroname={!r}, arguments_spec_list={!r})'.format(
            self.macroname, self.arguments_spec_list
        )

    def get_node_parser(self, token):
        return LatexMacroCallParser(token, self)




class EnvironmentSpec(_SpecBase):
    r"""
    Stores the specification of a LaTeX environment.

    This stores the environment name and instructions on how to parse any
    arguments provided after ``\begin{environment}<args>``.

    .. py:attribute:: environmentname

       The name of the environment, i.e., the argument of ``\begin{...}`` and
       ``\end{...}``.

    .. py:attribute:: args_parser

       The parser instance that can understand this environment's arguments.
       For standard LaTeX environment this is usually a
       :py:class:`MacroStandardArgsParser` instance.

       If you specify a string, then for convenience this is interpreted as an
       argspec argument for :py:class:`MacroStandardArgsParser` and such an
       instance is automatically created.

    .. py:attribute:: is_math_mode

       A boolean that indicates whether or not the contents is to be interpreted
       in Math Mode.  This would be True for environments like
       ``\begin{equation}``, ``\begin{align}``, etc., but False for
       ``\begin{figure}``, etc.

    .. note::

       Starred variants of environments (as in ``\begin{equation*}``) must not
       be specified using an argspec as for macros (e.g., `argspec='*'`).
       Rather, we need to define a separate environment spec for the starred
       variant with the star in the name itself (``EnvironmentSpec('equation*',
       None)``) because the star really is part of the environment name.  If you
       happened to use ``EnvironmentSpec('equation', '*')``, then the parser
       would recognize the expression ``\begin{equation}*`` but not
       ``\begin{equation*}``.
    """
    def __init__(self, environmentname, arguments_spec_list=None,
                 is_math_mode=False, body_parser=None, **kwargs):
        super(EnvironmentSpec, self).__init__(
            arguments_spec_list=arguments_spec_list,
            **kwargs
        )

        self.environmentname = environmentname
        self.is_math_mode = is_math_mode
        self.body_parser = body_parser


    def __repr__(self):
        return (
            'EnvironmentSpec(environmentname={!r}, arguments_spec_list={!r}, '
            'is_math_mode={!r}, body_parser={!r})'
            .format(
                self.environmentname, self.arguments_spec_list,
                self.is_math_mode, self.body_parser
            )
        )

    def get_node_parser(self, token):
        return LatexEnvironmentCallParser(token, self)




class SpecialsSpec(_SpecBase):
    r"""
    Specification of a LaTeX "special char sequence": an active char, a
    ligature, or some other non-macro char sequence that has a special meaning.

    For instance, '&', '~', and '``' are considered as "specials".

    .. py:attribute:: specials_chars
    
       The string (one or several characters) that has a special meaning. E.g.,
       '&', '~', '``', etc.

    .. py:attribute:: args_parser
    
       A parser (e.g. :py:class:`MacroStandardArgsParser`) that is invoked when
       the specials is encountered.  Can/should be set to `None` if the specials
       should not parse any arguments (e.g. '~').
    """
    def __init__(self, specials_chars, arguments_spec_list=None, **kwargs):
        super(SpecialsSpec, self).__init__(arguments_spec_list=arguments_spec_list, **kwargs)

        self.specials_chars = specials_chars

    def __repr__(self):
        return 'SpecialsSpec(specials_chars={!r}, arguments_spec_list={!r})'.format(
            self.specials_chars, self.arguments_spec_list
        )

    def get_node_parser(self, token):
        return LatexSpecialsCallParser(token, self)





### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

from ._argumentsparser import _LegacyPyltxenc2MacroArgsParserWrapper


def _legacy_pyltxenc2_init_from_args_parser(spec, kwargs):

    args_parser = kwargs.pop('args_parser', None)
    if args_parser is None:
        return

    # legacy support
    if spec.arguments_spec_list is not None:
        raise ValueError("You cannot specify both arguments_spec_list= and args_parser=")

    if isinstance(args_parser, _basestring):
        spec.arguments_spec_list = args_parser
        spec.arguments_parser = LatexArgumentsParser(args_parser)
    else:
        spec.arguments_spec_list = list(args_parser.argspec)
        spec.arguments_parser = _LegacyPyltxenc2MacroArgsParserWrapper(args_parser, spec)


setattr(_SpecBase, '_legacy_pyltxenc2_init_from_args_parser',
        _legacy_pyltxenc2_init_from_args_parser)


def _legacy_pyltxenc2_run_parse_args(spec, w, pos, parsing_state=None):
    r"""
    .. deprecated:: 3.0

        This method is not recommented starting from `pylatexenc 3`.  You can
        use parser stored as the `arguments_parser` attribute instead.
    """

    parsed, carryover_info = latex_walker.parse_content(
        spec.arguments_parser,
        latex_walker,
        w.make_token_reader(pos=pos),
        parsing_state,
    )

    if carryover_info is not None:
        return parsed, parsed.pos, parsed.len, carryover_info._to_legacy_pyltxenc2_dict()

    return parsed, parsed.pos, parsed.len


setattr(_SpecBase, 'parse_args', _legacy_pyltxenc2_run_parse_args)

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
