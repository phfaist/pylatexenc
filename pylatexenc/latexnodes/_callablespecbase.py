# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2022 Philippe Faist
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



class CallableSpecBase(object):
    r"""
    The base class for macro, environment, and specials spec classes (see the
    :py:mod:`pylatexenc.macrospec` module).

    As far as this :py:mod:`latexnodes` module's classes are concerned, a spec
    object is simply something that can provide a parser to parse the given
    construct (macro, environment, or specials).

    The spec object should implement :py:meth:`get_node_parser()`, and it should
    return a parser instance that can be used to parse the entire construct.

    See :py:class:`macrospec.MacroSpec` for how this is implemented in the
    :py:mod:`pylatexenc.macrospec` module.

    .. versionadded:: 3.0
    
       The :py:class:`CallableSpecBase` class was added in `pylatexenc 3.0`.
    """

    def get_node_parser(self, token):
        raise RuntimeError("Subclasses must reimplement get_node_parser()")
