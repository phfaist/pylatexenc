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

Since `pylatexenc 3`, the parsing work itself is carried out by *parser
objects*, which are specialized in parsing a given LaTeX construct and which
are provided by :py:mod:`pylatexenc.latexnodes.parsers`.  A
:py:class:`LatexWalker` instance holds the LaTeX code along with the
information required to parse it (the "latex context", see below), and it runs
such parser objects on that code with
:py:meth:`LatexWalker.parse_content()`.

The result of the parsing is a node tree, along with any information about
parsing state changes that the parsed code caused (say, a ``\newcommand``).
The nodes are instances of the classes provided in
:py:mod:`pylatexenc.latexnodes.nodes`, and lists of nodes are wrapped in a
:py:class:`~pylatexenc.latexnodes.nodes.LatexNodeList` object.  (For
compatibility with earlier versions, the node classes can also be imported
directly from :py:mod:`pylatexenc.latexwalker`.)

Simple example usage::

    >>> from pylatexenc.latexwalker import LatexWalker
    >>> from pylatexenc.latexnodes.nodes import LatexEnvironmentNode
    >>> w = LatexWalker(r"""
    ... \textbf{Hi there!} Here is \emph{a list}:
    ... \begin{enumerate}[label=(i)]
    ... \item One
    ... \item Two
    ... \end{enumerate}
    ... and $x$ is a variable.
    ... """)
    >>> nodelist, parsing_state_delta = w.parse_content()
    >>> nodelist[1].macroname
    'textbf'
    >>> (nodelist[1].pos, nodelist[1].pos_end)
    (1, 19)
    >>> nodelist[1].latex_verbatim()
    '\\textbf{Hi there!}'
    >>> nodelist[5].isNodeType(LatexEnvironmentNode)
    True
    >>> nodelist[5].environmentname
    'enumerate'
    >>> nodelist[7].latex_verbatim()
    '$x$'

Macro, environment and specials arguments are collected in a
:py:class:`pylatexenc.latexnodes.ParsedArguments` object stored as the node's
`nodeargd` attribute.  Use
:py:class:`pylatexenc.latexnodes.ParsedArgumentsInfo` to inspect them, by
position or by argument name::

    >>> from pylatexenc.latexnodes import ParsedArgumentsInfo
    >>> arguments = ParsedArgumentsInfo(node=nodelist[5]).get_all_arguments_info()
    >>> arguments[0].get_content_nodelist().latex_verbatim()
    'label=(i)'

You can also use `latexwalker` directly in command-line, producing a
human-readable node tree or JSON::

    $ latexwalker --code '\textit{italic} text'
    --- NODES ---

    * \textit
        {.}: Group:
            * 'italic'
    * ' text'

    -------------

    $ latexwalker --output-format=json --code '\textit{italic} text'
    {
      "nodelist": [
        {
          "nodetype": "LatexMacroNode",
          "pos": 0,
          "pos_end": 15,
          "parsing_state": {
    [...]

    $ latexwalker --help
    [...]

The parser can be influenced by specifying a collection of known macros and
environments (the "latex context") that are specified using
:py:class:`pylatexenc.macrospec.MacroSpec` and
:py:class:`pylatexenc.macrospec.EnvironmentSpec` objects in a
:py:class:`pylatexenc.macrospec.LatexContextDb` object.  See the doc of the
module :py:mod:`pylatexenc.macrospec` for more information.

.. versionchanged:: 3.0

   Parsing is now carried out by parser objects that are invoked via
   :py:meth:`LatexWalker.parse_content()`, in a significant API redesign.  See
   :doc:`What's new in pylatexenc 3 <new-in-pylatexenc-3>` for the differences
   between the two interfaces, and the :ref:`list of changes that might affect
   existing code <new-in-pylatexenc-3-possible-pitfall-changes>`.

   The `pylatexenc 2` interface of :py:class:`LatexWalker` —
   `get_latex_nodes()`, `get_token()`, `get_latex_expression()`,
   `get_latex_braced_group()`, `get_latex_environment()` and
   `get_latex_maybe_optional_arg()` — remains fully supported and should work in
   the vast majority of cases without code changes.
'''


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
