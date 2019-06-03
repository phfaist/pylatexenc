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

"""
A simplistic, heuristic LaTeX code parser allowing to returns a text-only
approximation.  Suitable, e.g. for indexing tex code in a database for full text
searching.

The main class is :py:class:`LatexNodes2Text`.  For a quick start, try::

    from pylatexenc.latex2text import LatexNodes2Text
    
    latex = "... LaTeX code ..."
    text = LatexNodes2Text(strict_latex_spaces='macros').latex_to_text(latex)

"""

from __future__ import print_function #, absolute_import

import os
import unicodedata
import logging
import sys
import inspect

if sys.version_info.major >= 3:
    def unicode(string): return string
    basestring = str
    getfullargspec = inspect.getfullargspec
else:
    getfullargspec = inspect.getargspec


from . import latexwalker

logger = logging.getLogger(__name__)



class EnvDef:
    """
    An environment definition.

    - `envname`: the name of the environment

    - `simplify_repl`: the replacement text of the environment.  This is either
       a callable or a string.  If it is a callable, it must accept a single
       argument, the :py:class:`pylatexenc.latexwalker.LatexEnvironmentNode`
       representing the LaTeX environment.  If it is a string, it may contain
       '%s' which will be replaced by the environment contents converted to
       text.

    - `discard`: if set to `True`, then the full environment is discarded, i.e.,
       it is converted to an empty string.
    """
    def __init__(self, envname, simplify_repl=None, discard=False):
        self.envname = envname
        self.simplify_repl = simplify_repl
        self.discard = discard


class MacroDef:
    """
    A macro definition.

    - `macname`: the name of the macro (no backslash)

    - `simplify_repl`: either a string or a callable. The string may contain '%s'
      replacements, in which the macro arguments will be substituted. The callable should
      accept the corresponding :py:class:`pylatexenc.latexwalker.LatexMacroNode` as an
      argument.

    - `discard`: if set to `True`, then the macro call is discarded, i.e., it is
       converted to an empty string.
    """
    def __init__(self, macname, simplify_repl=None, discard=None):
        if (isinstance(macname, MacroDef)):
            o = macname
            self.macname = o.macname
            self.discard = o.discard
            self.simplify_repl = o.simplify_repl
        elif (isinstance(macname, tuple)):
            (self.macname, self.simplify_repl) = macname
            self.discard = True if (discard is None) else discard
            if (simplify_repl is not None or discard is not None):
                raise ValueError("macname=%r is tuple but other parameters specified" %(macname,))
        else:
            self.macname = macname
            self.discard = True if (discard is None) else discard
            self.simplify_repl = simplify_repl


def _fmt_equation(n, l2tobj):
    with _PushEquationContext(l2tobj):

        contents = l2tobj._nodelistcontents_to_text(n.nodelist).strip()
        # indent equation, separate by newlines
        indent = ' '*4
        return ("\n"+indent + contents.replace("\n", "\n"+indent) + "\n")


_default_env_list = [
    EnvDef('', discard=False), # default for unknown environments

    EnvDef('equation', simplify_repl=_fmt_equation),
    EnvDef('eqnarray', simplify_repl=_fmt_equation),
    EnvDef('align', simplify_repl=_fmt_equation),
    EnvDef('multline', simplify_repl=_fmt_equation),
    EnvDef('gather', simplify_repl=_fmt_equation),
    EnvDef('dmath', simplify_repl=_fmt_equation),

    # spaces added so that database indexing doesn't index the word "array" or "pmatrix"
    EnvDef('array', simplify_repl='< a r r a y >'),
    EnvDef('pmatrix', simplify_repl='< p m a t r i x >'),
    EnvDef('bmatrix', simplify_repl='< b m a t r i x >'),
    EnvDef('smallmatrix', simplify_repl='< s m a l l m a t r i x >'),

    EnvDef('center', simplify_repl='\n%s\n'),
    EnvDef('flushleft', simplify_repl='\n%s\n'),
    EnvDef('flushright', simplify_repl='\n%s\n'),
    
    EnvDef('exenumerate', discard=False),
    EnvDef('enumerate', discard=False),
    EnvDef('list', discard=False),
    EnvDef('itemize', discard=False),
    EnvDef('subequations', discard=False),
    EnvDef('figure', discard=False),
    EnvDef('table', discard=False),
    ]


# NOTE: macro will only be assigned arguments if they are explicitely defined as accepting arguments
#       in latexwalker.py.

_default_macro_list = [
    MacroDef('', discard=True), # default for unknown macros

    MacroDef('emph', discard=False),
    MacroDef('textbf', discard=False),
    MacroDef('textit', discard=False),
    MacroDef('textsl', discard=False),
    MacroDef('textsc', discard=False),
    MacroDef('text', discard=False),
    MacroDef('mathrm', discard=False),

    # spaces added so that database indexing doesn't index the word "graphics"
    ('includegraphics', '< g r a p h i c s >'),

    ('ref', '<ref>'),
    ('eqref', '(<ref>)'),
    ('url', '<%s>'),
    ('item', lambda r: '\n  '+(latexnodes2text([r.nodeoptarg]) if r.nodeoptarg else '*')),
    ('footnote', '[%s]'),

    ('texorpdfstring', lambda node: latexnodes2text(node.nodeargs[1:2])), # use second argument

    ('oe', u'\u0153'),
    ('OE', u'\u0152'),
    ('ae', u'\u00e6'),
    ('AE', u'\u00c6'),
    ('aa', u'\u00e5'), # a norvegien/nordique
    ('AA', u'\u00c5'), # A norvegien/nordique
    ('o', u'\u00f8'), # o norvegien/nordique
    ('O', u'\u00d8'), # O norvegien/nordique
    ('ss', u'\u00df'), # s-z allemand
    ('L', u"\N{LATIN CAPITAL LETTER L WITH STROKE}"),
    ('l', u"\N{LATIN SMALL LETTER L WITH STROKE}"),
    ('i', u"\N{LATIN SMALL LETTER DOTLESS I}"),
    ('j', u"\N{LATIN SMALL LETTER DOTLESS J}"),

    ("~", "~" ),
    ("&", "\\&" ), # HACK, see below for text replacement of '&'
    ("$", "$" ),
    ("{", "{" ),
    ("}", "}" ),
    ("%", lambda arg: u"%" ), # careful: % is formatting substitution symbol...
    ("#", "#" ),
    ("_", "_" ),

    ("\\", '\n'),

    ("textquoteleft", "`"),
    ("textquoteright", "'"),
    ("textquotedblright", u"\N{RIGHT DOUBLE QUOTATION MARK}"),
    ("textquotedblleft", u"\N{LEFT DOUBLE QUOTATION MARK}"),
    ("textendash", u"\N{EN DASH}"),
    ("textemdash", u"\N{EM DASH}"),

    ('textpm', u"\N{PLUS-MINUS SIGN}"),
    ('textmp', u"\N{MINUS-OR-PLUS SIGN}"),

    ("texteuro", u"\N{EURO SIGN}"),

    # math stuff

    ("hbar", u"\N{LATIN SMALL LETTER H WITH STROKE}"),
    ("ell", u"\N{SCRIPT SMALL L}"),

    ('forall', u"\N{FOR ALL}"),
    ('complement', u"\N{COMPLEMENT}"),
    ('partial', u"\N{PARTIAL DIFFERENTIAL}"),
    ('exists', u"\N{THERE EXISTS}"),
    ('nexists', u"\N{THERE DOES NOT EXIST}"),
    ('varnothing', u"\N{EMPTY SET}"),
    ('emptyset', u"\N{EMPTY SET}"),
    ('aleph', u"\N{ALEF SYMBOL}"),
    # increment?
    ('nabla', u"\N{NABLA}"),
    #
    ('in', u"\N{ELEMENT OF}"),
    ('notin', u"\N{NOT AN ELEMENT OF}"),
    ('ni', u"\N{CONTAINS AS MEMBER}"),
    ('prod', u'\N{N-ARY PRODUCT}'),
    ('coprod', u'\N{N-ARY COPRODUCT}'),
    ('sum', u'\N{N-ARY SUMMATION}'),
    ('setminus', u'\N{SET MINUS}'),
    ('smallsetminus', u'\N{SET MINUS}'),
    ('ast', u'\N{ASTERISK OPERATOR}'),
    ('circ', u'\N{RING OPERATOR}'),
    ('bullet', u'\N{BULLET OPERATOR}'),
    ('sqrt', u'\N{SQUARE ROOT}(%s)'),
    ('propto', u'\N{PROPORTIONAL TO}'),
    ('infty', u'\N{INFINITY}'),
    ('parallel', u'\N{PARALLEL TO}'),
    ('nparallel', u'\N{NOT PARALLEL TO}'),
    ('wedge', u"\N{LOGICAL AND}"),
    ('vee', u"\N{LOGICAL OR}"),
    ('cap', u'\N{INTERSECTION}'),
    ('cup', u'\N{UNION}'),
    ('int', u'\N{INTEGRAL}'),
    ('iint', u'\N{DOUBLE INTEGRAL}'),
    ('iiint', u'\N{TRIPLE INTEGRAL}'),
    ('oint', u'\N{CONTOUR INTEGRAL}'),

    ('sim', u'\N{TILDE OPERATOR}'),
    ('backsim', u'\N{REVERSED TILDE}'),
    ('simeq', u'\N{ASYMPTOTICALLY EQUAL TO}'),
    ('approx', u'\N{ALMOST EQUAL TO}'),
    ('neq', u'\N{NOT EQUAL TO}'),
    ('equiv', u'\N{IDENTICAL TO}'),
    ('ge', u'>'),#
    ('le', u'<'),#
    ('leq', u'\N{LESS-THAN OR EQUAL TO}'),
    ('geq', u'\N{GREATER-THAN OR EQUAL TO}'),
    ('leqslant', u'\N{LESS-THAN OR EQUAL TO}'),
    ('geqslant', u'\N{GREATER-THAN OR EQUAL TO}'),
    ('leqq', u'\N{LESS-THAN OVER EQUAL TO}'),
    ('geqq', u'\N{GREATER-THAN OVER EQUAL TO}'),
    ('lneqq', u'\N{LESS-THAN BUT NOT EQUAL TO}'),
    ('gneqq', u'\N{GREATER-THAN BUT NOT EQUAL TO}'),
    ('ll', u'\N{MUCH LESS-THAN}'),
    ('gg', u'\N{MUCH GREATER-THAN}'),
    ('nless', u'\N{NOT LESS-THAN}'),
    ('ngtr', u'\N{NOT GREATER-THAN}'),
    ('nleq', u'\N{NEITHER LESS-THAN NOR EQUAL TO}'),
    ('ngeq', u'\N{NEITHER GREATER-THAN NOR EQUAL TO}'),
    ('lesssim', u'\N{LESS-THAN OR EQUIVALENT TO}'),
    ('gtrsim', u'\N{GREATER-THAN OR EQUIVALENT TO}'),
    ('lessgtr', u'\N{LESS-THAN OR GREATER-THAN}'),
    ('gtrless', u'\N{GREATER-THAN OR LESS-THAN}'),
    ('prec', u'\N{PRECEDES}'),
    ('succ', u'\N{SUCCEEDS}'),
    ('preceq', u'\N{PRECEDES OR EQUAL TO}'),
    ('succeq', u'\N{SUCCEEDS OR EQUAL TO}'),
    ('precsim', u'\N{PRECEDES OR EQUIVALENT TO}'),
    ('succsim', u'\N{SUCCEEDS OR EQUIVALENT TO}'),
    ('nprec', u'\N{DOES NOT PRECEDE}'),
    ('nsucc', u'\N{DOES NOT SUCCEED}'),
    ('subset', u'\N{SUBSET OF}'),
    ('supset', u'\N{SUPERSET OF}'),
    ('subseteq', u'\N{SUBSET OF OR EQUAL TO}'),
    ('supseteq', u'\N{SUPERSET OF OR EQUAL TO}'),
    ('nsubseteq', u'\N{NEITHER A SUBSET OF NOR EQUAL TO}'),
    ('nsupseteq', u'\N{NEITHER A SUPERSET OF NOR EQUAL TO}'),
    ('subsetneq', u'\N{SUBSET OF WITH NOT EQUAL TO}'),
    ('supsetneq', u'\N{SUPERSET OF WITH NOT EQUAL TO}'),


    ('cdot', u'\N{MIDDLE DOT}'),
    ('times', u'\N{MULTIPLICATION SIGN}'),
    ('otimes', u'\N{CIRCLED TIMES}'),
    ('oplus', u'\N{CIRCLED PLUS}'),
    ('bigotimes', u'\N{CIRCLED TIMES}'),
    ('bigoplus', u'\N{CIRCLED PLUS}'),

    ('frac', '%s/%s'),
    ('nicefrac', '%s/%s'),

    ('cos', 'cos'),
    ('sin', 'sin'),
    ('tan', 'tan'),
    ('arccos', 'arccos'),
    ('arcsin', 'arcsin'),
    ('arctan', 'arctan'),

    ('prime', "'"),
    ('dag', u"\N{DAGGER}"),
    ('dagger', u"\N{DAGGER}"),
    ('pm', u"\N{PLUS-MINUS SIGN}"),
    ('mp', u"\N{MINUS-OR-PLUS SIGN}"),

    (',', u" "),
    (';', u" "),
    (':', u" "),
    (' ', u" "),
    ('!', u""), # sorry, no negative space in ascii
    ('quad', u"  "),
    ('qquad', u"    "),

    ('ldots', u"..."),
    ('cdots', u"..."),
    ('ddots', u"..."),
    ('dots', u"..."),
    
    ('langle', u'\N{LEFT ANGLE BRACKET}'),
    ('rangle', u'\N{RIGHT ANGLE BRACKET}'),
    ('mid', u'|'),
    ('nmid', u'\N{DOES NOT DIVIDE}'),
    
    ('ket', u'|%s\N{RIGHT ANGLE BRACKET}'),
    ('bra', u'\N{LEFT ANGLE BRACKET}%s|'),
    ('braket', u'\N{LEFT ANGLE BRACKET}%s|%s\N{RIGHT ANGLE BRACKET}'),
    ('ketbra', u'|%s\N{RIGHT ANGLE BRACKET}\N{LEFT ANGLE BRACKET}%s|'),
    ('uparrow', u'\N{UPWARDS ARROW}'),
    ('downarrow', u'\N{DOWNWARDS ARROW}'),
    ('rightarrow', u'\N{RIGHTWARDS ARROW}'),
    ('to', u'\N{RIGHTWARDS ARROW}'),
    ('leftarrow', u'\N{LEFTWARDS ARROW}'),
    ('longrightarrow', u'\N{LONG RIGHTWARDS ARROW}'),
    ('longleftarrow', u'\N{LONG LEFTWARDS ARROW}'),

    # we use these conventions as Identity operator (\mathbbm{1})
    ('id', u'\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}'),
    ('Ident', u'\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}'),
    ]



def _format_uebung(n):
    s = '\n%s\n' %(latexnodes2text([n.nodeargs[0]]))
    optarg = n.nodeargs[1]
    if (optarg is not None):
        s += '[%s]\n' %(latexnodes2text([optarg]))
    return s


_default_macro_list += [
    # some ethuebung.sty macros
    ('exercise', _format_uebung),
    ('uebung', _format_uebung),
    ('hint', 'Hint: %s'),
    ('hints', 'Hints: %s'),
    ('hinweis', 'Hinweis: %s'),
    ('hinweise', 'Hinweise: %s'),
    ]





def _greekletters(letterlist):
    for l in letterlist:
        ucharname = l.upper()
        if (ucharname == 'LAMBDA'):
            ucharname = 'LAMDA'
        smallname = "GREEK SMALL LETTER "+ucharname
        if (ucharname == 'EPSILON'):
            smallname = "GREEK LUNATE EPSILON SYMBOL"
        if (ucharname == 'PHI'):
            smallname = "GREEK PHI SYMBOL"
        _default_macro_list.append(
            (l, unicodedata.lookup(smallname))
            )
        _default_macro_list.append(
            (l[0].upper()+l[1:], unicodedata.lookup("GREEK CAPITAL LETTER "+ucharname))
            )
_greekletters( ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa',
                'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
                'chi', 'psi', 'omega') )
_default_macro_list += [
    ('varepsilon', u'\N{GREEK SMALL LETTER EPSILON}'),
    ('vartheta', u'\N{GREEK THETA SYMBOL}'),
    ('varpi', u'\N{GREEK PI SYMBOL}'),
    ('varrho', u'\N{GREEK RHO SYMBOL}'),
    ('varsigma', u'\N{GREEK SMALL LETTER FINAL SIGMA}'),
    ('varphi', u'\N{GREEK SMALL LETTER PHI}'),
    ]

unicode_accents_list = (
    # see http://en.wikibooks.org/wiki/LaTeX/Special_Characters for a list
    ("'", u"\N{COMBINING ACUTE ACCENT}"),
    ("`", u"\N{COMBINING GRAVE ACCENT}"),
    ('"', u"\N{COMBINING DIAERESIS}"),
    ("c", u"\N{COMBINING CEDILLA}"),
    ("^", u"\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("~", u"\N{COMBINING TILDE}"),
    ("H", u"\N{COMBINING DOUBLE ACUTE ACCENT}"),
    ("k", u"\N{COMBINING OGONEK}"),
    ("=", u"\N{COMBINING MACRON}"),
    ("b", u"\N{COMBINING MACRON BELOW}"),
    (".", u"\N{COMBINING DOT ABOVE}"),
    ("d", u"\N{COMBINING DOT BELOW}"),
    ("r", u"\N{COMBINING RING ABOVE}"),
    ("u", u"\N{COMBINING BREVE}"),
    ("v", u"\N{COMBINING CARON}"),

    ("vec", u"\N{COMBINING RIGHT ARROW ABOVE}"),
    ("dot", u"\N{COMBINING DOT ABOVE}"),
    ("hat", u"\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("check", u"\N{COMBINING CARON}"),
    ("breve", u"\N{COMBINING BREVE}"),
    ("acute", u"\N{COMBINING ACUTE ACCENT}"),
    ("grave", u"\N{COMBINING GRAVE ACCENT}"),
    ("tilde", u"\N{COMBINING TILDE}"),
    ("bar", u"\N{COMBINING OVERLINE}"),
    ("ddot", u"\N{COMBINING DIAERESIS}"),

    ("not", u"\N{COMBINING LONG SOLIDUS OVERLAY}"),

    )

def make_accented_char(node, combining):
    nodearg = node.nodeargs[0] if len(node.nodeargs) else latexwalker.LatexCharsNode(chars=' ')

    c = latexnodes2text([nodearg]).strip()

    def getaccented(ch, combining):
        ch = unicode(ch)
        combining = unicode(combining)
        if (ch == u"\N{LATIN SMALL LETTER DOTLESS I}"):
            ch = u"i"
        if (ch == u"\N{LATIN SMALL LETTER DOTLESS J}"):
            ch = u"j"
        #print u"Accenting %s with %s"%(ch, combining) # this causes UnicdeDecodeError!!!
        return unicodedata.normalize('NFC', unicode(ch)+combining)

    return u"".join([getaccented(ch, combining) for ch in c])


for u in unicode_accents_list:
    (mname, mcombining) = u
    _default_macro_list.append(
        (mname, lambda x, c=mcombining: make_accented_char(x, c))
        )



default_env_dict = dict([(e.envname, e) for e in _default_env_list])
"""
The default context dictionary of known LaTeX environment definitions and how to
convert them to text.

This is a dictionary with keys the environment name (:py:class:`EnvDef.envname <EnvDef>`)
and values are :py:class:`EnvDef` instances.
"""
default_macro_dict = dict([(m.macname, m) for m in (MacroDef(m) for m in _default_macro_list)])
"""
The default context dictionary of known LaTeX macro definitions and how to convert them to text.

This is a dictionary with keys the macro name (:py:class:`MacroDef.macname <MacroDef>`)
and values are :py:class:`MacroDef` instances.
"""


default_text_replacements = (
    # remove indentation provided by LaTeX
    #(re.compile(r'\n[ \t]*'), '\n'),
    
    ("~", " "),
    ("``", '"'),
    ("''", '"'),

    (r'(?<!\\)&', '   '), # ignore tabular alignments, just add a little space
    ('\\&', '&'), # but preserve the \& escapes, that we before *hackingly* kept as '\&' for this purpose ...

    )
"""
Default text replacements (final touches) to apply to LaTeX code. (For instance,
converting ``~`` to (space) or ``''`` to ``"``.)

This is a list (or tuple) of pairs of `(regex-pattern, replacement-text)` of replacements
to perform.
"""



# ------------------------------------------------------------------------------

_strict_latex_spaces_predef = {
    'default': {
        'between-macro-and-chars': False,
        'between-latex-constructs': False,
        'after-comment': False,
        'in-equations': None,
    },
    'macros': {
        'between-macro-and-chars': True,
        'between-latex-constructs': True,
        'after-comment': False,
        'in-equations': False,
    },
    'except-in-equations': {
        'between-macro-and-chars': True,
        'between-latex-constructs': True,
        'after-comment': True,
        'in-equations': False,
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
    elif isinstance(strict_latex_spaces, dict):
        d.update(strict_latex_spaces)
        return d
    elif isinstance(strict_latex_spaces, basestring):
        if strict_latex_spaces == 'on':
            return _parse_strict_latex_spaces_dict(True)
        if strict_latex_spaces == 'off':
            return _parse_strict_latex_spaces_dict(False)
        if strict_latex_spaces not in _strict_latex_spaces_predef:
            raise ValueError("invalid value for strict_latex_spaces preset: {}"
                             .format(strict_latex_spaces))
        return _strict_latex_spaces_predef[strict_latex_spaces]
    else:
        for k in d.keys():
            d[k] = bool(strict_latex_spaces)
        return d


class LatexNodes2Text(object):
    """
    Simplistic Latex-To-Text Converter.

    This class parses a nodes structure generated by the :py:mod:`latexwalker` module,
    and creates a text representation of the structure.

    It is capable of parsing ``\\input`` directives safely, see
    :py:meth:`set_tex_input_directory()` and :py:meth:`read_input_file()`.  By default,
    ``\\input`` and ``\\include`` directives are ignored.

    Arguments to the constructor:

    - `env_dict`, `macro_dict` are dictionaries of known environment and macro
      definitions.  They default to :py:data:`default_env_dict` and
      :py:data:`default_macro_dict`, respectively.

    - `text_replacements` are string replacements to apply onto the final string, as final
      touches.  This defaults to :py:data:`default_text_replacements`.

    Additional keyword arguments are flags which may influence the behavior:

    - `keep_inline_math=True|False`: If set to `True`, then inline math is kept
      using dollar signs, otherwise it is incorporated as normal text.  (By
      default this is `False`)

    - `keep_comments=True|False`: If set to `True`, then LaTeX comments are kept
      (including the percent-sign); otherwise they are discarded.  (By default
      this is `False`)

    - `strict_latex_spaces=True|False`: If set to `True`, then we follow closely
      LaTeX's handling of whitespace.  For instance, whitespace following a bare
      macro (i.e. w/o any delimiting characters like '{') is consumed/removed.
      If set to `False` (the default), then some liberties are taken with
      respect to whitespace [hopefully making the result slightly more
      aesthetic, but this behavior is mostly there for historical reasons].

      You may also use one of the presets
      `strict_latex_spaces='default'|'macros'|'except-in-equations'`, which
      allow for finer control of how whitespace is handled. The 'default' is the
      same as `False`. Using 'macros' will make macros and other sequences
      of LaTeX constructions obey LaTeX space rules, but will keep indentations
      after comments and more liberal whitespace rules in equations. The
      'except-in-equations' preset goes as you'd expect, setting strict latex
      spacing only outside of equation contexts.

      Finally, the argument `strict_latex_spaces` may also be set to a
      dictionary with keys 'between-macro-and-chars', 'after-comment', and
      'between-latex-constructs', 'in-equations', with individual values either
      `True` or `False`, dictating whitespace behavior in specific cases (`True`
      indicates strict latex behavior).  The value for 'in-equations' may even
      be another dictionary with the same keys to override values in equations.

      In the future, the default value of this setting might change, e.g., to
      'macros'.

    - `keep_braced_groups=True|False`: If set to `True`, then braces delimiting
      a TeX group ``{Like this}`` will be kept in the output, with the contents
      of the group converted to text as usual.  (By default this is `False`)

    - `keep_braced_groups_minlen=<int>`: If `keep_braced_groups` is set to
      `True`, then we keep braced groups only if their contents length (after
      conversion to text) is longer than the given value.  E.g., if
      `keep_braced_groups_minlen=2`, then ``{\'e}tonnant`` still goes to
      ``\N{LATIN SMALL LETTER E WITH ACUTE}tonnant`` but ``{\'etonnant}``
      becomes ``{\N{LATIN SMALL LETTER E WITH ACUTE}tonnant}``.

    .. versionadded: 1.4
       Added the `strict_latex_spaces` and the `keep_braced_groups` flags
    """
    def __init__(self, env_dict=None, macro_dict=None, text_replacements=None, **flags):
        super(LatexNodes2Text, self).__init__()

        if env_dict is None:  env_dict = default_env_dict
        if macro_dict is None:  macro_dict = default_macro_dict
        if text_replacements is None: text_replacements = default_text_replacements

        self.env_dict = dict(env_dict)
        self.macro_dict = dict(macro_dict)
        self.text_replacements = text_replacements

        self.tex_input_directory = None
        self.strict_input = True

        self.keep_inline_math = flags.pop('keep_inline_math', False)
        self.keep_comments = flags.pop('keep_comments', False)

        strict_latex_spaces = flags.pop('strict_latex_spaces', False)
        self.strict_latex_spaces = _parse_strict_latex_spaces_dict(strict_latex_spaces)

        self.keep_braced_groups = flags.pop('keep_braced_groups', False)
        self.keep_braced_groups_minlen = flags.pop('keep_braced_groups_minlen', 2)

        if flags:
            # any flags left which we haven't recognized
            logger.warning("LatexNodes2Text(): Unknown flag(s) encountered: %r", flags.keys())
        

    def set_tex_input_directory(self, tex_input_directory, latex_walker_init_args=None, strict_input=True):
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
        
        if tex_input_directory:
            self.macro_dict['input'] = MacroDef('input', lambda n: self._callback_input(n))
            self.macro_dict['include'] = MacroDef('include', lambda n: self._callback_input(n))
        else:
            self.macro_dict['input'] = MacroDef('input', discard=True)
            self.macro_dict['include'] = MacroDef('include', discard=True)


    def read_input_file(self, fn):
        """
        This method may be overridden to implement a custom lookup mechanism when
        encountering ``\\input`` or ``\\include`` directives.

        The default implementation looks for a file of the given name relative
        to the directory set by :py:meth:`set_tex_input_directory()`.  If
        `strict_input=True` was set, we ensure strictly that the file resides in
        a subtree of the reference input directory (after canonicalizing the
        paths and resolving all symlinks).

        You may override this method to obtain the input data in however way you
        see fit.  (In that case, a call to `set_tex_input_directory()` may not
        be needed as that function simply sets properties which are used by the
        default implementation of `read_input_file()`.)

        This function accepts the referred filename as argument (the argument to
        the ``\\input`` macro), and should return a string with the file
        contents (or generate a warning or raise an error).
        """
        fnfull = os.path.realpath(os.path.join(self.tex_input_directory, fn))
        if self.strict_input:
            # make sure that the input file is strictly within dirfull, and didn't escape with
            # '../..' tricks or via symlinks.
            dirfull = os.path.realpath(self.tex_input_directory)
            if not fnfull.startswith(dirfull):
                logger.warning(
                    "Can't access path '%s' leading outside of mandated directory [strict input mode]",
                    fn
                )
                return ''

        if not os.path.exists(fnfull) and os.path.exists(fnfull + '.tex'):
            fnfull = fnfull + '.tex'
        if not os.path.exists(fnfull) and os.path.exists(fnfull + '.latex'):
            fnfull = fnfull + '.latex'
        if not os.path.isfile(fnfull):
            logger.warning(u"Error, file doesn't exist: '%s'", fn)
            return ''
        
        logger.debug("Reading input file %r", fnfull)

        try:
            with open(fnfull) as f:
                return f.read()
        except IOError as e:
            logger.warning(u"Error, can't access '%s': %s", fn, e)
            return ''


    def _callback_input(self, n):
        #
        # recurse into files upon '\input{}'
        #
        
        if len(n.nodeargs) != 1:
            logger.warning(u"Expected exactly one argument for '\\input' ! Got = %r", n.nodeargs)

        inputtex = self.read_input_file(self.nodelist_to_text([n.nodeargs[0]]).strip())

        return self._nodelistcontents_to_text(
            latexwalker.LatexWalker(inputtex, **self.latex_walker_init_args)
            .get_latex_nodes()[0]
        )


    def latex_to_text(self, latex, **parse_flags):
        """
        Parses the given `latex` code and returns its textual representation.

        The `parse_flags` are the flags to give on to the
        :py:class:`pylatexenc.latexwalker.LatexWalker` constructor.
        """
        return self.nodelist_to_text(latexwalker.LatexWalker(latex, **parse_flags).get_latex_nodes()[0])


    def nodelist_to_text(self, nodelist):
        """
        Extracts text from a node list. `nodelist` is a list of nodes as returned by
        :py:meth:`pylatexenc.latexwalker.LatexWalker.get_latex_nodes()`.

        In addition to converting each node in the list to text using
        `node_to_text()`, we apply some global replacements and fine-tuning to
        the resulting text to account for `text_replacements` (e.g., to fix
        quotes, tab alignment ``&`` chars, etc.)
        """

        s = self._nodelistcontents_to_text(nodelist)

        # now, perform suitable replacements
        for pattern, replacement in self.text_replacements:
            if (hasattr(pattern, 'sub')):
                s = pattern.sub(replacement, s)
            else:
                s = s.replace(pattern, replacement)

        if not self.keep_inline_math:
            s = s.replace('$', ''); # removing math mode inline signs, just keep their Unicode counterparts..

        return s


    def _nodelistcontents_to_text(self, nodelist):
        """
        Turn the node list to text representations of each node.  Basically apply
        `node_to_text()` to each node.  (But not quite actually, since we take
        some care as to where we add whitespace.)
        """
        s = ''
        prev_node = None
        for node in nodelist:
            if self._is_bare_macro_node(prev_node) and node.isNodeType(latexwalker.LatexCharsNode):
                if not self.strict_latex_spaces['between-macro-and-chars']:
                    # after a macro with absolutely no arguments, include post_space
                    # in output by default if there are other chars that follow.
                    # This is for more breathing space (especially in equations(?)),
                    # and for compatibility with earlier versions of pylatexenc (<=
                    # 1.3).  This is NOT LaTeX' default behavior (see issue #11), so
                    # only do this if `strict_latex_spaces=False`.
                    s += prev_node.macro_post_space
            s += self.node_to_text(node)
            prev_node = node
        return s

    def node_to_text(self, node, prev_node_hint=None):
        """
        Return the textual representation of the given `node`.

        If `prev_node_hint` is specified, then the current node is formatted
        suitably as following the node given in `prev_node_hint`.  This might
        affect how much space we keep/discard, etc.
        """
        if node is None:
            return ""
        
        if node.isNodeType(latexwalker.LatexCharsNode):
            # Unless in strict latex spaces mode, ignore nodes consisting only
            # of empty chars, as this tends to produce too much space...  These
            # have been inserted by LatexWalker() in some occasions to keep
            # track of all relevant pre_space of tokens, such as between two
            # braced groups ("{one} {two}") or other such situations.
            if not self.strict_latex_spaces['between-latex-constructs'] and len(node.chars.strip()) == 0:
                return ""
            return node.chars
        
        if node.isNodeType(latexwalker.LatexCommentNode):
            if self.keep_comments:
                if self.strict_latex_spaces['after-comment']:
                    return '%' + node.comment + '\n'
                else:
                    # default spaces, i.e., keep what spaces were already there after the comment
                    return '%' + node.comment + node.comment_post_space
            else:
                if self.strict_latex_spaces['after-comment']:
                    return ""
                else:
                    # default spaces, i.e., keep what spaces were already there after the comment
                    # This can be useful to preserve e.g. indentation of the next line
                    return node.comment_post_space
        
        if node.isNodeType(latexwalker.LatexGroupNode):
            contents = self._groupnodecontents_to_text(node)
            if self.keep_braced_groups and len(contents) >= self.keep_braced_groups_minlen:
                return "{" + contents + "}"
            return contents

        def apply_simplify_repl(node, simplify_repl, nodelistargs, what):
            if callable(simplify_repl):
                if 'l2tobj' in getfullargspec(simplify_repl)[0]:
                    # callable accepts an argument named 'l2tobj', provide pointer to self
                    return simplify_repl(node, l2tobj=self)
                return simplify_repl(node)
            if '%' in simplify_repl:
                try:
                    return simplify_repl % tuple([self._groupnodecontents_to_text(nn)
                                                  for nn in nodelistargs])
                except (TypeError, ValueError):
                    logger.warning(
                        "WARNING: Error in configuration: {} failed its substitution!".format(what)
                    )
                    return simplify_repl # too bad, keep the percent signs as they are...
            return simplify_repl
            
        
        if node.isNodeType(latexwalker.LatexMacroNode):
            # get macro behavior definition.
            macroname = node.macroname.rstrip('*')
            if macroname in self.macro_dict:
                mac = self.macro_dict[macroname]
            else:
                # no predefined behavior, use default:
                mac = self.macro_dict['']

            def get_macro_str_repl(node, macroname, mac):
                if mac.simplify_repl:
                    return apply_simplify_repl(node, mac.simplify_repl, node.nodeargs,
                                               what="macro '%s'"%(macroname))
                if mac.discard:
                    return ""
                a = node.nodeargs
                if (node.nodeoptarg):
                    a.prepend(node.nodeoptarg)
                return "".join([self._groupnodecontents_to_text(n) for n in a])

            macrostr = get_macro_str_repl(node, macroname, mac)
            return macrostr

        if node.isNodeType(latexwalker.LatexEnvironmentNode):
            # get environment behavior definition.
            envname = node.envname.rstrip('*')
            if (envname in self.env_dict):
                envdef = self.env_dict[envname]
            else:
                # no predefined behavior, use default:
                envdef = self.env_dict['']

            if envdef.simplify_repl:
                return apply_simplify_repl(node, envdef.simplify_repl, node.nodelist,
                                           what="environment '%s'"%(envname))
            if envdef.discard:
                return ""
            return self._nodelistcontents_to_text(node.nodelist)

        if node.isNodeType(latexwalker.LatexMathNode):
            if self.keep_inline_math:
                # we care about math modes and we should keep this verbatim
                return latexwalker.math_node_to_latex(node)
            else:
                # note, this here only happens if the latexwalker had keep_inline_math=True
                with _PushEquationContext(self):
                    return self._nodelistcontents_to_text(node.nodelist)

        logger.warning("LatexNodes2Text.node_to_text(): Unknown node: %r", node)

        # discard anything else.
        return ""

    def _is_bare_macro_node(self, node):
        return (node is not None and
                node.isNodeType(latexwalker.LatexMacroNode) and 
                node.nodeoptarg is None and 
                len(node.nodeargs) == 0)

    def _groupnodecontents_to_text(self, groupnode):
        return self._nodelistcontents_to_text(groupnode.nodelist)




class _PushEquationContext(latexwalker._PushPropOverride):
    def __init__(self, l2t):

        new_strict_latex_spaces = None
        if l2t.strict_latex_spaces['in-equations'] is not None:
            new_strict_latex_spaces = _parse_strict_latex_spaces_dict(
                l2t.strict_latex_spaces['in-equations']
            )

        super(_PushEquationContext, self).__init__(l2t, 'strict_latex_spaces',
                                                   new_strict_latex_spaces)








# ------------------------------------------------------------------------------



def latex2text(content, tolerant_parsing=False, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from `content` meant for database indexing. `content` is
    some LaTeX code.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    (nodelist, tpos, tlen) = latexwalker.get_latex_nodes(content, keep_inline_math=keep_inline_math,
                                                         tolerant_parsing=tolerant_parsing)

    return latexnodes2text(nodelist, keep_inline_math=keep_inline_math, keep_comments=keep_comments)


def latexnodes2text(nodelist, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from a node list. `nodelist` is a list of nodes as returned by
    :py:func:`pylatexenc.latexwalker.get_latex_nodes()`.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    return LatexNodes2Text(
        keep_inline_math=keep_inline_math,
        keep_comments=keep_comments
    ).nodelist_to_text(nodelist)




def main(argv):
    import fileinput
    import argparse

    parser = argparse.ArgumentParser()

    group = parser.add_argument_group("LatexWalker options")

    group.add_argument('--parser-keep-inline-math', action='store_const', const=True,
                       dest='parser_keep_inline_math', default=True)
    group.add_argument('--no-parser-keep-inline-math', action='store_const', const=False,
                       dest='parser_keep_inline_math',
                       help="Parse inline math between $ signs specially (default yes)")

    group.add_argument('--tolerant-parsing', action='store_const', const=True,
                       dest='tolerant_parsing', default=True)
    group.add_argument('--no-tolerant-parsing', action='store_const', const=False,
                       dest='tolerant_parsing',
                       help="Tolerate syntax errors when parsing, and attempt to continue (default yes)")

    group.add_argument('--strict-braces', action='store_const', const=True,
                       dest='strict_braces', default=False)
    group.add_argument('--no-strict-braces', action='store_const', const=False,
                       dest='strict_braces',
                       help="Report errors for mismatching LaTeX braces (default no)")

    group = parser.add_argument_group("LatexNodes2Text options")

    group.add_argument('--text-keep-inline-math', action='store_const', const=True,
                       dest='text_keep_inline_math', default=False)
    group.add_argument('--no-text-keep-inline-math', action='store_const', const=False,
                       dest='text_keep_inline_math',
                       help="Keep inline math between $ signs verbatim in text output (default no)")

    group.add_argument('--keep-comments', action='store_const', const=True,
                       dest='keep_comments', default=False)
    group.add_argument('--no-keep-comments', action='store_const', const=False,
                       dest='keep_comments',
                       help="Keep LaTeX comments in text output (default no)")

    group.add_argument('--strict-latex-spaces',
                       choices=['off', 'on']+list(_strict_latex_spaces_predef.keys()),
                       dest='strict_latex_spaces', default='macros',
                       help="How to handle whitespace. See documentation for the class "
                       "LatexNodes2Text().")

    group.add_argument('--keep-braced-groups', action='store_const', const=True,
                       dest='keep_braced_groups', default=False)
    group.add_argument('--no-keep-braced-groups', action='store_const', const=False,
                       dest='keep_braced_groups',
                       help="Keep LaTeX {braced groups} in text output (default no)")

    group.add_argument('--keep-braced-groups-minlen', type=int, default=2,
                       dest='keep_braced_groups_minlen',
                       help="Only apply --keep-braced-groups to groups that contain at least"
                       "this many characters")

    parser.add_argument('files', metavar="FILE", nargs='*',
                        help='Input files (if none specified, read from stdandard input)')

    args = parser.parse_args(argv)

    latex = ''
    for line in fileinput.input(files=args.files):
        latex += line
    
    lw = latexwalker.LatexWalker(latex,
                                 keep_inline_math=args.parser_keep_inline_math,
                                 tolerant_parsing=args.tolerant_parsing,
                                 strict_braces=args.strict_braces)

    (nodelist, pos, len_) = lw.get_latex_nodes()

    ln2t = LatexNodes2Text(keep_inline_math=args.text_keep_inline_math,
                           keep_comments=args.keep_comments,
                           strict_latex_spaces=args.strict_latex_spaces,
                           keep_braced_groups=args.keep_braced_groups,
                           keep_braced_groups_minlen=args.keep_braced_groups_minlen)

    print(ln2t.nodelist_to_text(nodelist) + "\n")



if __name__ == '__main__':

    try:

        main(sys.argv[1:])

    except SystemExit:
        raise
    except: # lgtm [py/catch-base-exception]
        import pdb
        import traceback
        traceback.print_exc()
        pdb.post_mortem()


