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


# Internal module. May change without notice.

import unicodedata
import sys

if sys.version_info.major >= 3:
    def unicode(string): return string
    basestring = str
else:
    pass



from ..latex2text import MacroTextSpec, EnvironmentTextSpec, SpecialsTextSpec, \
    fmt_equation_environment, fmt_placeholder_node, placeholder_node_formatter, fmt_input_macro



def _format_uebung(n, l2t):
    s = '\n' + l2t.nodelist_to_text([n.nodeargs[0]]) + '\n'
    optarg = n.nodeargs[1]
    if optarg is not None:
        s += '[{}]\n'.format(l2t.nodelist_to_text([optarg]))
    return s


# construct the specs structure, more than the just the following definition

latex_base_specs = {
    
    'environments': [

        EnvironmentTextSpec('equation', simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec('eqnarray', simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec('align', simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec('multline', simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec('gather', simplify_repl=fmt_equation_environment),
        EnvironmentTextSpec('dmath', simplify_repl=fmt_equation_environment),

        EnvironmentTextSpec('array', simplify_repl=fmt_placeholder_node),
        EnvironmentTextSpec('pmatrix', simplify_repl=fmt_placeholder_node),
        EnvironmentTextSpec('bmatrix', simplify_repl=fmt_placeholder_node),
        EnvironmentTextSpec('smallmatrix', simplify_repl=fmt_placeholder_node),

        EnvironmentTextSpec('center', simplify_repl='\n%s\n'),
        EnvironmentTextSpec('flushleft', simplify_repl='\n%s\n'),
        EnvironmentTextSpec('flushright', simplify_repl='\n%s\n'),

        EnvironmentTextSpec('exenumerate', discard=False),
        EnvironmentTextSpec('enumerate', discard=False),
        EnvironmentTextSpec('list', discard=False),
        EnvironmentTextSpec('itemize', discard=False),
        EnvironmentTextSpec('subequations', discard=False),
        EnvironmentTextSpec('figure', discard=False),
        EnvironmentTextSpec('table', discard=False),

    ],
    'specials': [
        SpecialsTextSpec('&', '   '), # ignore tabular alignments, just add a little space
    ],

    'macros': [
        # NOTE: macro will only be assigned arguments if they are explicitly defined as
        #       accepting arguments in latexwalker.py.
        MacroTextSpec('emph', discard=False),
        MacroTextSpec('textrm', discard=False),
        MacroTextSpec('textit', discard=False),
        MacroTextSpec('textbf', discard=False),
        MacroTextSpec('textsc', discard=False),
        MacroTextSpec('textsl', discard=False),
        MacroTextSpec('text', discard=False),

        MacroTextSpec('mathrm', discard=False),
        MacroTextSpec('mathbb', discard=False),
        MacroTextSpec('mathbf', discard=False),
        MacroTextSpec('mathsf', discard=False),
        MacroTextSpec('mathscr', discard=False),
        MacroTextSpec('mathfrak', discard=False),


        MacroTextSpec('input', simplify_repl=fmt_input_macro),
        MacroTextSpec('include', simplify_repl=fmt_input_macro),

    ] + [ MacroTextSpec(x, simplify_repl=y) for x, y in (

        ('includegraphics', placeholder_node_formatter('graphics')),

        ('ref', '<ref>'),
        ('autoref', '<ref>'),
        ('cref', '<ref>'),
        ('Cref', '<Ref>'),
        ('eqref', '(<ref>)'),
        ('url', '<%s>'),
        ('item',
         lambda r, l2tobj: '\n  '+(
             l2tobj.nodelist_to_text([r.nodeoptarg]) if r.nodeoptarg else '* '
         )
        ) ,
        ('footnote', '[%s]'),
        ('href', lambda n, l2tobj:  \
         '{} <{}>'.format(l2tobj.nodelist_to_text([n.nodeargd.argnlist[1]]), 
                          l2tobj.nodelist_to_text([n.nodeargd.argnlist[0]]))),

        ('cite', '<cit.>'),
        ('citet', '<cit.>'),
        ('citep', '<cit.>'),

        # use second argument:
        ('texorpdfstring', lambda node, l2t: l2t.nodelist_to_text(node.nodeargs[1:2])),


        ('part',
         lambda n, l2tobj: u'\n\nPART: {}\n'.format(l2tobj.node_arg_to_text(n, 2).upper())),
        ('chapter',
         lambda n, l2tobj: u'\n\nCHAPTER: {}\n'.format(l2tobj.node_arg_to_text(n, 2).upper())),
        ('section',
         lambda n, l2tobj: u'\n\n\N{SECTION SIGN} {}\n'.format(l2tobj.node_arg_to_text(n, 2).upper())),
        ('subsection',
         lambda n, l2tobj: u'\n\n \N{SECTION SIGN}.\N{SECTION SIGN} {}\n'.format(
             l2tobj.node_arg_to_text(n, 2))),
        ('subsubsection',
         lambda n, l2tobj: u'\n\n  \N{SECTION SIGN}.\N{SECTION SIGN}.\N{SECTION SIGN} {}\n'.format(
             l2tobj.node_arg_to_text(n, 2))),
        ('paragraph',
         lambda n, l2tobj: u'\n\n  {}\n'.format(l2tobj.node_arg_to_text(n, 2))),
        ('subparagraph',
         lambda n, l2tobj: u'\n\n    {}\n'.format(
             l2tobj.node_arg_to_text(n, 2))),


        ('hspace', ''),
        ('vspace', '\n'),

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
        ("&", "&" ),
        ("$", "$" ),
        ("{", "{" ),
        ("}", "}" ),
        ("%", lambda arg: "%" ), # careful: % is formatting substitution symbol...
        ("#", "#" ),
        ("_", "_" ),

        ("\\", '\n'),

        ("textquoteleft", "\N{LEFT SINGLE QUOTATION MARK}"),
        ("textquoteright", "\N{RIGHT SINGLE QUOTATION MARK}"),
        ("textquotedblright", u"\N{RIGHT DOUBLE QUOTATION MARK}"),
        ("textquotedblleft", u"\N{LEFT DOUBLE QUOTATION MARK}"),
        ("textendash", u"\N{EN DASH}"),
        ("textemdash", u"\N{EM DASH}"),

        ('textpm', u"\N{PLUS-MINUS SIGN}"),
        ('textmp', u"\N{MINUS-OR-PLUS SIGN}"),

        ("texteuro", u"\N{EURO SIGN}"),

        ("backslash", "\\"),
        ("textbackslash", "\\"),

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
        ('sqrt', u'\N{SQUARE ROOT}(%(2)s)'),
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
        ('cosh', 'cosh'),
        ('sinh', 'sinh'),
        ('tanh', 'tanh'),
        ('arccosh', 'arccosh'),
        ('arcsinh', 'arcsinh'),
        ('arctanh', 'arctanh'),
        
        ('ln', 'ln'),
        ('log', 'log'),

        ('max', 'max'),
        ('min', 'min'),
        ('sup', 'sup'),
        ('inf', 'inf'),
        ('lim', 'lim'),
        ('limsup', 'lim sup'),
        ('liminf', 'lim inf'),

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
        ('lvert', u'|'),
        ('rvert', u'|'),
        ('vert', u'|'),
        ('lVert', u'\u2016'),
        ('rVert', u'\u2016'),
        ('Vert', u'\u2016'),
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
    )]
}


specs = [
    #
    # CATEGORY: latex-base
    #
    ('latex-base', latex_base_specs),

    #
    # CATEGORY: nonascii-specials
    #
    ('nonascii-specials', {
        'macros': [],
        'environments': [],
        'specials': [
            SpecialsTextSpec('~', u"\N{NO-BREAK SPACE}"),
            SpecialsTextSpec('``', u"\N{LEFT DOUBLE QUOTATION MARK}"),
            SpecialsTextSpec("''", u"\N{RIGHT DOUBLE QUOTATION MARK}"),
            SpecialsTextSpec("--", u"\N{EN DASH}"),
            SpecialsTextSpec("---", u"\N{EM DASH}"),
            SpecialsTextSpec("!`", u"\N{INVERTED EXCLAMATION MARK}"),
            SpecialsTextSpec("?`", u"\N{INVERTED QUESTION MARK}"),
        ]
    }),

    #
    # CATEGORY: latex-ethuebung
    #
    ('latex-ethuebung', {
        'macros': [
            MacroTextSpec('exercise', simplify_repl=_format_uebung),
            MacroTextSpec('uebung', simplify_repl=_format_uebung),
            MacroTextSpec('hint', 'Hint: %s'),
            MacroTextSpec('hints', 'Hints: %s'),
            MacroTextSpec('hinweis', 'Hinweis: %s'),
            MacroTextSpec('hinweise', 'Hinweise: %s'),
        ],
        'environments': [],
        'specials': []
    }),

]





def _greekletters(letterlist):
    for l in letterlist:
        ucharname = l.upper()
        if ucharname == 'LAMBDA':
            ucharname = 'LAMDA'
        smallname = "GREEK SMALL LETTER "+ucharname
        if ucharname == 'EPSILON':
            smallname = "GREEK LUNATE EPSILON SYMBOL"
        if ucharname == 'PHI':
            smallname = "GREEK PHI SYMBOL"
        latex_base_specs['macros'].append(
            MacroTextSpec(l, unicodedata.lookup(smallname))
        )
        latex_base_specs['macros'].append(
            MacroTextSpec(l[0].upper()+l[1:], unicodedata.lookup("GREEK CAPITAL LETTER "+ucharname))
            )
_greekletters(
    ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa',
     'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
     'chi', 'psi', 'omega')
)
latex_base_specs['macros'] += [
    MacroTextSpec('varepsilon', u'\N{GREEK SMALL LETTER EPSILON}'),
    MacroTextSpec('vartheta', u'\N{GREEK THETA SYMBOL}'),
    MacroTextSpec('varpi', u'\N{GREEK PI SYMBOL}'),
    MacroTextSpec('varrho', u'\N{GREEK RHO SYMBOL}'),
    MacroTextSpec('varsigma', u'\N{GREEK SMALL LETTER FINAL SIGMA}'),
    MacroTextSpec('varphi', u'\N{GREEK SMALL LETTER PHI}'),
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

def make_accented_char(node, combining, l2tobj):
    if len(node.nodeargs):
        nodearg = node.nodeargs[0]
        c = l2tobj.nodelist_to_text([nodearg]).strip()
    else:
        c = ' '

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
    latex_base_specs['macros'].append(
        MacroTextSpec(mname, lambda x, l2tobj, c=mcombining: make_accented_char(x, c, l2tobj))
    )

# specs structure now complete

