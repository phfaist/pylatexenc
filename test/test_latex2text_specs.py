# -*- coding: utf-8 -*-
#
# Tests for the *default definitions* that `pylatexenc.latex2text` ships with,
# that is, the catalogue of macros, environments and specials collected in
# `pylatexenc/latex2text/_defaultspecs.py`.
#
# The conversion engine itself, the options of `LatexNodes2Text` and the
# machinery that applies a replacement string are the subject of a separate
# test file; here we only check *what the definitions say*: which character or
# which piece of text each macro stands for, and what the formatter functions
# that the definitions install actually produce.
#
# The expected characters are written out as literals or as `\N{...}` escapes
# on purpose.  A test that looked the characters up the same way the library
# does would only be checking that the library agrees with itself; spelling
# them out is what pins down which character each macro produces.
#

import unittest

from pylatexenc.latex2text import LatexNodes2Text

# The two default definition databases have to be imported from the modules
# that hold them and threaded through explicitly, because the convenience
# function `get_default_latex_context_db()` of the two main modules is one of
# the pieces that are left out of the JavaScript build.
from pylatexenc.latexwalker._get_defaultspecs import (
    get_default_latex_context_db as get_latexwalker_default_context_db
)
from pylatexenc.latex2text._get_defaultspecs import (
    get_default_latex_context_db as get_latex2text_default_context_db
)


def convert(latex, **options):
    r"""
    Convert `latex` to text with the default definitions, passing `options` on
    to `LatexNodes2Text`.  With no options this is the library's out-of-the-box
    behavior, which includes the 'fancy' math mode and the unicode font styles.
    """
    l2t = LatexNodes2Text(latex_context=get_latex2text_default_context_db(),
                          **options)
    return l2t.latex_to_text(latex,
                             latex_context=get_latexwalker_default_context_db())


def convert_plain(latex):
    r"""
    Convert `latex` to text with every embellishment switched off: formulas are
    rendered by the simple engine that pylatexenc 2 used, and no unicode
    alphabet is used for the font styles.  This is the setting in which the
    plain replacement text of a definition shows through undisturbed.
    """
    return convert(latex, math_mode='text', math_fontstyle=None,
                   text_fontstyle=False)


# ------------------------------------------------------------------------------
# Font styles
# ------------------------------------------------------------------------------

class TestTextFontStyleMacros(unittest.TestCase):
    r"""
    The text mode font macros, `\textbf{}` and friends.  Each of them selects a
    unicode alphabet for its argument; the ones that stand for the plain
    upright font select none.
    """

    def test_upright_families_leave_the_letters_alone(self):
        # '\textrm', '\textup' and '\textmd' all take the text back to the
        # plain upright font, for which unicode has no alphabet of its own
        self.assertEqual(convert(r'\textrm{ab}'), 'ab')
        self.assertEqual(convert(r'\textup{ab}'), 'ab')
        self.assertEqual(convert(r'\textmd{ab}'), 'ab')

    def test_bold(self):
        self.assertEqual(convert(r'\textbf{ab}'), u'\U0001D41A\U0001D41B') # '𝐚𝐛'

    def test_italic(self):
        self.assertEqual(convert(r'\textit{ab}'), u'\U0001D44E\U0001D44F') # '𝑎𝑏'

    def test_slanted_uses_the_italic_alphabet(self):
        # unicode has no slanted alphabet, so the italic one stands in for it
        self.assertEqual(convert(r'\textsl{ab}'), convert(r'\textit{ab}'))
        self.assertEqual(convert(r'\textsl{ab}'), u'\U0001D44E\U0001D44F')

    def test_sans_serif(self):
        self.assertEqual(convert(r'\textsf{ab}'), u'\U0001D5BA\U0001D5BB') # '𝖺𝖻'

    def test_monospace(self):
        self.assertEqual(convert(r'\texttt{ab}'), u'\U0001D68A\U0001D68B') # '𝚊𝚋'

    def test_text_and_mbox_do_not_change_the_font(self):
        # '\text{}' and '\mbox{}' only switch to text mode; the font style they
        # find in force is the one they leave in force
        self.assertEqual(convert(r'\text{ab}'), 'ab')
        self.assertEqual(convert(r'\mbox{ab}'), 'ab')
        self.assertEqual(convert(r'\textit{a\text{b}}'),
                         u'\U0001D44E\U0001D44F') # both letters italic
        self.assertEqual(convert(r'\textit{a\mbox{b}}'),
                         u'\U0001D44E\U0001D44F')

    def test_textsc_keeps_its_argument(self):
        # small capitals have no unicode alphabet either, and the definition
        # simply keeps the text
        self.assertEqual(convert(r'\textsc{ab}'), 'ab')

    def test_a_font_macro_replaces_the_one_in_force(self):
        # each of these macros stands for a whole font and not for one of the
        # axes that LaTeX varies independently, so the inner one wins outright
        self.assertEqual(convert(r'\textbf{a \textit{b} c}'),
                         u'\U0001D41A \U0001D44F \U0001D41C') # '𝐚 𝑏 𝐜'
        self.assertEqual(convert(r'\textbf{a \textrm{b}}'),
                         u'\U0001D41A b') # '𝐚 b'
        self.assertEqual(convert(r'\textsf{a \textbf{b}}'),
                         u'\U0001D5BA \U0001D41B') # '𝖺 𝐛'

    def test_font_styles_switched_off_altogether(self):
        # `text_fontstyle=False` says that no unicode alphabet is to be used in
        # text mode at all; the macros leave that value where they find it
        self.assertEqual(convert(r'\textbf{ab}', text_fontstyle=False), 'ab')
        self.assertEqual(convert(r'\textit{ab}', text_fontstyle=False), 'ab')
        self.assertEqual(convert(r'\texttt{ab}', text_fontstyle=False), 'ab')

    def test_text_font_macros_inside_a_formula(self):
        # a text mode font macro used inside a formula still typesets its
        # argument in text mode, with the text font style it names
        self.assertEqual(convert(r'$\text{ab}$'), 'ab')
        self.assertEqual(convert(r'$\mbox{ab}$'), 'ab')
        self.assertEqual(convert(r'$\textbf{ab}$'), u'\U0001D41A\U0001D41B')

    def test_text_font_survives_an_excursion_into_math_mode(self):
        # the text font and the math font are stacked independently: the '[b]'
        # is back in the italic text font that '\textit{}' installed, although
        # the formula around it is set in the bold math font
        self.assertEqual(
            convert(r'\textit{x $\mathbf{a+\text{[b]}}$}'),
            u'\U0001D465 \U0001D41A + [\U0001D44F]' # '𝑥 𝐚 + [𝑏]'
        )


class TestMathFontStyleMacros(unittest.TestCase):
    r"""
    The math mode font macros, `\mathbf{}` and friends.
    """

    def test_mathrm_is_the_upright_font(self):
        # letters in a formula are italicized by default; '\mathrm{}' is what
        # stops that for the length of its argument
        self.assertEqual(convert(r'$ab$'), u'\U0001D44E\U0001D44F') # '𝑎𝑏'
        self.assertEqual(convert(r'$\mathrm{ab}$'), 'ab')

    def test_mathbf(self):
        self.assertEqual(convert(r'$\mathbf{ab}$'), u'\U0001D41A\U0001D41B') # '𝐚𝐛'

    def test_mathit(self):
        self.assertEqual(convert(r'$\mathit{ab}$'), u'\U0001D44E\U0001D44F') # '𝑎𝑏'

    def test_mathsf(self):
        self.assertEqual(convert(r'$\mathsf{ab}$'), u'\U0001D5BA\U0001D5BB') # '𝖺𝖻'

    def test_mathbb(self):
        self.assertEqual(convert(r'$\mathbb{ab}$'), u'\U0001D552\U0001D553') # '𝕒𝕓'
        # some of the double-struck capitals live outside the block of
        # mathematical alphanumeric symbols, as separate letterlike symbols
        self.assertEqual(convert(r'$\mathbb{R}$'), u'\N{DOUBLE-STRUCK CAPITAL R}')

    def test_mathtt(self):
        self.assertEqual(convert(r'$\mathtt{ab}$'), u'\U0001D68A\U0001D68B') # '𝚊𝚋'

    def test_mathcal(self):
        self.assertEqual(convert(r'$\mathcal{ab}$'), u'\U0001D4B6\U0001D4B7') # '𝒶𝒷'
        self.assertEqual(convert(r'$\mathcal{H}$'), u'\N{SCRIPT CAPITAL H}')

    def test_mathscr_uses_the_same_alphabet_as_mathcal(self):
        self.assertEqual(convert(r'$\mathscr{ab}$'), convert(r'$\mathcal{ab}$'))
        self.assertEqual(convert(r'$\mathscr{ab}$'), u'\U0001D4B6\U0001D4B7')

    def test_mathfrak(self):
        self.assertEqual(convert(r'$\mathfrak{ab}$'), u'\U0001D51E\U0001D51F') # '𝔞𝔟'

    def test_math_font_macros_nest_by_replacement(self):
        # as in text mode, the innermost font macro decides the whole font
        self.assertEqual(convert(r'$\mathbf{\mathit{a}}$'), u'\U0001D44E') # '𝑎'
        self.assertEqual(convert(r'$\mathbf{a \mathrm{b}}$'), u'\U0001D41Ab')

    def test_math_font_macro_applies_only_to_its_argument(self):
        self.assertEqual(convert(r'$\mathbf{a}b$'),
                         u'\U0001D41A\U0001D44F') # '𝐚𝑏'

    def test_math_font_styles_switched_off_altogether(self):
        self.assertEqual(convert(r'$\mathbf{ab}$', math_fontstyle=False), 'ab')
        self.assertEqual(convert(r'$\mathcal{ab}$', math_fontstyle=False), 'ab')

    def test_math_font_macro_outside_of_math_mode(self):
        # using a math font macro in text is an error in LaTeX; we still honor
        # it, and it is then the text font that it installs
        self.assertEqual(convert(r'\mathbf{ab}'), u'\U0001D41A\U0001D41B')


class TestEmph(unittest.TestCase):
    r"""
    `\emph{}` switches the italic shape on where it is off and off where it is
    on, the way LaTeX restores an upright shape inside an italic context.
    """

    def test_emph_in_upright_text_is_italic(self):
        self.assertEqual(convert(r'\emph{ab}'), u'\U0001D44E\U0001D44F') # '𝑎𝑏'

    def test_emph_inside_emph_goes_back_to_upright(self):
        self.assertEqual(convert(r'\emph{a \emph{b} c}'),
                         u'\U0001D44E b \U0001D450') # '𝑎 b 𝑐'

    def test_emph_composes_with_bold(self):
        # bold and italic together, and not plain italic: the toggling table is
        # what makes the two compose
        self.assertEqual(convert(r'\textbf{a \emph{b} c}'),
                         u'\U0001D41A \U0001D483 \U0001D41C') # '𝐚 𝒃 𝐜'

    def test_emph_composes_with_sans_serif(self):
        self.assertEqual(convert(r'\textsf{a \emph{b}}'),
                         u'\U0001D5BA \U0001D623') # '𝖺 𝘣'

    def test_emph_takes_italic_back_off(self):
        self.assertEqual(convert(r'\textit{a \emph{b}}'),
                         u'\U0001D44E b') # '𝑎 b'

    def test_emph_with_font_styles_switched_off(self):
        self.assertEqual(convert(r'\emph{ab}', text_fontstyle=False), 'ab')

    def test_emph_inside_a_formula(self):
        # '\emph{}' typesets its argument in text mode, like '\text{}' does
        self.assertEqual(convert(r'$a \emph{b} c$'),
                         u'\U0001D44E \U0001D44F \U0001D450') # '𝑎 𝑏 𝑐'


# ------------------------------------------------------------------------------
# Greek letters
# ------------------------------------------------------------------------------

class TestGreekLetters(unittest.TestCase):
    r"""
    Every greek letter, in its lowercase and uppercase form, and in the plain
    ('\alpha') as well as the up-greek ('\upalpha', '\Upalpha') spelling.  The
    up-greek macros come from packages such as `upgreek` and stand for the same
    letters, set upright.
    """

    def _check(self, name, small, capital):
        # the four macros that the definitions generate for each letter
        capname = name[0].upper() + name[1:]
        self.assertEqual(convert('\\' + name + ' '), small)
        self.assertEqual(convert('\\' + capname + ' '), capital)
        self.assertEqual(convert('\\up' + name + ' '), small)
        self.assertEqual(convert('\\Up' + name + ' '), capital)

    def test_alpha(self):
        self._check('alpha', u'α', u'Α') # U+03B1, U+0391

    def test_beta(self):
        self._check('beta', u'β', u'Β') # U+03B2, U+0392

    def test_gamma(self):
        self._check('gamma', u'γ', u'Γ') # U+03B3, U+0393

    def test_delta(self):
        self._check('delta', u'δ', u'Δ') # U+03B4, U+0394

    def test_epsilon(self):
        # LaTeX's '\epsilon' is the *lunate* epsilon U+03F5 and not the plain
        # greek small letter epsilon U+03B5, which is what '\varepsilon' is
        self._check('epsilon', u'\N{GREEK LUNATE EPSILON SYMBOL}', u'Ε')
        self.assertEqual(convert(r'\epsilon '), u'ϵ') # U+03F5

    def test_zeta(self):
        self._check('zeta', u'ζ', u'Ζ') # U+03B6, U+0396

    def test_eta(self):
        self._check('eta', u'η', u'Η') # U+03B7, U+0397

    def test_theta(self):
        self._check('theta', u'θ', u'Θ') # U+03B8, U+0398

    def test_iota(self):
        self._check('iota', u'ι', u'Ι') # U+03B9, U+0399

    def test_kappa(self):
        self._check('kappa', u'κ', u'Κ') # U+03BA, U+039A

    def test_lambda(self):
        # unicode spells the name of this letter 'LAMDA', without the 'b'
        self._check('lambda', u'λ', u'Λ') # U+03BB, U+039B

    def test_mu(self):
        # the greek letter U+03BC, not the micro sign U+00B5
        self._check('mu', u'\N{GREEK SMALL LETTER MU}', u'Μ')
        self.assertEqual(convert(r'\mu '), u'μ') # U+03BC

    def test_nu(self):
        self._check('nu', u'ν', u'Ν') # U+03BD, U+039D

    def test_xi(self):
        self._check('xi', u'ξ', u'Ξ') # U+03BE, U+039E

    def test_omicron(self):
        self._check('omicron', u'ο', u'Ο') # U+03BF, U+039F

    def test_pi(self):
        self._check('pi', u'π', u'Π') # U+03C0, U+03A0

    def test_rho(self):
        self._check('rho', u'ρ', u'Ρ') # U+03C1, U+03A1

    def test_sigma(self):
        # the ordinary small sigma U+03C3, not the final sigma U+03C2, which is
        # what '\varsigma' stands for
        self._check('sigma', u'σ', u'Σ') # U+03C3, U+03A3

    def test_tau(self):
        self._check('tau', u'τ', u'Τ') # U+03C4, U+03A4

    def test_upsilon(self):
        self._check('upsilon', u'υ', u'Υ') # U+03C5, U+03A5

    def test_phi(self):
        # LaTeX's '\phi' is the *phi symbol* U+03D5, the closed shape, and not
        # the greek small letter phi U+03C6, which is what '\varphi' is
        self._check('phi', u'\N{GREEK PHI SYMBOL}', u'Φ')
        self.assertEqual(convert(r'\phi '), u'ϕ') # U+03D5

    def test_chi(self):
        self._check('chi', u'χ', u'Χ') # U+03C7, U+03A7

    def test_psi(self):
        self._check('psi', u'ψ', u'Ψ') # U+03C8, U+03A8

    def test_omega(self):
        # the greek letter U+03C9 and the greek capital U+03A9, not the ohm
        # sign U+2126
        self._check('omega', u'\N{GREEK SMALL LETTER OMEGA}',
                    u'\N{GREEK CAPITAL LETTER OMEGA}')
        self.assertEqual(convert(r'\Omega '), u'Ω') # U+03A9

    def test_var_variants(self):
        # the '\var...' macros are the alternative shapes of six of the letters
        self.assertEqual(convert(r'\varepsilon '), u'ε') # U+03B5
        self.assertEqual(convert(r'\vartheta '), u'ϑ') # U+03D1
        self.assertEqual(convert(r'\varpi '), u'ϖ') # U+03D6
        self.assertEqual(convert(r'\varrho '), u'ϱ') # U+03F1
        self.assertEqual(convert(r'\varsigma '), u'ς') # U+03C2
        self.assertEqual(convert(r'\varphi '), u'φ') # U+03C6

    def test_up_var_variants(self):
        # the up-greek spellings of the same six shapes
        self.assertEqual(convert(r'\upvarepsilon '), u'ε') # U+03B5
        self.assertEqual(convert(r'\upvartheta '), u'ϑ') # U+03D1
        self.assertEqual(convert(r'\upvarpi '), u'ϖ') # U+03D6
        self.assertEqual(convert(r'\upvarrho '), u'ϱ') # U+03F1
        self.assertEqual(convert(r'\upvarsigma '), u'ς') # U+03C2
        self.assertEqual(convert(r'\upvarphi '), u'φ') # U+03C6

    def test_varkappa(self):
        # this one comes from the 'advanced symbols' category rather than from
        # the greek letter table
        self.assertEqual(convert(r'\varkappa '), u'ϰ') # U+03F0

    def test_greek_letters_inside_a_formula(self):
        # the letters are single characters that stand for themselves; the math
        # font styles do not reach them
        self.assertEqual(convert(r'$\alpha\Gamma\upalpha$'), u'αΓα')


# ------------------------------------------------------------------------------
# Accents
# ------------------------------------------------------------------------------

class TestAccentMacros(unittest.TestCase):
    r"""
    The accent macros of `unicode_accents_list`.  Each of them puts a combining
    character behind the letter it is applied to; where unicode has a single
    character for the combination, that is the character we get.
    """

    def test_accents_named_by_a_punctuation_character(self):
        # the accents that LaTeX spells with a punctuation character, which are
        # the ones one meets in ordinary prose
        self.assertEqual(convert(r"\'e"), u'\N{LATIN SMALL LETTER E WITH ACUTE}')
        self.assertEqual(convert('\\`e'), u'\N{LATIN SMALL LETTER E WITH GRAVE}')
        self.assertEqual(convert(r'\^e'),
                         u'\N{LATIN SMALL LETTER E WITH CIRCUMFLEX}')
        self.assertEqual(convert(r'\"e'),
                         u'\N{LATIN SMALL LETTER E WITH DIAERESIS}')
        self.assertEqual(convert(r'\~n'), u'\N{LATIN SMALL LETTER N WITH TILDE}')
        self.assertEqual(convert(r'\=a'),
                         u'\N{LATIN SMALL LETTER A WITH MACRON}')
        self.assertEqual(convert(r'\.a'),
                         u'\N{LATIN SMALL LETTER A WITH DOT ABOVE}')

    def test_accents_named_by_a_letter(self):
        # the accents that LaTeX spells with a letter
        self.assertEqual(convert(r'\c c'),
                         u'\N{LATIN SMALL LETTER C WITH CEDILLA}')
        self.assertEqual(convert(r'\k a'),
                         u'\N{LATIN SMALL LETTER A WITH OGONEK}')
        self.assertEqual(convert(r'\d a'),
                         u'\N{LATIN SMALL LETTER A WITH DOT BELOW}')
        self.assertEqual(convert(r'\r a'),
                         u'\N{LATIN SMALL LETTER A WITH RING ABOVE}')
        self.assertEqual(convert(r'\u a'),
                         u'\N{LATIN SMALL LETTER A WITH BREVE}')
        self.assertEqual(convert(r'\v c'),
                         u'\N{LATIN SMALL LETTER C WITH CARON}')
        self.assertEqual(convert(r'\H o'),
                         u'\N{LATIN SMALL LETTER O WITH DOUBLE ACUTE}')

    def test_accent_with_no_single_character_for_the_combination(self):
        # unicode has no letter with a macron below, so the combining character
        # simply stays behind the letter
        self.assertEqual(convert(r'\b a'), u'a\N{COMBINING MACRON BELOW}')

    def test_accents_with_a_spelled_out_name(self):
        # the accents that are written with a word, which are mostly used in
        # formulas
        self.assertEqual(convert(r'\vec x'),
                         u'x\N{COMBINING RIGHT ARROW ABOVE}')
        self.assertEqual(convert(r'\dot x'),
                         u'\N{LATIN SMALL LETTER X WITH DOT ABOVE}')
        self.assertEqual(convert(r'\hat x'),
                         u'x\N{COMBINING CIRCUMFLEX ACCENT}')
        self.assertEqual(convert(r'\check x'), u'x\N{COMBINING CARON}')
        self.assertEqual(convert(r'\breve x'), u'x\N{COMBINING BREVE}')
        self.assertEqual(convert(r'\acute x'), u'x\N{COMBINING ACUTE ACCENT}')
        self.assertEqual(convert(r'\grave x'), u'x\N{COMBINING GRAVE ACCENT}')
        self.assertEqual(convert(r'\tilde x'), u'x\N{COMBINING TILDE}')
        self.assertEqual(convert(r'\ddot x'),
                         u'\N{LATIN SMALL LETTER X WITH DIAERESIS}')
        # '\bar' is defined with the combining overline and not with a macron
        self.assertEqual(convert(r'\bar x'), u'x\N{COMBINING OVERLINE}')

    def test_accent_on_a_braced_argument_and_on_a_capital(self):
        self.assertEqual(convert(r"\'{e}"), u'\N{LATIN SMALL LETTER E WITH ACUTE}')
        self.assertEqual(convert(r"\'A"), u'\N{LATIN CAPITAL LETTER A WITH ACUTE}')
        self.assertEqual(convert(r'\c{C}'),
                         u'\N{LATIN CAPITAL LETTER C WITH CEDILLA}')

    def test_not(self):
        # '\not' overlays a long solidus, which unicode has a single character
        # for on the most common relations
        self.assertEqual(convert(r'\not='), u'\N{NOT EQUAL TO}')
        self.assertEqual(convert(r'\not\in'), u'\N{NOT AN ELEMENT OF}')

    def test_dotless_i_and_j(self):
        # '\i' and '\j' are the dotless letters, which is what one writes under
        # an accent in LaTeX; the accent macros put the dot back before
        # combining, so that a real precomposed letter comes out
        self.assertEqual(convert(r'\i '), u'\N{LATIN SMALL LETTER DOTLESS I}')
        self.assertEqual(convert(r'\j '), u'\N{LATIN SMALL LETTER DOTLESS J}')
        self.assertEqual(convert(r"\'{\i}"),
                         u'\N{LATIN SMALL LETTER I WITH ACUTE}')
        self.assertEqual(convert(r"\'\i"),
                         u'\N{LATIN SMALL LETTER I WITH ACUTE}')
        self.assertEqual(convert(r'\"{\i}'),
                         u'\N{LATIN SMALL LETTER I WITH DIAERESIS}')
        self.assertEqual(convert(r'\^{\j}'),
                         u'\N{LATIN SMALL LETTER J WITH CIRCUMFLEX}')

    def test_accent_on_several_letters(self):
        # an accent whose argument is more than one character accents each of
        # them in turn, for want of anything better to do
        self.assertEqual(convert(r"\'{ab}"),
                         u'\N{LATIN SMALL LETTER A WITH ACUTE}'
                         u'b\N{COMBINING ACUTE ACCENT}')

    def test_accent_on_an_empty_argument(self):
        self.assertEqual(convert(r"\'{}"), '')

    def test_accent_inside_a_formula(self):
        # in a formula the letter reaches the accent macro already italicized,
        # and the combining character goes behind the italic letter
        self.assertEqual(convert(r'$\hat{x}$'),
                         u'\U0001D465\N{COMBINING CIRCUMFLEX ACCENT}')
        self.assertEqual(convert(r'$\vec{v}$'),
                         u'\U0001D463\N{COMBINING RIGHT ARROW ABOVE}')


# ------------------------------------------------------------------------------
# Function and operator names
# ------------------------------------------------------------------------------

class TestMathOperatorNames(unittest.TestCase):
    r"""
    The names of the standard functions and operators.  Each of them renders as
    itself; the ones whose name is written as two words in print render as two
    words here too.
    """

    def test_trigonometric_functions(self):
        self.assertEqual(convert_plain(r'$\cos$'), 'cos')
        self.assertEqual(convert_plain(r'$\sin$'), 'sin')
        self.assertEqual(convert_plain(r'$\tan$'), 'tan')
        self.assertEqual(convert_plain(r'$\sec$'), 'sec')
        self.assertEqual(convert_plain(r'$\csc$'), 'csc')
        self.assertEqual(convert_plain(r'$\cot$'), 'cot')

    def test_inverse_trigonometric_functions(self):
        self.assertEqual(convert_plain(r'$\arccos$'), 'arccos')
        self.assertEqual(convert_plain(r'$\arcsin$'), 'arcsin')
        self.assertEqual(convert_plain(r'$\arctan$'), 'arctan')

    def test_hyperbolic_functions(self):
        self.assertEqual(convert_plain(r'$\cosh$'), 'cosh')
        self.assertEqual(convert_plain(r'$\sinh$'), 'sinh')
        self.assertEqual(convert_plain(r'$\tanh$'), 'tanh')
        self.assertEqual(convert_plain(r'$\coth$'), 'coth')
        self.assertEqual(convert_plain(r'$\arccosh$'), 'arccosh')
        self.assertEqual(convert_plain(r'$\arcsinh$'), 'arcsinh')
        self.assertEqual(convert_plain(r'$\arctanh$'), 'arctanh')

    def test_logarithms_and_exponential(self):
        self.assertEqual(convert_plain(r'$\ln$'), 'ln')
        self.assertEqual(convert_plain(r'$\lg$'), 'lg')
        self.assertEqual(convert_plain(r'$\log$'), 'log')
        self.assertEqual(convert_plain(r'$\exp$'), 'exp')

    def test_extrema_and_limits(self):
        self.assertEqual(convert_plain(r'$\max$'), 'max')
        self.assertEqual(convert_plain(r'$\min$'), 'min')
        self.assertEqual(convert_plain(r'$\sup$'), 'sup')
        self.assertEqual(convert_plain(r'$\inf$'), 'inf')
        self.assertEqual(convert_plain(r'$\lim$'), 'lim')
        # these are two words in print, and they are two words here
        self.assertEqual(convert_plain(r'$\limsup$'), 'lim sup')
        self.assertEqual(convert_plain(r'$\liminf$'), 'lim inf')

    def test_amsmath_limit_operators(self):
        # the '\var...' spellings are alternative typesettings of the same
        # operators -- a bar or an arrow drawn over the 'lim' instead of the
        # words spelled out -- which plain text cannot show
        self.assertEqual(convert_plain(r'$\injlim$'), 'inj lim')
        self.assertEqual(convert_plain(r'$\projlim$'), 'proj lim')
        self.assertEqual(convert_plain(r'$\varlimsup$'), 'lim sup')
        self.assertEqual(convert_plain(r'$\varliminf$'), 'lim inf')
        self.assertEqual(convert_plain(r'$\varinjlim$'), 'inj lim')
        self.assertEqual(convert_plain(r'$\varprojlim$'), 'proj lim')

    def test_remaining_operator_names(self):
        self.assertEqual(convert_plain(r'$\arg$'), 'arg')
        self.assertEqual(convert_plain(r'$\deg$'), 'deg')
        self.assertEqual(convert_plain(r'$\det$'), 'det')
        self.assertEqual(convert_plain(r'$\dim$'), 'dim')
        self.assertEqual(convert_plain(r'$\gcd$'), 'gcd')
        self.assertEqual(convert_plain(r'$\hom$'), 'hom')
        self.assertEqual(convert_plain(r'$\ker$'), 'ker')
        self.assertEqual(convert_plain(r'$\Pr$'), 'Pr')

    def test_operator_names_are_set_apart_from_their_argument(self):
        # the operator names say that they *are* operators, so that the joiner
        # of the fancy engine keeps them apart from what follows
        self.assertEqual(convert(r'$\sin x$'), u'sin \U0001D465') # 'sin 𝑥'
        self.assertEqual(convert(r'$\log x$'), u'log \U0001D465')
        self.assertEqual(convert(r'$\limsup x$'), u'lim sup \U0001D465')


class TestOperatornameAndModulo(unittest.TestCase):
    r"""
    `\operatorname{}` and the three modulo constructs.
    """

    def test_operatorname(self):
        # the argument is typeset upright, as '\mathrm{}' would, and the result
        # behaves like any other function name
        self.assertEqual(convert(r'$\operatorname{tr}\rho$'), u'tr ρ')

    def test_operatorname_star(self):
        # the star of '\operatorname*{}' only says where the limits of the
        # operator go, which does not concern plain text
        self.assertEqual(convert(r'$\operatorname*{tr}\rho$'), u'tr ρ')

    def test_operatorname_argument_is_upright(self):
        self.assertEqual(convert(r'$\operatorname{ab}$'), 'ab')

    def test_bmod(self):
        # the infix operator, which wants a space on each side
        self.assertEqual(convert(r'$a\bmod b$'),
                         u'\U0001D44E mod \U0001D44F') # '𝑎 mod 𝑏'
        self.assertEqual(convert_plain(r'$\bmod$'), 'mod')

    def test_pmod(self):
        self.assertEqual(convert(r'$a\equiv b\pmod{n}$'),
                         u'\U0001D44E \N{IDENTICAL TO} \U0001D44F (mod \U0001D45B)')

    def test_mod(self):
        self.assertEqual(convert(r'$a\equiv b\mod{n}$'),
                         u'\U0001D44E \N{IDENTICAL TO} \U0001D44F mod \U0001D45B')


# ------------------------------------------------------------------------------
# Fractions and roots
# ------------------------------------------------------------------------------

class TestFractionsAndRoots(unittest.TestCase):
    r"""
    `\frac{}{}` and its relatives, and `\sqrt{}` with and without its optional
    degree.
    """

    def test_frac(self):
        self.assertEqual(convert_plain(r'$\frac{a}{b}$'), 'a/b')

    def test_frac_delimits_a_compound_operand(self):
        # a numerator or denominator that is more than a single item would lose
        # its extent in the 'a/b' notation, so it gets the delimiters of the
        # `math_expression_in` option around it
        self.assertEqual(convert_plain(r'$\frac{a+b}{c}$'), '(a+b)/c')
        self.assertEqual(convert_plain(r'$\frac{a}{b+c}$'), 'a/(b+c)')

    def test_nicefrac_and_textfrac_are_the_same_thing(self):
        self.assertEqual(convert_plain(r'$\nicefrac{a}{b}$'), 'a/b')
        self.assertEqual(convert_plain(r'$\textfrac{a}{b}$'), 'a/b')

    def test_frac_outside_of_math_mode(self):
        self.assertEqual(convert_plain(r'\frac{a}{b}'), 'a/b')
        self.assertEqual(convert(r'\frac{a}{b}'), 'a/b')

    def test_frac_in_the_fancy_engine(self):
        self.assertEqual(convert(r'$\frac{a}{b}$'),
                         u'\U0001D44E/\U0001D44F') # '𝑎/𝑏'
        self.assertEqual(convert(r'$\frac{a+b}{c}$'),
                         u'(\U0001D44E + \U0001D44F)/\U0001D450')

    def test_sqrt(self):
        self.assertEqual(convert_plain(r'$\sqrt{2}$'), u'\N{SQUARE ROOT}(2)')

    def test_sqrt_cube_and_fourth_root_signs(self):
        # unicode has dedicated signs for these two degrees
        self.assertEqual(convert_plain(r'$\sqrt[3]{2}$'), u'\N{CUBE ROOT}(2)')
        self.assertEqual(convert_plain(r'$\sqrt[4]{2}$'), u'\N{FOURTH ROOT}(2)')

    def test_sqrt_other_degree(self):
        # any other degree is written out in front of the root sign, the way it
        # is typeset
        self.assertEqual(convert_plain(r'$\sqrt[n]{2}$'), u'n\N{SQUARE ROOT}(2)')

    def test_sqrt_in_the_fancy_engine(self):
        # a radicand of a single character is clear enough on its own and gets
        # no parentheses
        self.assertEqual(convert(r'$\sqrt{2}$'), u'\N{SQUARE ROOT}2')
        self.assertEqual(convert(r'$\sqrt[3]{2}$'), u'\N{CUBE ROOT}2')
        self.assertEqual(convert(r'$\sqrt[4]{2}$'), u'\N{FOURTH ROOT}2')
        self.assertEqual(convert(r'$\sqrt{a+b}$'),
                         u'\N{SQUARE ROOT}(\U0001D44E + \U0001D44F)')

    def test_sqrt_hugs_what_precedes_it(self):
        self.assertEqual(convert(r'$2\sqrt{x}$'),
                         u'2\N{SQUARE ROOT}\U0001D465') # '2√𝑥'


# ------------------------------------------------------------------------------
# Document structure
# ------------------------------------------------------------------------------

class TestSectioningMacros(unittest.TestCase):
    r"""
    The sectioning commands.  The top three levels are set in capitals and
    carry a marker; the lower ones are only indented.
    """

    def test_part_and_chapter(self):
        # the two highest levels announce themselves by name
        self.assertEqual(convert(r'\part{Foo}'), '\n\nPART: FOO\n')
        self.assertEqual(convert(r'\chapter{Foo bar}'), '\n\nCHAPTER: FOO BAR\n')

    def test_section_levels(self):
        # the section levels are marked with as many section signs as their
        # depth; only the top one is set in capitals
        self.assertEqual(convert(r'\section{Foo}'),
                         u'\n\n\N{SECTION SIGN} FOO\n')
        self.assertEqual(convert(r'\subsection{Foo}'),
                         u'\n\n \N{SECTION SIGN}.\N{SECTION SIGN} Foo\n')
        self.assertEqual(
            convert(r'\subsubsection{Foo}'),
            u'\n\n  \N{SECTION SIGN}.\N{SECTION SIGN}.\N{SECTION SIGN} Foo\n'
        )

    def test_paragraph_levels(self):
        # the lowest levels are only set on a line of their own and indented
        self.assertEqual(convert(r'\paragraph{Foo}'), '\n\n  Foo\n')
        self.assertEqual(convert(r'\subparagraph{Foo}'), '\n\n    Foo\n')

    def test_starred_and_short_forms(self):
        # the star and the short title that goes into the table of contents are
        # both ignored; it is the real title that is rendered
        self.assertEqual(convert(r'\section*{Foo}'),
                         u'\n\n\N{SECTION SIGN} FOO\n')
        self.assertEqual(convert(r'\section[short]{Foo}'),
                         u'\n\n\N{SECTION SIGN} FOO\n')


class TestTitleMacros(unittest.TestCase):
    r"""
    `\title`, `\author` and `\date` set the title fields aside, and
    `\maketitle` is what puts them together.
    """

    def test_title_fields_render_as_nothing_on_their_own(self):
        self.assertEqual(convert(r'\title{T}\author{A}\date{D}'), '')

    def test_maketitle(self):
        self.assertEqual(convert(r'\title{T}\author{A}\date{D}\maketitle'),
                         'T\n    A\n    D\n=====\n\n')

    def test_maketitle_short_forms_of_the_fields(self):
        # the fields are declared with a leading optional argument (the "short"
        # form that beamer and the AMS classes accept), and it is the last
        # argument that carries the field itself
        self.assertEqual(convert(r'\title[s]{T}\author[s]{A}\date{D}\maketitle'),
                         'T\n    A\n    D\n=====\n\n')

    def test_maketitle_placeholder_for_a_missing_title(self):
        text = convert(r'\author{A}\date{D}\maketitle')
        self.assertEqual(text, '[NO \\title GIVEN]\n    A\n    D\n'
                         + '=' * len('[NO \\title GIVEN]') + '\n\n')

    def test_maketitle_placeholder_for_a_missing_author(self):
        text = convert(r'\title{T}\date{D}\maketitle')
        self.assertEqual(text, 'T\n    [NO \\author GIVEN]\n    D\n'
                         + '=' * (4 + len('[NO \\author GIVEN]')) + '\n\n')

    def test_maketitle_falls_back_on_todays_date(self):
        # a document with no '\date' gets today's date, which we cannot pin to
        # a value; we only check that a date was put in where 'D' would go
        text = convert(r'\title{T}\author{A}\maketitle')
        lines = text.split('\n')
        self.assertEqual(lines[0], 'T')
        self.assertEqual(lines[1], '    A')
        self.assertTrue(lines[2].startswith('    '))
        self.assertTrue(len(lines[2].strip()) > 0)

    def test_today(self):
        # the current date; its exact value is of course not ours to pin
        today = convert(r'\today')
        self.assertTrue(len(today) > 0)


class TestReferencesAndLinks(unittest.TestCase):
    r"""
    Cross references, citations, links and the other placeholders.
    """

    def test_href(self):
        self.assertEqual(convert(r'\href{https://example.org}{the text}'),
                         'the text <https://example.org>')

    def test_url(self):
        self.assertEqual(convert(r'\url{https://example.org}'),
                         '<https://example.org>')

    def test_footnote(self):
        self.assertEqual(convert(r'\footnote{a note}'), '[a note]')

    def test_footnote_with_a_mark(self):
        # the optional mark is dropped and the text of the note is kept
        self.assertEqual(convert(r'\footnote[3]{a note}'), '[a note]')

    def test_cross_references(self):
        self.assertEqual(convert(r'\ref{sec:a}'), '<ref>')
        self.assertEqual(convert(r'\autoref{sec:a}'), '<ref>')
        self.assertEqual(convert(r'\cref{sec:a}'), '<ref>')
        self.assertEqual(convert(r'\Cref{sec:a}'), '<Ref>')
        self.assertEqual(convert(r'\eqref{eq:a}'), '(<ref>)')

    def test_citations(self):
        self.assertEqual(convert(r'\cite{smith}'), '<cit.>')
        self.assertEqual(convert(r'\citet{smith}'), '<cit.>')
        self.assertEqual(convert(r'\citep{smith}'), '<cit.>')
        self.assertEqual(convert(r'\cite[p.~3]{smith}'), '<cit.>')

    def test_includegraphics(self):
        self.assertEqual(convert(r'\includegraphics{fig.png}'),
                         '\n    < g r a p h i c s >\n')
        self.assertEqual(convert(r'\includegraphics[width=3cm]{fig.png}'),
                         '\n    < g r a p h i c s >\n')

    def test_texorpdfstring_takes_the_second_argument(self):
        self.assertEqual(convert(r'\texorpdfstring{math}{text}'), 'text')


class TestColorAndSpacingMacros(unittest.TestCase):
    r"""
    The color boxes, which keep their contents and drop the colors, and the
    explicit spacing commands.
    """

    def test_textcolor(self):
        self.assertEqual(convert(r'\textcolor{red}{hello}'), 'hello')

    def test_colorbox(self):
        self.assertEqual(convert(r'\colorbox{red}{hello}'), 'hello')

    def test_fcolorbox(self):
        self.assertEqual(convert(r'\fcolorbox{red}{blue}{hello}'), 'hello')

    def test_hspace_and_vspace(self):
        # a horizontal space of an unknown width is dropped; a vertical one
        # becomes a line break
        self.assertEqual(convert(r'a\hspace{1cm}b'), 'ab')
        self.assertEqual(convert(r'a\vspace{1cm}b'), 'a\nb')

    def test_end_of_line(self):
        self.assertEqual(convert('a\\\\b'), 'a\nb')

    def test_math_spacing_macros(self):
        self.assertEqual(convert_plain(r'a\,b'), 'a b')
        self.assertEqual(convert_plain(r'a\;b'), 'a b')
        self.assertEqual(convert_plain(r'a\:b'), 'a b')
        self.assertEqual(convert_plain('a\\ b'), 'a b')
        # a backslash at the end of a line is the control space, so it stands
        # for a space and not for nothing
        self.assertEqual(convert_plain('a\\\nb'), 'a b')
        # there is no negative space in plain text
        self.assertEqual(convert_plain(r'a\!b'), 'ab')

    def test_quad_and_qquad(self):
        self.assertEqual(convert_plain(r'\quad'), '  ')
        self.assertEqual(convert_plain(r'\qquad'), '    ')

    def test_tabular_alignment_character(self):
        # an '&' outside of an environment we know how to lay out simply leaves
        # a little space
        self.assertEqual(convert(r'a&b'), 'a   b')


# ------------------------------------------------------------------------------
# Escaped characters, ligatures, quotation marks and dashes
# ------------------------------------------------------------------------------

class TestEscapedCharacters(unittest.TestCase):
    r"""
    The macros that stand for a character which cannot be written on its own.
    """

    def test_reserved_characters(self):
        # the characters that LaTeX gives a meaning of its own and that have to
        # be escaped to be written literally
        self.assertEqual(convert(r'\&'), '&')
        self.assertEqual(convert(r'\$'), '$')
        self.assertEqual(convert(r'\{'), '{')
        self.assertEqual(convert(r'\}'), '}')
        self.assertEqual(convert(r'\%'), '%')
        self.assertEqual(convert(r'\#'), '#')
        self.assertEqual(convert(r'\_'), '_')

    def test_backslash(self):
        self.assertEqual(convert(r'\backslash'), '\\')
        self.assertEqual(convert(r'\textbackslash'), '\\')

    def test_soft_hyphen(self):
        self.assertEqual(convert(r'a\-b'), u'a\N{SOFT HYPHEN}b')


class TestLigaturesAndLetters(unittest.TestCase):
    r"""
    The letters and ligatures that LaTeX writes with a macro.
    """

    def test_ligatures(self):
        self.assertEqual(convert(r'\oe '), u'\N{LATIN SMALL LIGATURE OE}')
        self.assertEqual(convert(r'\OE '), u'\N{LATIN CAPITAL LIGATURE OE}')
        self.assertEqual(convert(r'\ae '), u'\N{LATIN SMALL LETTER AE}')
        self.assertEqual(convert(r'\AE '), u'\N{LATIN CAPITAL LETTER AE}')

    def test_nordic_letters(self):
        self.assertEqual(convert(r'\aa '),
                         u'\N{LATIN SMALL LETTER A WITH RING ABOVE}')
        self.assertEqual(convert(r'\AA '),
                         u'\N{LATIN CAPITAL LETTER A WITH RING ABOVE}')
        self.assertEqual(convert(r'\o '), u'\N{LATIN SMALL LETTER O WITH STROKE}')
        self.assertEqual(convert(r'\O '),
                         u'\N{LATIN CAPITAL LETTER O WITH STROKE}')

    def test_sharp_s_and_l_with_stroke(self):
        self.assertEqual(convert(r'\ss '), u'\N{LATIN SMALL LETTER SHARP S}')
        self.assertEqual(convert(r'\l '), u'\N{LATIN SMALL LETTER L WITH STROKE}')
        self.assertEqual(convert(r'\L '),
                         u'\N{LATIN CAPITAL LETTER L WITH STROKE}')

    def test_dotless_letters(self):
        self.assertEqual(convert(r'\i '), u'\N{LATIN SMALL LETTER DOTLESS I}')
        self.assertEqual(convert(r'\j '), u'\N{LATIN SMALL LETTER DOTLESS J}')

    def test_other_national_letters(self):
        self.assertEqual(convert(r'\DH '), u'\N{LATIN CAPITAL LETTER ETH}')
        self.assertEqual(convert(r'\dh '), u'\N{LATIN SMALL LETTER ETH}')
        self.assertEqual(convert(r'\TH '), u'\N{LATIN CAPITAL LETTER THORN}')
        self.assertEqual(convert(r'\th '), u'\N{LATIN SMALL LETTER THORN}')
        self.assertEqual(convert(r'\DJ '),
                         u'\N{LATIN CAPITAL LETTER D WITH STROKE}')
        self.assertEqual(convert(r'\dj '),
                         u'\N{LATIN SMALL LETTER D WITH STROKE}')
        self.assertEqual(convert(r'\IJ '), u'\N{LATIN CAPITAL LIGATURE IJ}')
        self.assertEqual(convert(r'\ij '), u'\N{LATIN SMALL LIGATURE IJ}')
        self.assertEqual(convert(r'\NG '), u'\N{LATIN CAPITAL LETTER ENG}')
        self.assertEqual(convert(r'\ng '), u'\N{LATIN SMALL LETTER ENG}')


class TestQuotationMarksAndDashes(unittest.TestCase):
    r"""
    The quotation marks and dashes, both as macros and as the "specials" that
    recognize LaTeX's traditional spellings in the source.
    """

    def test_quotation_mark_macros(self):
        self.assertEqual(convert(r'\textquoteleft '),
                         u'\N{LEFT SINGLE QUOTATION MARK}')
        self.assertEqual(convert(r'\textquoteright '),
                         u'\N{RIGHT SINGLE QUOTATION MARK}')
        self.assertEqual(convert(r'\textquotedblleft '),
                         u'\N{LEFT DOUBLE QUOTATION MARK}')
        self.assertEqual(convert(r'\textquotedblright '),
                         u'\N{RIGHT DOUBLE QUOTATION MARK}')

    def test_dash_macros(self):
        self.assertEqual(convert(r'\textendash '), u'\N{EN DASH}')
        self.assertEqual(convert(r'\textemdash '), u'\N{EM DASH}')

    def test_double_quotation_mark_specials(self):
        self.assertEqual(convert("``x''"),
                         u'\N{LEFT DOUBLE QUOTATION MARK}x'
                         u'\N{RIGHT DOUBLE QUOTATION MARK}')

    def test_dash_specials(self):
        self.assertEqual(convert('a--b'), u'a\N{EN DASH}b')
        self.assertEqual(convert('a---b'), u'a\N{EM DASH}b')

    def test_tie_special(self):
        # an unbreakable space in the source becomes an unbreakable space in
        # the output
        self.assertEqual(convert('a~b'), u'a\N{NO-BREAK SPACE}b')

    def test_inverted_punctuation_specials(self):
        self.assertEqual(convert('!`'), u'\N{INVERTED EXCLAMATION MARK}')
        self.assertEqual(convert('?`'), u'\N{INVERTED QUESTION MARK}')


# ------------------------------------------------------------------------------
# Environments
# ------------------------------------------------------------------------------

class TestListEnvironments(unittest.TestCase):
    r"""
    The list environments and the `\item` macro as the definitions wire them
    up.
    """

    def test_itemize(self):
        self.assertEqual(convert(r'\begin{itemize}\item a\item b\end{itemize}'),
                         u'\n  \N{BULLET} a\n  \N{BULLET} b\n')

    def test_enumerate(self):
        self.assertEqual(
            convert(r'\begin{enumerate}\item a\item b\end{enumerate}'),
            '\n  1. a\n  2. b\n'
        )

    def test_description(self):
        # the optional argument of '\item' is the term being described
        self.assertEqual(
            convert(r'\begin{description}\item[Foo] a\end{description}'),
            '\n  Foo a\n'
        )

    def test_list(self):
        self.assertEqual(convert(r'\begin{list}{}{}\item a\end{list}'),
                         u'\n  \N{BULLET} a\n')

    def test_exenumerate(self):
        self.assertEqual(convert(r'\begin{exenumerate}\item a\end{exenumerate}'),
                         '\n  1. a\n')

    def test_nested_lists_change_the_bullet(self):
        self.assertEqual(
            convert(r'\begin{itemize}\item a'
                    r'\begin{itemize}\item b\end{itemize}\end{itemize}'),
            u'\n  \N{BULLET} a\n    \N{EN DASH} b\n'
        )

    def test_item_outside_of_a_known_list_environment(self):
        # a bare '\item' is rendered by the '\item' macro definition itself
        self.assertEqual(convert(r'\item x'), u'\n  \N{BULLET} x')


class TestTextBlockEnvironments(unittest.TestCase):
    r"""
    The environments that only set their contents apart, or that are simply
    transparent.
    """

    def test_centering_environments(self):
        self.assertEqual(convert(r'\begin{center}hello\end{center}'),
                         '\nhello\n')
        self.assertEqual(convert(r'\begin{flushleft}hello\end{flushleft}'),
                         '\nhello\n')
        self.assertEqual(convert(r'\begin{flushright}hello\end{flushright}'),
                         '\nhello\n')

    def test_floats_are_transparent(self):
        self.assertEqual(convert(r'\begin{figure}hi\end{figure}'), 'hi')
        self.assertEqual(convert(r'\begin{table}hi\end{table}'), 'hi')

    def test_subequations_is_transparent(self):
        self.assertEqual(
            convert(r'\begin{subequations}'
                    r'\begin{equation}a\end{equation}\end{subequations}'),
            u'\n    \U0001D44E\n'
        )


class TestEquationEnvironments(unittest.TestCase):
    r"""
    The displayed equation environments, all of which are laid out the same
    way: on their own lines, indented.
    """

    def test_equation(self):
        self.assertEqual(convert_plain(r'\begin{equation}a=b\end{equation}'),
                         '\n    a=b\n')

    def test_equation_star(self):
        self.assertEqual(convert_plain(r'\begin{equation*}a=b\end{equation*}'),
                         '\n    a=b\n')

    def test_align_and_its_starred_form(self):
        self.assertEqual(convert(r'\begin{align}a&=b\\c&=d\end{align}'),
                         u'\n    \U0001D44E   = \U0001D44F'
                         u'\n    \U0001D450   = \U0001D451\n')
        self.assertEqual(convert(r'\begin{align*}a&=b\end{align*}'),
                         u'\n    \U0001D44E   = \U0001D44F\n')

    def test_gather_and_multline(self):
        self.assertEqual(convert(r'\begin{gather}a\end{gather}'),
                         u'\n    \U0001D44E\n')
        self.assertEqual(convert(r'\begin{gather*}a\end{gather*}'),
                         u'\n    \U0001D44E\n')
        self.assertEqual(convert(r'\begin{multline}a\end{multline}'),
                         u'\n    \U0001D44E\n')
        self.assertEqual(convert(r'\begin{multline*}a\end{multline*}'),
                         u'\n    \U0001D44E\n')

    def test_eqnarray(self):
        self.assertEqual(convert(r'\begin{eqnarray}a&=&b\end{eqnarray}'),
                         u'\n    \U0001D44E   =   \U0001D44F\n')
        self.assertEqual(convert(r'\begin{eqnarray*}a&=&b\end{eqnarray*}'),
                         u'\n    \U0001D44E   =   \U0001D44F\n')

    def test_dmath_from_the_breqn_package(self):
        self.assertEqual(convert_plain(r'\begin{dmath}a=b\end{dmath}'),
                         '\n    a=b\n')
        self.assertEqual(convert_plain(r'\begin{dmath*}a=b\end{dmath*}'),
                         '\n    a=b\n')

    def test_equation_contents_are_in_math_mode(self):
        self.assertEqual(convert(r'\begin{equation}a=b\end{equation}'),
                         u'\n    \U0001D44E = \U0001D44F\n')


class TestMatrixEnvironments(unittest.TestCase):
    r"""
    The matrix-like environments.  They are all laid out the same way, with the
    columns separated by spaces and the rows by semicolons; the shape of the
    delimiters that each of them would draw in print is not reproduced.
    """

    def test_pmatrix(self):
        self.assertEqual(
            convert_plain(r'$\begin{pmatrix}a&b\\c&d\end{pmatrix}$'),
            '[ a b; c d ]'
        )

    def test_bmatrix(self):
        self.assertEqual(
            convert_plain(r'$\begin{bmatrix}a&b\\c&d\end{bmatrix}$'),
            '[ a b; c d ]'
        )

    def test_array(self):
        self.assertEqual(
            convert_plain(r'$\begin{array}{cc}a&b\\c&d\end{array}$'),
            '[ a b; c d ]'
        )

    def test_small_matrix_variants(self):
        self.assertEqual(
            convert_plain(r'$\begin{smallmatrix}a&b\\c&d\end{smallmatrix}$'),
            '[ a b; c d ]'
        )
        self.assertEqual(
            convert_plain(r'$\begin{psmallmatrix}a&b\\c&d\end{psmallmatrix}$'),
            '[ a b; c d ]'
        )
        self.assertEqual(
            convert_plain(r'$\begin{bsmallmatrix}a&b\\c&d\end{bsmallmatrix}$'),
            '[ a b; c d ]'
        )

    def test_matrix_entries_are_in_math_mode(self):
        self.assertEqual(
            convert(r'$\begin{pmatrix}a&b\\c&d\end{pmatrix}$'),
            u'[ \U0001D44E \U0001D44F; \U0001D450 \U0001D451 ]'
        )


# ------------------------------------------------------------------------------
# Symbols
# ------------------------------------------------------------------------------

class TestRelationSymbols(unittest.TestCase):
    r"""
    A representative sample of the relation symbols.
    """

    def test_order_relations(self):
        self.assertEqual(convert(r'\leq '), u'\N{LESS-THAN OR EQUAL TO}')
        self.assertEqual(convert(r'\geq '), u'\N{GREATER-THAN OR EQUAL TO}')
        self.assertEqual(convert(r'\le '), u'\N{LESS-THAN OR EQUAL TO}')
        self.assertEqual(convert(r'\ge '), u'\N{GREATER-THAN OR EQUAL TO}')
        self.assertEqual(convert(r'\ll '), u'\N{MUCH LESS-THAN}')
        self.assertEqual(convert(r'\gg '), u'\N{MUCH GREATER-THAN}')
        self.assertEqual(convert(r'\leqslant '),
                         u'\N{LESS-THAN OR SLANTED EQUAL TO}')
        self.assertEqual(convert(r'\geqslant '),
                         u'\N{GREATER-THAN OR SLANTED EQUAL TO}')

    def test_equalities(self):
        self.assertEqual(convert(r'\neq '), u'\N{NOT EQUAL TO}')
        self.assertEqual(convert(r'\ne '), u'\N{NOT EQUAL TO}')
        self.assertEqual(convert(r'\equiv '), u'\N{IDENTICAL TO}')
        self.assertEqual(convert(r'\approx '), u'\N{ALMOST EQUAL TO}')
        self.assertEqual(convert(r'\simeq '), u'\N{ASYMPTOTICALLY EQUAL TO}')
        self.assertEqual(convert(r'\sim '), u'\N{TILDE OPERATOR}')

    def test_negated_order_relations(self):
        self.assertEqual(convert(r'\nless '), u'\N{NOT LESS-THAN}')
        self.assertEqual(convert(r'\ngtr '), u'\N{NOT GREATER-THAN}')
        self.assertEqual(convert(r'\nleq '),
                         u'\N{NEITHER LESS-THAN NOR EQUAL TO}')
        self.assertEqual(convert(r'\ngeq '),
                         u'\N{NEITHER GREATER-THAN NOR EQUAL TO}')

    def test_precedence_relations(self):
        self.assertEqual(convert(r'\prec '), u'\N{PRECEDES}')
        self.assertEqual(convert(r'\succ '), u'\N{SUCCEEDS}')
        self.assertEqual(convert(r'\preceq '), u'\N{PRECEDES OR EQUAL TO}')
        self.assertEqual(convert(r'\succeq '), u'\N{SUCCEEDS OR EQUAL TO}')

    def test_set_relations(self):
        self.assertEqual(convert(r'\in '), u'\N{ELEMENT OF}')
        self.assertEqual(convert(r'\notin '), u'\N{NOT AN ELEMENT OF}')
        self.assertEqual(convert(r'\ni '), u'\N{CONTAINS AS MEMBER}')
        self.assertEqual(convert(r'\subset '), u'\N{SUBSET OF}')
        self.assertEqual(convert(r'\supset '), u'\N{SUPERSET OF}')
        self.assertEqual(convert(r'\subseteq '), u'\N{SUBSET OF OR EQUAL TO}')
        self.assertEqual(convert(r'\supseteq '), u'\N{SUPERSET OF OR EQUAL TO}')
        self.assertEqual(convert(r'\nsubseteq '),
                         u'\N{NEITHER A SUBSET OF NOR EQUAL TO}')
        self.assertEqual(convert(r'\subsetneq '),
                         u'\N{SUBSET OF WITH NOT EQUAL TO}')


class TestOperatorSymbols(unittest.TestCase):
    r"""
    A representative sample of the operator and arrow symbols.
    """

    def test_arithmetic_operators(self):
        self.assertEqual(convert(r'\pm '), u'\N{PLUS-MINUS SIGN}')
        self.assertEqual(convert(r'\mp '), u'\N{MINUS-OR-PLUS SIGN}')
        self.assertEqual(convert(r'\times '), u'\N{MULTIPLICATION SIGN}')
        self.assertEqual(convert(r'\cdot '), u'\N{MIDDLE DOT}')
        self.assertEqual(convert(r'\ast '), u'\N{ASTERISK OPERATOR}')
        self.assertEqual(convert(r'\circ '), u'\N{RING OPERATOR}')
        self.assertEqual(convert(r'\bullet '), u'\N{BULLET OPERATOR}')

    def test_circled_operators(self):
        self.assertEqual(convert(r'\otimes '), u'\N{CIRCLED TIMES}')
        self.assertEqual(convert(r'\oplus '), u'\N{CIRCLED PLUS}')
        # the large forms have no separate character to render them with
        self.assertEqual(convert(r'\bigotimes '), u'\N{CIRCLED TIMES}')
        self.assertEqual(convert(r'\bigoplus '), u'\N{CIRCLED PLUS}')

    def test_large_operators(self):
        self.assertEqual(convert(r'\sum '), u'\N{N-ARY SUMMATION}')
        self.assertEqual(convert(r'\prod '), u'\N{N-ARY PRODUCT}')
        self.assertEqual(convert(r'\coprod '), u'\N{N-ARY COPRODUCT}')

    def test_integrals(self):
        self.assertEqual(convert(r'\int '), u'\N{INTEGRAL}')
        self.assertEqual(convert(r'\iint '), u'\N{DOUBLE INTEGRAL}')
        self.assertEqual(convert(r'\iiint '), u'\N{TRIPLE INTEGRAL}')
        self.assertEqual(convert(r'\oint '), u'\N{CONTOUR INTEGRAL}')

    def test_set_operators(self):
        self.assertEqual(convert(r'\cap '), u'\N{INTERSECTION}')
        self.assertEqual(convert(r'\cup '), u'\N{UNION}')
        self.assertEqual(convert(r'\setminus '), u'\N{SET MINUS}')
        self.assertEqual(convert(r'\smallsetminus '), u'\N{SET MINUS}')

    def test_logical_operators(self):
        self.assertEqual(convert(r'\wedge '), u'\N{LOGICAL AND}')
        self.assertEqual(convert(r'\land '), u'\N{LOGICAL AND}')
        self.assertEqual(convert(r'\vee '), u'\N{LOGICAL OR}')
        self.assertEqual(convert(r'\lor '), u'\N{LOGICAL OR}')

    def test_arrows(self):
        self.assertEqual(convert(r'\to '), u'\N{RIGHTWARDS ARROW}')
        self.assertEqual(convert(r'\rightarrow '), u'\N{RIGHTWARDS ARROW}')
        self.assertEqual(convert(r'\leftarrow '), u'\N{LEFTWARDS ARROW}')
        self.assertEqual(convert(r'\uparrow '), u'\N{UPWARDS ARROW}')
        self.assertEqual(convert(r'\downarrow '), u'\N{DOWNWARDS ARROW}')
        self.assertEqual(convert(r'\longrightarrow '),
                         u'\N{LONG RIGHTWARDS ARROW}')
        self.assertEqual(convert(r'\longleftarrow '),
                         u'\N{LONG LEFTWARDS ARROW}')


class TestMiscellaneousMathSymbols(unittest.TestCase):
    r"""
    The remaining symbols: the quantifiers, the constants, the ellipses and the
    delimiters.
    """

    def test_quantifiers_and_logic(self):
        self.assertEqual(convert(r'\forall '), u'\N{FOR ALL}')
        self.assertEqual(convert(r'\exists '), u'\N{THERE EXISTS}')
        self.assertEqual(convert(r'\nexists '), u'\N{THERE DOES NOT EXIST}')
        self.assertEqual(convert(r'\complement '), u'\N{COMPLEMENT}')

    def test_analysis_symbols(self):
        self.assertEqual(convert(r'\partial '), u'\N{PARTIAL DIFFERENTIAL}')
        self.assertEqual(convert(r'\nabla '), u'\N{NABLA}')
        self.assertEqual(convert(r'\infty '), u'\N{INFINITY}')
        self.assertEqual(convert(r'\propto '), u'\N{PROPORTIONAL TO}')

    def test_letterlike_constants(self):
        self.assertEqual(convert(r'\hbar '),
                         u'\N{LATIN SMALL LETTER H WITH STROKE}')
        self.assertEqual(convert(r'\ell '), u'\N{SCRIPT SMALL L}')
        self.assertEqual(convert(r'\aleph '), u'\N{ALEF SYMBOL}')

    def test_empty_set(self):
        self.assertEqual(convert(r'\emptyset '), u'\N{EMPTY SET}')
        self.assertEqual(convert(r'\varnothing '), u'\N{EMPTY SET}')

    def test_parallel(self):
        self.assertEqual(convert(r'\parallel '), u'\N{PARALLEL TO}')
        self.assertEqual(convert(r'\nparallel '), u'\N{NOT PARALLEL TO}')

    def test_ellipses(self):
        self.assertEqual(convert(r'\ldots '), u'\N{HORIZONTAL ELLIPSIS}')
        self.assertEqual(convert(r'\cdots '), u'\N{MIDLINE HORIZONTAL ELLIPSIS}')
        self.assertEqual(convert(r'\vdots '), u'\N{VERTICAL ELLIPSIS}')
        self.assertEqual(convert(r'\ddots '),
                         u'\N{DOWN RIGHT DIAGONAL ELLIPSIS}')
        self.assertEqual(convert(r'\iddots '), u'\N{UP RIGHT DIAGONAL ELLIPSIS}')

    def test_amsmath_ellipsis_spellings(self):
        # the '\dots...' family names the ellipsis by what surrounds it, which
        # plain text has no way of distinguishing
        self.assertEqual(convert(r'\dots '), u'\N{HORIZONTAL ELLIPSIS}')
        self.assertEqual(convert(r'\dotsc '), u'\N{HORIZONTAL ELLIPSIS}')
        self.assertEqual(convert(r'\dotsb '), u'\N{HORIZONTAL ELLIPSIS}')
        self.assertEqual(convert(r'\dotsm '), u'\N{HORIZONTAL ELLIPSIS}')
        self.assertEqual(convert(r'\dotsi '), u'\N{HORIZONTAL ELLIPSIS}')
        self.assertEqual(convert(r'\dotso '), u'\N{HORIZONTAL ELLIPSIS}')

    def test_angle_brackets(self):
        self.assertEqual(convert(r'\langle '),
                         u'\N{MATHEMATICAL LEFT ANGLE BRACKET}')
        self.assertEqual(convert(r'\rangle '),
                         u'\N{MATHEMATICAL RIGHT ANGLE BRACKET}')

    def test_vertical_bars(self):
        self.assertEqual(convert(r'\vert '), '|')
        self.assertEqual(convert(r'\lvert '), '|')
        self.assertEqual(convert(r'\rvert '), '|')
        self.assertEqual(convert(r'\mid '), '|')
        self.assertEqual(convert(r'\Vert '), u'\N{DOUBLE VERTICAL LINE}')
        self.assertEqual(convert(r'\lVert '), u'\N{DOUBLE VERTICAL LINE}')
        self.assertEqual(convert(r'\rVert '), u'\N{DOUBLE VERTICAL LINE}')
        self.assertEqual(convert(r'\nmid '), u'\N{DOES NOT DIVIDE}')

    def test_prime_and_daggers(self):
        self.assertEqual(convert(r'\prime '), "'")
        self.assertEqual(convert(r'\dag '), u'\N{DAGGER}')
        self.assertEqual(convert(r'\dagger '), u'\N{DAGGER}')

    def test_ensuremath_keeps_its_argument(self):
        self.assertEqual(convert_plain(r'\ensuremath{x}'), 'x')
        self.assertEqual(convert_plain(r'$\ensuremath{x}$'), 'x')

    def test_decorations_are_dropped(self):
        # a bar, a brace or an arrow drawn over an expression cannot be shown
        # in plain text, so the expression is kept and the decoration dropped
        self.assertEqual(convert_plain(r'$\overline{x}$'), 'x')
        self.assertEqual(convert_plain(r'$\underline{x}$'), 'x')
        self.assertEqual(convert_plain(r'$\widehat{x}$'), 'x')
        self.assertEqual(convert_plain(r'$\widetilde{x}$'), 'x')
        self.assertEqual(convert_plain(r'$\overbrace{x}$'), 'x')
        self.assertEqual(convert_plain(r'$\underbrace{x}$'), 'x')
        self.assertEqual(convert_plain(r'$\overrightarrow{x}$'), 'x')
        self.assertEqual(convert_plain(r'$\underleftarrow{x}$'), 'x')


class TestSuperscriptsAndSubscripts(unittest.TestCase):
    r"""
    The '^' and '_' specials.  In a formula they pick up an argument, which is
    rendered with the unicode superscript or subscript characters whenever
    unicode has them; in text they have no argument and stand for themselves.
    """

    def test_superscript_with_unicode_characters(self):
        self.assertEqual(convert_plain(r'$x^2$'), u'x\N{SUPERSCRIPT TWO}')

    def test_subscript_with_unicode_characters(self):
        self.assertEqual(convert_plain(r'$x_i$'), u'x\N{LATIN SUBSCRIPT SMALL LETTER I}')

    def test_superscript_of_several_characters(self):
        self.assertEqual(convert_plain(r'$x^{abc}$'),
                         u'x\N{MODIFIER LETTER SMALL A}'
                         u'\N{MODIFIER LETTER SMALL B}'
                         u'\N{MODIFIER LETTER SMALL C}')

    def test_subscript_that_unicode_cannot_render(self):
        # unicode has no subscript 'b' or 'c', so the whole lookup fails and we
        # fall back onto LaTeX's own notation
        self.assertEqual(convert_plain(r'$x_{abc}$'), 'x_(abc)')

    def test_the_characters_stand_for_themselves_in_text_mode(self):
        self.assertEqual(convert('a^b'), 'a^b')
        self.assertEqual(convert('a_b'), 'a_b')


class TestQuantumInformationMacros(unittest.TestCase):
    r"""
    The bra-ket notation of the 'nonstandard-qit' category.
    """

    def test_ket(self):
        self.assertEqual(convert(r'$\ket{\psi}$'),
                         u'|\N{GREEK SMALL LETTER PSI}'
                         u'\N{MATHEMATICAL RIGHT ANGLE BRACKET}')

    def test_bra(self):
        self.assertEqual(convert(r'$\bra{\psi}$'),
                         u'\N{MATHEMATICAL LEFT ANGLE BRACKET}'
                         u'\N{GREEK SMALL LETTER PSI}|')

    def test_braket(self):
        self.assertEqual(convert(r'$\braket{\phi}{\psi}$'),
                         u'\N{MATHEMATICAL LEFT ANGLE BRACKET}'
                         u'\N{GREEK PHI SYMBOL}|\N{GREEK SMALL LETTER PSI}'
                         u'\N{MATHEMATICAL RIGHT ANGLE BRACKET}')

    def test_ketbra(self):
        self.assertEqual(convert(r'$\ketbra{\phi}{\psi}$'),
                         u'|\N{GREEK PHI SYMBOL}'
                         u'\N{MATHEMATICAL RIGHT ANGLE BRACKET}'
                         u'\N{MATHEMATICAL LEFT ANGLE BRACKET}'
                         u'\N{GREEK SMALL LETTER PSI}|')

    def test_identity_operator(self):
        # the double-struck capital I is the convention these definitions use
        # for the identity operator
        self.assertEqual(convert(r'$\id$'),
                         u'\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}')
        self.assertEqual(convert(r'$\Ident$'),
                         u'\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}')


class TestEthuebungMacros(unittest.TestCase):
    r"""
    The macros of the 'latex-ethuebung' category, which come from a set of
    exercise sheets and are kept for backwards compatibility.
    """

    def test_hint(self):
        self.assertEqual(convert(r'\hint{look at the appendix}'),
                         'Hint: look at the appendix')

    def test_hints(self):
        self.assertEqual(convert(r'\hints{look}'), 'Hints: look')

    def test_hinweis(self):
        self.assertEqual(convert(r'\hinweis{schau}'), 'Hinweis: schau')

    def test_hinweise(self):
        self.assertEqual(convert(r'\hinweise{schau}'), 'Hinweise: schau')

    def test_exercise(self):
        self.assertEqual(convert(r'\exercise{Do it}'), '\nDo it\n')

    def test_uebung(self):
        self.assertEqual(convert(r'\uebung{Do it}'), '\nDo it\n')

    def test_exercise_with_its_optional_argument(self):
        # the optional argument follows the mandatory one for these macros
        self.assertEqual(convert(r'\exercise{Do it}[extra]'),
                         '\nDo it\n[extra]\n')


class TestAdvancedSymbolMacros(unittest.TestCase):
    r"""
    A sample of the 'advanced-symbols' category, the definitions that mirror
    the conversion rules of `pylatexenc.latexencode`.
    """

    def test_currency_signs(self):
        self.assertEqual(convert(r'\texteuro '), u'\N{EURO SIGN}')
        self.assertEqual(convert(r'\textsterling '), u'\N{POUND SIGN}')
        self.assertEqual(convert(r'\textcent '), u'\N{CENT SIGN}')
        self.assertEqual(convert(r'\textyen '), u'\N{YEN SIGN}')
        self.assertEqual(convert(r'\textcurrency '), u'\N{CURRENCY SIGN}')

    def test_typographic_signs(self):
        self.assertEqual(convert(r'\textcopyright '), u'\N{COPYRIGHT SIGN}')
        self.assertEqual(convert(r'\textregistered '), u'\N{REGISTERED SIGN}')
        self.assertEqual(convert(r'\textsection '), u'\N{SECTION SIGN}')
        self.assertEqual(convert(r'\textparagraph '), u'\N{PILCROW SIGN}')
        self.assertEqual(convert(r'\textdegree '), u'\N{DEGREE SIGN}')
        self.assertEqual(convert(r'\textbrokenbar '), u'\N{BROKEN BAR}')

    def test_inverted_punctuation_macros(self):
        self.assertEqual(convert(r'\textexclamdown '),
                         u'\N{INVERTED EXCLAMATION MARK}')
        self.assertEqual(convert(r'\textquestiondown '),
                         u'\N{INVERTED QUESTION MARK}')

    def test_guillemets(self):
        self.assertEqual(convert(r'\guillemotleft '),
                         u'\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}')
        self.assertEqual(convert(r'\guillemotright '),
                         u'\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}')

    def test_vulgar_fractions(self):
        self.assertEqual(convert(r'\textonequarter '),
                         u'\N{VULGAR FRACTION ONE QUARTER}')
        self.assertEqual(convert(r'\textonehalf '),
                         u'\N{VULGAR FRACTION ONE HALF}')
        self.assertEqual(convert(r'\textthreequarters '),
                         u'\N{VULGAR FRACTION THREE QUARTERS}')

    def test_superscript_digits(self):
        self.assertEqual(convert(r'\textonesuperior '), u'\N{SUPERSCRIPT ONE}')
        self.assertEqual(convert(r'\texttwosuperior '), u'\N{SUPERSCRIPT TWO}')
        self.assertEqual(convert(r'\textthreesuperior '),
                         u'\N{SUPERSCRIPT THREE}')

    def test_arithmetic_signs_in_text(self):
        self.assertEqual(convert(r'\texttimes '), u'\N{MULTIPLICATION SIGN}')
        self.assertEqual(convert(r'\textdiv '), u'\N{DIVISION SIGN}')
        self.assertEqual(convert(r'\textpm '), u'\N{PLUS-MINUS SIGN}')
        self.assertEqual(convert(r'\textmp '), u'\N{MINUS-OR-PLUS SIGN}')
        self.assertEqual(convert(r'\textlnot '), u'\N{NOT SIGN}')

    def test_ordinal_indicators(self):
        self.assertEqual(convert(r'\textordfeminine '),
                         u'\N{FEMININE ORDINAL INDICATOR}')
        self.assertEqual(convert(r'\textordmasculine '),
                         u'\N{MASCULINE ORDINAL INDICATOR}')

    def test_phonetic_letters(self):
        self.assertEqual(convert(r'\textschwa '), u'\N{LATIN SMALL LETTER SCHWA}')
        self.assertEqual(convert(r'\textglotstop '),
                         u'\N{LATIN LETTER GLOTTAL STOP}')
        self.assertEqual(convert(r'\textflorin '),
                         u'\N{LATIN SMALL LETTER F WITH HOOK}')
        self.assertEqual(convert(r'\textmu '), u'\N{MICRO SIGN}')

    def test_greek_symbol_variants(self):
        self.assertEqual(convert(r'\varkappa '), u'\N{GREEK KAPPA SYMBOL}')
        self.assertEqual(convert(r'\backepsilon '),
                         u'\N{GREEK REVERSED LUNATE EPSILON SYMBOL}')

    def test_cyrillic_letters(self):
        self.assertEqual(convert(r'\CYRA '), u'\N{CYRILLIC CAPITAL LETTER A}')
        self.assertEqual(convert(r'\CYRYO '), u'\N{CYRILLIC CAPITAL LETTER IO}')

    def test_spacing_accent_characters(self):
        # these stand for the accent characters themselves, not for an accent
        # placed on a letter
        self.assertEqual(convert(r'\textasciidieresis '), u'\N{DIAERESIS}')
        self.assertEqual(convert(r'\textasciimacron '), u'\N{MACRON}')
        self.assertEqual(convert(r'\textasciiacute '), u'\N{ACUTE ACCENT}')
        self.assertEqual(convert(r'\textasciicaron '), u'\N{CARON}')
        self.assertEqual(convert(r'\textasciibreve '), u'\N{BREVE}')
        self.assertEqual(convert(r'\textacutedbl '), u'\N{DOUBLE ACUTE ACCENT}')
        self.assertEqual(convert(r'\textasciitilde '), u'\N{TILDE}')
