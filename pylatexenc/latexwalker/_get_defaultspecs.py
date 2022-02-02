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


# don't define this function in the `_defaultspecs.py` source file because we
# would like to be able to define this function without having to actually load
# the entire default specs module.

def get_default_latex_context_db():
    r"""
    Return a :py:class:`pylatexenc.macrospec.LatexContextDb` instance
    initialized with a collection of known macros and environments.

    TODO: document categories.

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
