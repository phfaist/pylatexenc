
# -*- coding: utf-8 -*-

import unittest

import re
import os
import os.path
import shutil
import tempfile
import unicodedata
import datetime
import logging
import warnings

import pytest

from pylatexenc.latexwalker import LatexWalker
from pylatexenc import latex2text
from pylatexenc.latex2text import LatexNodes2Text


# These tests exercise the pylatexenc 2.x compatibility API on purpose, so the
# associated deprecation warnings are expected and would only drown out the
# pytest output.  (The warnings.simplefilter() calls in the test case
# constructors below don't help under pytest, which resets the warning filters
# around each test.)
pytestmark = pytest.mark.filterwarnings("ignore:Deprecated \\(pylatexenc")


#
# Helpers for the math_mode='fancy' tests further down.
#
# That math mode writes the letters of a formula with the unicode
# "mathematical alphanumeric symbols", which in most editors look exactly like
# the ordinary latin letters.  Spelling the expected values out as literal
# characters would therefore make the tests unreadable, so we build them here
# out of plain ASCII instead.  The characters are looked up by their unicode
# name rather than computed from a table of code points, so that the
# expectations do not lean on the very table that is being tested.
#

_math_alphabet_unicode_name_prefix = {
    'bold': 'MATHEMATICAL BOLD',
    'italic': 'MATHEMATICAL ITALIC',
    'bold-italic': 'MATHEMATICAL BOLD ITALIC',
    'script': 'MATHEMATICAL SCRIPT',
    'fraktur': 'MATHEMATICAL FRAKTUR',
    'doublestruck': 'MATHEMATICAL DOUBLE-STRUCK',
    'sans': 'MATHEMATICAL SANS-SERIF',
    'sans-italic': 'MATHEMATICAL SANS-SERIF ITALIC',
    'monospace': 'MATHEMATICAL MONOSPACE',
}

# The letters for which there is no such "MATHEMATICAL ..." character, because
# unicode had already given that symbol a code point of its own somewhere else.
_math_alphabet_unicode_holes = {
    ('italic', 'h'): u'\N{PLANCK CONSTANT}',
    ('script', 'B'): u'\N{SCRIPT CAPITAL B}',
    ('script', 'E'): u'\N{SCRIPT CAPITAL E}',
    ('script', 'F'): u'\N{SCRIPT CAPITAL F}',
    ('script', 'H'): u'\N{SCRIPT CAPITAL H}',
    ('script', 'I'): u'\N{SCRIPT CAPITAL I}',
    ('script', 'L'): u'\N{SCRIPT CAPITAL L}',
    ('script', 'M'): u'\N{SCRIPT CAPITAL M}',
    ('script', 'R'): u'\N{SCRIPT CAPITAL R}',
    ('script', 'e'): u'\N{SCRIPT SMALL E}',
    ('script', 'g'): u'\N{SCRIPT SMALL G}',
    ('script', 'o'): u'\N{SCRIPT SMALL O}',
    ('fraktur', 'C'): u'\N{BLACK-LETTER CAPITAL C}',
    ('fraktur', 'H'): u'\N{BLACK-LETTER CAPITAL H}',
    ('fraktur', 'I'): u'\N{BLACK-LETTER CAPITAL I}',
    ('fraktur', 'R'): u'\N{BLACK-LETTER CAPITAL R}',
    ('fraktur', 'Z'): u'\N{BLACK-LETTER CAPITAL Z}',
    ('doublestruck', 'C'): u'\N{DOUBLE-STRUCK CAPITAL C}',
    ('doublestruck', 'H'): u'\N{DOUBLE-STRUCK CAPITAL H}',
    ('doublestruck', 'N'): u'\N{DOUBLE-STRUCK CAPITAL N}',
    ('doublestruck', 'P'): u'\N{DOUBLE-STRUCK CAPITAL P}',
    ('doublestruck', 'Q'): u'\N{DOUBLE-STRUCK CAPITAL Q}',
    ('doublestruck', 'R'): u'\N{DOUBLE-STRUCK CAPITAL R}',
    ('doublestruck', 'Z'): u'\N{DOUBLE-STRUCK CAPITAL Z}',
}

def math_alphabet(style, s):
    r"""Return the plain-ASCII string `s` rewritten with the unicode
    mathematical alphanumeric characters of the given `style`.  Characters that
    are not latin letters are left alone."""
    result = ''
    for c in s:
        if not (('a' <= c <= 'z') or ('A' <= c <= 'Z')):
            result += c
        elif (style, c) in _math_alphabet_unicode_holes:
            result += _math_alphabet_unicode_holes[(style, c)]
        else:
            result += unicodedata.lookup(
                _math_alphabet_unicode_name_prefix[style]
                + (' SMALL ' if c.islower() else ' CAPITAL ')
                + c.upper()
            )
    return result

def mvar(s):
    r"""The way the fancy text engine renders the variable name `s`, i.e. in
    math italics, which is its default `math_fontstyle=`."""
    return math_alphabet('italic', s)


class TestLatexNodes2Text(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexNodes2Text, self).__init__(*args, **kwargs)
        self.maxDiff = None
        warnings.simplefilter('ignore', DeprecationWarning)

    #
    # Note: many of the tests below ask for math_mode='text' explicitly, even
    # where the feature they test has nothing to do with math mode.  They were
    # written against the rendering that `pylatexenc 2` produced, which is what
    # 'text' still does; the default became 'fancy' in `pylatexenc 3.0`, and
    # that mode also styles the letters of '\textbf{}' and friends with the
    # unicode alphabets, so the expected strings would no longer match.  The
    # rendering of that mode is tested on its own further down.
    #

    def test_default_math_mode_is_fancy(self):

        self.assertEqual(LatexNodes2Text().math_mode, 'fancy')
        self.assertEqual(LatexNodes2Text().latex_to_text(r'$\sin 2x$'),
                         'sin 2' + mvar('x'))

    def test_basic(self):

        self.assertEqual(
            LatexNodes2Text(math_mode='text')
                .nodelist_to_text(LatexWalker(r'\textbf{A}').get_latex_nodes()[0]),
            'A'
        )

        latex = r'''\textit{hi there!} This is {\em an equation}:
\begin{equation}
    x + y i = 0
\end{equation}

where $i$ is the ``imaginary unit.''
'''
        self.assertEqualUpToWhitespace(
            LatexNodes2Text(math_mode='text')
                .nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
            u'''hi there! This is an equation:

    x + y i = 0

where i is the “imaginary unit.”
'''
        )
        self.assertEqualUpToWhitespace(
            LatexNodes2Text(math_mode='with-delimiters').nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
            u'''hi there! This is an equation:
\\begin{equation}
    x + y i = 0
\\end{equation}
where $i$ is the “imaginary unit.”
'''
        )

        self.assertEqual(
            LatexNodes2Text(math_mode='text')
                .nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
            LatexNodes2Text(math_mode='text').latex_to_text(latex)
        )

    def test_accents(self):
        self.assertEqual(
            LatexNodes2Text().nodelist_to_text(LatexWalker(r"Fran\c cais").get_latex_nodes()[0]),
            '''Fran\N{LATIN SMALL LETTER C WITH CEDILLA}ais'''
        )
        self.assertEqual(
            LatexNodes2Text().nodelist_to_text(LatexWalker(r"Fr\'en{\'{e}}tique").get_latex_nodes()[0]),
            '''Fr\N{LATIN SMALL LETTER E WITH ACUTE}n\N{LATIN SMALL LETTER E WITH ACUTE}tique'''
        )
        self.assertEqual(
            LatexNodes2Text(math_mode='with-delimiters')
            .nodelist_to_text(LatexWalker(r"$1 \not= 2$").get_latex_nodes()[0]),
            '''$1 {} 2$'''.format(unicodedata.normalize('NFC', "=\N{COMBINING LONG SOLIDUS OVERLAY}"))
        )


    def test_keep_braced_groups(self):
        self.assertEqual(
            LatexNodes2Text(math_mode='text', keep_braced_groups=True)
            .nodelist_to_text(
                LatexWalker(
                    r"\textit{Voil\`a du texte}. Il est \'{e}crit {en fran{\c{c}}ais}"
                ).get_latex_nodes()[0]
            ),
            '''Voil\N{LATIN SMALL LETTER A WITH GRAVE} du texte. Il est \N{LATIN SMALL LETTER E WITH ACUTE}crit {en fran\N{LATIN SMALL LETTER C WITH CEDILLA}ais}'''
        )

        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            keep_braced_groups=True, keep_braced_groups_minlen=4)
            .nodelist_to_text(LatexWalker(r"A{XYZ}{ABCD}").get_latex_nodes()[0]),
            '''AXYZ{ABCD}'''
        )
        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            keep_braced_groups=True, keep_braced_groups_minlen=0)
            .nodelist_to_text(LatexWalker(r"{A}{XYZ}{ABCD}").get_latex_nodes()[0]),
            '''{A}{XYZ}{ABCD}'''
        )

    #
    # Handling of spaces
    #

    def test_spaces_strictlatex(self):

        def do_test(tex, uni, math_mode=None):
            kwargs = {}
            if math_mode is not None:
                kwargs['math_mode'] = math_mode
            self.assertEqual(
                LatexNodes2Text(strict_latex_spaces=True, **kwargs).latex_to_text(tex),
                uni,
                msg="For TeX=r'{}'".format(tex)
            )

        # from https://github.com/phfaist/pylatexenc/issues/11

        from itertools import combinations_with_replacement
        chars = ((r'\"{o} ', 'ö '),
                 (r'{\"o} ', 'ö '),
                 (r'\L ', 'Ł'),
                 (r'{\L} ', 'Ł '),
                 ('u ', 'u '))

        for cc in combinations_with_replacement(chars, 3):
            ttex, uuni = list(zip(*cc))

            tex = ''.join(ttex).strip()
            uni = ''.join(uuni).strip()

            do_test(tex, uni)

        # from https://github.com/phfaist/pylatexenc/issues/15

        do_test(r'$\alpha$ $\beta$ $\gamma$', r'$\alpha$ $\beta$ $\gamma$', math_mode='verbatim')
        do_test(r'$\gamma$ detector', r'$\gamma$ detector', math_mode='verbatim')
        do_test(r'$\gamma$ $\gamma$ coincidence', r'$\gamma$ $\gamma$ coincidence',
                math_mode='verbatim')


    def test_spaces_strictlatex_options(self):

        def do_test(tex, uni, strict_latex_spaces=None, keep_comments=None, **kwargs):
            self.assertEqual(
                LatexNodes2Text(math_mode='text', strict_latex_spaces=strict_latex_spaces,
                                keep_comments=keep_comments,
                                **kwargs)
                .latex_to_text(tex, **kwargs),
                uni
            )

        testlatex = r'''{A} {B} \L \AA xyz:
inline math $\alpha\beta \gamma = x + i y$
line with comment % comment here
	  indented line.
\begin{equation}
    \zeta = a + i b
\end{equation}
the end.'''

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ = x + i y
line with comment % comment here
	  indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces=False, keep_comments=True)

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ = x + i y
line with comment 
	  indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces=False, keep_comments=False)

        do_test(testlatex, r'''ABŁÅ xyz:
inline math αβγ = x + i y
line with comment % comment here
	  indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces='based-on-source', keep_comments=True)
        do_test(testlatex, r'''ABŁÅ xyz:
inline math αβγ = x + i y
line with comment 
	  indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces='based-on-source', keep_comments=False)

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ = x + i y
line with comment % comment here
	  indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces='macros', keep_comments=True)

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ = x + i y
line with comment 
	  indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces='macros', keep_comments=False)

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ = x + i y
line with comment % comment here
indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces='except-in-equations', keep_comments=True)

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ = x + i y
line with comment indented line.

    ζ = a + i b

the end.''',
                strict_latex_spaces='except-in-equations', keep_comments=False)

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ= x + i y
line with comment % comment here
indented line.

    ζ= a + i b

the end.''',
                strict_latex_spaces=True, keep_comments=True)

        do_test(testlatex, r'''A B ŁÅxyz:
inline math αβγ= x + i y
line with comment indented line.

    ζ= a + i b

the end.''',
                strict_latex_spaces=True, keep_comments=False)


    def test_spaces_basedonsource(self):

        # from https://github.com/phfaist/pylatexenc/issues/11 --- earlier
        # behavior is called 'based-on-source' in pylatexenc 2.x

        def do_test(tex, uni):
            self.assertEqual(
                LatexNodes2Text(strict_latex_spaces='based-on-source').latex_to_text(tex),
                uni,
                msg="For TeX=r'{}'".format(tex)
            )

        do_test(r'\"{o} \"{o} \"{o}', 'ööö')
        do_test(r'\"{o} \"{o} {\"o}', 'ööö')
        do_test(r'\"{o} \"{o} \L', 'ööŁ')
        do_test(r'\"{o} \"{o} {\L}', 'ööŁ')
        do_test(r'\"{o} \"{o} u', 'öö u')
        do_test(r'\"{o} {\"o} {\"o}', 'ööö')
        do_test(r'\"{o} {\"o} \L', 'ööŁ')
        do_test(r'\"{o} {\"o} {\L}', 'ööŁ')
        do_test(r'\"{o} {\"o} u', 'öö u')
        do_test(r'\"{o} \L \L', 'öŁŁ') #
        do_test(r'\"{o} \L {\L}', 'öŁŁ') #
        do_test(r'\"{o} \L u', 'öŁ u')
        do_test(r'\"{o} {\L} {\L}', 'öŁŁ')
        do_test(r'\"{o} {\L} u', 'öŁ u')
        do_test(r'\"{o} u u', 'ö u u')
        do_test(r'{\"o} {\"o} {\"o}', 'ööö')
        do_test(r'{\"o} {\"o} \L', 'ööŁ')
        do_test(r'{\"o} {\"o} {\L}', 'ööŁ')
        do_test(r'{\"o} {\"o} u', 'öö u')
        do_test(r'{\"o} \L \L', 'öŁŁ') #
        do_test(r'{\"o} \L {\L}', 'öŁŁ') #
        do_test(r'{\"o} \L u', 'öŁ u')
        do_test(r'{\"o} {\L} {\L}', 'öŁŁ')
        do_test(r'{\"o} {\L} u', 'öŁ u')
        do_test(r'{\"o} u u', 'ö u u')
        do_test(r'\L \L \L', 'ŁŁŁ') #
        do_test(r'\L \L {\L}', 'ŁŁŁ') #
        do_test(r'\L \L u', 'ŁŁ u') #
        do_test(r'\L {\L} {\L}', 'ŁŁŁ') #
        do_test(r'\L {\L} u', 'ŁŁ u') #
        do_test(r'\L u u', 'Ł u u')
        do_test(r'{\L} {\L} {\L}', 'ŁŁŁ')
        do_test(r'{\L} {\L} u', 'ŁŁ u')
        do_test(r'{\L} u u', 'Ł u u')
        do_test(r'u u u', 'u u u')



    def test_spacing_specials(self):

        self.assertEqualUpToWhitespace(
            LatexNodes2Text(math_mode='text').latex_to_text(
                r"""``Hello,'' \emph{she} said."""
            ),
            r"""“Hello,” she said."""
        )




    def test_input(self):
        latex = r'''ABCDEF fdksanfkld safnkd anfklsa

\input{test_input_1.tex}

MORENKFDNSN'''
        correct_text = r'''ABCDEF fdksanfkld safnkd anfklsa

hi there! This is an equation:

    x + y i = 0

where i is the imaginary unit.

MORENKFDNSN'''

        testdir = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))

        l2t = LatexNodes2Text(math_mode='text')
        l2t.set_tex_input_directory(testdir)

        output = l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0])

        self.assertEqualUpToWhitespace(
            output,
            correct_text
        )

        latex = r'''ABCDEF fdksanfkld safnkd anfklsa

\input{test_input_1}

MORENKFDNSN'''

        self.assertEqualUpToWhitespace(
            l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
            correct_text
        )

        latex = r'''ABCDEF fdksanfkld safnkd anfklsa

\input{../test_input_1}

MORENKFDNSN'''

        correct_text_unsafe = correct_text # as before
        correct_text_safe = r'''ABCDEF fdksanfkld safnkd anfklsa

MORENKFDNSN'''

        # make sure that the \input{} directive failed to include the file.
        l2t = LatexNodes2Text(math_mode='text')
        l2t.set_tex_input_directory(os.path.join(testdir, 'dummy'))
        self.assertEqualUpToWhitespace(
            l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
            correct_text_safe
        )
        # but without the strict_input flag, it can access it.
        l2t.set_tex_input_directory(os.path.join(testdir, 'dummy'), strict_input=False)
        self.assertEqualUpToWhitespace(
            l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
            correct_text_unsafe
        )


    def test_mathmodes_00(self):
        latex = r"""
If $\alpha=1$ and \(\beta=2\), then
\[
  \beta=2\alpha\ ,
\]
or, equivalently,
$$ \alpha = \frac1{\beta}\ .$$
"""
        correct_text = r"""
If α=1 and β=2, then

    β=2α ,

or, equivalently,

    α = 1/β .

"""
        l2t = LatexNodes2Text(math_mode='text')
        self.assertEqualUpToWhitespace(
            l2t.latex_to_text(latex),
            correct_text
        )

    def test_mathmodes_01(self):
        latex = r"""
If $\alpha=1$ and \(\beta=2\), then
\[
  \beta=2\alpha\ ,
\]
or, equivalently,
$$ \alpha = \frac1{\beta}\ .$$
"""
        correct_text = r"""
If $α=1$ and \(β=2\), then
\[
    β=2α ,
\]
or, equivalently,
$$
    α = 1/β .
$$
"""
        l2t = LatexNodes2Text(math_mode='with-delimiters')
        self.assertEqualUpToWhitespace(
            l2t.latex_to_text(latex),
            correct_text
        )

    def test_mathmodes_02(self):
        latex = r"""
If $\alpha=1$ and \(\beta=2\), then
\[
  \beta=2\alpha\ ,
\]
or, equivalently,
$$ \alpha = \frac1{\beta}\ .$$
"""

        l2t = LatexNodes2Text(math_mode='verbatim')
        self.assertEqualUpToWhitespace(
            l2t.latex_to_text(latex),
            latex # math stays verbatim
        )


    #
    # test math_mode='fancy'
    #
    # This math mode ignores the whitespace of the source, the way LaTeX itself
    # does, and puts spaces back where they help a reader.  The expected values
    # below are built with the mvar()/math_alphabet() helpers defined at the top
    # of this file, because the characters involved are visually
    # indistinguishable from plain ASCII letters in most editors.
    #

    def fancy(self, latex, **flags):
        r"""Convert `latex` with the fancy math text engine.  Any additional
        keyword arguments are passed on to the `LatexNodes2Text` constructor."""
        kwargs = dict(math_mode='fancy')
        kwargs.update(flags)
        return LatexNodes2Text(**kwargs).latex_to_text(latex)

    # --- the spacing rule, one test per rule ---

    def test_mathmodes_fancy_spacing_binary_or_relation(self):
        # rule 1: either side is a binary operator or a relation
        self.assertEqual(self.fancy(r'$x+y$'), mvar('x') + ' + ' + mvar('y'))
        self.assertEqual(self.fancy(r'$a=b$'), mvar('a') + ' = ' + mvar('b'))
        self.assertEqual(self.fancy(r'$a\le b$'),
                         mvar('a') + u' \N{LESS-THAN OR EQUAL TO} ' + mvar('b'))
        # '\ne' is an alias of '\neq'
        self.assertEqual(self.fancy(r'$a\ne b$'),
                         mvar('a') + u' \N{NOT EQUAL TO} ' + mvar('b'))

    def test_mathmodes_fancy_spacing_open_ended(self):
        # rule 2: either side is a rendering with no visible extent on that
        # edge, such as the 'q' of 'x^q' or either operand of 'a/b'
        self.assertEqual(self.fancy(r'$x^q p$'),
                         mvar('x') + '^' + mvar('q') + ' ' + mvar('p'))
        self.assertEqual(self.fancy(r'$\frac{a}{b}c$'),
                         mvar('a') + '/' + mvar('b') + ' ' + mvar('c'))
        self.assertEqual(self.fancy(r'$c\frac{a}{b}$'),
                         mvar('c') + ' ' + mvar('a') + '/' + mvar('b'))
        # the root sign delimits the left edge, so only the right edge is open
        self.assertEqual(self.fancy(r'$\sqrt{x}2$'),
                         u'\N{SQUARE ROOT}' + mvar('x') + ' 2')
        self.assertEqual(self.fancy(r'$2\sqrt{x}$'),
                         '2' + u'\N{SQUARE ROOT}' + mvar('x'))

    def test_mathmodes_fancy_spacing_operator_or_text_on_the_left(self):
        # rule 3: the left side is a large operator or a text fragment, unless
        # a delimiter follows (a delimiter hugs what it encloses)
        self.assertEqual(self.fancy(r'$\sin x$'), 'sin ' + mvar('x'))
        self.assertEqual(self.fancy(r'$\sin(x)$'), 'sin(' + mvar('x') + ')')
        self.assertEqual(self.fancy(r'$a+\text{[xyz]}$'),
                         mvar('a') + ' + [xyz]')

    def test_mathmodes_fancy_spacing_operator_or_text_on_the_right(self):
        # rule 4: the right side is a large operator or a text fragment, unless
        # an opening delimiter precedes
        self.assertEqual(self.fancy(r'$2\sin x$'), '2 sin ' + mvar('x'))
        self.assertEqual(self.fancy(r'$(\sin x)$'), '(sin ' + mvar('x') + ')')
        self.assertEqual(self.fancy(r'$2\text{kg}$'), '2 kg')

    def test_mathmodes_fancy_spacing_punctuation(self):
        # rule 5: the left side is punctuation (never merely because the right
        # side is)
        self.assertEqual(self.fancy(r'$a, b; c$'),
                         mvar('a') + ', ' + mvar('b') + '; ' + mvar('c'))
        self.assertEqual(self.fancy(r'$f(x, y)$'),
                         mvar('f') + '(' + mvar('x') + ', ' + mvar('y') + ')')

    def test_mathmodes_fancy_spacing_adjacent_digits(self):
        # rule 6: two adjacent digits, which would otherwise run together into
        # a single number.  The braces are what makes the two digits separate
        # items in the first place; '$12$' is one number and stays one.
        self.assertEqual(self.fancy(r'${1}2$'), '1 2')
        self.assertEqual(self.fancy(r'${12}{34}$'), '12 34')
        self.assertEqual(self.fancy(r'$12$'), '12')
        # ... and only for digits: a letter next to a digit stays tight
        self.assertEqual(self.fancy(r'${a}2$'), mvar('a') + '2')

    def test_mathmodes_fancy_spacing_otherwise_tight(self):
        # rule 7: everything else is joined tightly
        self.assertEqual(self.fancy(r'$4\pi c$'),
                         '4' + u'\N{GREEK SMALL LETTER PI}' + mvar('c'))
        self.assertEqual(self.fancy(r'$f(x)$'),
                         mvar('f') + '(' + mvar('x') + ')')

    def test_mathmodes_fancy_unary_minus(self):
        # a binary operator whose left neighbour is a binary operator, a
        # relation, an opening delimiter, punctuation or nothing at all is
        # really a unary one, and binds tightly rightwards
        self.assertEqual(self.fancy(r'$-x$'), '-' + mvar('x'))
        self.assertEqual(self.fancy(r'$x = -y$'), mvar('x') + ' = -' + mvar('y'))
        self.assertEqual(self.fancy(r'$-x + (-y)$'),
                         '-' + mvar('x') + ' + (-' + mvar('y') + ')')
        self.assertEqual(self.fancy(r'$(-a, -b)$'),
                         '(-' + mvar('a') + ', -' + mvar('b') + ')')
        # ... but a genuine binary minus still gets its spaces
        self.assertEqual(self.fancy(r'$a - b$'), mvar('a') + ' - ' + mvar('b'))

    # --- implicit multiplication and the whitespace of the source ---

    def test_mathmodes_fancy_implicit_multiplication_stays_tight(self):
        self.assertEqual(self.fancy(r'$4\pi c$'),
                         '4' + u'\N{GREEK SMALL LETTER PI}' + mvar('c'))
        self.assertEqual(self.fancy(r'$2xy$'), '2' + mvar('xy'))

    def test_mathmodes_fancy_source_whitespace_is_ignored(self):
        # math mode ignores the whitespace of the source, the way LaTeX does
        self.assertEqual(self.fancy(r'$4 \pi c$'), self.fancy(r'$4\pi c$'))
        self.assertEqual(self.fancy('$  4  \\pi  c  $'), self.fancy(r'$4\pi c$'))
        self.assertEqual(self.fancy(r'$2 x y$'), self.fancy(r'$2xy$'))
        self.assertEqual(self.fancy(r'$x+y$'), self.fancy(r'$x + y$'))

    # --- superscripts and subscripts ---

    def test_mathmodes_fancy_scripts_unicode(self):
        # where unicode has the superscript or subscript character, use it
        self.assertEqual(self.fancy(r'$x^2$'),
                         mvar('x') + u'\N{SUPERSCRIPT TWO}')
        self.assertEqual(self.fancy(r'$a_i$'),
                         mvar('a') + u'\N{LATIN SUBSCRIPT SMALL LETTER I}')
        self.assertEqual(self.fancy(r'$x_h$'),
                         mvar('x') + u'\N{LATIN SUBSCRIPT SMALL LETTER H}')

    def test_mathmodes_fancy_scripts_fallback_notation(self):
        # unicode has no superscript 'q', so we fall back on LaTeX's own
        # notation
        self.assertEqual(self.fancy(r'$x^q$'), mvar('x') + '^' + mvar('q'))

    def test_mathmodes_fancy_scripts_padding(self):
        # a script written with the '^' notation has no visible extent on the
        # right, so it is set apart from its neighbours -- and a space is
        # inserted in front of its base as well, retroactively
        self.assertEqual(self.fancy(r'$4\pi c x^q p$'),
                         '4' + u'\N{GREEK SMALL LETTER PI}' + mvar('c') + ' '
                         + mvar('x') + '^' + mvar('q') + ' ' + mvar('p'))
        # ... whereas a script written with the unicode characters shows where
        # it ends, and needs no padding at all
        self.assertEqual(self.fancy(r'$4\pi c x^2 p$'),
                         '4' + u'\N{GREEK SMALL LETTER PI}' + mvar('c')
                         + mvar('x') + u'\N{SUPERSCRIPT TWO}' + mvar('p'))

    def test_mathmodes_fancy_scripts_reordering(self):
        # 'x^a_b' is reordered into 'x_b^a', so that the subscript attaches to
        # the base first and the two scripts do not run together
        self.assertEqual(self.fancy(r'$x^a_b$'),
                         mvar('x') + '_' + mvar('b')
                         + u'\N{MODIFIER LETTER SMALL A}')

    def test_mathmodes_fancy_scripts_compact(self):
        # the spaces the joiner puts inside the argument of a script are taken
        # back out if that makes the unicode characters usable
        self.assertEqual(self.fancy(r'$\sum_{i=1}^n$'),
                         u'\N{N-ARY SUMMATION}'
                         + u'\N{LATIN SUBSCRIPT SMALL LETTER I}'
                         + u'\N{SUBSCRIPT EQUALS SIGN}'
                         + u'\N{SUBSCRIPT ONE}'
                         + u'\N{SUPERSCRIPT LATIN SMALL LETTER N}')
        self.assertEqual(self.fancy(r'$x^{a+b}$'),
                         mvar('x') + u'\N{MODIFIER LETTER SMALL A}'
                         + u'\N{SUPERSCRIPT PLUS SIGN}'
                         + u'\N{MODIFIER LETTER SMALL B}')
        self.assertEqual(self.fancy(r'$x^{abc}$'),
                         mvar('x') + u'\N{MODIFIER LETTER SMALL A}'
                         + u'\N{MODIFIER LETTER SMALL B}'
                         + u'\N{MODIFIER LETTER SMALL C}')

    def test_mathmodes_fancy_lazy_delimiters(self):
        # The four cases of the design, each pinned on its own rather than left
        # to the rule.  Delimiters go around a subscript only where a
        # separating space would still leave its extent unclear.
        #
        # nothing follows, so the subscript needs nothing:
        self.assertEqual(self.fancy(r'$x_{abc}$'),
                         mvar('x') + '_' + mvar('abc'))
        # something follows, but a space is enough to show where it ends:
        self.assertEqual(self.fancy(r'$x_{abc} p$'),
                         mvar('x') + '_' + mvar('abc') + ' ' + mvar('p'))
        # the relation already separates the two, so again nothing is needed:
        self.assertEqual(self.fancy(r'$x_{abc} = 1$'),
                         mvar('x') + '_' + mvar('abc') + ' = 1')
        # a second script attaches to the same base, and a space would not be
        # enough to tell 'x_(abc)^2' from 'x_(ab)(c^2)', so we do wrap:
        self.assertEqual(self.fancy(r'$x_{abc}^2$'),
                         mvar('x') + '_(' + mvar('abc') + ')'
                         + u'\N{SUPERSCRIPT TWO}')

    # --- text mode inside math mode ---

    def test_mathmodes_fancy_text_is_opaque(self):
        # the joiner never looks inside a text fragment
        self.assertEqual(self.fancy(r'$\text{a+b}$'), 'a+b')
        # a space that the fragment brings along is kept, and the joiner does
        # not add one of its own next to it
        self.assertEqual(self.fancy(r'$\text{if } x > 0$'),
                         'if ' + mvar('x') + ' > 0')
        self.assertEqual(self.fancy(r'$x \text{ if } y$'),
                         mvar('x') + ' if ' + mvar('y'))

    def test_mathmodes_fancy_nested_font_example(self):
        # '\text{}' restores the surrounding *text* font, which the excursion
        # into math mode never disturbed, so '[something]' comes back out
        # italic while the 'a' stays bold
        self.assertEqual(
            self.fancy(
                r'\textit{Italic text with math: $\mathbf{a+\text{[something]}}$}'
            ),
            mvar('Italic text with math: ')
            + math_alphabet('bold', 'a') + ' + [' + mvar('something') + ']'
        )

    # --- the font macro families ---

    def test_mathmodes_fancy_math_font_macros(self):
        self.assertEqual(self.fancy(r'$\mathrm{d}x$'), 'd' + mvar('x'))
        self.assertEqual(self.fancy(r'$\mathbf{x}$'), math_alphabet('bold', 'x'))
        self.assertEqual(self.fancy(r'$\mathit{x}$'), mvar('x'))
        self.assertEqual(self.fancy(r'$\mathsf{x}$'), math_alphabet('sans', 'x'))
        self.assertEqual(self.fancy(r'$\mathtt{x}$'),
                         math_alphabet('monospace', 'x'))
        self.assertEqual(self.fancy(r'$\mathbb{R}$'),
                         math_alphabet('doublestruck', 'R'))
        self.assertEqual(self.fancy(r'$\mathcal{B}$'),
                         math_alphabet('script', 'B'))
        self.assertEqual(self.fancy(r'$\mathscr{H}$'),
                         math_alphabet('script', 'H'))
        self.assertEqual(self.fancy(r'$\mathfrak{Z}$'),
                         math_alphabet('fraktur', 'Z'))
        # the style is pushed before the argument is rendered, so it really
        # reaches the individual letters
        self.assertEqual(self.fancy(r'$\mathbf{a+b}$'),
                         math_alphabet('bold', 'a') + ' + '
                         + math_alphabet('bold', 'b'))
        self.assertEqual(self.fancy(r'$\mathbf{a\mathrm{b}c}$'),
                         math_alphabet('bold', 'a') + 'b'
                         + math_alphabet('bold', 'c'))

    def test_mathmodes_fancy_text_font_macros(self):
        # in math mode each of these switches back to text mode, and all but
        # '\text' and '\mbox' also select a font style
        self.assertEqual(self.fancy(r'$\text{xy}$'), 'xy')
        self.assertEqual(self.fancy(r'$\mbox{xy}$'), 'xy')
        self.assertEqual(self.fancy(r'$\textrm{xy}$'), 'xy')
        self.assertEqual(self.fancy(r'$\textup{xy}$'), 'xy')
        self.assertEqual(self.fancy(r'$\textmd{xy}$'), 'xy')
        self.assertEqual(self.fancy(r'$\textbf{xy}$'), math_alphabet('bold', 'xy'))
        self.assertEqual(self.fancy(r'$\textit{xy}$'), mvar('xy'))
        self.assertEqual(self.fancy(r'$\textsl{xy}$'), mvar('xy'))
        self.assertEqual(self.fancy(r'$\textsf{xy}$'), math_alphabet('sans', 'xy'))
        self.assertEqual(self.fancy(r'$\texttt{xy}$'),
                         math_alphabet('monospace', 'xy'))
        # ... and they work in ordinary text as well
        self.assertEqual(self.fancy(r'A\text{xy}B'), 'AxyB')
        self.assertEqual(self.fancy(r'A\mbox{xy}B'), 'AxyB')
        self.assertEqual(self.fancy(r'A\textrm{xy}B'), 'AxyB')
        self.assertEqual(self.fancy(r'A\textup{xy}B'), 'AxyB')
        self.assertEqual(self.fancy(r'A\textmd{xy}B'), 'AxyB')
        self.assertEqual(self.fancy(r'A\textbf{xy}B'),
                         'A' + math_alphabet('bold', 'xy') + 'B')
        self.assertEqual(self.fancy(r'A\textit{xy}B'), 'A' + mvar('xy') + 'B')
        self.assertEqual(self.fancy(r'A\textsl{xy}B'), 'A' + mvar('xy') + 'B')
        self.assertEqual(self.fancy(r'A\textsf{xy}B'),
                         'A' + math_alphabet('sans', 'xy') + 'B')
        self.assertEqual(self.fancy(r'A\texttt{xy}B'),
                         'A' + math_alphabet('monospace', 'xy') + 'B')

    def test_mathmodes_fancy_emph_toggles(self):
        # '\emph' toggles italics on and off, and composes with an outer bold
        # or sans-serif
        self.assertEqual(self.fancy(r'\emph{xy}'), mvar('xy'))
        self.assertEqual(self.fancy(r'\emph{\emph{xy}}'), 'xy')
        self.assertEqual(self.fancy(r'\textit{a\emph{b}c}'),
                         mvar('a') + 'b' + mvar('c'))
        self.assertEqual(self.fancy(r'\textbf{a\emph{b}c}'),
                         math_alphabet('bold', 'a')
                         + math_alphabet('bold-italic', 'b')
                         + math_alphabet('bold', 'c'))
        self.assertEqual(self.fancy(r'\textbf{a\emph{\emph{b}}c}'),
                         math_alphabet('bold', 'abc'))
        # '\textmd{}' selects the plain font, and so undoes the bold
        self.assertEqual(self.fancy(r'\textbf{a\textmd{b}c}'),
                         math_alphabet('bold', 'a') + 'b'
                         + math_alphabet('bold', 'c'))
        self.assertEqual(self.fancy(r'\textsf{a\emph{b}c}'),
                         math_alphabet('sans', 'a')
                         + math_alphabet('sans-italic', 'b')
                         + math_alphabet('sans', 'c'))

    # --- named operators ---

    def test_mathmodes_fancy_operator_names(self):
        # a named operator is set apart from its neighbours, and hugs a
        # delimiter that follows it
        self.assertEqual(self.fancy(r'$\det(A) \neq 0$'),
                         'det(' + mvar('A') + ') '
                         + u'\N{NOT EQUAL TO}' + ' 0')
        self.assertEqual(self.fancy(r'$2\gcd(a,b)$'),
                         '2 gcd(' + mvar('a') + ', ' + mvar('b') + ')')
        self.assertEqual(self.fancy(r'$\lg n + \coth x$'),
                         'lg ' + mvar('n') + ' + coth ' + mvar('x'))

    def test_mathmodes_fancy_limit_operators(self):
        # amsmath's limit operators.  The '\var...' ones are the same operators
        # typeset with a bar or an arrow instead of the words, which plain text
        # cannot show, so each renders as the operator it stands for.
        self.assertEqual(self.fancy(r'$\injlim_i A_i$'),
                         'inj lim' + u'\N{LATIN SUBSCRIPT SMALL LETTER I}'
                         + ' ' + mvar('A') + u'\N{LATIN SUBSCRIPT SMALL LETTER I}')
        self.assertEqual(self.fancy(r'$\projlim A$'), 'proj lim ' + mvar('A'))
        self.assertEqual(self.fancy(r'$\varlimsup_n x_n$'),
                         self.fancy(r'$\limsup_n x_n$'))
        self.assertEqual(self.fancy(r'$\varliminf_n x_n$'),
                         self.fancy(r'$\liminf_n x_n$'))
        self.assertEqual(self.fancy(r'$\varinjlim A$'), self.fancy(r'$\injlim A$'))
        self.assertEqual(self.fancy(r'$\varprojlim A$'), self.fancy(r'$\projlim A$'))

    def test_mathmodes_fancy_operatorname(self):
        # '\operatorname{}' names an operator that has no macro of its own; its
        # argument is typeset upright, the way '\mathrm{}' is, and the result
        # behaves exactly like one of the named operators above
        self.assertEqual(self.fancy(r'$\operatorname{tr}(A)$'),
                         'tr(' + mvar('A') + ')')
        self.assertEqual(self.fancy(r'$2\operatorname{tr}A$'),
                         '2 tr ' + mvar('A'))
        # the star of '\operatorname*{}' only says where the limits of the
        # operator are placed, which plain text cannot show anyway
        self.assertEqual(self.fancy(r'$\operatorname*{argmax}_x f(x)$'),
                         'argmax' + u'\N{LATIN SUBSCRIPT SMALL LETTER X}'
                         + ' ' + mvar('f') + '(' + mvar('x') + ')')

    def test_mathmodes_fancy_modulo(self):
        # '\bmod' is a binary operator, so it takes a space on each side even
        # where the source has none
        self.assertEqual(self.fancy(r'$x\bmod y$'),
                         mvar('x') + ' mod ' + mvar('y'))
        # '\pmod{}' and '\mod{}' follow the expression they qualify
        self.assertEqual(self.fancy(r'$a \equiv b \pmod{n}$'),
                         mvar('a') + u' \N{IDENTICAL TO} ' + mvar('b')
                         + ' (mod ' + mvar('n') + ')')
        self.assertEqual(self.fancy(r'$a \equiv b \mod{n}$'),
                         mvar('a') + u' \N{IDENTICAL TO} ' + mvar('b')
                         + ' mod ' + mvar('n'))

    # --- large objects ---

    def test_mathmodes_fancy_matrix(self):
        self.assertEqual(
            self.fancy(r'$A = \begin{pmatrix}1&2\\3&4\end{pmatrix}$'),
            mvar('A') + ' = [ 1 2; 3 4 ]'
        )
        # a matrix carries its own delimiters, so it hugs its neighbours
        self.assertEqual(self.fancy(r'$x\begin{pmatrix}1&2\end{pmatrix}y$'),
                         mvar('x') + '[ 1 2 ]' + mvar('y'))
        self.assertEqual(self.fancy(r'$\sin\begin{pmatrix}1&2\end{pmatrix}$'),
                         'sin[ 1 2 ]')
        self.assertEqual(self.fancy(r'$2\begin{pmatrix}1&2\end{pmatrix}^{qr}$'),
                         '2[ 1 2 ]^' + mvar('qr'))

    # --- the math_fontstyle= option ---

    def test_mathmodes_fancy_math_fontstyle_none(self):
        # the unicode math alphanumeric characters live in a high unicode plane
        # that many terminal fonts do not cover; math_fontstyle=None leaves the
        # letters upright and in plain ASCII
        self.assertEqual(self.fancy(r'$2 x y$', math_fontstyle=None), '2xy')
        self.assertEqual(self.fancy(r'$2 \sin x$', math_fontstyle=None),
                         '2 sin x')
        self.assertEqual(self.fancy(r'$x + y$', math_fontstyle=None), 'x + y')
        # for comparison, the same with the default italics
        self.assertEqual(self.fancy(r'$2 x y$'), '2' + mvar('xy'))
        self.assertEqual(self.fancy(r'$2 \sin x$'), '2 sin ' + mvar('x'))
        # `None` only sets the style the letters start out in, so the math font
        # macros still install one of their own
        self.assertEqual(self.fancy(r'$x + \mathbf{a}$', math_fontstyle=None),
                         'x + ' + math_alphabet('bold', 'a'))

    def test_mathmodes_fancy_text_fontstyle(self):
        # the style that ordinary text starts out in; the default is `None`,
        # i.e. upright
        self.assertEqual(self.fancy(r'plain'), 'plain')
        self.assertEqual(self.fancy(r'plain', text_fontstyle='sans'),
                         math_alphabet('sans', 'plain'))
        # as for math, `None` only sets what the text starts out in, and the
        # text font macros still install a style of their own
        self.assertEqual(self.fancy(r'a\textbf{b}', text_fontstyle=None),
                         'a' + math_alphabet('bold', 'b'))
        # '\emph{}' composes with the style in force, so it italicizes the
        # sans-serif alphabet rather than the serif one
        self.assertEqual(self.fancy(r'\emph{e}', text_fontstyle='sans'),
                         math_alphabet('sans-italic', 'e'))

    def test_mathmodes_fancy_fontstyle_off(self):
        # `False` is the stronger value: no unicode alphabet is used in that
        # mode at all, and the font style macros leave the letters alone
        self.assertEqual(self.fancy(r'\textbf{b} \emph{e} \textsf{s}',
                                    text_fontstyle=False),
                         'b e s')
        self.assertEqual(self.fancy(r'$x + \mathbf{a}$', math_fontstyle=False),
                         'x + a')
        # the two together are what gives plain ASCII output throughout
        self.assertEqual(self.fancy(r'\textbf{bold} $x + \mathbf{a} + \sin y$',
                                    text_fontstyle=False, math_fontstyle=False),
                         'bold x + a + sin y')
        # a `False` survives nesting, since no macro replaces it
        self.assertEqual(self.fancy(r'\textbf{a \emph{b} \textsf{c}}',
                                    text_fontstyle=False),
                         'a b c')
        # each mode is switched off on its own
        self.assertEqual(self.fancy(r'\textbf{b} $x$', text_fontstyle=False),
                         'b ' + mvar('x'))
        self.assertEqual(self.fancy(r'\textbf{b} $x$', math_fontstyle=False),
                         math_alphabet('bold', 'b') + ' x')

    # --- display math ---

    def test_mathmodes_fancy_display_math(self):
        self.assertEqual(self.fancy(r'\[ x = \frac{a+b}{c} \]'),
                         '\n    ' + mvar('x') + ' = (' + mvar('a') + ' + '
                         + mvar('b') + ')/' + mvar('c') + '\n')
        self.assertEqual(self.fancy(r'$$ E = mc^2 $$'),
                         '\n    ' + mvar('E') + ' = ' + mvar('mc')
                         + u'\N{SUPERSCRIPT TWO}' + '\n')
        self.assertEqual(
            self.fancy(r'\begin{equation} a^2 + b^2 = c^2 \end{equation}'),
            '\n    ' + mvar('a') + u'\N{SUPERSCRIPT TWO}' + ' + ' + mvar('b')
            + u'\N{SUPERSCRIPT TWO}' + ' = ' + mvar('c')
            + u'\N{SUPERSCRIPT TWO}' + '\n'
        )
        self.assertEqual(self.fancy(r'Before \[ x = 1 \] after.'),
                         'Before \n    ' + mvar('x') + ' = 1\n after.')

    # --- accents; these used to raise an AttributeError ---

    def test_mathmodes_fancy_accents(self):
        # make_accented_char() and friends render a node list and then treat
        # the result as a string, which in this math mode is a math piece and
        # not a string; a regression test for the str() coercions that fixed it
        self.assertEqual(self.fancy(r'$\vec{x}$'),
                         mvar('x') + u'\N{COMBINING RIGHT ARROW ABOVE}')
        self.assertEqual(self.fancy(r'$\hat a$'),
                         mvar('a') + u'\N{COMBINING CIRCUMFLEX ACCENT}')
        self.assertEqual(self.fancy(r'$\vec{x} \cdot \hat{y} = 1$'),
                         mvar('x') + u'\N{COMBINING RIGHT ARROW ABOVE}'
                         + u' \N{MIDDLE DOT} '
                         + mvar('y') + u'\N{COMBINING CIRCUMFLEX ACCENT}'
                         + ' = 1')
        self.assertEqual(self.fancy(r'$1 \not= 2$'),
                         u'1 \N{NOT EQUAL TO} 2')

    #
    # The four math modes that existed before the fancy text engine was added
    # must be unaffected by it.  The table below was produced by rendering each
    # snippet with each mode, and checked against a checkout of the revision
    # that preceded the work.  A snippet is included for each part of the
    # conversion machinery that the new engine touched.
    #
    # The macros that had no text specification at all before this work are the
    # one deliberate exception: the specifications they were given fix a real
    # loss of content in these modes as well, so the entries for '\mbox' and
    # friends, for the named operators and for the modulo constructs pin the
    # fixed rendering and not the historical one.
    #

    def test_mathmodes_old_modes_unaffected(self):

        old_math_modes_corpus = [
            (
                '$\\alpha=1$',
                {
                    'text': 'α=1',
                    'with-delimiters': '$α=1$',
                    'verbatim': '$\\alpha=1$',
                    'remove': '',
                },
            ),
            (
                '$4 \\pi c$',
                {
                    'text': '4 π c',
                    'with-delimiters': '$4 π c$',
                    'verbatim': '$4 \\pi c$',
                    'remove': '',
                },
            ),
            (
                '$x^2 + y_i$',
                {
                    'text': 'x² + yᵢ',
                    'with-delimiters': '$x² + yᵢ$',
                    'verbatim': '$x^2 + y_i$',
                    'remove': '',
                },
            ),
            (
                '$x^{\\mathbf{a}}$',
                {
                    'text': 'x^𝐚',
                    'with-delimiters': '$x^𝐚$',
                    'verbatim': '$x^{\\mathbf{a}}$',
                    'remove': '',
                },
            ),
            (
                '$x_{abc}$',
                {
                    'text': 'x_(abc)',
                    'with-delimiters': '$x_(abc)$',
                    'verbatim': '$x_{abc}$',
                    'remove': '',
                },
            ),
            (
                '$\\frac{a+b}{c}$',
                {
                    'text': '(a+b)/c',
                    'with-delimiters': '$(a+b)/c$',
                    'verbatim': '$\\frac{a+b}{c}$',
                    'remove': '',
                },
            ),
            (
                '$\\sqrt{x} + \\sqrt{a+b}$',
                {
                    'text': '√(x) + √(a+b)',
                    'with-delimiters': '$√(x) + √(a+b)$',
                    'verbatim': '$\\sqrt{x} + \\sqrt{a+b}$',
                    'remove': '',
                },
            ),
            (
                '$\\sin x + \\cos y$',
                {
                    'text': 'sin x + cos y',
                    'with-delimiters': '$sin x + cos y$',
                    'verbatim': '$\\sin x + \\cos y$',
                    'remove': '',
                },
            ),
            (
                '$\\lim_{n} a_n$',
                {
                    'text': 'limₙ aₙ',
                    'with-delimiters': '$limₙ aₙ$',
                    'verbatim': '$\\lim_{n} a_n$',
                    'remove': '',
                },
            ),
            (
                '$\\vec{x} \\cdot \\hat{y}$',
                {
                    'text': 'x⃗·ŷ',
                    'with-delimiters': '$x⃗·ŷ$',
                    'verbatim': '$\\vec{x} \\cdot \\hat{y}$',
                    'remove': '',
                },
            ),
            (
                '$\\text{if } x > 0$',
                {
                    'text': 'if  x > 0',
                    'with-delimiters': '$if  x > 0$',
                    'verbatim': '$\\text{if } x > 0$',
                    'remove': '',
                },
            ),
            (
                '\\textbf{bold} \\emph{emph} \\textit{it}',
                {
                    'text': 'bold emph it',
                    'with-delimiters': 'bold emph it',
                    'verbatim': 'bold emph it',
                    'remove': 'bold emph it',
                },
            ),
            (
                # these five select a font that plain text cannot render, so
                # outside of the fancy engine they simply render their argument
                'A\\mbox{m}\\textsf{s}\\texttt{t}\\textup{u}\\textmd{d}B',
                {
                    'text': 'AmstudB',
                    'with-delimiters': 'AmstudB',
                    'verbatim': 'AmstudB',
                    'remove': 'AmstudB',
                },
            ),
            (
                # the named operators render as their own name, here and in
                # every other math mode
                '$\\det(A) \\neq 0$',
                {
                    'text': 'det(A) ≠ 0',
                    'with-delimiters': '$det(A) ≠ 0$',
                    'verbatim': '$\\det(A) \\neq 0$',
                    'remove': '',
                },
            ),
            (
                '$a \\bmod n$',
                {
                    'text': 'a mod n',
                    'with-delimiters': '$a mod n$',
                    'verbatim': '$a \\bmod n$',
                    'remove': '',
                },
            ),
            (
                '$a \\equiv b \\pmod{n}$',
                {
                    'text': 'a ≡ b (mod n)',
                    'with-delimiters': '$a ≡ b (mod n)$',
                    'verbatim': '$a \\equiv b \\pmod{n}$',
                    'remove': '',
                },
            ),
            (
                '$\\operatorname{tr}(A)$',
                {
                    'text': 'tr(A)',
                    'with-delimiters': '$tr(A)$',
                    'verbatim': '$\\operatorname{tr}(A)$',
                    'remove': '',
                },
            ),
            (
                '$\\mathbf{a} \\mathrm{b} \\mathcal{C}$',
                {
                    'text': '𝐚b𝒞',
                    'with-delimiters': '$𝐚b𝒞$',
                    'verbatim': '$\\mathbf{a} \\mathrm{b} \\mathcal{C}$',
                    'remove': '',
                },
            ),
            (
                '$A = \\begin{pmatrix}1&2\\\\3&4\\end{pmatrix}$',
                {
                    'text': 'A = [ 1 2; 3 4 ]',
                    'with-delimiters': '$A = [ 1 2; 3 4 ]$',
                    'verbatim': '$A = \\begin{pmatrix}1&2\\\\3&4\\end{pmatrix}$',
                    'remove': '',
                },
            ),
            (
                '\\[ \\beta = 2\\alpha \\]',
                {
                    'text': '\n    β = 2α\n',
                    'with-delimiters': '\\[\nβ = 2α\n\\]',
                    'verbatim': '\n\\[ \\beta = 2\\alpha \\]\n',
                    'remove': '',
                },
            ),
            (
                '\\begin{equation} a^2+b^2=c^2 \\end{equation}',
                {
                    'text': '\n    a²+b²=c²\n',
                    'with-delimiters': '\\begin{equation}\na²+b²=c²\n\\end{equation}',
                    'verbatim': '\n\\begin{equation} a^2+b^2=c^2 \\end{equation}\n',
                    'remove': '',
                },
            ),
            (
                'Hello $x+y$ and \\(a \\le b\\).',
                {
                    'text': 'Hello x+y and a ≤ b.',
                    'with-delimiters': 'Hello $x+y$ and \\(a ≤ b\\).',
                    'verbatim': 'Hello $x+y$ and \\(a \\le b\\).',
                    'remove': 'Hello  and .',
                },
            ),
        ]

        for latex, expected_per_mode in old_math_modes_corpus:
            for math_mode, expected in expected_per_mode.items():
                self.assertEqual(
                    LatexNodes2Text(math_mode=math_mode).latex_to_text(latex),
                    expected,
                    msg="math_mode={!r}, latex={!r}".format(math_mode, latex)
                )


    #
    # test text filling etc.
    #

    def test_text_filling(self):

        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            fill_text=20, strict_latex_spaces=True).latex_to_text(
                r"""
Hello world.  This   is
some weirdly formatted \textbf{text} which
will appear much    better after running latex2text."""
            ),
r"""Hello world.  This
is some weirdly
formatted text which
will appear much
better after running
latex2text."""
        )

    def test_text_filling_InitEndPar(self):

        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            fill_text=True, strict_latex_spaces=True).latex_to_text(
                r"""

  Hello \emph{world}.  % comment
more text.

"""
            ),
            "\n\nHello world. more text.\n\n"
        )


        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            fill_text=True, strict_latex_spaces=True).latex_to_text(
                r"""
  Hello \emph{world}.  % comment
more text.

"""
            ),
            "Hello world. more text.\n\n"
        )


    def test_empty_pars(self):

        self.assertEqual(
            LatexNodes2Text(fill_text=10, strict_latex_spaces=True).latex_to_text(
                r"""
A car once was very fast.

Another car came by.  And then some space:



Note the few space tokens in the otherwise empty line above.
"""
            ),
r"""A car once
was very
fast.

Another
car came
by.  And
then some
space:

Note the
few space
tokens in
the
otherwise
empty line
above. """
        )




    #
    # test replacement strings
    #


    def test_repl_item(self):

        # exact replacement text may change in the future

        self.assertEqual(
            LatexNodes2Text().latex_to_text(
                r"""
\begin{itemize}
\item First item
\item[b] The item ``B''
\item Last item
\end{itemize}
""".strip()
            ),
            u"""
  \N{BULLET} First item
  b The item “B”
  \N{BULLET} Last item
"""
        )

    def test_repl_item_enumerate(self):

        self.assertEqual(
            LatexNodes2Text().latex_to_text(
                r"""
\begin{enumerate}
\item First item
\item Second item
\item[(*)] Item with an explicit label
\item Last item
\end{enumerate}
""".strip()
            ),
            u"""
  1. First item
  2. Second item
  (*) Item with an explicit label
  3. Last item
"""
        )

    def test_repl_item_nested(self):

        # nested lists get their own item counters and marker styles, and are
        # indented according to the item they appear in.  As in LaTeX, the
        # marker style follows the nesting depth among lists of the same kind,
        # so the {itemize} here is still a first-level itemize.

        self.assertEqual(
            LatexNodes2Text().latex_to_text(
                r"""
\begin{enumerate}
\item one \begin{enumerate}\item inner a \item inner b \begin{itemize}\item deep\end{itemize}\end{enumerate}
\item two
\end{enumerate}
""".strip()
            ),
            u"""
  1. one
     (a) inner a
     (b) inner b
         \N{BULLET} deep
  2. two
"""
        )

    def test_repl_item_multiline(self):

        # continuation lines of an item are aligned with the item text

        self.assertEqual(
            LatexNodes2Text().latex_to_text(
                r"""
\begin{enumerate}
\item first line
second line
\item another item
\end{enumerate}
""".strip()
            ),
            u"""
  1. first line
     second line
  2. another item
"""
        )

    def test_repl_item_description(self):

        self.assertEqual(
            LatexNodes2Text().latex_to_text(
                r"""
\begin{description}
\item[Foo] a thing
\item[Bar] another thing
\end{description}
""".strip()
            ),
            u"""
  Foo a thing
  Bar another thing
"""
        )

    def test_repl_item_stray(self):

        # an \item outside of any known list environment still produces a
        # bullet, as it did in earlier versions of pylatexenc

        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"Stray \item here."),
            u"Stray \n  \N{BULLET} here."
        )

    def test_repl_item_empty_list(self):

        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"\begin{itemize}\end{itemize}"),
            u"\n"
        )

    def test_repl_placeholders(self):

        # environments that are currently replaced by a dummy placeholder

        # --- these environments are now approximated as of pylatexenc 2.8 ---
        #for env in ('array', 'pmatrix', 'bmatrix', 'smallmatrix'):
        #    self.assertEqualUpToWhitespace(
        #        LatexNodes2Text().latex_to_text(
        #            r"\begin{%(env)s}stuff stuff\end{%(env)s}"%{'env':env}
        #        ),
        #        "< " + " ".join(env) + " >" # substituted by placeholder (for now)
        #    )

        self.assertEqualUpToWhitespace(
            LatexNodes2Text().latex_to_text(
                r"\includegraphics[width=3in]{fig/some_graphics.png}"
            ),
            "< g r a p h i c s >"
        )

    def test_repl_eqn(self):

        for env in ('equation', #'equation*', 'eqnarray', 'eqnarray*',
                    #'align', 'align*', 'multline', 'multline*',
                    #'gather', 'gather*',
 'dmath', 'dmath*'):

            self.assertEqualUpToWhitespace(
                LatexNodes2Text(math_mode='text',
                                strict_latex_spaces='except-in-equations').latex_to_text(
                    r"\begin{%(env)s} e \approx 2.718 \end{%(env)s}"%{'env':env}
                ),
                u"e ≈ 2.718"
            )

    def test_repl_matrix_environment(self):

        for env, arg in (('array', '{lll}'), ('pmatrix', ''), ('bmatrix', ''),
                          ('smallmatrix', '')):
            self.assertEqualUpToWhitespace(
                LatexNodes2Text().latex_to_text(
                    r"\begin{%(env)s}%(arg)s1 &   2 & abcdef\\ 3 & 4\end{%(env)s}"
                    %{'env':env,'arg':arg}
                ),
                "[      1      2 abcdef;      3      4 ]"
            )

    def test_repl_matrix_environment_empty(self):

        # an empty matrix or array is valid LaTeX; make sure it doesn't raise
        for env, arg in (('array', '{lll}'), ('pmatrix', ''), ('bmatrix', ''),
                          ('smallmatrix', '')):
            self.assertEqualUpToWhitespace(
                LatexNodes2Text().latex_to_text(
                    r"\begin{%(env)s}%(arg)s\end{%(env)s}"
                    %{'env':env,'arg':arg}
                ),
                "[ ]"
            )

    def test_repl_sqrt(self):

        # the root degree must not be silently dropped; unicode has dedicated
        # signs for the cube and the fourth root
        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"\sqrt{x}"),
            u"\N{SQUARE ROOT}(x)"
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"\sqrt[3]{x}"),
            u"\N{CUBE ROOT}(x)"
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"\sqrt[4]{x}"),
            u"\N{FOURTH ROOT}(x)"
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"\sqrt[n]{x+y}"),
            u"n\N{SQUARE ROOT}(x+y)"
        )

    def test_repl_subsuperscript(self):

        # in math mode, '^' and '_' pick up an argument which we render with
        # unicode superscript/subscript characters whenever we can
        for latex, text in (
                (r"$x^2$", u"x\N{SUPERSCRIPT TWO}"),
                (r"$x^{10}$", u"x\N{SUPERSCRIPT ONE}\N{SUPERSCRIPT ZERO}"),
                (r"$x^{-1}$", u"x\N{SUPERSCRIPT MINUS}\N{SUPERSCRIPT ONE}"),
                (r"$H_2O$", u"H\N{SUBSCRIPT TWO}O"),
                (r"$a_{n+1}$", u"a\N{LATIN SUBSCRIPT SMALL LETTER N}"
                 u"\N{SUBSCRIPT PLUS SIGN}\N{SUBSCRIPT ONE}"),
                # the argument can be a macro along with its own arguments
                (r"$x_\mathrm{max}$", u"x\N{LATIN SUBSCRIPT SMALL LETTER M}"
                 u"\N{LATIN SUBSCRIPT SMALL LETTER A}\N{LATIN SUBSCRIPT SMALL LETTER X}"),
                (r"$x_\beta$", u"x\N{GREEK SUBSCRIPT SMALL LETTER BETA}"),
                # capital letters have superscript versions, but no subscript ones
                (r"$X^{AB}$", u"X\N{MODIFIER LETTER CAPITAL A}\N{MODIFIER LETTER CAPITAL B}"),
        ):
            self.assertEqual(LatexNodes2Text(math_mode='text').latex_to_text(latex), text)

    def test_repl_subsuperscript_no_unicode_version(self):

        # if the argument cannot be fully typeset with unicode
        # superscript/subscript characters, we keep latex's own notation, and
        # we delimit the argument with the `math_expression_in=` delimiters if
        # it is longer than a single character.  The default delimiters are
        # parentheses, see `default_math_expression_in`.
        for latex, text in (
                # there is no unicode superscript alpha
                (r"$x^\alpha$", u"x^\N{GREEK SMALL LETTER ALPHA}"),
                (r"$A^\dagger$", u"A^\N{DAGGER}"),
                # 'C' has no superscript version, so the whole argument falls back
                (r"$X^{ABC}$", u"X^(ABC)"),
                (r"$e^{i\pi}$", u"e^(i\N{GREEK SMALL LETTER PI})"),
                # capital letters have no subscript version at all
                (r"$x_N$", u"x_N"),
                # a superscript within a superscript can't be typeset in unicode
                (r"$x^{a^b}$", u"x^(a\N{MODIFIER LETTER SMALL B})"),
        ):
            self.assertEqual(LatexNodes2Text(math_mode='text').latex_to_text(latex), text)

    def test_repl_subsuperscript_text_mode(self):

        # outside of math mode, '^' and '_' don't pick up any argument (they
        # are in fact errors in LaTeX there); they're rendered as themselves so
        # that e.g. file names in \input{...} stay in one piece
        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"a_b and a^b"),
            "a_b and a^b"
        )

    def test_repl_subsuperscript_empty_argument(self):

        # an empty superscript or subscript renders as nothing at all
        self.assertEqual(
            LatexNodes2Text(math_mode='text').latex_to_text(r"$x^{}$"),
            "x"
        )

    def test_math_expression_in_subsuperscript(self):

        # the `math_expression_in=` option picks the delimiters that show where
        # a superscript or a subscript that we could not render with unicode
        # super/subscript characters begins and ends
        for math_expression_in, text in (
                ('braces', u"x_{abc}"),
                ('parens', u"x_(abc)"),
                (('[', ']',), u"x_[abc]"),
                (None, u"x_abc"),
        ):
            self.assertEqual(
                LatexNodes2Text(math_mode='text', math_expression_in=math_expression_in)
                .latex_to_text(r"$x_{abc}$"),
                text
            )

        # the delimiters are what makes these two distinguishable
        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            math_expression_in='parens').latex_to_text(r"$x_{ab}c$"),
            u"x_(ab)c"
        )
        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            math_expression_in='parens').latex_to_text(r"$x_{abc}$"),
            u"x_(abc)"
        )

    def test_math_expression_in_not_needed(self):

        # no delimiters are added when the superscript or subscript can be
        # rendered with unicode characters ...
        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            math_expression_in='parens').latex_to_text(r"$x^2$"),
            u"x\N{SUPERSCRIPT TWO}"
        )
        # ... nor around a sub-expression of a single character, where they
        # wouldn't carry any information
        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            math_expression_in='parens').latex_to_text(r"$x^\Gamma$"),
            u"x^\N{GREEK CAPITAL LETTER GAMMA}"
        )

    def test_math_expression_in_frac(self):

        # the numerator and the denominator of a fraction are also
        # sub-expressions that would be ambiguous without delimiters
        for math_expression_in, text in (
                ('braces', u"{a+b}/c"),
                ('parens', u"(a+b)/c"),
                (None, u"a+b/c"),
        ):
            self.assertEqual(
                LatexNodes2Text(math_mode='text', math_expression_in=math_expression_in)
                .latex_to_text(r"$\frac{a+b}{c}$"),
                text
            )
        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            math_expression_in='parens').latex_to_text(r"$\frac{a}{b+c}$"),
            u"a/(b+c)"
        )
        # single-character numerators and denominators need no delimiters
        self.assertEqual(
            LatexNodes2Text(math_mode='text',
                            math_expression_in='parens').latex_to_text(r"$\frac12$"),
            u"1/2"
        )

    def test_math_expression_in_invalid_value(self):

        self.assertRaises(
            ValueError,
            lambda: LatexNodes2Text(math_expression_in='not-a-preset-name')
        )
        self.assertRaises(
            ValueError,
            lambda: LatexNodes2Text(math_expression_in=('<', '|', '>',))
        )

    def test_math_expression_in_default(self):

        # the default is given by a single module-level constant, so that it
        # can be changed in one place
        for latex in (r"$x_{abc}$", r"$\frac{a+b}{c}$",):
            self.assertEqual(
                LatexNodes2Text().latex_to_text(latex),
                LatexNodes2Text(
                    math_expression_in=latex2text.default_math_expression_in
                ).latex_to_text(latex)
            )

    def test_math_expression_in_state(self):

        # the option lives on the conversion state, so it can be changed for
        # part of the document only
        l2t = LatexNodes2Text(math_mode='text', math_expression_in='braces')
        with l2t.push_state(math_expression_in='parens'):
            self.assertEqual(l2t.latex_to_text(r"$x_{abc}$"), u"x_(abc)")
        self.assertEqual(l2t.latex_to_text(r"$x_{abc}$"), u"x_{abc}")

    def test_deprecated_latex2text_warns_only_about_the_callers_line(self):

        # the module-level latex2text() function is deprecated, but the
        # deprecation warning must point at the code that called it and it must
        # not be accompanied by warnings about pylatexenc's own internals
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter("always")
            text = latex2text.latex2text(r"\textbf{Hello}")

        self.assertEqual(text, "Hello")
        self.assertEqual(len(wlist), 1)
        self.assertEqual(os.path.basename(wlist[0].filename), os.path.basename(__file__))

    def test_repl_escape_char_at_end_of_line(self):

        # an escape character immediately followed by the end of a line is the
        # control space, so it stands for a space
        self.assertEqual(
            LatexNodes2Text().latex_to_text("chair\\\ntable"),
            "chair table"
        )
        # a double escape character is still a line break
        self.assertEqual(
            LatexNodes2Text().latex_to_text("chair\\\\table"),
            "chair\ntable"
        )

    def test_repl_part(self):

        # \part is rendered like \chapter and friends; check that its argument
        # is actually picked up and not left in the text
        self.assertEqualUpToWhitespace(
            LatexNodes2Text().latex_to_text(r"\part{The Part}" + "\nSome text."),
            "PART: THE PART Some text."
        )

    def test_repl_href(self):

        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"\href{https://example.com/}{the link}"),
            "the link <https://example.com/>"
        )

    def test_repl_url(self):

        self.assertEqual(
            LatexNodes2Text().latex_to_text(r"\url{https://example.com/}"),
            "<https://example.com/>"
        )

    def test_repl_href_url_special_chars(self):

        # the target of \href and \url is read verbatim, so characters that are
        # special to LaTeX survive.  Without that, a percent sign starts a
        # comment and swallows the rest of the line, and a tilde turns into a
        # non-breaking space.
        for latex, text in (
                (r"\url{http://x.org/a%20b}", "<http://x.org/a%20b>"),
                (r"\url{http://x.org/~user}", "<http://x.org/~user>"),
                (r"\url{http://x.org/page#frag}", "<http://x.org/page#frag>"),
                (r"\url{http://x.org/a_b}", "<http://x.org/a_b>"),
                (r"\url{http://x.org/a&b=c}", "<http://x.org/a&b=c>"),
                (r"\href{http://x.org/a%20b}{link}", "link <http://x.org/a%20b>"),
                (r"\href{http://x.org/q?a=1&b=2#f}{link}",
                 "link <http://x.org/q?a=1&b=2#f>"),
        ):
            self.assertEqual(LatexNodes2Text().latex_to_text(latex), text)

    def test_repl_href_url_repeated_with_braces(self):

        # the verbatim parser reading the target lives in the macro's
        # specification and is reused for every occurrence, so its nesting
        # depth bookkeeping must not leak from one target to the next
        self.assertEqual(
            LatexNodes2Text().latex_to_text(
                r"\url{http://a.org/x{y}} and \url{http://b.org/p{q}}"
            ),
            "<http://a.org/x{y}> and <http://b.org/p{q}>"
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text(
                r"\href{http://a.org/{x}}{A} and \href{http://b.org/{y}}{B}"
            ),
            "A <http://a.org/{x}> and B <http://b.org/{y}>"
        )

    def test_repl_href_text_is_still_latex(self):

        # only the target is verbatim; the link text is ordinary LaTeX
        self.assertEqual(
            LatexNodes2Text(math_mode='text').latex_to_text(
                r"\href{http://x.org/a%20b}{\textbf{bold} link}"
            ),
            "bold link <http://x.org/a%20b>"
        )

    def test_repl_doc_title(self):

        # test that \title/\author/\date work and produce something reasonable
        # (exact output might change in the future)

        self.assertEqualUpToWhitespace(
                LatexNodes2Text().latex_to_text(
                    r"""
\title{The Title}
\author{The Author(s)}
\date{July 4, 2020}
\maketitle
"""
                ),
            r"""
The Title
    The Author(s)
    July 4, 2020
=================
"""
        )
        # missing all \title, \author, \date
        today = '{dt:%B} {dt.day}, {dt.year}'.format(dt=datetime.datetime.now())
        eqhrule = '=' * max(4+len(r'[NO \author GIVEN]'), 4+len(today))
        self.assertEqualUpToWhitespace(
                LatexNodes2Text().latex_to_text(
                    r"""
\maketitle
"""
                ),
            r"""
[NO \title GIVEN]
    [NO \author GIVEN]
    %(today)s
%(eqhrule)s
""" % { 'today': today, 'eqhrule': eqhrule }
        )


    def test_math_alphabets(self):

        def gen_latex(macroname):
            return r"""
%s{-ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz-}
""".strip() % ('\\'+macroname)

        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathbf') ),
            '-𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙 𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳-'
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathit') ),
            '-𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍 𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧-'
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathsf') ),
            '-𝖠𝖡𝖢𝖣𝖤𝖥𝖦𝖧𝖨𝖩𝖪𝖫𝖬𝖭𝖮𝖯𝖰𝖱𝖲𝖳𝖴𝖵𝖶𝖷𝖸𝖹 𝖺𝖻𝖼𝖽𝖾𝖿𝗀𝗁𝗂𝗃𝗄𝗅𝗆𝗇𝗈𝗉𝗊𝗋𝗌𝗍𝗎𝗏𝗐𝗑𝗒𝗓-'
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathbb') ),
            '-𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ 𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫-'
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathtt') ),
            '-𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉 𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣-'
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathcal') ),
            '-𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵 𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏-'
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathscr') ),
            '-𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵 𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏-'
        )
        self.assertEqual(
            LatexNodes2Text().latex_to_text( gen_latex('mathfrak') ),
            '-𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ 𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷-'
        )



    def test_upgreek_letters(self):

        upgreek_letters = (
            ("\\upmu", "μ"),
            ("\\upalpha", "α"),
            ("\\upbeta", "β"),
            ("\\upgamma", "γ"),
            ("\\updelta", "δ"),
            ("\\upepsilon", "ϵ"),     # not sure...
            ("\\upvarepsilon", "ε"),  #
            ("\\upzeta", "ζ"),
            ("\\upeta", "η"),
            ("\\uptheta", "θ"),     # not sure...
            ("\\upvartheta", "ϑ"),  #
            ("\\upiota", "ι"),
            ("\\upkappa", "κ"),
            ("\\uplambda", "λ"),
            ("\\upmu", "μ"),
            ("\\upnu", "ν"),
            ("\\upxi", "ξ"),
            ("\\uppi", "π"),
            ("\\upvarpi", "ϖ"),
            ("\\uprho", "ρ"),     # not sure...
            ("\\upvarrho", "ϱ"),  #
            ("\\upsigma", "σ"),     # not sure...
            ("\\upvarsigma", "ς"),  #
            ("\\uptau", "τ"),
            ("\\upupsilon", "υ"),
            ("\\upphi", "ϕ"),     # not sure...
            ("\\upvarphi", "φ"),  # NB: 'ϕ' != 'φ'
            ("\\upchi", "χ"),
            ("\\uppsi", "ψ"),
            ("\\upomega", "ω"),
            #
            ("\\Upgamma", "Γ"),
            ("\\Updelta", "Δ"),
            ("\\Uptheta", "Θ"),
            ("\\Uplambda", "Λ"),
            ("\\Upxi", "Ξ"),
            ("\\Uppi", "Π"),
            ("\\Upsigma", "Σ"),
            ("\\Upupsilon", "Υ"),
            ("\\Upphi", "Φ"),
            ("\\Uppsi", "Ψ"),
            ("\\Upomega", "Ω"),
        )

        for source, expected_dest in upgreek_letters:
            self.assertEqual(
                LatexNodes2Text().nodelist_to_text(
                    LatexWalker(source).get_latex_nodes()[0]),
                expected_dest
            )


    #
    # The verbatim constructs, as rendered to text.  These tests pin down the
    # behavior independently of which argument parser implements the verbatim
    # constructs of the default latex context.
    #

    def test_verbatim_verb_is_not_interpreted(self):
        # the verbatim content is not interpreted as latex code; note that
        # latex2text does not currently reproduce the content of \verb itself
        self.assertEqual(
            LatexNodes2Text().nodelist_to_text(
                LatexWalker(r'before \verb+\textbf{x}$y$+ after').get_latex_nodes()[0]),
            'before  after'
        )

    def test_verbatim_environment_is_not_interpreted(self):
        # the contents of a verbatim environment are reproduced as they appear
        # in the source, and are not interpreted as latex code
        latex = '\\begin{verbatim}\n\\textbf{x} $y$\n\\end{verbatim}'
        self.assertEqual(
            LatexNodes2Text().nodelist_to_text(
                LatexWalker(latex).get_latex_nodes()[0]),
            '\\textbf{x} $y$\n'
        )

    def test_verbatim_content_available_on_the_node(self):
        # the verbatim content must be reachable on the parsed nodes, both
        # through the node structure and through the `verbatim_text` and
        # `verbatim_delimiters` attributes that ‘pylatexenc 2’ provided
        nodelist = LatexWalker(r'\verb+\textbf{x}+').get_latex_nodes()[0]
        verbgroup = nodelist[0].nodeargd.argnlist[0]
        self.assertEqual(verbgroup.nodelist[0].chars, r'\textbf{x}')
        self.assertEqual(verbgroup.delimiters, ('+', '+'))
        self.assertEqual(nodelist[0].nodeargd.verbatim_text, r'\textbf{x}')
        self.assertEqual(nodelist[0].nodeargd.verbatim_delimiters, ('+', '+'))

        nodelist = LatexWalker(
            '\\begin{verbatim}\nraw $ text\n\\end{verbatim}').get_latex_nodes()[0]
        self.assertEqual(nodelist[0].nodelist[0].chars, 'raw $ text\n')
        self.assertEqual(nodelist[0].nodeargd.verbatim_text, 'raw $ text\n')
        self.assertIsNone(nodelist[0].nodeargd.verbatim_delimiters)


    def test_item_macro_with_explicit_label(self):
        # an explicit ``\item[Label]`` label is already separated from the item
        # contents in the source; we must not add another space after it
        self.assertEqual(
            LatexNodes2Text().latex_to_text(r'\item[Label] text'),
            '\n  Label text'
        )
        # ... whereas the marker that we generate for a bare ``\item`` does need
        # a space to separate it from the contents
        text = LatexNodes2Text().latex_to_text(r'\item text')
        self.assertTrue(text.endswith(' text'))
        self.assertFalse(text.endswith('  text'))


    def test_textfrac(self):
        # \textfrac needs to be declared with its two arguments in the
        # latexwalker specs, otherwise the substitution in the latex2text specs
        # fails and the format string itself shows up in the output
        self.assertEqual(
            LatexNodes2Text().latex_to_text(r'\textfrac{1}{2}'),
            '1/2'
        )


    def test_input_strict_input_sibling_directory(self):
        # with strict_input=True, a sibling directory whose name merely starts
        # with the name of the mandated directory must not become readable
        tempdir = tempfile.mkdtemp()
        try:
            okdir = os.path.join(tempdir, 'dir')
            evildir = os.path.join(tempdir, 'dir-evil')
            os.mkdir(okdir)
            os.mkdir(evildir)
            with open(os.path.join(okdir, 'ok.tex'), 'w') as f:
                f.write('legit content')
            with open(os.path.join(evildir, 'secret.tex'), 'w') as f:
                f.write('secret content')

            l2t = LatexNodes2Text()
            l2t.set_tex_input_directory(okdir, strict_input=True)

            self.assertEqualUpToWhitespace(
                l2t.nodelist_to_text(
                    LatexWalker(r'\input{../dir-evil/secret}').get_latex_nodes()[0]
                ),
                ''
            )
            # a file that really is in the mandated directory is still read
            self.assertEqualUpToWhitespace(
                l2t.nodelist_to_text(
                    LatexWalker(r'\input{ok}').get_latex_nodes()[0]
                ),
                'legit content'
            )
        finally:
            shutil.rmtree(tempdir)








    #
    # test utilities
    #

    def assertEqualUpToWhitespace(self, a, b):
        a2 = re.sub(r'\s+', ' ', a).strip()
        b2 = re.sub(r'\s+', ' ', b).strip()
        self.assertEqual(a2, b2)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
