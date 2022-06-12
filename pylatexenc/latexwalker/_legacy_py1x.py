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

from .. import macrospec
from .. import _util

from ._walker import LatexWalker

from ._get_defaultspecs import get_default_latex_context_db


# provide an interface compatibile with pylatexenc 1.x
def MacrosDef(macname, optarg, numargs):
    r"""
    .. deprecated:: 2.0

       Use :py:func:`pylatexenc.macrospec.std_macro` instead which does the same
       thing, or invoke the :py:class:`~pylatexenc.macrospec.MacroSpec` class
       directly (or a subclass).

       In `pylatexenc 1.x`, `MacrosDef` was a class.  Since `pylatexenc 2.0`,
       `MacrosDef` is a function which returns a
       :py:class:`~pylatexenc.macrospec.MacroSpec` instance.  In this way the
       earlier idiom ``MacrosDef(...)`` still works in `pylatexenc 2`.  The
       field names of the constructed object might have changed since
       `pylatexenc 1.x`, so you might have to adapt existing code if you were
       accessing individual fields of `MacrosDef` objects.

       In the object returned by `MacrosDef()`, we provide the legacy attributes
       `macname`, `optarg`, and `numargs`, so that existing code accessing those
       properties can continue to work.
    """
    _util.pylatexenc_deprecated_2(
        "`pylatexenc.latexwalker.MacrosDef` is now obsolete. "
        "It should still work in most use cases, but new code should use "
        "`pylatexenc.macrospec.MacroSpec` instead."
    )

    m = macrospec.std_macro(macname, optarg, numargs)
    # make accessible legacy attributes
    m.macname = m.macroname
    m.optarg = optarg
    m.numargs = numargs
    # also, make the macro args parser ignore any leading '*'-s to emulate
    # pylatexenc 1.x behavior
    m.args_parser._like_pylatexenc1x_ignore_leading_star = True
    return m


default_macro_dict = _util.LazyDict(
    generate_dict_fn=lambda: dict([
        (m.macroname, m)
        for m in get_default_latex_context_db().iter_macro_specs()
    ])
)
r"""
.. deprecated:: 2.0

   Use :py:func:`get_default_latex_context_db()` instead, or create your own
   :py:class:`pylatexenc.macrospec.LatexContextDb` object.


Provide an access to the default macro specs for `latexwalker` in a form
that is compatible with `pylatexenc 1.x`\ 's `default_macro_dict` module-level
dictionary.

This is implemented using a custom lazy mutable mapping, which behaves just like
a regular dictionary but that loads the data only once the dictionary is
accessed.  In this way the default latex specs into a python dictionary unless
they are actually queried or modified, and thus users of `pylatexenc 2.0` that
don't rely on the default macro/environment definitions shouldn't notice any
decrease in performance.
"""
    

# ------------------------------------------------------------------------------

def get_token(s, pos, brackets_are_chars=True, environments=True, **parse_flags):
    """
    Parse the next token in the stream.

    Returns a `LatexToken`. Raises `LatexWalkerEndOfStream` if end of stream reached.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_token()` instead.
    """
    return LatexWalker(s, **parse_flags).get_token(pos=pos,
                                                   brackets_are_chars=brackets_are_chars,
                                                   environments=environments)


def get_latex_expression(s, pos, **parse_flags):
    """
    Reads a latex expression, e.g. macro argument. This may be a single char, an escape
    sequence, or a expression placed in braces.

    Returns a tuple `(<LatexNode instance>, pos, len)`. `pos` is the first char of the
    expression, and `len` is its length.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_expression()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_expression(pos=pos)


def get_latex_maybe_optional_arg(s, pos, **parse_flags):
    """
    Attempts to parse an optional argument. Returns a tuple `(groupnode, pos, len)` if
    success, otherwise returns None.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_maybe_optional_arg()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_maybe_optional_arg(pos=pos)

    
def get_latex_braced_group(s, pos, brace_type='{', **parse_flags):
    """
    Reads a latex expression enclosed in braces {...}. The first token of `s[pos:]` must
    be an opening brace.

    Returns a tuple `(node, pos, len)`. `pos` is the first char of the
    expression (which has to be an opening brace), and `len` is its length,
    including the closing brace.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_braced_group()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_braced_group(pos=pos, brace_type=brace_type)


def get_latex_environment(s, pos, environmentname=None, **parse_flags):
    """
    Reads a latex expression enclosed in a \\begin{environment}...\\end{environment}. The first
    token in the stream must be the \\begin{environment}.

    Returns a tuple (node, pos, len) with node being a :py:class:`LatexEnvironmentNode`.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_environment()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_environment(pos=pos,
                                                               environmentname=environmentname)

def get_latex_nodes(s, pos=0, stop_upon_closing_brace=None, stop_upon_end_environment=None,
                    stop_upon_closing_mathmode=None, **parse_flags):
    """
    Parses latex content `s`.

    Returns a tuple `(nodelist, pos, len)` where nodelist is a list of `LatexNode` 's.

    If `stop_upon_closing_brace` is given, then `len` includes the closing brace, but the
    closing brace is not included in any of the nodes in the `nodelist`.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_nodes()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_nodes(
        stop_upon_closing_brace=stop_upon_closing_brace,
        stop_upon_end_environment=stop_upon_end_environment,
        stop_upon_closing_mathmode=stop_upon_closing_mathmode
    )




