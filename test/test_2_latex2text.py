
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import unittest

import sys
import re
import os
import os.path
import unicodedata
import datetime
import logging
import warnings

import pytest

from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text


# These tests exercise the pylatexenc 2.x compatibility API on purpose, so the
# associated deprecation warnings are expected and would only drown out the
# pytest output.  (The warnings.simplefilter() calls in the test case
# constructors below don't help under pytest, which resets the warning filters
# around each test.)
pytestmark = pytest.mark.filterwarnings("ignore:Deprecated \\(pylatexenc")


class TestLatexNodes2Text(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexNodes2Text, self).__init__(*args, **kwargs)
        self.maxDiff = None
        warnings.simplefilter('ignore', DeprecationWarning)

    def test_basic(self):

        self.assertEqual(
            LatexNodes2Text().nodelist_to_text(LatexWalker(r'\textbf{A}').get_latex_nodes()[0]),
            'A'
        )

        latex = r'''\textit{hi there!} This is {\em an equation}:
\begin{equation}
    x + y i = 0
\end{equation}

where $i$ is the ``imaginary unit.''
'''
        self.assertEqualUpToWhitespace(
            LatexNodes2Text().nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
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
            LatexNodes2Text().nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
            LatexNodes2Text().latex_to_text(latex)
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
            LatexNodes2Text(keep_braced_groups=True)
            .nodelist_to_text(
                LatexWalker(
                    r"\textit{Voil\`a du texte}. Il est \'{e}crit {en fran{\c{c}}ais}"
                ).get_latex_nodes()[0]
            ),
            '''Voil\N{LATIN SMALL LETTER A WITH GRAVE} du texte. Il est \N{LATIN SMALL LETTER E WITH ACUTE}crit {en fran\N{LATIN SMALL LETTER C WITH CEDILLA}ais}'''
        )

        self.assertEqual(
            LatexNodes2Text(keep_braced_groups=True, keep_braced_groups_minlen=4)
            .nodelist_to_text(LatexWalker(r"A{XYZ}{ABCD}").get_latex_nodes()[0]),
            '''AXYZ{ABCD}'''
        )
        self.assertEqual(
            LatexNodes2Text(keep_braced_groups=True, keep_braced_groups_minlen=0)
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
                LatexNodes2Text(strict_latex_spaces=strict_latex_spaces,
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
            LatexNodes2Text().latex_to_text(
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

        l2t = LatexNodes2Text()
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
        l2t = LatexNodes2Text()
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
    # test text filling etc.
    #

    def test_text_filling(self):

        self.assertEqual(
            LatexNodes2Text(fill_text=20, strict_latex_spaces=True).latex_to_text(
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
            LatexNodes2Text(fill_text=True, strict_latex_spaces=True).latex_to_text(
                r"""

  Hello \emph{world}.  % comment
more text.

"""
            ),
            "\n\nHello world. more text.\n\n"
        )


        self.assertEqual(
            LatexNodes2Text(fill_text=True, strict_latex_spaces=True).latex_to_text(
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
                LatexNodes2Text(strict_latex_spaces='except-in-equations').latex_to_text(
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
            self.assertEqual(LatexNodes2Text().latex_to_text(latex), text)

    def test_repl_subsuperscript_no_unicode_version(self):

        # if the argument cannot be fully typeset with unicode
        # superscript/subscript characters, we keep latex's own notation, with
        # braces only if the argument is longer than a single character
        for latex, text in (
                # there is no unicode superscript alpha
                (r"$x^\alpha$", u"x^\N{GREEK SMALL LETTER ALPHA}"),
                (r"$A^\dagger$", u"A^\N{DAGGER}"),
                # 'C' has no superscript version, so the whole argument falls back
                (r"$X^{ABC}$", u"X^{ABC}"),
                (r"$e^{i\pi}$", u"e^{i\N{GREEK SMALL LETTER PI}}"),
                # capital letters have no subscript version at all
                (r"$x_N$", u"x_N"),
                # a superscript within a superscript can't be typeset in unicode
                (r"$x^{a^b}$", u"x^{a\N{MODIFIER LETTER SMALL B}}"),
        ):
            self.assertEqual(LatexNodes2Text().latex_to_text(latex), text)

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
            LatexNodes2Text().latex_to_text(r"$x^{}$"),
            "x"
        )

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
            LatexNodes2Text().latex_to_text(
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


    @unittest.skipIf( sys.maxunicode < 0x10FFFF,
                      "no math alphabets on narrow python builds")
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

        # on Py 2.7, r"\u..." still tries to interpolate unicode escapes \uXXXX !
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
