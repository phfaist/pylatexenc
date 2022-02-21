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

r'''
The ``latexwalker`` module provides a simple API for parsing LaTeX snippets,
and representing the contents using a data structure based on node classes.

LatexWalker will understand the syntax of most common macros.  However,
``latexwalker`` is NOT a replacement for a full LaTeX engine.  (Originally,
``latexwalker`` was designed to extract useful text for indexing for text
database searches of LaTeX content.)

Simple example usage::

    >>> from pylatexenc.latexwalker import LatexWalker, LatexEnvironmentNode
    >>> w = LatexWalker(r"""
    ... \textbf{Hi there!} Here is \emph{a list}:
    ... \begin{enumerate}[label=(i)]
    ... \item One
    ... \item Two
    ... \end{enumerate}
    ... and $x$ is a variable.
    ... """)
    >>> (nodelist, pos, len_) = w.get_latex_nodes(pos=0)
    >>> nodelist[0]
    LatexCharsNode(pos=0, len=1, chars='\n')
    >>> nodelist[1]
    LatexMacroNode(pos=1, len=18, macroname='textbf',
    nodeargd=ParsedMacroArgs(argnlist=[LatexGroupNode(pos=8, len=11,
    nodelist=[LatexCharsNode(pos=9, len=9, chars='Hi there!')],
    delimiters=('{', '}'))], argspec='{'), macro_post_space='')
    >>> nodelist[5].isNodeType(LatexEnvironmentNode)
    True
    >>> nodelist[5].environmentname
    'enumerate'
    >>> nodelist[5].nodeargd.argspec
    '['
    >>> nodelist[5].nodeargd.argnlist
    [LatexGroupNode(pos=60, len=11, nodelist=[LatexCharsNode(pos=61, len=9,
    chars='label=(i)')], delimiters=('[', ']'))]
    >>> nodelist[7].latex_verbatim()
    '$x$'

You can also use `latexwalker` directly in command-line, producing JSON or a
human-readable node tree::

    $ echo '\textit{italic} text' | latexwalker --output-format=json
    {
      "nodelist": [
        {
          "nodetype": "LatexMacroNode",
          "pos": 0,
          "len": 15,
          "macroname": "textit",
    [...]

    $ latexwalker --help
    [...]

The parser can be influenced by specifying a collection of known macros and
environments (the "latex context") that are specified using
:py:class:`pylatexenc.macrospec.MacroSpec` and
:py:class:`pylatexenc.macrospec.EnvironmentSpec` objects in a
:py:class:`pylatexenc.macrospec.LatexContextDb` object.  See the doc of the
module :py:mod:`pylatexenc.macrospec` for more information.
'''

from __future__ import print_function, unicode_literals


import logging
logger = logging.getLogger(__name__)



from .. import macrospec


# ------------------------------------------------------------------------------


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE
from ..latexnodes._exctypes import *
from ..latexnodes.nodes import *
from ..latexnodes._token import LatexToken
### END_PYLATEXENC2_LEGACY_SUPPORT_CODE



from ..latexnodes import ParsingState

from ._walker import LatexWalker


### BEGIN_PYLATEXENC_GET_DEFAULT_SPECS_FN
from ._get_defaultspecs import get_default_latex_context_db
### END_PYLATEXENC_GET_DEFAULT_SPECS_FN


### BEGIN_PYLATEXENC1_LEGACY_SUPPORT_CODE
from ._legacy_py1x import (
    MacrosDef,
    default_macro_dict,
    get_token,
    get_latex_expression,
    get_latex_maybe_optional_arg,
    get_latex_braced_group,
    get_latex_environment,
    get_latex_nodes,
)
### END_PYLATEXENC1_LEGACY_SUPPORT_CODE



### BEGIN_LATEXWALKER_HELPERS
from ._helpers import (
    nodelist_to_latex,
    put_in_braces,
    disp_node,
    make_json_encoder,
)
### END_LATEXWALKER_HELPERS
