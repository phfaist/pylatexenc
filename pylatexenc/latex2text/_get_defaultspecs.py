# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2018 Philippe Faist
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
    initialized with a collection of text replacements for known macros and
    environments.

    The text replacements are grouped into the following categories, which you
    can select or discard individually with
    :py:meth:`pylatexenc.macrospec.LatexContextDb.filter_context()`:

      - ``'latex-base'`` — the bulk of the standard LaTeX constructs, including
        sectioning commands, font commands, accents, Greek letters, and the
        common math symbols, each mapped to a unicode text rendering.

      - ``'latex-base-subsuperscripts'`` — the text rendering of the ``^`` and
        ``_`` specials, i.e., the unicode superscripts and subscripts.  This
        category matches the one of the same name in
        :py:func:`pylatexenc.latexwalker.get_default_latex_context_db()`, so
        that discarding it in both databases restores the `pylatexenc 2`
        behavior in which ``^`` and ``_`` were ordinary characters.

      - ``'latex-approximations'`` — constructs for which the text rendering can
        only be an approximation of the typeset result, such as the alignment
        environments, the list environments, and matrix environments.

      - ``'latex-placeholders'`` — constructs that are replaced by a placeholder
        rather than by their contents, such as ``\includegraphics``, the
        cross-referencing macros (rendered as ``<ref>``) and the citation macros
        (rendered as ``<cit.>``).

      - ``'nonascii-specials'`` — the character sequences that LaTeX gives a
        special meaning, mapped to the corresponding unicode character (``~`` to
        a no-break space, ``---`` to an em dash, and so on).

      - ``'advanced-symbols'`` — the symbol macros that correspond to the
        built-in rules of :py:mod:`pylatexenc.latexencode`, i.e., the reverse
        direction of the unicode-to-LaTeX conversion.

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
        db.add_context_category(cat,
                                macros=catspecs['macros'],
                                environments=catspecs['environments'],
                                specials=catspecs['specials'])

    return db
