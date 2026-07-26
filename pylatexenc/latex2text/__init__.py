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

r"""
A simplistic, heuristic LaTeX code parser allowing to returns a text-only
approximation.  Suitable, e.g. for indexing tex code in a database for full text
searching.

The main class is :py:class:`LatexNodes2Text`.  For a quick start, try::

    from pylatexenc.latex2text import LatexNodes2Text

    latex = "... LaTeX code ..."
    text = LatexNodes2Text().latex_to_text(latex)

You may also use the command-line version of `latex2text`::

    $ echo '\textit{italic} \`acc\^ented text' | latex2text
    𝑖𝑡𝑎𝑙𝑖𝑐 àccênted text

The italics come from the `math_mode='fancy'` rendering, which is the default;
see :py:class:`LatexNodes2Text`.  Use `math_mode='text'` (``latex2text
--math-mode=text``) for the plainer rendering that `pylatexenc 2` produced.

"""

import re
import inspect
import textwrap




#import pylatexenc
from .. import latexwalker
from ..latexnodes import nodes as latexnodes_nodes
from ..latexnodes import parsers as latexnodes_parsers
from .. import macrospec
from .. import _util

import logging
logger = logging.getLogger(__name__)



class MacroTextSpec(object):
    """
    A specification of how to obtain a textual representation of a macro.

    .. py:attribute:: macroname

       The name of the macro (no backslash)

    .. py:attribute:: simplify_repl

       The replacement text of the macro invocation.  This is either a string or
       a callable:

         - If `simplify_repl` is a string, this string is used as the text
           representation of this macro node.

           The string may contain a single '%s' replacement placeholder which
           will be replaced by the concatenated textual representation of all
           macro arguments.  Alternatively, the string may contain '%(<n>)s'
           (where `<n>` is an integer) to refer to the n-th argument (starting
           at '%(1)s').  You cannot mix the two %-formatting styles.

         - If `simplify_repl` is a callable, it should accept the corresponding
           :py:class:`pylatexenc.latexwalker.LatexMacroNode` as an argument.

           The callable will be inspected to see what other arguments it
           accepts.  If it accepts an argument named `l2tobj`, the
           :py:class:`LatexNodes2Text` instance is provided to that argument.
           If it accepts an argument named `macroname`, the name of the macro is
           provided to that argument.  If it accepts an argument named
           `l2tstate`, the :py:class:`TextConversionState` that applies where
           this macro sits in the node tree is provided to that argument.

    .. py:attribute:: discard

       If set to `True`, then the macro call is discarded, i.e., it is converted
       to an empty string.


    .. versionadded:: 2.0

       The class :py:class:`MacroTextSpec` was introduced in `pylatexenc
       2.0` to succeed to the previously named `MacroDef` class.
    """
    def __init__(self, macroname, simplify_repl=None, discard=None):
        super(MacroTextSpec, self).__init__()
        self.macroname = macroname
        self.discard = True if (discard is None) else discard
        self.simplify_repl = simplify_repl


class EnvironmentTextSpec(object):
    """
    A specification of how to obtain a textual representation of an environment.

    .. py:attribute:: environmentname

       The name of the environment

    .. py:attribute:: simplify_repl

       The replacement text of the environment.  This is either a string or a
       callable:

         - If `simplify_repl` is a string, this string is used as the text
           representation of this environment node.

           The string may contain a single '%s' replacement placeholder, in
           which the (processed) environment body will be substituted.

           Alternatively, the `simplify_repl` string may contain '%(<n>)s'
           (where `<n>` is an integer) to refer to the n-th argument after
           ``\begin{environment}`` (starting at '%(1)s').  The body of the
           environment has to be referred to with `%(body)s`.

           You cannot mix the two %-formatting styles.

         - If `simplify_repl` is a callable, it should accept the corresponding
           :py:class:`pylatexenc.latexwalker.LatexEnvironmentNode` as an
           argument.

           The callable will be inspected to see what other arguments it
           accepts.  If it accepts an argument named `l2tobj`, the
           :py:class:`LatexNodes2Text` instance is provided to that argument.
           If it accepts an argument named `environmentname`, the name of the
           environment is provided to that argument.  If it accepts an argument
           named `l2tstate`, the :py:class:`TextConversionState` that applies
           where this environment sits in the node tree is provided to that
           argument.

    .. py:attribute:: discard

       If set to `True`, then the full environment is discarded, i.e., it is
       converted to an empty string.


    .. versionadded:: 2.0

       The class :py:class:`EnvironmentTextSpec` was introduced in `pylatexenc
       2.0` to succeed to the previously named `EnvDef` class.
    """
    def __init__(self, environmentname, simplify_repl=None, discard=False):
        super(EnvironmentTextSpec, self).__init__()
        self.environmentname = environmentname
        self.simplify_repl = simplify_repl
        self.discard = discard


class SpecialsTextSpec(object):
    """
    A specification of how to obtain a textual representation of latex specials.

    .. py:attribute:: specials_chars

       The sequence of special LaTeX characters

    .. py:attribute:: simplify_repl

       The replacement text for the given latex specials.  This is either a
       string or a callable:

         - If `simplify_repl` is a string, this string is used as the text
           representation of this specials node.

           The string may contain a single '%s' replacement placeholder which
           will be replaced by the concatenated textual representation of all
           macro arguments.

           Alternatively, the string may contain '%(<n>)s' (where `<n>` is an
           integer) to refer to the n-th argument (starting at '%(1)s').  You
           cannot mix the two %-formatting styles.

         - If `simplify_repl` is a callable, it should accept the corresponding
           :py:class:`pylatexenc.latexwalker.LatexSpecialsNode` as an argument.

           The callable will be inspected to see what other arguments it
           accepts.  If it accepts an argument named `l2tobj`, the
           :py:class:`LatexNodes2Text` instance is provided to that argument.
           If it accepts an argument named `specials_chars`, the characters that
           were parsed this "latex specials" node are provided to that argument.
           If it accepts an argument named `l2tstate`, the
           :py:class:`TextConversionState` that applies where these specials
           sit in the node tree is provided to that argument.

    .. versionadded:: 2.0

       Latex specials were introduced in `pylatexenc 2.0`.
    """
    def __init__(self, specials_chars, simplify_repl=None):
        super(SpecialsTextSpec, self).__init__()
        self.specials_chars = specials_chars
        self.simplify_repl = simplify_repl



def EnvDef(envname, simplify_repl=None, discard=False):
    r"""
    .. deprecated:: 2.0

       Instantiate a :py:class:`EnvironmentTextSpec` instead.

       Since `pylatexenc 2.0`, `EnvDef` is a function which returns a
       :py:class:`~pylatexenc.macrospec.EnvironmentTextSpec` instance.  In this
       way the earlier idiom ``EnvDef(...)`` still works in `pylatexenc 2`.
    """
    e = EnvironmentTextSpec(environmentname=envname, simplify_repl=simplify_repl,
                            discard=discard)
    e.envname = e.environmentname
    return e

def MacroDef(macname, simplify_repl=None, discard=None):
    r"""
    .. deprecated:: 2.0

       Instantiate a :py:class:`MacroTextSpec` instead.

       Since `pylatexenc 2.0`, `MacroDef` is a function which returns a
       :py:class:`~pylatexenc.macrospec.MacroTextSpec` instance.  In this way
       the earlier idiom ``MacroDef(...)`` still works in `pylatexenc 2`.
    """
    m = MacroTextSpec(macroname=macname, simplify_repl=simplify_repl, discard=discard)
    m.macname = m.macroname
    return m



#
# NOTE: while internally documented (but not in the public docs), these fmt_***
# functions should be considered internal API and should not be relied upon for
# the moment in production code.  I intend to change some things in how common
# rendering procedures (for equations, for non-textual content that probably
# requires a placeholder, etc.) by some other means such as by extending the
# latex context database object directly.
#

def fmt_equation_environment(envnode, l2tobj):
    r"""
    Can be used as callback for display equation environments.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """

    return l2tobj.math_node_to_text(envnode)


def fmt_input_macro(macronode, l2tobj):
    r"""
    This function can be used as callback in :py:class:`MacroTextSpec` for
    ``\input`` or ``\include`` macros.  The `macronode` must be a macro node
    with a single argument.  If
    :py:meth:`~LatexNodes2Text.set_tex_input_directory()` was called
    with a nonempty input directory in the :py:class:`LatexNodes2Text` object,
    then this method reads the contents of the file name in the macro argument
    according to the provided settings.  Otherwise, returns an empty string.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """
    return l2tobj._input_node_simplify_repl(macronode)


def placeholder_node_formatter(placeholdertext, block=True):
    r"""
    This function returns a callable that can be used in
    :py:class:`MacroTextSpec`, :py:class:`EnvironmentTextSpec`, or
    :py:class:`SpecialsTextSpec` for latex nodes that do not have a good textual
    representation, providing as text replacement the simple placeholder text
    ``'< P L A C E H O L D E R   T E X T >'``.

    If `block=True` (the default), the placeholder text is typeset in an
    indented block on its own.  Otherwise, it is typeset inline.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """
    return  lambda n, l2tobj, pht=placeholdertext: \
        _do_fmt_placeholder_node(pht, l2tobj, block=block)

def _do_fmt_placeholder_node(placeholdertext, l2tobj, block=True):
    # spaces added so that database indexing doesn't index the word "array" or
    # "pmatrix"
    txt = '< ' + " ".join(placeholdertext) + ' >'
    if block:
        return l2tobj._fmt_indented_block(txt, indent='    ')
    return ' ' + txt + ' '

def fmt_placeholder_node(node, l2tobj):
    r"""
    This function can be used as callable in :py:class:`MacroTextSpec`,
    :py:class:`EnvironmentTextSpec`, or :py:class:`SpecialsTextSpec` for latex
    nodes that do not have a good textual representation.  The text replacement
    is the placeholder text
    ``'< N A M E   O F   T H E   M A C R O   O R   E N V I R O N M E N T >'``.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """

    for att in ('macroname', 'environmentname', 'specials_chars'):
        if hasattr(node, att):
            name = getattr(node, att)
            break
    else:
        name = '<unknown>'

    return _do_fmt_placeholder_node(name, l2tobj)


def fmt_matrix_environment_node(node, l2tobj):
    r"""
    This function can be used as a callable in :py:class:`EnvironmentTextSpec`
    for matrix-like environments like ``\begin{bmatrix}...\end{bmatrix}``.

    The contents is parsed by separating columns with ``&``'s and rows with
    ``\\``'s, and is rendered in the form ``[  a11  a12  ;  a21  a22  ]``.

    .. versionadded:: 2.8

       This function was introduced in `pylatexenc 2.8`.

    .. versionchanged:: 3.0

       In math mode with ``math_mode='fancy'``, this function returns a
       *math piece* (see :py:meth:`LatexNodes2Text.make_math_piece()`)
       instead of a string, so
       that the formula joiner treats the whole object as a single item and
       does not look inside it.  The rendering itself is unchanged.
    """

    class StateType:
        def __init__(self):
            self.matrix_rows = []
            self.buffer_this_column = []
            self.buffer_nodes = []

        def add_content(self, node):
            self.buffer_nodes.append(node)

        def new_column(self):
            if self.buffer_nodes:
                # str() because the contents of a cell are a formula of their
                # own, and in the 'fancy' math mode rendering a formula
                # gives a math piece rather than a string
                self.buffer_this_column.append(
                    str(l2tobj.nodelist_to_text(self.buffer_nodes)) .strip()
                )
            self.buffer_nodes = []

        def new_row(self):
            self.new_column()
            self.matrix_rows.append( self.buffer_this_column )
            self.buffer_this_column = []
            
    state = StateType()

    # iterate the nodelist and find column and row separators
    for n in node.nodelist:
        if n.isNodeType(latexwalker.LatexSpecialsNode) and n.specials_chars == '&':
            # column separator
            state.new_column()
            continue
        if n.isNodeType(latexwalker.LatexMacroNode) and n.macroname == "\\":
            # row separator
            state.new_row()
            continue
        state.add_content(n)

    state.new_row() # finish the last row

    # now format the contents as array --
    block = _MathBlockPiece(rows=state.matrix_rows, delimiters=('[', ']',))

    if l2tobj.math_mode == 'fancy' and l2tobj.state.in_math_mode:
        # The 'fancy' math mode hands the whole object to the joiner as a
        # single item, so that the joiner treats it as opaque and never
        # looks inside it; the brackets are what shows where it begins and where
        # it ends, so both of its edges are of the 'block' class, which the
        # joiner treats as delimiters.  The rendering is the same either way.
        return block

    return block.to_text()

#
# List environments (itemize, enumerate, description, ...).
#
# The item markers mirror LaTeX's own defaults for the successive nesting
# levels, so that nested lists remain readable in the text rendering.
#

_itemize_markers = (
    u"\N{BULLET}",
    u"\N{EN DASH}",
    u"*",
    u"\N{MIDDLE DOT}",
)

def _fmt_counter_alph(value):
    # 1 -> 'a', 26 -> 'z', 27 -> 'aa', ...
    s = ''
    while value > 0:
        value, r = divmod(value-1, 26)
        s = chr(ord('a')+r) + s
    return s

_roman_numerals = (
    (1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'), (90, 'xc'),
    (50, 'l'), (40, 'xl'), (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i'),
)

def _fmt_counter_roman(value):
    s = ''
    for numvalue, numsym in _roman_numerals:
        while value >= numvalue:
            s += numsym
            value -= numvalue
    return s

_enumerate_markers = (
    lambda value: '{}.'.format(value),
    lambda value: '({})'.format(_fmt_counter_alph(value)),
    lambda value: '{}.'.format(_fmt_counter_roman(value)),
    lambda value: '{}.'.format(_fmt_counter_alph(value).upper()),
)

_list_environment_kinds = {
    'itemize': 'itemize',
    'list': 'itemize',
    'trivlist': 'itemize',
    'enumerate': 'enumerate',
    'exenumerate': 'enumerate',
    'description': 'description',
}


class _ListLevel(object):
    r"""
    One nesting level of a list environment.  Instances of this class are what
    make up the `list_stack` field of a
    :py:class:`TextConversionState` object.

    .. py:attribute:: environmentname

       The name of the list environment that opened this level.

    .. py:attribute:: kind

       One of 'itemize', 'enumerate' or 'description'; it determines how the
       item markers are generated.

    .. py:attribute:: depth

       The nesting depth of this level among all list environments, starting at
       1 for an outermost list.

    .. py:attribute:: marker_depth

       The nesting depth of this level among the list environments of the same
       `kind`, starting at 1.  This is what selects the marker style, so that,
       as in LaTeX, an `itemize` nested inside an `enumerate` still uses the
       first-level itemize marker.

    .. py:attribute:: counter

       How many items have been seen so far in this level.
    """
    def __init__(self, environmentname, kind, depth, marker_depth):
        super(_ListLevel, self).__init__()
        self.environmentname = environmentname
        self.kind = kind
        self.depth = depth
        self.marker_depth = marker_depth
        self.counter = 0

    def next_marker(self):
        r"""
        Advance the item counter of this level and return the marker text for the
        new item (e.g. '•' or '2.').  Descriptions have no automatic marker, so
        an empty string is returned for those.
        """
        self.counter += 1
        if self.kind == 'description':
            return ''
        if self.kind == 'enumerate':
            fmt = _enumerate_markers[(self.marker_depth-1) % len(_enumerate_markers)]
            return fmt(self.counter)
        return _itemize_markers[(self.marker_depth-1) % len(_itemize_markers)]

    def __repr__(self):
        return ("_ListLevel(environmentname={!r}, kind={!r}, depth={!r}, "
                "marker_depth={!r}, counter={!r})").format(
                    self.environmentname, self.kind, self.depth,
                    self.marker_depth, self.counter)


def _split_nodelist_at_items(nodelist):
    # Split a list environment's contents at the '\item' macro nodes.  Returns
    # the nodes that precede the first '\item' along with a list of
    # (item node, item body node list) pairs.
    preamble = []
    items = []
    item_node = None
    item_body = None
    for n in (nodelist if nodelist is not None else []):
        if n is not None and n.isNodeType(latexwalker.LatexMacroNode) \
           and n.macroname == 'item':
            if item_body is not None:
                items.append( (item_node, item_body,) )
            item_node = n
            item_body = []
            continue
        if item_body is None:
            preamble.append(n)
        else:
            item_body.append(n)
    if item_body is not None:
        items.append( (item_node, item_body,) )
    return preamble, items


def _fmt_indent_block(contents, indent):
    # Indent all lines of `contents`, leaving blank lines empty rather than
    # filling them with trailing whitespace.
    return "\n".join([
        (indent + line).rstrip() if line.strip() else ''
        for line in contents.split('\n')
    ])


def _fmt_hanging_indent(prefix, contents):
    # Place `prefix` in front of the first line of `contents` and align the
    # remaining lines with the text that follows the prefix.
    if not contents:
        return prefix.rstrip()
    lines = contents.split('\n')
    hang = ' ' * len(prefix)
    return "\n".join(
        [ (prefix + lines[0]).rstrip() ] + [
            (hang + line).rstrip() if line.strip() else ''
            for line in lines[1:]
        ]
    )


def fmt_list_environment(node, l2tobj, environmentname):
    r"""
    This function can be used as a callable in :py:class:`EnvironmentTextSpec`
    for list environments like ``\begin{itemize}...\end{itemize}`` and
    ``\begin{enumerate}...\end{enumerate}``.

    The environment contents is split at the ``\item`` macros and each item is
    rendered as an indented block introduced by an item marker.  Items are
    numbered where relevant, and the marker style is chosen according to the
    lists that we are already inside of, as recorded in the `list_stack` field
    of the current :py:class:`TextConversionState`, so that nested lists are
    rendered correctly.

    An explicit item label given as ``\item[label]`` is used as the item marker
    and, as in LaTeX, does not advance the item counter.

    .. versionadded:: 3.0

       This function was introduced in `pylatexenc 3.0`.
    """

    kind = _list_environment_kinds.get(environmentname, 'itemize')
    list_stack = l2tobj.state.list_stack
    level = _ListLevel(
        environmentname,
        kind,
        depth=len(list_stack)+1,
        marker_depth=1 + len([ lvl for lvl in list_stack if lvl.kind == kind ]),
    )

    with l2tobj.push_state(list_stack=list_stack + [level]):
        preamble_nodes, items = _split_nodelist_at_items(node.nodelist)
        # str() because a list environment can, however oddly, be met in math
        # mode, where the 'fancy' math mode renders a node list to a math
        # piece rather than to a string
        preamble = str(l2tobj.nodelist_to_text(preamble_nodes)).strip()
        item_texts = [
            fmt_list_item(itemnode, itembody, l2tobj, level)
            for (itemnode, itembody) in items
        ]

    chunks = [ x for x in ([preamble] + item_texts) if x ]
    if not chunks:
        return "\n"

    contents = "\n".join(chunks)

    # Only the outermost list is indented as a block; deeper levels are already
    # offset by the hanging indent of the item they appear in.
    if level.depth == 1:
        contents = _fmt_indent_block(contents, '  ')

    return "\n" + contents + "\n"


def fmt_list_item(itemnode, itembody, l2tobj, level):
    r"""
    Render a single item of a list environment.  The `itemnode` is the
    ``\item`` macro node (or `None`), `itembody` is the list of nodes that make
    up the contents of the item, and `level` describes the list level in which
    this item appears (see :py:func:`fmt_list_environment`).

    .. versionadded:: 3.0

       This function was introduced in `pylatexenc 3.0`.
    """
    label = ''
    if itemnode is not None:
        label = l2tobj.node_arg_to_text(itemnode, 0).strip()

    if label:
        # an explicit \item[label] doesn't advance the counter, as in LaTeX
        marker = label
    else:
        marker = level.next_marker()

    # str() for the same reason as in fmt_list_environment()
    contents = str(l2tobj.nodelist_to_text(itembody)).strip()

    prefix = (marker + ' ') if marker else ''
    return _fmt_hanging_indent(prefix, contents)


def fmt_item_macro(node, l2tobj):
    r"""
    This function can be used as a callable in :py:class:`MacroTextSpec` for the
    ``\item`` macro.  It is only used for ``\item`` macros that appear outside
    of any list environment that we know how to format; items within a known
    list environment are rendered by :py:func:`fmt_list_environment`.

    .. versionadded:: 3.0

       This function was introduced in `pylatexenc 3.0`.
    """
    label = l2tobj.node_arg_to_text(node, 0).strip()
    if not label:
        list_stack = l2tobj.state.list_stack
        if list_stack:
            label = list_stack[-1].next_marker()
        else:
            label = _itemize_markers[0]
        # the marker we generated here needs a space to separate it from the
        # item's contents; an explicit label given as ``\item[Label]`` is
        # already followed by whatever separates it from the contents in the
        # source, so don't add another space in that case.
        label = label + ' '
    return '\n  ' + label


#
# see reference: https://unicode.org/charts/PDF/U1D400.pdf
#

_fmt_math_style_offsets = {
    'bold': (0x1D400, 0x1D41A),
    'italic': (0x1D434, 0x1D44E),
    'bold-italic': (0x1D468, 0x1D482),
    'script': (0x1D49C, 0x1D4B6),
    'bold-script': (0x1D4D0, 0x1D4EA),
    'fraktur': (0x1D504, 0x1D51E),
    'doublestruck': (0x1D538, 0x1D552),
    'bold-fraktur': (0x1D56C, 0x1D586),
    'sans': (0x1D5A0, 0x1D5BA),
    'sans-bold': (0x1D5D4, 0x1D5EE),
    'sans-italic': (0x1D608, 0x1D622),
    'sans-bold-italic': (0x1D63C, 0x1D656),
    'monospace': (0x1D670, 0x1D68A),
}
# account for "holes" in code point chart because some symbols have already
# been allocated earlier code points (see reference linked above)
_fmt_math_style_exceptions = {
    'italic': {
        ord('h'): chr(0x210E), # PLANK CONSTANT
    },
    'script': {
        ord('B'): chr(0x212C),
        ord('E'): chr(0x2130),
        ord('F'): chr(0x2131),
        ord('H'): chr(0x210B),
        ord('I'): chr(0x2110),
        ord('L'): chr(0x2112),
        ord('M'): chr(0x2133),
        ord('R'): chr(0x211B),
        ord('e'): chr(0x212F),
        ord('g'): chr(0x210A),
        ord('o'): chr(0x2134),
    },
    'fraktur': {
        ord('C'): chr(0x212D),
        ord('H'): chr(0x210C),
        ord('I'): chr(0x2111),
        ord('R'): chr(0x211C),
        ord('Z'): chr(0x2128),
    },
    'doublestruck': {
        ord('C'): chr(0x2102),
        ord('H'): chr(0x210D),
        ord('N'): chr(0x2115),
        ord('P'): chr(0x2119),
        ord('Q'): chr(0x211A),
        ord('R'): chr(0x211D),
        ord('Z'): chr(0x2124),
    },
}

_oA, _oZ, _oa, _oz = ord('A'), ord('Z'), ord('a'), ord('z')

def _fmt_math_style_char(c, style):
    oc = ord(c)
    z = _fmt_math_style_exceptions.get(style, {}).get(oc, None)
    if z is not None:
        return z

    offset_up, offset_lo = _fmt_math_style_offsets.get(style, (_oA, _oa,))

    if oc >= _oA and oc <= _oZ:
        return chr(offset_up + oc - _oA)
    if oc >= _oa and oc <= _oz:
        return chr(offset_lo + oc - _oa)

    # don't know how to handle this char
    return c



def fmt_math_text_style(text, style):
    r"""
    Return the text with letters replaced by unicode characters so that the
    style `style` is applied.  (We use the unicode math alphanumeric symbols,
    see `the unicode chart <https://unicode.org/charts/PDF/U1D400.pdf>`_.)

    The `style` must be one of 'bold', 'italic', 'bold-italic', 'script',
    'bold-script', 'fraktur', 'doublestruck', 'bold-fraktur', 'sans',
    'sans-bold', 'sans-italic', 'sans-bold-italic', or 'monospace'.

    The character `c` is essentially expected to be an ascii letter, and any
    other character will be returned unchanged.  (Possible exceptions might be
    implemented in the future, for instance to implement the double-struck
    one/identity operator ``\mathbbm{1}``.)
    """
    return "".join( (_fmt_math_style_char(c, style=style) for c in text) )



def _make_fmt_math_style_plain_chars():
    # The inverse of the mapping that _fmt_math_style_char() applies: it takes a
    # letter of the unicode math alphanumeric symbols back to the plain ascii
    # letter it was made from.  It is built from the same two tables, so that it
    # cannot fall out of step with them.
    d = {}
    for offsets in _fmt_math_style_offsets.values():
        offset_up, offset_lo = offsets
        for k in range(26):
            d[chr(offset_up + k)] = chr(_oA + k)
            d[chr(offset_lo + k)] = chr(_oa + k)
    # The exceptions have to come last: they occupy code points that lie outside
    # of the blocks above, but the holes that they leave behind in those blocks
    # were given an entry in the loop above, which we now know to be spurious.
    # (Those code points are unassigned, so nothing is lost by leaving them in;
    # what matters is that the exception characters themselves are mapped.)
    for exceptions in _fmt_math_style_exceptions.values():
        for oc, c in exceptions.items():
            d[c] = chr(oc)
    return d

_fmt_math_style_plain_chars = _make_fmt_math_style_plain_chars()



#
# Unicode only provides superscript and subscript versions of a limited set of
# characters.  The tables below list those that are of interest for rendering
# latex superscripts and subscripts; they are collected from the "superscripts
# and subscripts" chart (https://unicode.org/charts/PDF/U2070.pdf) along with
# the modifier letters that live in the "spacing modifier letters" and
# "phonetic extensions" charts.
#
# (Note: MODIFIER LETTER CAPITAL C, F and Q also exist as of Unicode 14, but
# they are recent enough that most fonts don't have them yet, so we don't use
# them here.  There are no capital-letter subscripts at all.)
#

_fmt_superscript_chars = {
    '0': u'\N{SUPERSCRIPT ZERO}',
    '1': u'\N{SUPERSCRIPT ONE}',
    '2': u'\N{SUPERSCRIPT TWO}',
    '3': u'\N{SUPERSCRIPT THREE}',
    '4': u'\N{SUPERSCRIPT FOUR}',
    '5': u'\N{SUPERSCRIPT FIVE}',
    '6': u'\N{SUPERSCRIPT SIX}',
    '7': u'\N{SUPERSCRIPT SEVEN}',
    '8': u'\N{SUPERSCRIPT EIGHT}',
    '9': u'\N{SUPERSCRIPT NINE}',
    '+': u'\N{SUPERSCRIPT PLUS SIGN}',
    '-': u'\N{SUPERSCRIPT MINUS}',
    u'\N{MINUS SIGN}': u'\N{SUPERSCRIPT MINUS}',
    '=': u'\N{SUPERSCRIPT EQUALS SIGN}',
    '(': u'\N{SUPERSCRIPT LEFT PARENTHESIS}',
    ')': u'\N{SUPERSCRIPT RIGHT PARENTHESIS}',
    # lowercase latin letters; all of them except 'q'
    'a': u'\N{MODIFIER LETTER SMALL A}',
    'b': u'\N{MODIFIER LETTER SMALL B}',
    'c': u'\N{MODIFIER LETTER SMALL C}',
    'd': u'\N{MODIFIER LETTER SMALL D}',
    'e': u'\N{MODIFIER LETTER SMALL E}',
    'f': u'\N{MODIFIER LETTER SMALL F}',
    'g': u'\N{MODIFIER LETTER SMALL G}',
    'h': u'\N{MODIFIER LETTER SMALL H}',
    'i': u'\N{SUPERSCRIPT LATIN SMALL LETTER I}',
    'j': u'\N{MODIFIER LETTER SMALL J}',
    'k': u'\N{MODIFIER LETTER SMALL K}',
    'l': u'\N{MODIFIER LETTER SMALL L}',
    'm': u'\N{MODIFIER LETTER SMALL M}',
    'n': u'\N{SUPERSCRIPT LATIN SMALL LETTER N}',
    'o': u'\N{MODIFIER LETTER SMALL O}',
    'p': u'\N{MODIFIER LETTER SMALL P}',
    'r': u'\N{MODIFIER LETTER SMALL R}',
    's': u'\N{MODIFIER LETTER SMALL S}',
    't': u'\N{MODIFIER LETTER SMALL T}',
    'u': u'\N{MODIFIER LETTER SMALL U}',
    'v': u'\N{MODIFIER LETTER SMALL V}',
    'w': u'\N{MODIFIER LETTER SMALL W}',
    'x': u'\N{MODIFIER LETTER SMALL X}',
    'y': u'\N{MODIFIER LETTER SMALL Y}',
    'z': u'\N{MODIFIER LETTER SMALL Z}',
    # uppercase latin letters; 'C', 'F', 'Q', 'S', 'X', 'Y' and 'Z' are missing
    'A': u'\N{MODIFIER LETTER CAPITAL A}',
    'B': u'\N{MODIFIER LETTER CAPITAL B}',
    'D': u'\N{MODIFIER LETTER CAPITAL D}',
    'E': u'\N{MODIFIER LETTER CAPITAL E}',
    'G': u'\N{MODIFIER LETTER CAPITAL G}',
    'H': u'\N{MODIFIER LETTER CAPITAL H}',
    'I': u'\N{MODIFIER LETTER CAPITAL I}',
    'J': u'\N{MODIFIER LETTER CAPITAL J}',
    'K': u'\N{MODIFIER LETTER CAPITAL K}',
    'L': u'\N{MODIFIER LETTER CAPITAL L}',
    'M': u'\N{MODIFIER LETTER CAPITAL M}',
    'N': u'\N{MODIFIER LETTER CAPITAL N}',
    'O': u'\N{MODIFIER LETTER CAPITAL O}',
    'P': u'\N{MODIFIER LETTER CAPITAL P}',
    'R': u'\N{MODIFIER LETTER CAPITAL R}',
    'T': u'\N{MODIFIER LETTER CAPITAL T}',
    'U': u'\N{MODIFIER LETTER CAPITAL U}',
    'V': u'\N{MODIFIER LETTER CAPITAL V}',
    'W': u'\N{MODIFIER LETTER CAPITAL W}',
    # greek letters.  The variant forms (e.g. 'ϕ', which is what we render
    # \phi as, vs 'φ' for \varphi) share the same superscript character.
    u'\N{GREEK SMALL LETTER BETA}': u'\N{MODIFIER LETTER SMALL BETA}',
    u'\N{GREEK SMALL LETTER GAMMA}': u'\N{MODIFIER LETTER SMALL GREEK GAMMA}',
    u'\N{GREEK SMALL LETTER DELTA}': u'\N{MODIFIER LETTER SMALL DELTA}',
    u'\N{GREEK SMALL LETTER THETA}': u'\N{MODIFIER LETTER SMALL THETA}',
    u'\N{GREEK THETA SYMBOL}': u'\N{MODIFIER LETTER SMALL THETA}',
    u'\N{GREEK SMALL LETTER PHI}': u'\N{MODIFIER LETTER SMALL GREEK PHI}',
    u'\N{GREEK PHI SYMBOL}': u'\N{MODIFIER LETTER SMALL GREEK PHI}',
    u'\N{GREEK SMALL LETTER CHI}': u'\N{MODIFIER LETTER SMALL CHI}',
}

_fmt_subscript_chars = {
    '0': u'\N{SUBSCRIPT ZERO}',
    '1': u'\N{SUBSCRIPT ONE}',
    '2': u'\N{SUBSCRIPT TWO}',
    '3': u'\N{SUBSCRIPT THREE}',
    '4': u'\N{SUBSCRIPT FOUR}',
    '5': u'\N{SUBSCRIPT FIVE}',
    '6': u'\N{SUBSCRIPT SIX}',
    '7': u'\N{SUBSCRIPT SEVEN}',
    '8': u'\N{SUBSCRIPT EIGHT}',
    '9': u'\N{SUBSCRIPT NINE}',
    '+': u'\N{SUBSCRIPT PLUS SIGN}',
    '-': u'\N{SUBSCRIPT MINUS}',
    u'\N{MINUS SIGN}': u'\N{SUBSCRIPT MINUS}',
    '=': u'\N{SUBSCRIPT EQUALS SIGN}',
    '(': u'\N{SUBSCRIPT LEFT PARENTHESIS}',
    ')': u'\N{SUBSCRIPT RIGHT PARENTHESIS}',
    # lowercase latin letters; 'b', 'c', 'd', 'f', 'g', 'q', 'w', 'y' and 'z'
    # are missing
    'a': u'\N{LATIN SUBSCRIPT SMALL LETTER A}',
    'e': u'\N{LATIN SUBSCRIPT SMALL LETTER E}',
    'h': u'\N{LATIN SUBSCRIPT SMALL LETTER H}',
    'i': u'\N{LATIN SUBSCRIPT SMALL LETTER I}',
    'j': u'\N{LATIN SUBSCRIPT SMALL LETTER J}',
    'k': u'\N{LATIN SUBSCRIPT SMALL LETTER K}',
    'l': u'\N{LATIN SUBSCRIPT SMALL LETTER L}',
    'm': u'\N{LATIN SUBSCRIPT SMALL LETTER M}',
    'n': u'\N{LATIN SUBSCRIPT SMALL LETTER N}',
    'o': u'\N{LATIN SUBSCRIPT SMALL LETTER O}',
    'p': u'\N{LATIN SUBSCRIPT SMALL LETTER P}',
    'r': u'\N{LATIN SUBSCRIPT SMALL LETTER R}',
    's': u'\N{LATIN SUBSCRIPT SMALL LETTER S}',
    't': u'\N{LATIN SUBSCRIPT SMALL LETTER T}',
    'u': u'\N{LATIN SUBSCRIPT SMALL LETTER U}',
    'v': u'\N{LATIN SUBSCRIPT SMALL LETTER V}',
    'x': u'\N{LATIN SUBSCRIPT SMALL LETTER X}',
    # greek letters, cf. the remark in _fmt_superscript_chars above
    u'\N{GREEK SMALL LETTER BETA}': u'\N{GREEK SUBSCRIPT SMALL LETTER BETA}',
    u'\N{GREEK SMALL LETTER GAMMA}': u'\N{GREEK SUBSCRIPT SMALL LETTER GAMMA}',
    u'\N{GREEK SMALL LETTER RHO}': u'\N{GREEK SUBSCRIPT SMALL LETTER RHO}',
    u'\N{GREEK RHO SYMBOL}': u'\N{GREEK SUBSCRIPT SMALL LETTER RHO}',
    u'\N{GREEK SMALL LETTER PHI}': u'\N{GREEK SUBSCRIPT SMALL LETTER PHI}',
    u'\N{GREEK PHI SYMBOL}': u'\N{GREEK SUBSCRIPT SMALL LETTER PHI}',
    u'\N{GREEK SMALL LETTER CHI}': u'\N{GREEK SUBSCRIPT SMALL LETTER CHI}',
}

_fmt_subsuperscript_charmaps = {
    'superscript': _fmt_superscript_chars,
    'subscript': _fmt_subscript_chars,
}


def fmt_subsuperscript_text(text, which, normalize_math_style_chars=False):
    r"""
    Return `text` typeset with unicode superscript characters
    (`which='superscript'`) or with unicode subscript characters
    (`which='subscript'`).

    Unicode only offers superscript and subscript versions of a limited set of
    characters.  If any character in `text` does not have a corresponding
    superscript/subscript character, then `None` is returned.  It is then up to
    the caller to represent the superscript or subscript in some other way.

    If `normalize_math_style_chars` is set, then a letter of the unicode math
    alphanumeric symbols (see :py:func:`fmt_math_text_style()`) is taken back to
    the plain ascii letter it was made from before it is looked up, because
    unicode offers no styled superscript or subscript characters; the style of
    such a letter is then lost, but the superscript or subscript can still be
    typeset.  This is what the ``math_mode='fancy'`` rendering of
    :py:class:`LatexNodes2Text` needs, because that mode italicizes variable
    names
    where they are typeset, so that the argument of a superscript reaches this
    function already styled.  By default the option is off, and a styled letter
    simply has no superscript or subscript version.

    The default text replacement specs fall back onto writing out the '^' or
    '_' character followed by the superscript or subscript rendered as ordinary
    text; whether and how that text is enclosed in delimiters is decided by the
    `math_expression_in=` option of :py:class:`LatexNodes2Text` (see
    :py:func:`fmt_math_expression_in_delimiters()`).

    .. versionadded:: 3.0

       This function was introduced in `pylatexenc 3.0`.
    """
    charmap = _fmt_subsuperscript_charmaps[which]
    result = []
    for c in text:
        if normalize_math_style_chars:
            # A letter that was typeset with the unicode math alphanumeric
            # symbols, say because it is a variable name in a math mode that
            # italicizes those, has to be taken back to the plain ascii letter
            # first: the tables above are keyed by the ascii character, and
            # unicode has no italic superscripts to offer anyway.
            c = _fmt_math_style_plain_chars.get(c, c)
        cc = charmap.get(c, None)
        if cc is None:
            # this character has no superscript/subscript version; the text
            # cannot be typeset in unicode super/subscript characters
            return None
        result.append(cc)
    return "".join(result)



#
# Delimiters that show the extent of a mathematical sub-expression which we
# could not render directly in plain text.  See the `math_expression_in=`
# option of LatexNodes2Text.
#

_math_expression_in_presets = {
    'braces': ('{', '}',),
    'parens': ('(', ')',),
}


default_math_expression_in = 'parens'
r"""
The value that the `math_expression_in=` option of
:py:class:`LatexNodes2Text` takes when it is not specified.  See the
documentation of that option for the accepted values.

Change this single constant if you would like all
:py:class:`LatexNodes2Text` objects to use different delimiters by default.

.. versionadded:: 3.0

   This constant was introduced in `pylatexenc 3.0`.
"""


def _parse_math_expression_in(math_expression_in):
    # Normalize the value of the `math_expression_in=` option into either a
    # two-item tuple with the opening and the closing delimiter, or `None`.
    if math_expression_in is None:
        return None
    if isinstance(math_expression_in, str):
        if math_expression_in not in _math_expression_in_presets:
            raise ValueError(
                "invalid value for math_expression_in: {!r} (expected 'braces', "
                "'parens', a pair of delimiters, or None)"
                .format(math_expression_in)
            )
        return _math_expression_in_presets[math_expression_in]
    delimiters = tuple(math_expression_in)
    if len(delimiters) != 2:
        raise ValueError(
            "invalid value for math_expression_in: {!r} (a pair of delimiters must "
            "have exactly two items)".format(math_expression_in)
        )
    return delimiters


def fmt_math_expression_in_delimiters(text, math_expression_in):
    r"""
    Return the text representation `text` of a mathematical sub-expression,
    enclosed in the delimiters given by `math_expression_in`.  The latter is
    the value of the `math_expression_in=` option of
    :py:class:`LatexNodes2Text`, i.e., one of the preset names 'braces' or
    'parens', a pair of delimiter strings, or `None` for no delimiters at all.

    The delimiters are only added where they are needed to see where the
    sub-expression begins and ends, that is, if `text` is longer than a single
    character.

    .. versionadded:: 3.0

       This function was introduced in `pylatexenc 3.0`.
    """
    delimiters = _parse_math_expression_in(math_expression_in)
    if delimiters is None or len(text) <= 1:
        return text
    return delimiters[0] + text + delimiters[1]




# ------------------------------------------------------------------------------
#
# Math pieces.
#
# A mathematical expression is rendered item by item, and the resulting bits of
# text then have to be assembled into a single string.  Assembling them is not
# simply a matter of concatenating them: some neighbors have to be kept tight
# together ("4\pi c" reads best as "4πc"), while others need a space between
# them or the result becomes unreadable ("4\pi c x^q p" must not come out as
# "4πcx^qp").
#
# The information needed to make that decision cannot be recovered from the
# rendered strings alone, so each item that knows something useful about itself
# returns a small object, a "math piece", that carries both the rendered text
# and a short description of how the item wants to be joined to its neighbors.
# The description is a pair of "atom classes", one for the left edge of the item
# and one for its right edge (the two edges really can differ: the rendering
# "√x" is closed off by the root sign on the left but is wide open on the
# right).  An item that knows nothing about all this simply returns an ordinary
# string, which is then classified by inspecting its characters; that is less
# precise but it always works.
#
# This machinery serves the 'fancy' math mode of LatexNodes2Text.
#
# Introduced in pylatexenc 3.0.
#


#
# The atom classes.  These are the seven classes that TeX itself uses to decide
# how much space to put between two neighboring items of a formula, plus four
# of our own for situations that TeX handles by other means.
#
# The values are strings so that they can be used directly, and readably, as
# argument values of the public method that creates math pieces.
#

# ordinary: variables, digits, ordinary symbols
_ORD = 'ord'
# named functions and large operators ("sin", "∑")
_OP = 'op'
# binary operators ("+", "×")
_BIN = 'bin'
# relations ("=", "∈", "→")
_REL = 'rel'
# opening and closing delimiters
_OPEN = 'open'
_CLOSE = 'close'
# the punctuation marks "," and ";"
_PUNCT = 'punct'
# a rendering that has no visible extent on that side, such as "x^q", "a/b" or
# "√x"; whatever comes next would look as if it were part of it
_OPENEND = 'openend'
# a fragment of ordinary text, which the joiner treats as opaque
_TEXT = 'text'
# a superscript or a subscript, which binds to the piece on its left
_SCRIPT = 'script'
# a large object such as a matrix, which brings its own delimiters
_BLOCK = 'block'

_math_atom_classes = (
    _ORD, _OP, _BIN, _REL, _OPEN, _CLOSE, _PUNCT, _OPENEND, _TEXT, _SCRIPT,
    _BLOCK,
)

# a binary operator whose left neighbor presents one of these classes (or which
# has no left neighbor at all) is in fact a unary operator, and it binds tightly
# to what follows it: "x = −y", not "x = − y"
_math_unary_left_classes = (_BIN, _REL, _OPEN, _PUNCT,)

# a piece whose right edge presents one of these classes already shows where it
# ends, so a superscript or subscript that attaches to it does not need a space
# in front of the piece to make its extent clear
_math_self_delimited_classes = (_CLOSE, _BLOCK,)


def _parse_math_cls(cls):
    # Normalize an atom class specification into a pair (left edge class, right
    # edge class).  A single class stands for both edges.
    if cls is None:
        return (_ORD, _ORD,)
    if isinstance(cls, str):
        if cls not in _math_atom_classes:
            raise ValueError("Invalid math atom class: {!r}".format(cls))
        return (cls, cls,)
    cls_pair = tuple(cls)
    if len(cls_pair) != 2:
        raise ValueError(
            "Invalid math atom class specification: {!r} (expected a class, or a "
            "pair of classes for the left and the right edge)".format(cls)
        )
    for c in cls_pair:
        if c not in _math_atom_classes:
            raise ValueError("Invalid math atom class: {!r}".format(c))
    return cls_pair



class _MathPiece(object):
    r"""
    A bit of rendered math along with a description of how it wants to be joined
    to its neighbors.

    This is deliberately a plain object and not a subclass of :py:class:`str`,
    because the rendered text must be allowed to be generated only when it is
    needed: a matrix renders differently inline and in display math, and a
    sub-expression can only decide whether it needs delimiters around itself
    once it knows what its neighbors are.

    Arguments and attributes:

    - `text` is the rendered text.  Subclasses that generate their text lazily
      leave it at `None` and reimplement :py:meth:`to_text()` instead.

    - `cls` is the atom class of this piece: either a single class, which then
      applies to both edges, or a pair with the class of the left edge and the
      class of the right edge.  It is stored in the attributes `cls_left` and
      `cls_right`.

    - `script_kind` is 'superscript' or 'subscript' if this piece is a
      superscript or a subscript, and `None` otherwise.  The joiner uses it to
      swap a superscript and a subscript that follow one another, so that the
      subscript attaches to the base first.

    - `script_latex_notation` says whether a superscript or subscript piece had
      to fall back onto LaTeX's own '^' and '_' notation instead of the unicode
      superscript and subscript characters.  In that case the joiner also puts a
      space in front of the base that the script attaches to, so that one can
      see where the base begins.
    """

    def __init__(self, text=None, cls=None, script_kind=None,
                 script_latex_notation=False):
        super(_MathPiece, self).__init__()
        self.text = text
        cls_left, cls_right = _parse_math_cls(cls)
        self.cls_left = cls_left
        self.cls_right = cls_right
        self.script_kind = script_kind
        self.script_latex_notation = script_latex_notation

    def to_text(self, display=False):
        r"""
        Return the text rendering of this piece.  The `display` flag says whether
        we are in display math (an equation set on its own lines) rather than in
        inline math.

        Subclasses reimplement this method to generate their text only when it
        is actually needed.
        """
        if self.text is None:
            return ''
        return self.text

    def realize(self, cls_left_neighbor=None, cls_right_neighbor=None,
                display=False):
        r"""
        Return the triple `(text, cls_left, cls_right)` that this piece
        contributes, given the atom classes that its neighbors present to it
        (`None` where there is no neighbor).

        Pieces that adapt themselves to their surroundings reimplement this
        method; the base implementation simply ignores the neighbors.
        """
        return (self.to_text(display=display), self.cls_left, self.cls_right,)

    def __str__(self):
        return self.to_text()

    def __repr__(self):
        return "{}(text={!r}, cls=({!r}, {!r}))".format(
            self.__class__.__name__, self.to_text(), self.cls_left, self.cls_right
        )



class _MathWrappablePiece(_MathPiece):
    r"""
    A math piece that decides only when it is joined to its neighbors whether to
    enclose its contents in delimiters.

    There are two quite different reasons for putting delimiters around a
    sub-expression.  The first is internal: the numerator of a fraction has to
    be parenthesized in "(a+b)/c", and the fraction knows that all by itself.
    The second is external: the subscript in "x_{abc}" needs no delimiters when
    nothing follows it, but it does need them in "x_{abc}^2", where a space
    would not be enough to show where the subscript ends.  Only the second
    reason requires knowing the neighbors, and that is what this class is for.

    The rule is deliberately short: wrap only when a separating space would
    still leave the extent of the contents ambiguous, that is, when another
    script attaches to the same base, when the contents themselves contain a
    space, or when the contents are themselves open-ended.  Everything else gets
    a space from the joiner, or nothing at all when the neighbor is separated
    anyway.

    Arguments and attributes, in addition to those of :py:class:`_MathPiece`:

    - `inner_text` is the rendered contents that may or may not end up enclosed
      in delimiters.

    - `prefix` is text that always precedes the contents and always stays
      outside the delimiters, such as the '^' or '_' of a script.

    - `math_expression_in` is the delimiters to use, in the form accepted by the
      `math_expression_in=` option of :py:class:`LatexNodes2Text`.  A value of
      `None` means that this piece never wraps its contents.  The delimiters are
      applied with :py:func:`fmt_math_expression_in_delimiters()`, which also
      leaves contents of a single character alone.

    - `inner_cls` is the atom class of the contents themselves, used to find out
      whether the contents are open-ended.  It defaults to the classification of
      `inner_text` by :py:func:`_classify_plain_str()`.

    - `cls` is the atom class of this piece when the contents are *not* wrapped,
      and `cls_wrapped` is its atom class when they are.  The latter defaults to
      the left edge class of `cls` along with a right edge class of `_CLOSE`,
      since a closing delimiter is then the last thing in the rendering.
    """

    def __init__(self, inner_text='', prefix='', math_expression_in=None,
                 cls=None, cls_wrapped=None, inner_cls=None,
                 script_kind=None, script_latex_notation=False):
        super(_MathWrappablePiece, self).__init__(
            text=None,
            cls=cls,
            script_kind=script_kind,
            script_latex_notation=script_latex_notation,
        )
        self.inner_text = inner_text
        self.prefix = prefix
        self.math_expression_in = math_expression_in
        if cls_wrapped is None:
            cls_wrapped = (self.cls_left, _CLOSE,)
        cls_wrapped_left, cls_wrapped_right = _parse_math_cls(cls_wrapped)
        self.cls_wrapped_left = cls_wrapped_left
        self.cls_wrapped_right = cls_wrapped_right
        if inner_cls is None:
            inner_cls = _classify_plain_str(inner_text)
        inner_cls_left, inner_cls_right = _parse_math_cls(inner_cls)
        self.inner_cls_left = inner_cls_left
        self.inner_cls_right = inner_cls_right

    def to_text(self, display=False):
        # outside of a join we have no neighbors to worry about, so we show the
        # contents without delimiters
        return self.prefix + self.inner_text

    def needs_wrapping(self, cls_right_neighbor=None):
        r"""
        Return whether the contents have to be enclosed in delimiters, given the
        atom class that the neighbor on the right presents to this piece.
        """
        if cls_right_neighbor == _SCRIPT:
            # another script attaches to the same base; a space would not tell
            # the two of them apart
            return True
        if ' ' in self.inner_text:
            return True
        if self.inner_cls_right == _OPENEND:
            return True
        return False

    def realize(self, cls_left_neighbor=None, cls_right_neighbor=None,
                display=False):
        wrapped_inner = fmt_math_expression_in_delimiters(self.inner_text,
                                                          self.math_expression_in)
        if wrapped_inner != self.inner_text \
           and self.needs_wrapping(cls_right_neighbor=cls_right_neighbor):
            return (self.prefix + wrapped_inner,
                    self.cls_wrapped_left, self.cls_wrapped_right,)
        return (self.prefix + self.inner_text, self.cls_left, self.cls_right,)



class _MathBlockPiece(_MathPiece):
    r"""
    A large object made of rows and columns, such as a matrix, together with the
    pair of delimiters that surrounds it as a whole.

    The rendering is the inline one, ``[ 1 2; 3 4 ]``, with the columns padded
    to a common width; the rows are separated by a semicolon and the columns by
    a space.

    This is a math piece, rather than simply the string that the rendering
    amounts to, for one reason above all: a piece is opaque, so the joiner never
    looks inside it.  The contents of a matrix are a formula of their own, and
    the '+' or the ',' that sits in the middle of a cell has nothing to say
    about how the matrix as a whole is to be joined to its neighbors.  The
    delimiters are what does that, which is why both edges are of the class
    `_BLOCK`, which the joiner treats as an opening delimiter on the left and as
    a closing delimiter on the right.

    Arguments and attributes, in addition to those of :py:class:`_MathPiece`:

    - `rows` is the contents, as a list of rows, each of which is a list holding
      the rendered text of each of its columns.

    - `delimiters` is the pair of delimiters that goes around the whole object,
      an opening one and a closing one.  It defaults to square brackets.
    """

    def __init__(self, rows=None, delimiters=None, cls=None):
        if cls is None:
            cls = _BLOCK
        super(_MathBlockPiece, self).__init__(text=None, cls=cls)
        if rows is None:
            rows = []
        self.rows = rows
        if delimiters is None:
            delimiters = ('[', ']',)
        self.delimiters = delimiters

    def to_text(self, display=False):
        # TODO: in display math, where the formula is set on lines of its own
        # anyway, a block could be laid out over several lines instead, one row
        # per line, with the columns aligned on the padding widths that
        # column_width() already computes (a layout like that would probably
        # want one width per column rather than a single width for all of
        # them), and the joiner would then have to place the whole thing on
        # lines of its own.  This is left for later: it is separable from
        # everything else here, and it is the first thing in this engine that
        # starts to look like drawing a picture rather than like typesetting.
        # The `display` flag and this method being overridable are the seam it
        # would be built on.
        return self.to_text_inline()

    def column_width(self):
        r"""
        Return the width to which every column is padded, namely the width of the
        widest cell of the whole object.
        """
        all_char_widths = [ len(x)  for row in self.rows  for x in row ]
        # an empty matrix or array is valid LaTeX, and max() has no default here
        return max(all_char_widths) if all_char_widths else 0

    def to_text_inline(self):
        r"""
        Return the inline rendering, in the form ``[ a11 a12; a21 a22 ]``.
        """
        max_char_width = self.column_width()
        contents = "; ".join( (
            " ".join( (
                x.rjust(max_char_width, ' ')
                for x in row
            ) )
            for row in self.rows
        ) )
        return self.delimiters[0] + " " + contents + " " + self.delimiters[1]



#
# The classification of ordinary strings, for all the items that render to a
# plain string without saying anything about themselves.  Many of these are
# single characters coming from the symbol tables in _defaultspecs.py, such as
# ('leq', '≤'), but a string can just as well hold a whole run of characters:
# LaTeX's "x+y" reaches us as a single characters node, and a string-valued
# `simplify_repl` or the fallback for an unknown macro can produce anything at
# all.  Such a string is therefore split into the atoms it is made of, so that
# the joiner sees the '+' in the middle of it (see _segment_plain_str()).
#
# Only ordinary strings are split up this way.  A math piece is always opaque,
# which is the whole reason the piece type exists: the joiner must never look
# inside the rendering of, say, a fragment of ordinary text.
#
# We spell the character sets out explicitly instead of asking the unicodedata
# module for the unicode category of a character, because unicodedata is not
# available under Transcrypt and we would rather keep the door open to compiling
# this module to JavaScript one day.
#
# Any character that is not listed here is classified as ORD, which is the
# conservative outcome: ORD means "join tightly", and a missing space is a
# smaller error than a space in the wrong place.  This is why, for instance, the
# vertical bar '|' is absent — it is the rendering of \mid, a relation, but also
# the rendering of the absolute value delimiters, and there is no way to tell
# the two apart here.  For the same reason the slash '/' is absent, exactly as
# in TeX, where it is an ordinary atom so that "a/b" stays tight.
#

_math_bin_chars = (
    u'+'
    u'-'
    u'*'
    u'\N{MINUS SIGN}'                                   # −
    u'\N{PLUS-MINUS SIGN}'                              # ±
    u'\N{MINUS-OR-PLUS SIGN}'                           # ∓
    u'\N{MULTIPLICATION SIGN}'                          # ×
    u'\N{DIVISION SIGN}'                                # ÷
    u'\N{MIDDLE DOT}'                                   # ·
    u'\N{DOT OPERATOR}'                                 # ⋅
    u'\N{ASTERISK OPERATOR}'                            # ∗
    u'\N{STAR OPERATOR}'                                # ⋆
    u'\N{RING OPERATOR}'                                # ∘
    u'\N{BULLET OPERATOR}'                              # ∙
    u'\N{CIRCLED PLUS}'                                 # ⊕
    u'\N{CIRCLED MINUS}'                                # ⊖
    u'\N{CIRCLED TIMES}'                                # ⊗
    u'\N{CIRCLED DIVISION SLASH}'                       # ⊘
    u'\N{CIRCLED DOT OPERATOR}'                         # ⊙
    u'\N{UNION}'                                        # ∪
    u'\N{INTERSECTION}'                                 # ∩
    u'\N{MULTISET UNION}'                               # ⊎
    u'\N{SQUARE CUP}'                                   # ⊔
    u'\N{SQUARE CAP}'                                   # ⊓
    u'\N{LOGICAL AND}'                                  # ∧
    u'\N{LOGICAL OR}'                                   # ∨
    u'\N{SET MINUS}'                                    # ∖
    u'\N{WREATH PRODUCT}'                               # ≀
    u'\N{DAGGER}'                                       # †
    u'\N{DOUBLE DAGGER}'                                # ‡
)

_math_rel_chars = (
    u'='
    u'<'
    u'>'
    u':'
    u'\N{NOT EQUAL TO}'                                 # ≠
    u'\N{LESS-THAN OR EQUAL TO}'                        # ≤
    u'\N{GREATER-THAN OR EQUAL TO}'                     # ≥
    u'\N{MUCH LESS-THAN}'                               # ≪
    u'\N{MUCH GREATER-THAN}'                            # ≫
    u'\N{IDENTICAL TO}'                                 # ≡
    u'\N{ALMOST EQUAL TO}'                              # ≈
    u'\N{ASYMPTOTICALLY EQUAL TO}'                      # ≃
    u'\N{APPROXIMATELY EQUAL TO}'                       # ≅
    u'\N{TILDE OPERATOR}'                               # ∼
    u'\N{EQUIVALENT TO}'                                # ≍
    u'\N{APPROACHES THE LIMIT}'                         # ≐
    u'\N{DELTA EQUAL TO}'                               # ≜
    u'\N{PROPORTIONAL TO}'                              # ∝
    u'\N{ELEMENT OF}'                                   # ∈
    u'\N{NOT AN ELEMENT OF}'                            # ∉
    u'\N{CONTAINS AS MEMBER}'                           # ∋
    u'\N{SUBSET OF}'                                    # ⊂
    u'\N{SUPERSET OF}'                                  # ⊃
    u'\N{SUBSET OF OR EQUAL TO}'                        # ⊆
    u'\N{SUPERSET OF OR EQUAL TO}'                      # ⊇
    u'\N{SQUARE IMAGE OF}'                              # ⊏
    u'\N{SQUARE ORIGINAL OF}'                           # ⊐
    u'\N{SQUARE IMAGE OF OR EQUAL TO}'                  # ⊑
    u'\N{SQUARE ORIGINAL OF OR EQUAL TO}'               # ⊒
    u'\N{PRECEDES}'                                     # ≺
    u'\N{SUCCEEDS}'                                     # ≻
    u'\N{PRECEDES OR EQUAL TO}'                         # ≼
    u'\N{SUCCEEDS OR EQUAL TO}'                         # ≽
    u'\N{RIGHT TACK}'                                   # ⊢
    u'\N{LEFT TACK}'                                    # ⊣
    u'\N{UP TACK}'                                      # ⊥
    u'\N{TRUE}'                                         # ⊨
    u'\N{DIVIDES}'                                      # ∣
    u'\N{PARALLEL TO}'                                  # ∥
    u'\N{RIGHTWARDS ARROW}'                             # →
    u'\N{LEFTWARDS ARROW}'                              # ←
    u'\N{LEFT RIGHT ARROW}'                             # ↔
    u'\N{RIGHTWARDS DOUBLE ARROW}'                      # ⇒
    u'\N{LEFTWARDS DOUBLE ARROW}'                       # ⇐
    u'\N{LEFT RIGHT DOUBLE ARROW}'                      # ⇔
    u'\N{RIGHTWARDS ARROW FROM BAR}'                    # ↦
    u'\N{LONG RIGHTWARDS ARROW}'                        # ⟶
    u'\N{LONG LEFTWARDS ARROW}'                         # ⟵
    u'\N{LONG LEFT RIGHT ARROW}'                        # ⟷
    u'\N{LONG RIGHTWARDS DOUBLE ARROW}'                 # ⟹
    u'\N{LONG LEFTWARDS DOUBLE ARROW}'                  # ⟸
    u'\N{LONG LEFT RIGHT DOUBLE ARROW}'                 # ⟺
    u'\N{LONG RIGHTWARDS ARROW FROM BAR}'               # ⟼
)

_math_open_chars = (
    u'('
    u'['
    u'{'
    u'\N{MATHEMATICAL LEFT ANGLE BRACKET}'              # ⟨
    u'\N{LEFT ANGLE BRACKET}'                           # 〈
    u'\N{LEFT CEILING}'                                 # ⌈
    u'\N{LEFT FLOOR}'                                   # ⌊
    u'\N{MATHEMATICAL LEFT WHITE SQUARE BRACKET}'       # ⟦
    u'\N{MATHEMATICAL LEFT FLATTENED PARENTHESIS}'      # ⟮
)

_math_close_chars = (
    u')'
    u']'
    u'}'
    u'!'
    u'\N{MATHEMATICAL RIGHT ANGLE BRACKET}'             # ⟩
    u'\N{RIGHT ANGLE BRACKET}'                          # 〉
    u'\N{RIGHT CEILING}'                                # ⌉
    u'\N{RIGHT FLOOR}'                                  # ⌋
    u'\N{MATHEMATICAL RIGHT WHITE SQUARE BRACKET}'      # ⟧
    u'\N{MATHEMATICAL RIGHT FLATTENED PARENTHESIS}'     # ⟯
)

_math_punct_chars = (
    u','
    u';'
)

_math_op_chars = (
    u'\N{N-ARY SUMMATION}'                              # ∑
    u'\N{N-ARY PRODUCT}'                                # ∏
    u'\N{N-ARY COPRODUCT}'                              # ∐
    u'\N{INTEGRAL}'                                     # ∫
    u'\N{DOUBLE INTEGRAL}'                              # ∬
    u'\N{TRIPLE INTEGRAL}'                              # ∭
    u'\N{CONTOUR INTEGRAL}'                             # ∮
    u'\N{N-ARY UNION}'                                  # ⋃
    u'\N{N-ARY INTERSECTION}'                           # ⋂
    u'\N{N-ARY LOGICAL AND}'                            # ⋀
    u'\N{N-ARY LOGICAL OR}'                             # ⋁
    u'\N{N-ARY CIRCLED PLUS OPERATOR}'                  # ⨁
    u'\N{N-ARY CIRCLED TIMES OPERATOR}'                 # ⨂
    u'\N{N-ARY CIRCLED DOT OPERATOR}'                   # ⨀
    u'\N{N-ARY SQUARE UNION OPERATOR}'                  # ⨆
    u'\N{N-ARY UNION OPERATOR WITH PLUS}'               # ⨄
)

def _make_math_char_classes():
    # Collect the character sets above into a single lookup table.
    d = {}
    for chars, cls in ( (_math_bin_chars, _BIN,),
                        (_math_rel_chars, _REL,),
                        (_math_open_chars, _OPEN,),
                        (_math_close_chars, _CLOSE,),
                        (_math_punct_chars, _PUNCT,),
                        (_math_op_chars, _OP,), ):
        for c in chars:
            d[c] = cls
    return d

_math_char_classes = _make_math_char_classes()


def _is_ascii_digit(c):
    # deliberately not str.isdigit(), which also accepts the digits of other
    # scripts as well as characters such as the superscript two
    return (c >= '0' and c <= '9')


def _is_upright_latin_letter(c):
    # The math italic letters of the unicode math alphanumeric symbols block are
    # not in the ranges tested here, which is exactly the point: an upright run
    # of letters in math mode can only be the name of a function, because the
    # variables have been italicized.
    return ((c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z'))


def _segment_plain_str(s, upright_letters_are_op=True):
    r"""
    Split an ordinary string, one that carries no information about itself, into
    the atoms that make it up.  Return a list of pairs `(text, cls)` giving the
    text of each atom along with its atom class.

    The rules are:

    - a run of two or more upright latin letters is the name of a function such
      as 'sin' or 'log', and becomes a single large operator atom.  This holds
      only because the variables are italicized, which is what makes an upright
      run stand out as something other than a variable; where they are not (the
      ``math_fontstyle=None`` option of :py:class:`LatexNodes2Text`), the caller
      says so with `upright_letters_are_op=False` and the run is taken for a
      row of ordinary variables instead.  The function names then still come
      out right, because the specifications of '\sin' and friends say what they
      are;

    - a run of digits, taking in a decimal point that has digits on both sides
      so that '3.14' stays in one piece, becomes a single ordinary atom;

    - a character that is a binary operator, a relation, an opening or closing
      delimiter or a punctuation mark becomes an atom of its own;

    - anything else becomes an ordinary atom of its own, one per character.
      This is the conservative outcome, since ordinary atoms are joined tightly
      and a missing space is a smaller error than a space in the wrong place.
      Single upright letters end up here too, because in math mode a lone
      letter is a variable and not the name of a function.

      Such characters are deliberately *not* grouped with one another.  The
      spacing is the same either way, ordinary atoms being joined tightly, but
      the joiner puts a space in front of the atom that a superscript or a
      subscript attaches to, and that atom has to be the single character the
      script really applies to: '4πc x^q', not '4π cx^q'.
    """
    atoms = []
    i = 0
    num = len(s)

    while i < num:
        c = s[i]

        if _is_upright_latin_letter(c):
            if upright_letters_are_op:
                j = i
                while j < num and _is_upright_latin_letter(s[j]):
                    j = j + 1
                if j - i >= 2:
                    atoms.append( (s[i:j], _OP,) )
                    i = j
                    continue
            atoms.append( (c, _ORD,) )
            i = i + 1
            continue

        if _is_ascii_digit(c):
            j = i
            while j < num:
                if _is_ascii_digit(s[j]):
                    j = j + 1
                    continue
                if s[j] == '.' and j + 1 < num and _is_ascii_digit(s[j+1]):
                    j = j + 1
                    continue
                break
            atoms.append( (s[i:j], _ORD,) )
            i = j
            continue

        cls = _math_char_classes.get(c, _ORD)
        atoms.append( (c, cls,) )
        i = i + 1

    return atoms


def _classify_plain_str(s, upright_letters_are_op=True):
    r"""
    Return the pair `(cls_left, cls_right)` with the atom classes of the left
    and of the right edge of an ordinary string, taken from the classes of the
    first and of the last atom that the string is made of (see
    :py:func:`_segment_plain_str()`).
    """
    atoms = _segment_plain_str(s, upright_letters_are_op=upright_letters_are_op)
    if not atoms:
        return (_ORD, _ORD,)
    return (atoms[0][1], atoms[-1][1],)



def _math_needs_space(cls_left, cls_right, text_left, text_right):
    # Whether the right edge of one piece, presenting the class `cls_left`, and
    # the left edge of the next piece, presenting the class `cls_right`, have to
    # be separated by a space.  This is TeX's own table of the spacing between
    # neighboring atoms, collapsed from four widths down to two, which is why it
    # is this short and why it gives conventional-looking results.
    #
    # Unary binary operators have already been dealt with by the caller, which
    # turns them into ordinary atoms.

    # A large object such as a matrix carries its own delimiters, and it really
    # does delimit itself on both sides, so its left edge behaves exactly like
    # an opening delimiter and its right edge exactly like a closing one:
    # 'sin[ 1 2 ]' hugs the way 'sin(x)' does, and '2[ 1 2 ]' stays tight.
    #
    # The class is kept distinct from _OPEN and _CLOSE all the same, rather than
    # having a block simply declare itself to be a pair of delimiters: a block
    # is a different kind of thing, it is recognizable as such wherever its
    # class travels (a join hands the class of its outermost constituents on to
    # the piece it returns), and a rule that wants to tell the two apart can.
    # As things stand no rule does -- _math_self_delimited_classes holds both --
    # so the two descriptions happen to give the same output today.
    if cls_left == _BLOCK:
        cls_left = _CLOSE
    if cls_right == _BLOCK:
        cls_right = _OPEN

    # 1. either side is a binary operator or a relation
    if cls_left == _BIN or cls_left == _REL or cls_right == _BIN or cls_right == _REL:
        return True
    # 2. either side has no visible extent
    if cls_left == _OPENEND or cls_right == _OPENEND:
        return True
    # 3. the left side is a large operator or a text fragment, unless a
    #    delimiter follows.  A delimiter hugs what it encloses, on both sides:
    #    'sin(x)' of course, but also '[xyz]' where the 'xyz' looks like the
    #    name of a function.  A function name immediately followed by a closing
    #    delimiter essentially never happens in real mathematics, and where it
    #    does, no space is the better rendering anyway.
    if (cls_left == _OP or cls_left == _TEXT) \
       and cls_right != _OPEN and cls_right != _CLOSE:
        return True
    # 4. the right side is a large operator or a text fragment, unless an
    #    opening delimiter precedes
    if (cls_right == _OP or cls_right == _TEXT) and cls_left != _OPEN:
        return True
    # 5. the left side is punctuation (never merely because the right side is)
    if cls_left == _PUNCT:
        return True
    # 6. the two adjacent characters are both digits, which would otherwise run
    #    together into a single number
    if text_left and text_right \
       and _is_ascii_digit(text_left[-1]) and _is_ascii_digit(text_right[0]):
        return True
    # 7. otherwise, no space
    return False


def _math_separator(cls_left, cls_right, text_left, text_right):
    # The separator to place between two neighboring pieces.  A space that is
    # already there, at the end of the left rendering or at the beginning of the
    # right one, counts: this is what keeps '\text{if } x > 0' from ending up
    # with two spaces after the 'if'.
    if text_left and text_left[-1] == ' ':
        return ''
    if text_right and text_right[0] == ' ':
        return ''
    if _math_needs_space(cls_left, cls_right, text_left, text_right):
        return ' '
    return ''


def _math_pieces_prepare(pieces, upright_letters_are_op=True):
    # Turn the given list, which may mix math pieces with ordinary strings, into
    # a list of math pieces, and reorder the scripts in it.
    #
    # A math piece is taken as it is, because it is opaque.  An ordinary string,
    # on the other hand, is split into the atoms that make it up, so that the
    # joiner also sees the operators and the delimiters that sit in the middle
    # of it; without this, '$x+y$', which reaches us as a single characters
    # node, would come out as 'x+y' with nothing set apart.
    items = []
    for piece in pieces:
        if piece is None:
            continue
        if isinstance(piece, _MathPiece):
            items.append(piece)
            continue
        if not isinstance(piece, str):
            piece = str(piece)
        if not piece:
            continue
        for atom in _segment_plain_str(
                piece, upright_letters_are_op=upright_letters_are_op):
            items.append( _MathPiece(text=atom[0], cls=atom[1]) )

    # A superscript immediately followed by a subscript reads much better the
    # other way around, because the subscript then attaches to the base first:
    # 'x^a_b' comes out as 'xᵦᵃ' instead of running the two scripts together.
    # (The trick is taken from the flatlatex package.)
    for i in range(len(items) - 1):
        if items[i].script_kind == 'superscript' \
           and items[i+1].script_kind == 'subscript':
            item = items[i]
            items[i] = items[i+1]
            items[i+1] = item

    return items


def _join_math_pieces(pieces, display=False, upright_letters_are_op=True):
    r"""
    Join the given math pieces into a single :py:class:`_MathPiece`, inserting
    spaces where they help the reader.

    The `pieces` may mix :py:class:`_MathPiece` objects with ordinary strings.
    A math piece is opaque and is used as it is; an ordinary string is first
    split into the atoms that make it up (see :py:func:`_segment_plain_str()`).
    The `display` flag says whether we are in display math rather than in inline
    math; it is handed on to the pieces when they render themselves.  The
    `upright_letters_are_op` flag says whether a run of upright latin letters in
    such a string is to be taken for the name of a function; it belongs to the
    caller, which knows whether the variables are being italicized.

    The result is itself a math piece, presenting the left edge class of its
    first constituent and the right edge class of its last one, so that a group
    can be joined to its own neighbors in turn.

    The joining happens in two passes, because whether a piece encloses itself
    in delimiters depends on its neighbors while its edge classes depend on
    whether it did.  The first pass has each piece render itself against the
    classes that its neighbors *declare*, that is, the classes they present when
    they do not wrap; that is the conservative direction, and it always
    terminates.  The second pass computes the separators from the classes that
    the pieces actually ended up presenting.
    """

    items = _math_pieces_prepare(
        pieces, upright_letters_are_op=upright_letters_are_op)

    #
    # First pass: have each piece render itself, given what its neighbors
    # declare themselves to be.  Pieces that render to nothing at all are
    # dropped, so that they cannot cause a spurious separator.
    #
    r_items = []
    r_texts = []
    r_cls_left = []
    r_cls_right = []
    for i in range(len(items)):
        cls_left_neighbor = items[i-1].cls_right if i > 0 else None
        cls_right_neighbor = items[i+1].cls_left if i+1 < len(items) else None
        text, cls_left, cls_right = items[i].realize(
            cls_left_neighbor=cls_left_neighbor,
            cls_right_neighbor=cls_right_neighbor,
            display=display,
        )
        if not text:
            continue
        r_items.append(items[i])
        r_texts.append(text)
        r_cls_left.append(cls_left)
        r_cls_right.append(cls_right)

    num = len(r_texts)
    if num == 0:
        return _MathPiece(text='', cls=_ORD)

    #
    # A binary operator that has nothing suitable on its left is really a unary
    # operator, and it behaves like an ordinary atom: it binds tightly to what
    # follows it, and it does not push the preceding opening delimiter away.
    # All of them are identified before any of them is rewritten, so that the
    # outcome does not depend on the order in which we go through the list.
    #
    is_unary = []
    for i in range(num):
        is_unary.append(
            r_cls_left[i] == _BIN
            and (i == 0 or r_cls_right[i-1] in _math_unary_left_classes)
        )
    for i in range(num):
        if is_unary[i]:
            r_cls_left[i] = _ORD
            if r_cls_right[i] == _BIN:
                r_cls_right[i] = _ORD

    #
    # A script and the base it attaches to make up a single atom, and what that
    # atom presents to whatever comes after it is the class of the base, not the
    # class of the script: '\sum_i y' has to come out as '∑ᵢ y', with the space
    # that the large operator calls for, and not as '∑ᵢy'.  The one exception is
    # a script that has no visible extent of its own, such as 'x^q', which stays
    # open-ended whatever its base was.  Scripts chain, so we go through them
    # from left to right and let the class travel along the chain.
    #
    for i in range(1, num):
        if r_cls_left[i] == _SCRIPT and r_cls_right[i] != _OPENEND:
            r_cls_right[i] = r_cls_right[i-1]

    #
    # Second pass: the separators.
    #
    seps = []
    for i in range(num - 1):
        seps.append( _math_separator(r_cls_right[i], r_cls_left[i+1],
                                     r_texts[i], r_texts[i+1]) )

    #
    # In the node tree a superscript or a subscript is a node of its own,
    # separate from the base it applies to, so it simply arrives here as the
    # piece that follows its base.  It has to be attached to that base with
    # nothing in between.  And when the script had to fall back onto LaTeX's own
    # '^' or '_' notation, a space goes in front of the base as well, so that
    # one can see where the base begins: this is what turns '4πcx^qp' into
    # '4πc x^q p'.
    #
    # That space is pointless, or downright misleading, in a couple of cases:
    # when the base is itself a script, because scripts chain onto the same
    # base; when the base already shows where it ends, as a closing delimiter or
    # a matrix does; and of course when there is a space there already.
    #
    for i in range(1, num):
        if r_cls_left[i] != _SCRIPT:
            continue
        seps[i-1] = ''
        if not r_items[i].script_latex_notation:
            continue
        if i < 2:
            continue
        if r_cls_left[i-1] == _SCRIPT:
            continue
        if r_cls_right[i-1] in _math_self_delimited_classes:
            continue
        if seps[i-2] != '':
            continue
        if r_texts[i-2].endswith(' ') or r_texts[i-1].startswith(' '):
            continue
        seps[i-2] = ' '

    result = [ r_texts[0] ]
    for i in range(num - 1):
        result.append(seps[i])
        result.append(r_texts[i+1])

    return _MathPiece(
        text="".join(result),
        cls=(r_cls_left[0], r_cls_right[num-1],),
    )



# ------------------------------------------------------------------------------






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
    db = macrospec.LatexContextDb()

    from ._defaultspecs import specs

    for cat, catspecs in specs:
        db.add_context_category(cat,
                                macros=catspecs['macros'],
                                environments=catspecs['environments'],
                                specials=catspecs['specials'])

    return db




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


Provide an access to the default macro text replacement specs for `latex2text`
in a form that is compatible with `pylatexenc 1.x`\ 's `default_macro_dict`
module-level dictionary.

This is implemented using a custom lazy mutable mapping, which behaves just like
a regular dictionary but that loads the data only once the dictionary is
accessed.  In this way the default latex specs into a python dictionary unless
they are actually queried or modified, and thus users of `pylatexenc 2.0` that
don't rely on the default macro/environment definitions shouldn't notice any
decrease in performance.
"""

default_env_dict = _util.LazyDict(
    generate_dict_fn=lambda: dict([
        (m.environmentname, m)
        for m in get_default_latex_context_db().iter_environment_specs()
    ])
)
r"""
.. deprecated:: 2.0

   Use :py:func:`get_default_latex_context_db()` instead, or create your own
   :py:class:`pylatexenc.macrospec.LatexContextDb` object.


Provide an access to the default environment text replacement specs for
`latex2text` in a form that is compatible with `pylatexenc 1.x`\ 's
`default_macro_dict` module-level dictionary.

This is implemented using a custom lazy mutable mapping, which behaves just like
a regular dictionary but that loads the data only once the dictionary is
accessed.  In this way the default latex specs into a python dictionary unless
they are actually queried or modified, and thus users of `pylatexenc 2.0` that
don't rely on the default macro/environment definitions shouldn't notice any
decrease in performance.
"""


default_text_replacements = ( )
r"""
.. deprecated:: 2.0

   Text replacements are deprecated since `pylatexenc 2.0` with the advent of
   "latex specials".  See :py:meth:`LatexNodes2Text.apply_text_replacements()`
   for a quick solution to keep existing code working if it uses custom text
   replacements.
"""


# ------------------------------------------------------------------------------

_strict_latex_spaces_predef = {
    'based-on-source': {
        'between-macro-and-chars': False,
        'between-latex-constructs': False,
        'after-comment': False,
        'in-equations': None,
    },
    'macros': {
        'between-macro-and-chars': True,
        'between-latex-constructs': True,
        'after-comment': False,
        'in-equations': 'based-on-source',
    },
    'except-in-equations': {
        'between-macro-and-chars': True,
        'between-latex-constructs': True,
        'after-comment': True,
        'in-equations': 'based-on-source',
    },
}


def _parse_strict_latex_spaces_dict(strict_latex_spaces):
    d = {
        'between-macro-and-chars': False,
        'between-latex-constructs': False,
        'after-comment': False,
        'in-equations': None,
    }
    if strict_latex_spaces is None:
        return d
    elif strict_latex_spaces is False:
        # "False" == the actual default for non-strict latex spaces == "macros"
        # (return a copy so that instances don't share the same dictionary)
        return dict(_strict_latex_spaces_predef['macros'])
    elif strict_latex_spaces is True:
        return dict([(k, True) for k in d.keys()])
    elif isinstance(strict_latex_spaces, dict):
        d.update(strict_latex_spaces)
        return d
    elif isinstance(strict_latex_spaces, str):
        if strict_latex_spaces == 'on':
            return _parse_strict_latex_spaces_dict(True)
        if strict_latex_spaces == 'off':
            return _parse_strict_latex_spaces_dict(False)
        # translate the deprecated 'default' value before checking the value
        # against the known presets, because 'default' is deliberately not one
        # of them
        if strict_latex_spaces == 'default': # deprecated -- report this
            # compatibility with pylatexenc 1.x, but it is no longer the default!!
            _util.pylatexenc_deprecated_2(
                "The value 'default' for `strict_latex_spaces=` in LatexNodes2Text() "
                "is deprecated. The actual default changed to 'macros', and for "
                "backwards compatibility the obsolete value 'default' still refers to "
                "the earlier default which is now called 'based-on-source'.",
                # we are called from LatexNodes2Text.__init__(), which is
                # itself called by the code that we want to point the warning
                # at
                stacklevel=3
            )
            strict_latex_spaces = 'based-on-source'

        if strict_latex_spaces not in _strict_latex_spaces_predef:
            raise ValueError("invalid value for strict_latex_spaces preset: {}"
                             .format(strict_latex_spaces))

        # return a copy so that instances don't share the same dictionary
        return dict(_strict_latex_spaces_predef[strict_latex_spaces])
    else:
        raise ValueError("Invalid value for strict_latex_spaces: {!r}"
                         .format(strict_latex_spaces))

#


# ------------------------------------------------------------------------------


class TextConversionState(object):
    r"""
    Describes the surroundings in which a node is being converted to text, that
    is, everything that the text representation of a node may depend on beyond
    the node itself.

    This is the `latex2text` counterpart of
    :py:class:`pylatexenc.latexnodes.ParsingState`, which plays the same role
    while the LaTeX code is being parsed.  Note that the latex context database
    (:py:class:`pylatexenc.macrospec.LatexContextDb`) is a different thing
    altogether: it holds the definitions of macros, environments and specials,
    and it does not change as we walk the node tree.

    A :py:class:`LatexNodes2Text` object always has a "current state", stored in
    its :py:attr:`~LatexNodes2Text.state` attribute.  The state is inherited by
    the nodes that are converted deeper down in the node tree; a node that
    changes the surroundings of its contents (say, an equation, or a list
    environment) installs a modified state for the duration of the conversion of
    its contents.  See :py:meth:`LatexNodes2Text.push_state()`.

    A `simplify_repl` callable in a :py:class:`MacroTextSpec`,
    :py:class:`EnvironmentTextSpec` or :py:class:`SpecialsTextSpec` receives the
    current state if it declares an argument named `l2tstate` (see
    :py:meth:`LatexNodes2Text.apply_simplify_repl()`).

    .. py:attribute:: strict_latex_spaces

       The whitespace behavior that applies here, as a dictionary in the form
       returned by parsing the `strict_latex_spaces=` option of
       :py:class:`LatexNodes2Text` (with the keys 'between-macro-and-chars',
       'between-latex-constructs', 'after-comment' and 'in-equations').

    .. py:attribute:: in_math_mode

       Whether or not the node being converted lies in math mode.

    .. py:attribute:: list_stack

       The list environments that we are currently inside of, outermost first.
       Each entry describes one nesting level and provides the attributes
       `environmentname`, `kind`, `depth` and `counter`.  The list is empty
       outside of any list environment.

    .. py:attribute:: math_expression_in

       The delimiters that are placed here around a mathematical
       sub-expression which could not be rendered directly in plain text, for
       instance the argument of a superscript for which there is no rendering
       with unicode superscript characters.  This is a pair of strings with the
       opening and the closing delimiter, or `None` if no delimiters are to be
       added.

       This field is set up from the `math_expression_in=` option of
       :py:class:`LatexNodes2Text`, where the accepted values are documented.
       Because it is part of the state, it can be changed for one part of the
       document only, see :py:meth:`LatexNodes2Text.push_state()`.

    .. py:attribute:: text_fontstyle

       The font style that applies to the characters that are typeset here in
       text mode, as one of the style names accepted by
       :py:func:`fmt_math_text_style()`, or `None` for the upright style.  It
       is what ``\textbf{}``, ``\textsf{}``, ``\emph{}`` and friends install for
       the duration of their contents; its initial value comes from the
       `text_fontstyle=` option of :py:class:`LatexNodes2Text`.

       The value `False` is special: it says that the characters typeset here
       are to be left as they are, with no unicode alphabet applied to them at
       all.  The font style macros do not replace it — they leave a `False`
       where they find one — so it holds for the entire document, which is what
       the `text_fontstyle=False` option is for.

    .. py:attribute:: math_fontstyle

       The font style that applies to the characters that are typeset here in
       math mode, as one of the style names accepted by
       :py:func:`fmt_math_text_style()`, or `None` for the upright style.  It
       is what ``\mathbf{}``, ``\mathcal{}`` and friends install for the
       duration of their contents; its initial value comes from the
       `math_fontstyle=` option of :py:class:`LatexNodes2Text`.

       Math mode italicizes the variable names, so this field starts out as
       'italic' where `text_fontstyle` starts out upright.

       As for `text_fontstyle`, the value `False` says that no unicode alphabet
       is to be applied to these characters at all, and the font style macros
       leave it alone where they find it.

       The two font styles are kept apart because they are stacked
       independently: crossing into math mode and back out of it, as in
       ``\textit{... $\mathbf{a+\text{[b]}}$}``, has to restore the text style
       that was in force outside, which the excursion into math mode never
       disturbed.

    .. versionadded:: 3.0

       This class was introduced in `pylatexenc 3.0`.
    """

    _fields = ('strict_latex_spaces', 'in_math_mode', 'list_stack',
               'math_expression_in', 'text_fontstyle', 'math_fontstyle',)

    def __init__(self, strict_latex_spaces=None, in_math_mode=False,
                 list_stack=None, math_expression_in=default_math_expression_in,
                 text_fontstyle=None, math_fontstyle='italic'):
        super(TextConversionState, self).__init__()
        self.strict_latex_spaces = strict_latex_spaces
        self.in_math_mode = in_math_mode
        self.list_stack = list_stack if list_stack is not None else []
        self.math_expression_in = math_expression_in
        self.text_fontstyle = text_fontstyle
        self.math_fontstyle = math_fontstyle

    def sub_state(self, **kwargs):
        r"""
        Return a copy of this state in which the fields given as keyword
        arguments take the given new values.  All other fields keep the value
        they have in the present state.

        This state object itself is left unchanged.
        """
        d = dict([ (field, getattr(self, field)) for field in self._fields ])
        for field, value in kwargs.items():
            if field not in self._fields:
                raise ValueError("Invalid latex2text state field: {!r}".format(field))
            d[field] = value
        return TextConversionState(**d)

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join([ "{}={!r}".format(field, getattr(self, field))
                        for field in self._fields ])
        )


# ------------------------------------------------------------------------------



from ._inputlatexfile import read_latex_file




class LatexNodes2Text(object):
    r"""
    Simplistic Latex-To-Text Converter.

    This class parses a nodes structure generated by the :py:mod:`latexwalker` module,
    and creates a text representation of the structure.

    It is capable of parsing ``\input`` directives safely, see
    :py:meth:`~LatexNodes2Text.set_tex_input_directory()` and
    :py:meth:`~LatexNodes2Text.read_input_file()`.  By default,
    ``\input`` and ``\include`` directives are ignored.

    Arguments to the constructor:

    - `latex_context_db` is a :py:class:`pylatexenc.macrospec.LatexContextDb`
      class storing a collection of rules for converting macros, environments,
      and other latex specials to text.  The `LatexContextDb` should contain
      specifications via :py:class:`MacroTextSpec`,
      :py:class:`EnvironmentTextSpec`, and :py:class:`SpecialsTextSpec` objects.

      The default latex context database can be obtained using
      :py:func:`get_default_latex_context_db()`.

    Additional keyword arguments are flags which may influence the behavior:

    - `math_mode='fancy'|'text'|'with-delimiters'|'verbatim'|'remove'`: Specify
      how to treat chunks of LaTeX code that correspond to math modes.  If
      'fancy' (the default), the formula is rendered as described just below.
      If 'text', then the math mode contents is incorporated as normal text.
      If 'with-delimiters', the content is incorporated as normal text but it
      is still included in the original math-mode delimiters, such as '$...$'.
      If 'verbatim', then the math mode chunk is kept verbatim, including the
      delimiters.  The value 'remove' means to remove the math mode sections
      entirely and not to produce any replacement text.

      The default value 'fancy' selects a rendering of the formula that aims to
      look, as far as plain text allows, like the formula that LaTeX itself
      would typeset.  It is meant for text that a person is going to read — in
      a terminal, in an e-mail, in a search result; where the output is
      processed further by a program that expects plain ASCII, use 'text', or
      keep the letters upright with the `math_fontstyle=None` option below.  It
      differs from 'text' in four ways.

        * The whitespace of the source is ignored, exactly as LaTeX ignores
          it, and spaces are put back only where they help the reader.  So
          ``$4 \pi c$`` and ``$4\pi c$`` both give ``4π𝑐``, keeping the
          implicit multiplication tight, whereas ``$x+y$`` gives ``𝑥 + 𝑦``,
          setting the binary operator apart.  What decides this is LaTeX's own
          table of the spacing between neighboring atoms, reduced from four
          widths of space to two.

        * The letters of the formula are written with the unicode mathematical
          alphanumeric characters, so that a variable name is visibly not the
          name of a function: ``$\sin x$`` gives ``sin 𝑥``.  Which style is
          used is the `math_fontstyle=` option below, and macros such as
          ``\mathbf{}`` change it for their contents.

        * A sub-expression is put in delimiters only where its extent would
          otherwise be unclear, and where a separating space is enough, a space
          is used instead.  So ``$x_{abc}$`` gives ``𝑥_𝑎𝑏𝑐`` and
          ``$x_{abc} p$`` gives ``𝑥_𝑎𝑏𝑐 𝑝``, while ``$x_{abc}^2$``, where a
          second script attaches to the same base, does need the delimiters and
          gives ``𝑥_(𝑎𝑏𝑐)²``.

        * A text-mode fragment such as ``\text{...}`` is left alone.  The
          spaces it brings along survive, and no space of ours is added right
          next to one of them, so that ``$\text{if } x > 0$`` gives
          ``if 𝑥 > 0`` with exactly one space after the "if".

      The rendering stays one-dimensional: there is no two-dimensional layout
      and nothing is drawn out of characters.  A matrix, for instance, is
      rendered inline as ``[ 1 2; 3 4 ]``, in math mode and in display math
      alike.

      .. versionchanged:: 3.0

         The `math_mode='fancy'` value was introduced in `pylatexenc 3.0`, and
         is the default there.  In `pylatexenc 2` the math mode contents were
         always incorporated as normal text, which is what `math_mode='text'`
         does now.

    - `math_expression_in='braces'|'parens'|(left, right)|None`: Specify which
      delimiters to place around a mathematical sub-expression that we were not
      able to render directly in plain text.  Say we meet the superscript
      ``x^{abc}``; there are no unicode superscript characters for all of 'a',
      'b' and 'c', so the superscript is written out as ordinary text after a
      '^' character.  The delimiters are what makes it possible to still see
      where the superscript ends, i.e., to tell ``x^{ab}c`` from ``x^{abc}``.

      The value 'braces' uses the characters '{' and '}', and 'parens' uses '('
      and ')'.  You may also give a pair (a two-item tuple) with the opening
      and the closing delimiter of your choice.  Finally, the value `None`
      means that no delimiters are added at all, as was the case up to
      `pylatexenc 2`.

      Delimiters are only added where they are needed, that is, around
      sub-expressions that are longer than a single character.  Apart from
      superscripts and subscripts, the delimiters are used for the numerator
      and the denominator of the fraction macros (``\frac`` and friends), which
      are rendered as ``numerator/denominator``.

      The default value is given by the module-level constant
      :py:data:`default_math_expression_in`.  The setting can also be changed
      for one part of the document only, see the `math_expression_in` field of
      :py:class:`TextConversionState`.

      .. versionadded:: 3.0

         The `math_expression_in=` option was introduced in `pylatexenc 3.0`.

    - `math_fontstyle='italic'|None|False|<style name>`: The font style in which
      the letters of a formula are typeset, using the unicode math alphanumeric
      symbols (see :py:func:`fmt_math_text_style()`, whose style names are the
      accepted values here).  The default 'italic' follows the convention of
      mathematical typesetting, where a variable name is set in italics; the
      value `None` leaves the letters upright, and the value `False` switches
      the unicode alphabets off altogether (see below).

      The reason the option exists is that those characters live in a high
      unicode plane which a good many terminal fonts do not cover, and which
      they will therefore display as a row of empty boxes.  Give
      `math_fontstyle=None` if the output might be read in such a place; the
      letters then stay plain ASCII.

      Note that `None` sets the style that the letters of a formula start out
      in, and that ``\mathbf{}`` and friends still install their own style for
      the duration of their contents, so ``$x + \mathbf{a}$`` still gives
      ``x + 𝐚``.  The value `False` is the stronger one: it says that no
      unicode alphabet is to be used in math mode at all, and the font style
      macros then leave the letters alone, so the same formula gives
      ``x + a``.  Use it together with `text_fontstyle=False` for output that
      is plain ASCII throughout.

      There is a small price for switching the styling off.  A run of two or
      more upright latin letters is what the renderer takes for the name of a
      function, which is how ``\sin`` and ``\log`` are told apart from a
      product of variables without every such macro having to be annotated;
      that guess is only sound as long as the variables are being italicized.
      With `math_fontstyle=None` or `False`, ``$2xy$`` still comes out as
      ``2xy`` and ``$2\sin x$`` still as ``2 sin x``, but a construct that
      relies on the guess, such as ``$\mathrm{max} x$``, loses the space that
      separates the function name from its argument.

      This is the initial value of the `math_fontstyle` field of the conversion
      state; macros such as ``\mathbf{}`` change it for their contents, and it
      can also be changed for one part of the document only, see
      :py:class:`TextConversionState` and :py:meth:`push_state()`.

      The option is only in effect with ``math_mode='fancy'``, which is the
      math mode that renders formulas with the unicode math characters; the
      other math modes ignore it.

      .. versionadded:: 3.0

         The `math_fontstyle=` option was introduced in `pylatexenc 3.0`.

    - `text_fontstyle=None|False|<style name>`: The same thing for the text
      outside of the formulas.  It is the font style that ordinary text starts
      out in, given as one of the style names of
      :py:func:`fmt_math_text_style()`, or `None` — the default — for the
      upright style that ordinary text is normally set in.

      As above, `None` only sets the style that text starts out in, and
      ``\textbf{}``, ``\textsf{}``, ``\emph{}`` and friends still install their
      own for the duration of their contents, so ``\textbf{bold}`` gives
      ``𝐛𝐨𝐥𝐝``.  The value `False` switches the unicode alphabets off for text
      mode altogether: the font style macros then leave the letters alone and
      ``\textbf{bold}`` gives ``bold``.  This is what to give, along with
      `math_fontstyle=False`, when the output has to be plain ASCII — because
      it is going to be indexed, compared against stored strings, or read
      somewhere that has no font for the unicode math alphabets.

      Note that a style name here applies to the text that is *not* inside one
      of the font style macros: those macros select a whole font and not one of
      the axes (family, weight, shape) that LaTeX varies independently, so with
      `text_fontstyle='sans'` the argument of ``\textbf{}`` still comes out in
      the serif bold alphabet.

      This is the initial value of the `text_fontstyle` field of the conversion
      state, and as with `math_fontstyle=` it can be changed for one part of
      the document only, see :py:class:`TextConversionState` and
      :py:meth:`push_state()`.

      The option is only in effect with ``math_mode='fancy'``; the other math
      modes never apply a font style to the text.

      .. versionadded:: 3.0

         The `text_fontstyle=` option was introduced in `pylatexenc 3.0`.

    - `keep_comments=True|False`: If set to `True`, then LaTeX comments are kept
      (including the percent-sign); otherwise they are discarded.  (By default
      this is `False`)

    - `fill_text`: If set to `True` or to a positive integer, then the
      whitespace of LaTeX char blocks is re-layed out to fill at the given
      number of characters or 80 by default.  The fill is by far not perfect,
      but the resulting text might be slightly more readable.

    - `strict_latex_spaces=True|False`: If set to `True`, then we follow closely
      LaTeX's handling of whitespace.  For instance, whitespace following a bare
      macro (i.e. without any delimiting characters like '{') is
      consumed/removed.  If set to `False` (the default), then some liberties
      are taken with respect to whitespace [hopefully making the result slightly
      more aesthetic, but this behavior is mostly there for historical reasons].

      You may also use one of the presets
      `strict_latex_spaces='based-on-source'|'macros'|'except-in-equations'`,
      which allow for finer control of how whitespace is handled:

        - The value 'based-on-source' is the option that is furthest from
          latex's behavior with spaces, and takes liberties in incuding spaces
          that are present in the source file in several situations where LaTeX
          would remove them, including after macros.  This is meant to be
          hopefully slightly more aesthetic.  However, this option might
          inadvertently break up words: For instance::

              Sk\l odowska

          would be replaced by::

             Skł odowska

        - The value 'macros' is the same as specifying
          `strict_latex_spaces=False`, and it is the default.  It will make
          macros and other sequences of LaTeX constructions obey LaTeX space
          rules, but will keep indentations after comments and keep more liberal
          whitespace rules in equations for a hopefully more aesthetic result.

        - The 'except-in-equations' preset goes as you would expect, setting
          strict latex spacing only outside of equation contexts.

      Finally, the argument `strict_latex_spaces` may also be set to a
      dictionary with keys 'between-macro-and-chars', 'after-comment',
      'between-latex-constructs', and 'in-equations', with individual values
      either `True` or `False`, dictating whitespace behavior in specific cases
      (`True` indicates strict latex behavior).  The value for 'in-equations'
      may even be another dictionary with the same keys to override values in
      equations.  A value of `False` for 'in-equation' has the same meaning as
      'macros'.

      .. versionchanged:: 2.0

         Since `pylatexenc 2.0`, the default value of `strict_latex_spaces` is
         'macros', and no longer 'based-on-source'.

      .. deprecated:: 2.0

         The value 'default' is also accepted, but it is no longer the default!
         It is an alias for 'based-on-source'

      .. versionchanged:: 2.6

         In `pylatexenc` versions 2.0–2.5, contrary to the documentation, the
         default value of `strict_latex_spaces` was actually still
         'based-on-source'.  This bug was fixed in version 2.6, so that now, the
         default setting is actually 'macros'.

    - `keep_braced_groups=True|False`: If set to `True`, then braces delimiting
      a TeX group ``{Like this}`` will be kept in the output, with the contents
      of the group converted to text as usual.  (By default this is `False`)

    - `keep_braced_groups_minlen=<int>`: If `keep_braced_groups` is set to
      `True`, then we keep braced groups only if their contents length (after
      conversion to text) is longer than the given value.  E.g., if
      `keep_braced_groups_minlen=2`, then ``{\'e}tonnant`` still goes to
      ``étonnant`` but ``{\'etonnant}``
      becomes ``{étonnant}``.

    .. versionadded: 1.4

       Added the `strict_latex_spaces`, `keep_braced_groups`, and
       `keep_braced_groups_minlen` flags

    .. versionadded: 2.0

       Added the `math_mode=` flag to replace the poorly designed
       `keep_inline_math=` flag;

       Added the `fill_text=` flag.

    Additionally, the following arguments are accepted for backwards compatibility:

    - `keep_inline_math=True|False`: Obsolete since `pylatexenc 2`.  If set to
      `True`, then this is the same as `math_mode='verbatim'`, and if set to
      `False`, this is the same as `math_mode='text'`.

      .. deprecated:: 2.0

         The `keep_inline_math=` option is deprecated because it had a weird
         behavior and was poorly implemented, especially given that a similarly
         named option in :py:class:`LatexWalker` had a different effect.  See
         issue :issue:`14`.

    - `text_replacements` this argument is ignored starting from `pylatexenc 2`.

      .. deprecated:: 2.0

         Text replacements are no longer made at the end of the text conversion.
         This feature is replaced by the concept of LaTeX specials---see, e.g.,
         :py:class:`pylatexenc.latexwalker.LatexSpecialsNode`.

         To keep existing code working, add a call to
         :py:meth:`apply_text_replacements()` immediately after
         :py:meth:`nodelist_to_text()` to achieve the same effect as in
         `pylatexenc 1.x`.  See :py:meth:`apply_text_replacements()`.

    - `env_dict`, `macro_dict`: Obsolete since `pylatexenc 2`.  If set, they are
      dictionaries of known environment and macro definitions.  They default to
      :py:data:`default_env_dict` and :py:data:`default_macro_dict`,
      respectively.

      .. deprecated:: 2.0

         You should now use the more powerful option `latex_context_db=`.  You
         cannot specify both `macro_list` (or `env_list`) and
         `latex_context_db`.
    """
    def __init__(self, latex_context=None, **flags):
        super(LatexNodes2Text, self).__init__()

        # The state describes the surroundings of the node that is currently
        # being converted; it is set up here and then updated as we descend into
        # the node tree (see push_state()).
        self.state = TextConversionState()

        if latex_context is None:
            if 'macro_dict' in flags or 'env_dict' in flags:
                # LEGACY -- build a latex context using the given macro_dict
                _util.pylatexenc_deprecated_2(
                    "The `macro_dict=...` and `env_dict=...` options in LatexNodes2Text() are "
                    "obsolete since pylatexenc 2.  They will still work, but please consider "
                    "using instead the more versatile option `latex_context=...`."
                )

                macro_dict = flags.pop('macro_dict', [])
                env_dict = flags.pop('env_dict', [])

                latex_context = macrospec.LatexContextDb()
                latex_context.add_context_category('custom',
                                                   macros=macro_dict.values(),
                                                   environments=env_dict.values(),
                                                   specials=[])

            else:
                # default -- use default
                latex_context = get_default_latex_context_db()

        self.latex_context = latex_context

        self.tex_input_directory = None
        self.strict_input = True

        if 'keep_inline_math' in flags:
            if 'math_mode' in flags:
                raise TypeError("Cannot specify both math_mode= and keep_inline_math= "
                                "for LatexNodes2Text()")
            _util.pylatexenc_deprecated_2(
                "The keep_inline_math=... option in LatexNodes2Text() has been replaced by "
                "the math_mode=... option."
            )
            # the pylatexenc 1 and 2 option, which knew nothing of the 'fancy'
            # rendering, so it keeps selecting the mode it always selected
            self.math_mode = 'verbatim' if flags.pop('keep_inline_math') else 'text'
        else:
            self.math_mode = flags.pop('math_mode', 'fancy')

        if self.math_mode not in ('fancy', 'text', 'with-delimiters', 'verbatim',
                                  'remove'):
            raise ValueError("math_mode= option must be one of 'fancy', 'text', "
                             "'with-delimiters', 'verbatim', 'remove'")

        math_expression_in = flags.pop('math_expression_in', default_math_expression_in)
        self.math_expression_in = _parse_math_expression_in(math_expression_in)

        # The initial values of the `text_fontstyle` and `math_fontstyle` fields
        # of the conversion state; when an option is not given we keep whatever
        # value that state field starts out with (see TextConversionState).
        if 'text_fontstyle' in flags:
            self.state.text_fontstyle = flags.pop('text_fontstyle')
        if 'math_fontstyle' in flags:
            self.state.math_fontstyle = flags.pop('math_fontstyle')

        self.keep_comments = flags.pop('keep_comments', False)

        strict_latex_spaces = flags.pop('strict_latex_spaces', False)
        self.strict_latex_spaces = _parse_strict_latex_spaces_dict(strict_latex_spaces)

        self.keep_braced_groups = flags.pop('keep_braced_groups', False)
        self.keep_braced_groups_minlen = flags.pop('keep_braced_groups_minlen', 2)

        self.fill_text = flags.pop('fill_text', None)
        if not self.fill_text: # None, 0, False, or false-ish
            self.fill_text = None
        if self.fill_text is True: # exactly boolean true, not an int
            self.fill_text = 80

        if 'text_replacements' in flags:
            del flags['text_replacements']
            _util.pylatexenc_deprecated_2(
                "The text_replacements= argument is ignored since pylatexenc 2. "
                "To keep existing code working, add a call to "
                "`LatexNodes2Text.apply_text_replacements()`. "
                "New code should use \"latex specials\" instead."
            )

        if flags:
            # any flags left which we haven't recognized
            logger.warning("LatexNodes2Text(): Unknown flag(s) encountered: %r",
                           list(flags.keys()))


    @property
    def strict_latex_spaces(self):
        r"""
        The whitespace behavior that applies where we currently are in the node
        tree.  This is a shorthand for the `strict_latex_spaces` field of the
        current :py:attr:`state`.
        """
        return self.state.strict_latex_spaces

    @strict_latex_spaces.setter
    def strict_latex_spaces(self, value):
        self.state.strict_latex_spaces = value


    @property
    def math_expression_in(self):
        r"""
        The delimiters that are placed around a mathematical sub-expression which
        we could not render directly, where we currently are in the node tree.
        This is a shorthand for the `math_expression_in` field of the current
        :py:attr:`state`.
        """
        return self.state.math_expression_in

    @math_expression_in.setter
    def math_expression_in(self, value):
        self.state.math_expression_in = value


    def push_state(self, **kwargs):
        r"""
        Install a new current :py:attr:`state` in which the fields given as
        keyword arguments take the given new values (see
        :py:meth:`TextConversionState.sub_state()`), and restore the present
        state when we are done.

        The return value is meant to be used as a context manager::

            with l2tobj.push_state(in_math_mode=True):
                contents = l2tobj.nodelist_to_text(node.nodelist)

        Any conversion that happens within the ``with`` block, including in
        `simplify_repl` callables that are invoked there, sees the new state.

        .. versionadded:: 3.0

           This method was introduced in `pylatexenc 3.0`.
        """
        return _util.PushPropOverride(self, 'state', self.state.sub_state(**kwargs))


    def set_tex_input_directory(self, tex_input_directory, latex_walker_init_args=None,
                                strict_input=True):
        """
        Set where to look for input files when encountering the ``\\input`` or
        ``\\include`` macro.

        Alternatively, you may also override :py:meth:`read_input_file()` to
        implement a custom file lookup mechanism.

        The argument `tex_input_directory` is the directory relative to which to
        search for input files.

        If `strict_input` is set to `True`, then we always check that the
        referenced file lies within the subtree of `tex_input_directory`,
        prohibiting for instance hacks with '..' in filenames or using symbolic
        links to refer to files out of the directory tree.

        The argument `latex_walker_init_args` allows you to specify the parse
        flags passed to the constructor of
        :py:class:`pylatexenc.latexwalker.LatexWalker` when parsing the input
        file.
        """
        self.tex_input_directory = tex_input_directory
        self.latex_walker_init_args = latex_walker_init_args if latex_walker_init_args else {}
        self.strict_input = strict_input



    def read_input_file(self, fn):
        """
        This method may be overridden to implement a custom lookup mechanism when
        encountering ``\\input`` or ``\\include`` directives.

        The default implementation looks for a file of the given name relative
        to the directory set by
        :py:meth:`~LatexNodes2Text.set_tex_input_directory()`.  If
        `strict_input=True` was set, we ensure strictly that the file resides in
        a subtree of the reference input directory (after canonicalizing the
        paths and resolving all symlinks).

        If `set_tex_input_directory()` was not called, or if it was called with
        a value of `None`, then no file system access is attempted an an empty
        string is returned.

        You may override this method to obtain the input data in however way you
        see fit.  In that case, a call to `set_tex_input_directory()` may not be
        needed as that function simply sets properties which are used by the
        default implementation of `read_input_file()`.

        This function accepts the referred filename as argument (the argument to
        the ``\\input`` macro), and should return a string with the file
        contents (or generate a warning or raise an error).
        """

        if self.tex_input_directory is None:
            return ''

        return read_latex_file(self.tex_input_directory, self.strict_input, fn)


    def _input_node_simplify_repl(self, n):
        #
        # recurse into files upon '\input{}'
        #

        if len(n.nodeargs) != 1:
            logger.warning(u"Expected exactly one argument for '\\input' ! Got = %r",
                           n.nodeargs)

        # str() because '\input' can, however oddly, be met in math mode, where
        # the 'fancy' math mode renders a node list to a math piece rather
        # than to a string
        inputtex = self.read_input_file(
            str(self.nodelist_to_text([n.nodeargs[0]])).strip()
        )

        if not inputtex:
            return ''

        lw = latexwalker.LatexWalker(inputtex, **self.latex_walker_init_args)

        nodelist, _ = lw.parse_content(latexnodes_parsers.LatexGeneralNodesParser())

        return self.nodelist_to_text(nodelist)



    def latex_to_text(self, latex, **parse_flags):
        """
        Parses the given `latex` code and returns its textual representation.

        This is equivalent to constructing a
        :py:class:`pylatexenc.latexwalker.LatexWalker` with the given `latex`
        string, parsing the string into general nodes with a
        :py:class:`~pylatexenc.latexnodes.parsers.LatexGeneralNodesParser` (see
        :py:meth:`~pylatexenc.latexwalker.LatexWalker.parse_content()`), and
        providing the outcome to :py:meth:`nodelist_to_text()`.

        The `parse_flags` are keyword arguments to provide to the
        :py:class:`pylatexenc.latexwalker.LatexWalker` constructor.
        """

        lw = latexwalker.LatexWalker(latex, **parse_flags)
        nodelist, _ = lw.parse_content(latexnodes_parsers.LatexGeneralNodesParser())
        return self.nodelist_to_text( nodelist )


    def nodelist_to_text(self, nodelist, state=None):
        """
        Extracts text from a node list. `nodelist` is a list of
        `latexwalker` nodes, typically parsed using a
        :py:class:`~pylatexenc.latexnodes.parsers.LatexGeneralNodesParser` (see
        :py:meth:`~pylatexenc.latexwalker.LatexWalker.parse_content()`).

        This function basically applies `node_to_text()` to each node and
        concatenates the results into one string.  (This is not quite actually
        the case, since we take some care as to where we add whitespace
        according to the class options.)

        If `state` is given, it is a :py:class:`TextConversionState` instance
        that is used as the current conversion state while converting the given
        nodes.  By default (`state=None`) we keep the current state, which is
        what you want in the vast majority of cases; see
        :py:meth:`push_state()` to install a modified state.

        In math mode with ``math_mode='fancy'``, the return value is a *math
        piece* (see :py:meth:`make_math_piece()`) rather than a string,
        because the result of rendering a formula still has something to say
        about how it wants to be joined to whatever surrounds it.  Use `str()`
        on the result if you need the text itself; every other case returns an
        ordinary string as it always did.

        .. versionadded:: 3.0

           The `state` argument was introduced in `pylatexenc 3.0`, as was the
           math piece return value of ``math_mode='fancy'``.
        """

        if nodelist is None:
            return ''

        with _util.PushPropOverride(self, 'state', state):

            # In math mode the 'fancy' math mode assembles the rendered
            # items with the formula joiner instead of simply
            # concatenating them.  The items are therefore collected in a list
            # and handed to the joiner as they are: an item that is a math piece
            # says how it wants to be joined to its neighbors, and that
            # information would be lost if we turned it into a string here.
            fancy_math = ( self.math_mode == 'fancy' and self.state.in_math_mode )

            parts = [] # the rendered items, for the formula joiner
            s = '' # the text rendered so far, for the text filling
            prev_node = None
            for node in nodelist:
                if self._is_bare_macro_node(prev_node) and \
                   node.isNodeType(latexwalker.LatexCharsNode):

                    if not fancy_math \
                       and not self.strict_latex_spaces['between-macro-and-chars']:
                        # after a macro with absolutely no arguments, include
                        # post_space in output by default if there are other
                        # chars that follow.  This is for more breathing space
                        # (especially in equations(?)), and for compatibility
                        # with earlier versions of pylatexenc (<= 1.3).  This is
                        # NOT LaTeX' default behavior (see issue #11), so only do
                        # this if the corresponding `strict_latex_spaces=` flag
                        # is set.
                        #
                        # Never in the fancy engine's math mode: that space is
                        # whitespace of the source, which math mode ignores, and
                        # putting it back here would defeat the joiner --
                        # '$4 \pi c$' would come out as '4π 𝑐' instead of '4π𝑐'.
                        s += prev_node.macro_post_space

                if fancy_math:
                    # the text filling never applies to a formula
                    textcol = 0
                else:
                    last_nl_pos = s.rfind('\n')
                    if last_nl_pos != -1:
                        textcol = len(s)-last_nl_pos-1
                    else:
                        textcol = len(s)

                r = self.node_to_text(node, textcol=textcol)

                if fancy_math:
                    parts.append(r)
                else:
                    # No str() here on purpose: outside of the fancy engine's
                    # math mode the items really are meant to be strings, and a
                    # simplify_repl that returns something else should keep
                    # raising a TypeError here rather than have its str()
                    # silently rendered.
                    s += r

                prev_node = node

            if fancy_math:
                # whether a run of upright latin letters is to be taken for the
                # name of a function is only a sound guess as long as the
                # variables are being italicized; see _segment_plain_str()
                return _join_math_pieces(
                    parts,
                    upright_letters_are_op=bool(self.state.math_fontstyle),
                )

            return s

    def node_to_text(self, node, prev_node_hint=None, textcol=0, state=None):
        """
        Return the textual representation of the given `node`.

        If `prev_node_hint` is specified, then the current node is formatted
        suitably as following the node given in `prev_node_hint`.  This might
        affect how much space we keep/discard, etc.

        The `state` argument has the same meaning as in
        :py:meth:`nodelist_to_text()`.

        .. versionadded:: 3.0

           The `state` argument was introduced in `pylatexenc 3.0`.
        """
        if node is None:
            return ""

        # ### It doesn't look like we use prev_node_hint at all.  Eliminate at
        # ### some point?

        with _util.PushPropOverride(self, 'state', state):

            if node.isNodeType(latexwalker.LatexCharsNode):
                return self.chars_node_to_text(node, textcol=textcol)

            if node.isNodeType(latexwalker.LatexCommentNode):
                return self.comment_node_to_text(node)

            if node.isNodeType(latexwalker.LatexGroupNode):
                return self.group_node_to_text(node)

            if node.isNodeType(latexwalker.LatexMacroNode):
                return self.macro_node_to_text(node)

            if node.isNodeType(latexwalker.LatexEnvironmentNode):
                return self.environment_node_to_text(node)

            if node.isNodeType(latexwalker.LatexSpecialsNode):
                return self.specials_node_to_text(node)

            if node.isNodeType(latexwalker.LatexMathNode):
                return self.math_node_to_text(node)

            logger.warning("LatexNodes2Text.node_to_text(): Unknown node: %r", node)

            # discard anything else.
            return ""

    def chars_node_to_text(self, node, textcol=0):
        r"""
        Return the textual representation of the given `node` representing a block
        of simple latex text with no special characters or macros.  The `node`
        is :py:class:`~pylatexenc.latexwalker.LatexCharsNode`.

        The font style of the current conversion state, if there is one, is
        applied here, at the leaves of the node tree, so that it also reaches
        the characters that are nested inside groups and inside the arguments of
        macros.  See the `text_fontstyle` and `math_fontstyle` fields of
        :py:class:`TextConversionState`.
        """
        content = node.chars

        if self.math_mode == 'fancy' and self.state.in_math_mode:
            # In math mode LaTeX ignores the whitespace of the source, and so do
            # we; the spaces that make the result readable are put back where
            # they belong when the pieces of the formula are assembled.
            content = re.sub(r'\s+', '', content)
            # a style name applies; `None` (upright) and `False` (no unicode
            # alphabet at all) both leave the characters as they are
            if self.state.math_fontstyle:
                content = fmt_math_text_style(content, self.state.math_fontstyle)
            return content

        # Unless in strict latex spaces mode, ignore nodes consisting only
        # of empty chars, as this tends to produce too much space...  These
        # have been inserted by LatexWalker() in some occasions to keep
        # track of all relevant pre_space of tokens, such as between two
        # braced groups ("{one} {two}") or other such situations.
        if self.fill_text: # None or column width
            content = self.do_fill_text(content, textcol=textcol)
        if not self.strict_latex_spaces['between-latex-constructs'] \
           and len(content.strip()) == 0:
            return ""
        if self.math_mode == 'fancy' and self.state.text_fontstyle:
            content = fmt_math_text_style(content, self.state.text_fontstyle)
        return content

    def comment_node_to_text(self, node):
        r"""
        Return the textual representation of the given `node` representing a latex
        comment.  The `node` is
        :py:class:`~pylatexenc.latexwalker.LatexCommentNode`.
        """
        if self.keep_comments:
            if self.strict_latex_spaces['after-comment']:
                nl = '\n'
                if node.comment_post_space == '':
                    # this happens if two newlines follow a comment---the
                    # comment_post_space is empty, and the \n\n is reported as a
                    # char node to notify that there is a new paragraph.
                    nl = ''
                return '%' + node.comment + nl
            else:
                # default spaces, i.e., keep what spaces were already there
                # after the comment
                return '%' + node.comment + node.comment_post_space
        else:
            if self.strict_latex_spaces['after-comment']:
                return ""
            else:
                # default spaces, i.e., keep what spaces were already there
                # after the comment.  This can be useful to preserve
                # e.g. indentation of the next line
                return node.comment_post_space


    def group_node_to_text(self, node):
        r"""
        Return the textual representation of the given `node` representing a latex
        group.  The `node` is
        :py:class:`~pylatexenc.latexwalker.LatexGroupNode`.
        """
        contents = self._groupnodecontents_to_text(node)
        if self.keep_braced_groups and len(contents) >= self.keep_braced_groups_minlen:
            return node.delimiters[0] + contents + node.delimiters[1]
        return contents

    def macro_node_to_text(self, node):
        r"""
        Return the textual representation of the given `node` representing a latex
        macro invocation.  The `node` is
        :py:class:`~pylatexenc.latexwalker.LatexMacroNode`.
        """
        # get macro behavior definition.
        macroname = node.macroname
        mac = self.latex_context.get_macro_spec(macroname)
        if mac is None:
            # default for unknown macros
            mac = MacroTextSpec('', discard=True)

        def get_macro_str_repl(node, macroname, mac):
            if mac.simplify_repl:
                return self.apply_simplify_repl(node, mac.simplify_repl,
                                                what=r"macro '\%s'"%(macroname))
            if mac.discard:
                return ""
            a = []
            if node.nodeargd and node.nodeargd.argnlist:
                a = node.nodeargd.argnlist
            return "".join([self._groupnodecontents_to_text(n) for n in a])

        macrostr = get_macro_str_repl(node, macroname, mac)
        return macrostr

    def environment_node_to_text(self, node):
        r"""
        Return the textual representation of the given `node` representing a full
        latex environment.  The `node` is
        :py:class:`~pylatexenc.latexwalker.LatexEnvironmentNode`.
        """
        # get environment behavior definition.
        environmentname = node.environmentname
        envdef = self.latex_context.get_environment_spec(environmentname)
        if envdef is None:
            # default for unknown environments
            envdef = EnvironmentTextSpec('', discard=False)

        if envdef.simplify_repl:
            return self.apply_simplify_repl(node, envdef.simplify_repl,
                                            what="environment '%s'"%(environmentname))
        if envdef.discard:
            return ""

        return self.nodelist_to_text(node.nodelist)

    def specials_node_to_text(self, node):
        r"""
        Return the textual representation of the given `node` representing special a
        latex character (or characters).  The `node` is
        :py:class:`~pylatexenc.latexwalker.LatexSpecialsNode`.
        """
        # get the specials text spec
        specials_chars = node.specials_chars
        sspec = self.latex_context.get_specials_spec(specials_chars)
        if sspec is None:
            # no corresponding spec, leave the special chars unchanged:
            return specials_chars

        def get_specials_str_repl(node, specials_chars, spec):
            if spec.simplify_repl:
                return self.apply_simplify_repl(node, spec.simplify_repl,
                                                what="specials '%s'"%(specials_chars))
            if spec.discard:
                return ""
            a = []
            if node.nodeargd and node.nodeargd.argnlist:
                a = node.nodeargd.argnlist
            return "".join([self._groupnodecontents_to_text(n) for n in a])

        s = get_specials_str_repl(node, specials_chars, sspec)
        return s

    def math_node_to_text(self, node):
        r"""
        Return the textual representation of the given `node` representing a block
        of math mode latex.  The `node` is either a
        :py:class:`~pylatexenc.latexwalker.LatexMathNode` or a
        :py:class:`~pylatexenc.latexwalker.LatexEnvironmentNode`.

        This method is responsible for honoring the `math_mode=...` option
        provided to the constructor.
        """

        if self.math_mode == 'verbatim':
            if node.isNodeType(latexwalker.LatexEnvironmentNode) \
               or node.displaytype == 'display':
                return self._fmt_indented_block(node.latex_verbatim(), indent='')
            else:
                return node.latex_verbatim()

        elif self.math_mode == 'remove':
            return ''

        elif self.math_mode == 'with-delimiters':
            with _PushEquationState(self):
                content = self.nodelist_to_text(node.nodelist).strip()
            if node.isNodeType(latexwalker.LatexMathNode):
                delims = node.delimiters
            else: # environment node
                delims = (r'\begin{%s}'%(node.environmentname),
                          r'\end{%s}'%(node.environmentname),)
            if node.isNodeType(latexwalker.LatexEnvironmentNode) \
               or node.displaytype == 'display':
                return delims[0] + self._fmt_indented_block(content, indent='') + delims[1]
            else:
                return delims[0] + content + delims[1]

        elif self.math_mode == 'fancy':
            # display math is set on lines of its own, and the pieces of the
            # formula are told so when they render themselves.
            #
            # NOTE: today the flag only reaches the outermost piece, whose text
            # the join has already fixed, so nothing observable depends on it.
            # Handing it down to the pieces nested inside the formula would
            # mean carrying it through nodelist_to_text(), which is where the
            # inner joins happen; that is worth doing if and when a piece ever
            # renders differently in display math (see the TODO in
            # _MathBlockPiece.to_text(), the deferred multi-line layout of a
            # matrix), and not before.
            is_display = ( node.isNodeType(latexwalker.LatexEnvironmentNode)
                           or node.displaytype == 'display' )
            with _PushEquationState(self):
                # in this math mode rendering a formula gives a math piece, not
                # a string; here, at the outer edge of the formula, there is
                # nothing left to join it to, so we ask it for its text
                rendered = self.nodelist_to_text(node.nodelist)
            if isinstance(rendered, _MathPiece):
                content = rendered.to_text(display=is_display)
            else:
                content = str(rendered)
            content = content.strip()
            if is_display:
                return self._fmt_indented_block(content)
            else:
                return content

        elif self.math_mode == 'text':
            with _PushEquationState(self):
                content = self.nodelist_to_text(node.nodelist).strip()
            if node.isNodeType(latexwalker.LatexEnvironmentNode) \
               or node.displaytype == 'display':
                return self._fmt_indented_block(content)
            else:
                return content

        else:
            raise RuntimeError("unknown math_mode={} !".format(self.math_mode))


    def make_math_piece(self, *, text=None, cls=None, inner_text=None,
                        prefix='', cls_wrapped=None, inner_cls=None,
                        script_kind=None, script_latex_notation=False):
        r"""
        Create a *math piece*, the object that a `simplify_repl` callable returns
        instead of an ordinary string when it wants to say something about how
        its rendering should be joined to its neighbors in a formula.

        This is only meaningful with ``math_mode='fancy'``, and only for a
        node that sits in math mode; anywhere else a `simplify_repl` callable
        must keep returning an ordinary string.

        A math piece carries the rendered text along with a pair of *atom
        classes*, one describing its left edge and one describing its right
        edge.  The atom classes are the ones that TeX itself uses to decide how
        much space to leave between two neighboring items of a formula, plus a
        few of ours:

          - `'ord'`: ordinary — a variable, a digit, an ordinary symbol.  This
            is the default, and it means "join me tightly to my neighbor".
          - `'op'`: the name of a function or a large operator, such as 'sin'
            or '∑'.
          - `'bin'`: a binary operator, such as '+'.
          - `'rel'`: a relation, such as '=' or '→'.
          - `'open'` and `'close'`: an opening or a closing delimiter.
          - `'punct'`: the punctuation marks ',' and ';'.
          - `'openend'`: a rendering that has no visible extent on that side,
            such as 'x^q' or 'a/b'; whatever comes next would look as if it were
            part of it.
          - `'text'`: a fragment of ordinary text, which is treated as opaque.
          - `'script'`: a superscript or a subscript, which binds to the piece
            on its left.
          - `'block'`: a large object such as a matrix, which brings its own
            delimiters.

        The arguments are keyword-only:

        - `text` is the rendered text of the piece.

        - `cls` is its atom class: either one of the names above, which then
          applies to both edges, or a pair of names for the left and the right
          edge.  The default, `None`, means ordinary on both edges.

        - `inner_text`, if it is given instead of `text`, asks for a piece that
          decides only once it knows its neighbors whether to enclose its
          contents in delimiters.  This is what the superscript 'x_{abc}' needs:
          it can be written bare when nothing follows it, but it has to become
          'x_(abc)' in 'x_{abc}^2', where a space would not be enough to show
          where the subscript ends.  The delimiters are the ones given by the
          `math_expression_in=` option, taken from the current conversion state.

        - `prefix` is text that always precedes the contents of such a piece and
          always stays outside the delimiters, such as the '^' or '_' of a
          script.

        - `cls_wrapped` is the atom class that such a piece presents when its
          contents did end up enclosed in delimiters.  It defaults to the left
          edge class of `cls` along with a right edge class of `'close'`, since
          a closing delimiter is then the last thing in the rendering.

        - `inner_cls` is the atom class of the contents themselves, used to find
          out whether the contents are open-ended.  It defaults to a
          classification of `inner_text` by inspecting its characters.

        - `script_kind` is `'superscript'` or `'subscript'` if this piece is a
          superscript or a subscript, and `None` otherwise.  A superscript that
          is immediately followed by a subscript is swapped with it, so that the
          subscript attaches to the base first.

        - `script_latex_notation` says that a superscript or subscript piece had
          to fall back onto LaTeX's own '^' and '_' notation instead of the
          unicode superscript and subscript characters.  A space is then also
          placed in front of the base that the script attaches to, so that one
          can see where the base begins.

        .. versionadded:: 3.0

           This method was introduced in `pylatexenc 3.0`.
        """
        if inner_text is not None:
            if text is not None:
                raise ValueError(
                    "make_math_piece(): give either text= or inner_text=, not both"
                )
            return _MathWrappablePiece(
                inner_text=inner_text,
                prefix=prefix,
                math_expression_in=self.state.math_expression_in,
                cls=cls,
                cls_wrapped=cls_wrapped,
                inner_cls=inner_cls,
                script_kind=script_kind,
                script_latex_notation=script_latex_notation,
            )

        if prefix or cls_wrapped is not None or inner_cls is not None:
            raise ValueError(
                "make_math_piece(): prefix=, cls_wrapped= and inner_cls= only make "
                "sense for a piece created with inner_text="
            )

        return _MathPiece(
            text=text,
            cls=cls,
            script_kind=script_kind,
            script_latex_notation=script_latex_notation,
        )


    def do_fill_text(self, text, textcol=0):
        # keep trailing whitespace to have whitespace between macros in text as
        # in "see \ref{...} and blah blah"
        head_ws = re.search(r'^\s*', text).group()
        head_par = '\n\n' if ('\n\n' in head_ws) else ''
        #head_nl = '\n' if (not head_par and '\n' in head_ws) else ''
        trail_ws = re.search(r'\s*$', text).group()
        trail_par = '\n\n' if ('\n\n' in trail_ws) else ''
        #trail_nl = '\n' if (not trail_par and '\n' in trail_ws) else ''
        text = text.strip()

        def fill_chunk(x, textcol):
            #head_ws = ' ' if textcol>0 and x[0:1].isspace() else ''
            #trail_ws = ' ' if x[-1:].isspace() else ''
            head_ws, trail_ws = '', ''
            x = x.strip()
            if textcol >= self.fill_text-4:
                return '\n' + textwrap.fill(x, self.fill_text) + trail_ws
            else:
                return head_ws + \
                    textwrap.fill(x, self.fill_text, initial_indent='X'*textcol)[textcol:] + \
                    trail_ws

        rawchunks = re.compile(r'\n{2,}').split(text)

        chunks = [
            thechunk
            for (j, thechunk) in (
                    ( j, fill_chunk(x, textcol if j==0 else 0) )
                    for j, x in enumerate(rawchunks)
            )
            if thechunk.strip()
        ]

        return head_par + (' ' if textcol>0 and head_ws and not head_par else '') + \
            "\n\n".join(chunks) + \
            (' ' if trail_ws and not trail_par else '') + trail_par

    def apply_simplify_repl(self, node, simplify_repl, what):
        r"""
        Utility to get the replacement text associated with a `node` for which we
        have a `simplify_repl` object (given by e.g. a MacroTextSpec or
        similar).

        The argument `what` is used in error messages.
        """
        if callable(simplify_repl):
            kwargs = {}
            fn_args = inspect.getfullargspec(simplify_repl)[0]
            if 'l2tobj' in fn_args:
                # callable accepts an argument named 'l2tobj', provide pointer to self
                kwargs['l2tobj'] = self
            if 'l2tstate' in fn_args:
                # callable accepts an argument named 'l2tstate', provide the
                # conversion state that applies where this node sits in the
                # node tree
                kwargs['l2tstate'] = self.state
            if node.isNodeType(latexwalker.LatexEnvironmentNode) and \
               'environmentname' in fn_args:
                kwargs['environmentname'] = node.environmentname
            if node.isNodeType(latexwalker.LatexMacroNode) and \
               'macroname' in fn_args:
                kwargs['macroname'] = node.macroname
            if node.isNodeType(latexwalker.LatexSpecialsNode) and \
               'specials_chars' in fn_args:
                kwargs['specials_chars'] = node.specials_chars

            r = simplify_repl(node, **kwargs)
            if r:
                return r
            return '' # don't return None

        if '%' in simplify_repl and len(simplify_repl) != 1:
            # if simplify_repl contains a '%' sign then we will look for %-based
            # formatting placeholder(s), except if simplify_repl is the string
            # '%' itself (checked above with "len(simplify_repl)!=1") in which
            # case it is a literal replacement percent symbol.

            nodeargs = []
            if node.nodeargd and node.nodeargd.argnlist:
                nodeargs = list(node.nodeargd.argnlist)
            # make sure the argument list is long enough for the macro
            # arguments.  This can happen, for instance, if a macro is parsed as
            # a single-token argument to another macro.  E.g., in the (invalid)
            # r"\hat\sqrt{2}", the token "\sqrt" is the argument of "\hat"; in
            # tolerant parsing mode, the "\sqrt" node has a nodeargd that is
            # None.
            spec = getattr(node, 'spec', None)
            if spec is not None and spec.arguments_spec_list is not None \
               and len(nodeargs) < len(spec.arguments_spec_list):
                nodeargs += [
                    None for _ in range(len(spec.arguments_spec_list) - len(nodeargs))
                ]

            has_percent_s = re.search('(^|[^%])(%%)*%s', simplify_repl)

            if node.isNodeType(latexwalker.LatexEnvironmentNode):
                if has_percent_s:
                    x = (self.nodelist_to_text(node.nodelist), )
                else:
                    x = dict(
                        (str(1+j),val) for j, val in enumerate(
                            self._groupnodecontents_to_text(nn) for nn in nodeargs
                        )
                    )
                    x.update(body=self.nodelist_to_text(node.nodelist))
            elif has_percent_s:
                x = tuple([self._groupnodecontents_to_text(nn)
                           for nn in nodeargs])
            else:
                x = dict(
                    (str(1+j),val) for j, val in enumerate(
                        self._groupnodecontents_to_text(nn) for nn in nodeargs
                    )
                )

            try:
                return simplify_repl % x
            except (TypeError, ValueError, KeyError):
                logger.warning(
                    "WARNING: Error in configuration: {} failed its substitution!"
                    .format(what)
                )
                return simplify_repl # too bad, keep the percent signs as they are...
        return simplify_repl

    def _fmt_indented_block(self, contents, indent=' '*4):
        block = ("\n"+indent + contents.replace("\n", "\n"+indent) + "\n")
        if self.fill_text:
            # additional newlines because neighboring text gets trimmed
            block = '\n'+block+'\n'
        return block


    def _is_bare_macro_node(self, node):
        return (node is not None and
                node.isNodeType(latexwalker.LatexMacroNode) and
                node.nodeoptarg is None and
                len(node.nodeargs) == 0)

    def _groupnodecontents_to_text(self, groupnode):
        # The str() calls here are the boundary at which the math pieces of the
        # 'fancy' math mode stop.  This method, and node_arg_to_text() with
        # it, is what a `simplify_repl` callable sees,
        # and such code has every right to expect an ordinary string that it can
        # join, strip, slice or match.  Math pieces travel only between
        # nodelist_to_text(), node_to_text() and the joiner.
        if groupnode is None:
            return ''
        if isinstance(groupnode, latexnodes_nodes.LatexNodeList):
            return str(self.nodelist_to_text(groupnode))
        if not groupnode.isNodeType(latexwalker.LatexGroupNode):
            return str(self.node_to_text(groupnode))
        return str(self.nodelist_to_text(groupnode.nodelist))

    def node_arg_to_text(self, node, k):
        r"""
        Return the textual representation of the `k`\ -th argument of the given
        `node`.  This might be useful for substitution lambdas in macro and
        environment specs.
        """
        if node.nodeargd and node.nodeargd.argnlist:
            return self._groupnodecontents_to_text(node.nodeargd.argnlist[k])
        return ''

    def apply_text_replacements(self, s, text_replacements):
        r"""
        Convenience function for code that used `text_replacements=` in `pylatexenc
        1.x`.

        If you used custom `text_replacements=` in `pylatexenc 1.x` then you
        will have to change::

          # pylatexenc 1.x with text_replacements
          text_replacements = ...
          l2t = LatexNodes2Text(..., text_replacements=text_replacements)
          text = l2t.nodelist_to_text(...)

        to::

          # pylatexenc 2 text_replacements compatibility code
          text_replacements = ...
          l2t = LatexNodes2Text(...)
          temp = l2t.nodelist_to_text(...)
          text = l2t.apply_text_replacements(temp, text_replacements)

        as a quick fix.  It is recommended however to treat text replacements
        instead as "latex specials".  (Otherwise the brutal text replacements
        might act on text generated from macros and environments and give
        unwanted results.)  See :py:class:`pylatexenc.macrospec.SpecialsSpec`
        and :py:class:`SpecialsTextSpec`.

        .. deprecated:: 2.0

           The `apply_text_replacements()` method was introduced in `pylatexenc
           2.0` as a deprecated method.  You can use it as a quick fix to make
           existing code run as it did in `pylatexenc 1.x`.  Its use is however
           not recommended for new code.  You should use "latex specials"
           instead for characters that have special LaTeX meaning.
        """

        # perform suitable replacements
        for pattern, replacement in text_replacements:
            if hasattr(pattern, 'sub'):
                s = pattern.sub(replacement, s)
            else:
                s = s.replace(pattern, replacement)

        return s





class _PushEquationState(_util.PushPropOverride):
    def __init__(self, l2t):

        changes = {'in_math_mode': True}

        if l2t.strict_latex_spaces['in-equations'] is not None:
            changes['strict_latex_spaces'] = _parse_strict_latex_spaces_dict(
                l2t.strict_latex_spaces['in-equations']
            )

        super(_PushEquationState, self).__init__(l2t, 'state',
                                                   l2t.state.sub_state(**changes))








# ------------------------------------------------------------------------------



def latex2text(content, tolerant_parsing=False, keep_inline_math=False,
               keep_comments=False):
    """
    Heuristic conversion of LaTeX content `content` to unicode text.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    _util.pylatexenc_deprecated_ver(
        "1.0",
        "The module-level function `pylatexenc.latex2text.latex2text()` is deprecated "
        "in favor of the `pylatexenc.latex2text.LatexNodes2Text` class."
    )

    # Parse the content with the current interface rather than with the
    # deprecated `latexwalker.get_latex_nodes()`; the latter would emit further
    # deprecation warnings that point at this file instead of at the code that
    # called us.  (With no `stop_upon_*=` conditions, `get_latex_nodes()` does
    # exactly what the two lines below do.  The `keep_inline_math=` flag has no
    # effect at all when the latex code is parsed.)
    lw = latexwalker.LatexWalker(content, tolerant_parsing=tolerant_parsing)
    nodelist, _ = lw.parse_content(latexnodes_parsers.LatexGeneralNodesParser())

    return _latexnodes2text(nodelist,
                            keep_inline_math=keep_inline_math,
                            keep_comments=keep_comments)


def latexnodes2text(nodelist, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from a node list. `nodelist` is a list of nodes as returned by
    :py:func:`pylatexenc.latexwalker.get_latex_nodes()`.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    _util.pylatexenc_deprecated_ver(
        "1.0",
        "The module-level function `pylatexenc.latex2text.latexnodes2text()` is "
        "deprecated in favor of the `pylatexenc.latex2text.LatexNodes2Text` class."
    )

    return _latexnodes2text(nodelist,
                            keep_inline_math=keep_inline_math,
                            keep_comments=keep_comments)


def _latexnodes2text(nodelist, keep_inline_math, keep_comments):
    # The implementation behind the deprecated `latexnodes2text()`.  It sets up
    # the LatexNodes2Text object with the current `math_mode=` option instead of
    # the deprecated `keep_inline_math=` one, so that the caller doesn't get a
    # deprecation warning pointing at this file.
    return LatexNodes2Text(
        math_mode=('verbatim' if keep_inline_math else 'text'),
        keep_comments=keep_comments
    ).nodelist_to_text(nodelist)
