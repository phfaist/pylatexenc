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

from ._argparsers import MacroStandardArgsParser


# for Py3
_basestring = str

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
## End Py2 support code




class MacroSpec(object):
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
    def __init__(self, macroname, args_parser=MacroStandardArgsParser(), **kwargs):
        super(MacroSpec, self).__init__(**kwargs)
        self.macroname = macroname
        if isinstance(args_parser, _basestring):
            self.args_parser = MacroStandardArgsParser(args_parser)
        else:
            self.args_parser = args_parser

    def parse_args(self, *args, **kwargs):
        r"""
        Shorthand for calling the :py:attr:`args_parser`\ 's `parse_args()` method.
        See :py:class:`MacroStandardArgsParser`.
        """
        return self.args_parser.parse_args(*args, **kwargs)

    def __repr__(self):
        return 'MacroSpec(macroname=%r, args_parser=%r)'%(self.macroname, self.args_parser)



class EnvironmentSpec(object):
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
    def __init__(self, environmentname, args_parser=MacroStandardArgsParser(),
                 is_math_mode=False, **kwargs):
        super(EnvironmentSpec, self).__init__(**kwargs)
        self.environmentname = environmentname
        if isinstance(args_parser, _basestring):
            self.args_parser = MacroStandardArgsParser(args_parser)
        else:
            self.args_parser = args_parser
        self.is_math_mode = is_math_mode

    def parse_args(self, *args, **kwargs):
        r"""
        Shorthand for calling the :py:attr:`args_parser`\ 's `parse_args()` method.
        See :py:class:`MacroStandardArgsParser`.
        """
        return self.args_parser.parse_args(*args, **kwargs)

    def __repr__(self):
        return 'EnvironmentSpec(environmentname=%r, args_parser=%r, is_math_mode=%r)'%(
            self.environmentname, self.args_parser, self.is_math_mode
        )



class SpecialsSpec(object):
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
    def __init__(self, specials_chars,
                 args_parser=None,
                 **kwargs):
        super(SpecialsSpec, self).__init__(**kwargs)
        self.specials_chars = specials_chars
        self.args_parser = args_parser

    def parse_args(self, *args, **kwargs):
        r"""
        Basically a shorthand for calling the :py:attr:`args_parser`\ 's
        `parse_args()` method.  See :py:class:`MacroStandardArgsParser`.
        
        If however the py:attr:`args_parser` attribute is `None`, then this
        method returns `None`.
        """
        if self.args_parser is None:
            return None
        return self.args_parser.parse_args(*args, **kwargs)

    def __repr__(self):
        return 'SpecialsSpec(specials_chars=%r, args_parser=%r)'%(
            self.specials_chars, self.args_parser
        )


