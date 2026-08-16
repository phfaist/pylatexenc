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


# don't define this function in the `_defaultspecs.py` source file because we
# would like to be able to define this function without having to actually load
# the entire default specs module.

def get_default_latex_context_db():
    r"""
    Return a :py:class:`pylatexenc.macrospec.LatexContextDb` instance
    initialized with a collection of known macros and environments.

    The definitions are grouped into the following categories, which you can
    select or discard individually with
    :py:meth:`pylatexenc.macrospec.LatexContextDb.filter_context()`:

      - ``'latex-paragraph'`` — the paragraph break (a blank line) as a
        "specials" definition.

      - ``'latex-base'`` — the bulk of the standard LaTeX macros, environments
        and specials, i.e., what you can expect to be available in a plain LaTeX
        document.

      - ``'latex-base-subsuperscripts'`` — the ``^`` and ``_`` characters as
        "specials" definitions.  They belong to the base LaTeX definitions but
        have a category of their own, so that you can discard them and get back
        the `pylatexenc 2` behavior in which ``^`` and ``_`` were ordinary
        characters.

      - ``'nonascii-specials'`` — character sequences that LaTeX gives a special
        meaning: the non-breaking space ``~``, the quote and dash "fake
        ligatures" (a pair of backticks, ``''``, ``--`` and ``---``), and the
        inverted punctuation marks (an exclamation mark or a question mark
        followed by a backtick).

      - ``'verbatim'`` — the ``\verb`` macro and the ``{verbatim}``
        environment.

      - ``'lstlisting'`` — the ``{lstlisting}`` environment of the `listings`
        package, whose body is also read verbatim.

      - ``'theorems'`` — theorem-like environments (``{theorem}``, ``{lemma}``,
        ``{proof}``, etc., along with common short forms).

      - ``'enumitem'`` — the ``{enumerate}``, ``{itemize}`` and ``{description}``
        environments with the optional argument that the `enumitem` package
        gives them.

      - ``'natbib'`` — the citation macros of the `natbib` package (``\citet``,
        ``\citep``, etc.).

      - ``'latex-ethuebung'`` — macros of the `ethuebung` LaTeX package.

    If you want to add your own definitions, you should use the
    :py:meth:`pylatexenc.macrospec.LatexContextDb.add_context_category()`
    method.  If you would like to override some definitions, use that method
    with the argument `prepend=True`.  See docs for
    :py:meth:`pylatexenc.macrospec.LatexContextDb.add_context_category()`.

    If there are too many macro/environment definitions, or if there are some
    irrelevant ones, you can always filter the returned database using
    :py:meth:`pylatexenc.macrospec.LatexContextDb.filter_context()`.

    .. versionadded:: 2.0
 
       The :py:class:`pylatexenc.macrospec.LatexContextDb` class as well as this
       method, were all introduced in `pylatexenc 2.0`.
    """

    from .. import macrospec
    from ._defaultspecs import specs

    db = macrospec.LatexContextDb()
    
    for cat, catspecs in specs:
        db.add_context_category(
            cat,
            macros=catspecs['macros'],
            environments=catspecs['environments'],
            specials=catspecs['specials']
        )

    db.set_unknown_macro_spec(macrospec.MacroSpec(''))
    db.set_unknown_environment_spec(macrospec.EnvironmentSpec(''))

    return db

#
