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

import logging
logger = logging.getLogger(__name__)

from ..latexnodes import CallableSpecBase

from ._argumentsparser import LatexArgumentsParser, LatexNoArgumentsParser
from ._macrocallparser import (
    LatexMacroCallParser, LatexEnvironmentCallParser, LatexSpecialsCallParser
)


# for Py3
_basestring = str

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _basestring = basestring
### END_PYTHON2_SUPPORT_CODE


_legacy_pyltxenc2_do = lambda *args: None


class _SpecBase(CallableSpecBase):
    def __init__(self, arguments_spec_list=None, make_carryover_info=None,
                 finalize_node=None, **kwargs):

        self.arguments_spec_list = arguments_spec_list

        use_legacy_args_parser = _legacy_pyltxenc2_do(
            'SpecBase_init_from_args_parser', self, arguments_spec_list, kwargs
        )

        super(_SpecBase, self).__init__(**kwargs)

        if not use_legacy_args_parser:
            if self.arguments_spec_list:
                self.arguments_parser = LatexArgumentsParser(arguments_spec_list)
            else:
                self.arguments_parser = LatexNoArgumentsParser()

        self._fn_make_carryover_info = make_carryover_info
        self._fn_finalize_node = finalize_node


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

    @property
    def args_parser(self):
        return self.arguments_parser

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE


    def finalize_node(self, node):
        r"""
        ................

        MUST RETURN the new node instance.

        This is called from the LatexMacroCallParser instance, i.e., this
        function won't be called by default if you override get_node_parser()
        and return a different parser instance.
        """

        if self._fn_finalize_node is not None:
            return self._fn_finalize_node(node)

        return node


    def make_carryover_info(self, parsed_node):
        r"""
        If applicable, create a :py:class:`CarryoverInformation` class to convey any
        changes in the parsing state after completing this callable node.
        
        The default implementation returns `None`.  You do not have to override
        this method.  You can specify a custom callable to
        `make_carryover_info=...` in the constructor, and the constructor will
        reassign the attribute `spec.make_carryover_info` to that callable.


        This is called from the LatexMacroCallParser instance, i.e., this
        function won't be called by default if you override get_node_parser()
        and return a different parser instance.

        """

        if self._fn_make_carryover_info is not None:
            return self._fn_make_carryover_info(parsed_node)

        return None


    def needs_arguments(self):
        for arg in self.arguments_spec_list:
            if arg.spec.is_required():
                return True
        return False

    def __repr__(self):
        return (
            self.__class__.__name__ + "(" +
            ", ".join([ "{}={!r}".format(k,v)
                        for (k,v) in self.__dict__.items()
                        if not k.startswith("_") ])
            + ")"
        )
    


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
        make_carryover_info = kwargs.pop('make_carryover_info', None)
        super(MacroSpec, self).__init__(arguments_spec_list=arguments_spec_list,
                                        make_carryover_info=make_carryover_info,
                                        **kwargs)

        self.macroname = macroname

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

       Indicates if the contents is to be interpreted in Math Mode.  This would
       be `True` for environments like ``\begin{equation}``, ``\begin{align}``,
       etc., but is left to `None` for ``\begin{figure}``, etc.

       (In `pylatexenc 2`, this field would be `False` for general environments
       instead of `None`.  Since `pylatexenc 3`, setting this field to `False`
       indicates that the environment content is expressedly text/non-math
       mode.)

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
    def __init__(self, environmentname, arguments_spec_list=None, **kwargs):

        is_math_mode = kwargs.pop('is_math_mode', False)
        body_parser = kwargs.pop('body_parser', None)
        make_carryover_info = kwargs.pop('make_carryover_info', None)

        super(EnvironmentSpec, self).__init__(
            arguments_spec_list=arguments_spec_list,
            make_carryover_info=make_carryover_info,
            **kwargs
        )

        self.environmentname = environmentname
        self.is_math_mode = is_math_mode
        self.body_parser = body_parser

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

_legacy_pyltxenc2_do = \
    lambda what, *args: globals()['_legacy_pyltxenc2_'+what](*args)


def _legacy_pyltxenc2_SpecBase_init_from_args_parser(spec, arguments_spec_list, kwargs):

    def _make_carryover_info(parsed_node, spec=spec):
        carryover_info = getattr(parsed_node.nodeargd, '_legacy_pyltxenc2_set_carryover_info',
                                 None)
        return carryover_info

    def _init_with_legacy_wrapper(args_parser):
        logger.debug("Initializing spec with legacy args parser %r", args_parser)
        spec.arguments_spec_list = list(args_parser.argspec)
        spec.arguments_parser = _LegacyPyltxenc2MacroArgsParserWrapper(args_parser, spec)
        spec.make_carryover_info = _make_carryover_info
        return True

    args_parser = kwargs.pop('args_parser', None)
    if args_parser is None:

        from ._pyltxenc2_argparsers import MacroStandardArgsParser
        if isinstance(arguments_spec_list, MacroStandardArgsParser):
            return _init_with_legacy_wrapper(arguments_spec_list)

        return False

    # legacy support
    if spec.arguments_spec_list is not None:
        raise ValueError("You cannot specify both arguments_spec_list= and args_parser=")

    if isinstance(args_parser, _basestring):
        spec.arguments_spec_list = args_parser
        spec.arguments_parser = LatexArgumentsParser(args_parser)
    else:
        return _init_with_legacy_wrapper(args_parser)

    return False



def _legacy_pyltxenc2_SpecBase_parse_args(spec, w, pos, parsing_state=None):
    r"""
    .. deprecated:: 3.0

        This method is not recommented starting from `pylatexenc 3`.  You can
        use parser stored as the `arguments_parser` attribute instead.
    """

    parsed, carryover_info = w.parse_content(
        spec.arguments_parser,
        token_reader=w.make_token_reader(pos=pos),
        parsing_state=parsing_state,
    )

    if carryover_info is not None:
        return parsed, parsed.pos, parsed.len, carryover_info._to_legacy_pyltxenc2_dict()

    return parsed, parsed.pos, parsed.len

_SpecBase.parse_args = _legacy_pyltxenc2_SpecBase_parse_args


### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
