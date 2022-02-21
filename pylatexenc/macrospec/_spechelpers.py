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

from ._specclasses import MacroSpec, EnvironmentSpec, SpecialsSpec


# for Py3
_basestring = str

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _basestring = basestring
### END_PYTHON2_SUPPORT_CODE




def std_macro(macname, *args, **kwargs):
    r"""
    Return a macro specification for the given macro.  Syntax::
    
      spec = std_macro(macname, argspec)
      #  or
      spec = std_macro(macname, optarg, numargs)
      #  or
      spec = std_macro( (macname, argspec), )
      #  or
      spec = std_macro( (macname, optarg, numargs), )
      #  or
      spec = std_macro( spec ) # spec is already a `MacroSpec` -- no-op

    - `macname` is the name of the macro, without the leading backslash.

    - `argspec` is a string either characters "\*", "{" or "[", in which star
      indicates an optional asterisk character (e.g. starred macro variants),
      each curly brace specifies a mandatory argument and each square bracket
      specifies an optional argument in square brackets.  For example, "{{\*[{"
      expects two mandatory arguments, then an optional star, an optional
      argument in square brackets, and then another mandatory argument.

      `argspec` may also be `None`, which is the same as ``argspec=''``.

    - `optarg` may be one of `True`, `False`, or `None`, corresponding to these
      possibilities:

      + if `True`, the macro expects as first argument an optional argument in
        square brackets. Then, `numargs` specifies the number of additional
        mandatory arguments to the command, given in usual curly braces (or
        simply as one TeX token like a single macro)

      + if `False`, the macro only expects a number of mandatory arguments given
        by `numargs`. The mandatory arguments are given in usual curly braces
        (or simply as one TeX token like a single macro)

      + if `None`, then `numargs` is a string like `argspec` above.  I.e.,
        ``std_macro(macname, None, argspec)`` is the same as
        ``std_macro(macname, argspec)``.

    - `numargs`: depends on `optarg`, see above.
    
    To make environment specifications (:py:class:`EnvironmentSpec`) instead of
    a macro specification, use the function :py:func:`std_environment()`
    instead.

    The helper function :py:func:`std_environment()` is a shorthand for calling
    this function with additional keyword arguments.  An optional keyword
    argument `make_environment_spec=True` to the present function may be
    specified to return an `EnvironmentSpec` instead of a `MacroSpec`.  In this
    case, you can further specify the `environment_is_math_mode=True|False` to
    specify whether of not the environment represents a math mode.
    """

    if isinstance(macname, tuple):
        if len(args) != 0:
            raise TypeError("No positional arguments expected if first argument is a tuple")
        args = tuple(macname[1:])
        macname = macname[0]

    if isinstance(macname, MacroSpec):
        if len(args) != 0:
            raise TypeError("No positional arguments expected if first argument is a MacroSpec")
        return macname
    
    if isinstance(macname, EnvironmentSpec):
        if len(args) != 0:
            raise TypeError("No positional arguments expected if first argument is a EnvironmentSpec")
        return macname

    if len(args) == 1:
        # std_macro(macname, argspec)
        argspec = args[0]
    elif len(args) != 2:
        raise TypeError(
            "Wrong number of arguments for std_macro, macname={!r}, args={!r}".format(
                macname, args
            ))
    elif not args[0] and isinstance(args[1], _basestring):
        # argspec given in numargs
        argspec = args[1]
    else:
        argspec = ''
        if args[0]:
            argspec = '['
        argspec += '{'*args[1]

    if kwargs.get('make_environment_spec', False):
        return EnvironmentSpec(macname, argspec,
                               is_math_mode=kwargs.get('environment_is_math_mode', None))
    return MacroSpec(macname, argspec)


def std_environment(envname, *args, **kwargs):
    r"""
    Return an environment specification for the given environment.  Syntax::

      spec = std_environment(envname, argspec, is_math_mode=True|False|None)
      #  or
      spec = std_environment(envname, optarg, numargs, is_math_mode=True|False|None)
      #  or
      spec = std_environment( (envname, argspec), is_math_mode=True|False|None)
      #  or
      spec = std_environment( (envname, optarg, numargs), is_math_mode=True|False|None)
      #  or
      spec = std_environment( spec ) # spec is already a `EnvironmentSpec` -- no-op

    - `envname` is the name of the environment, i.e., the argument to
      ``\begin{...}``.

    - `argspec` is a string either characters "\*", "{" or "[", in which star
      indicates an optional asterisk character (e.g. starred environment
      variants), each curly brace specifies a mandatory argument and each square
      bracket specifies an optional argument in square brackets.  For example,
      "{{\*[{" expects two mandatory arguments, then an optional star, an
      optional argument in square brackets, and then another mandatory argument.

      `argspec` may also be `None`, which is the same as ``argspec=''``.

    .. note::

       See :py:class:`EnvironmentSpec` for an important remark about starred
       variants for environments.  TL;DR: a starred verison of an environment is
       defined as a separate `EnvironmentSpec` with the star in the name and
       *not* using an ``argspec='*'``.

    - `optarg` may be one of `True`, `False`, or `None`, corresponding to these
      possibilities:

      + if `True`, the environment expects as first argument an optional argument in
        square brackets. Then, `numargs` specifies the number of additional
        mandatory arguments to the command, given in usual curly braces (or
        simply as one TeX token like a single environment)

      + if `False`, the environment only expects a number of mandatory arguments given
        by `numargs`. The mandatory arguments are given in usual curly braces
        (or simply as one TeX token like a single environment)

      + if `None`, then `numargs` is a string like `argspec` above.  I.e.,
        ``std_environment(envname, None, argspec)`` is the same as
        ``std_environment(envname, argspec)``.

    - `numargs`: depends on `optarg`, see above.

    - `is_math_mode`: if set to True, then the environment represents a math
      mode environment (e.g., 'equation', 'align', 'gather', etc.), i.e., whose
      contents should be parsed in an appropriate math mode.  Note that
      `is_math_mode` *must* be given as a keyword argument, in contrast to all
      other arguments which must be positional (non-keyword) arguments.
    """
    is_math_mode = kwargs.pop('is_math_mode', None)
    kwargs2 = dict(kwargs)
    kwargs2.update(make_environment_spec=True,
                   environment_is_math_mode=is_math_mode)
    return std_macro(envname, *args, **kwargs2)


def std_specials(specials_chars):
    r"""
    Return a latex specials specification for the given character sequence.  Syntax::

      spec = std_specials(specials_chars)

    where `specials_chars` is the sequence of characters that has a special
    LaTeX meaning, e.g. ``&`` or ``''``.

    This helper function only allows to create specs for simple specials without
    any argument parsing.  For more complicated specials, you can instantiate a
    :py:class:`SpecialsSpec` directly.
    """
    return SpecialsSpec(specials_chars, None)

