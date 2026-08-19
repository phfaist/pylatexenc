# -*- coding: utf-8 -*-

#
# Tests for the conversion engine and the public interface of
# `pylatexenc.latex2text` — the code that lives in
# `pylatexenc/latex2text/__init__.py`.
#
# The catalogue of default macro and environment replacements (the data in
# `pylatexenc/latex2text/_defaultspecs.py`) is exercised by a separate test
# file; here we only reach for a handful of well known macros where an engine
# feature cannot reasonably be shown without one.
#
# This file is also compiled to JavaScript and run under node, so it sticks to
# the restricted subset of python that Transcrypt understands: no percent-style
# string formatting, no f-strings, no default argument that shadows a name of
# the enclosing scope, and no module that the JavaScript build does not have.
# Anything that cannot possibly run there — the file system, the `warnings`
# module — is placed between the TEST_PYLATEXENC_SKIP markers, which the source
# preprocessor comments out for that build.
#

import unittest

import re
import logging

logger = logging.getLogger(__name__)


from pylatexenc import macrospec
from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latexnodes import parsers as latexnodes_parsers
# `std_macro()` and `std_environment()` are only re-exported by the
# `macrospec` package as part of its `pylatexenc 2` compatibility layer, which
# the JavaScript build leaves out; import them from the module that defines them
from pylatexenc.macrospec._spechelpers import (
    std_macro,
    std_environment,
)
from pylatexenc.macrospec import (
    SpecialsSpec,
)

from pylatexenc import latex2text
from pylatexenc.latex2text import (
    LatexNodes2Text,
    MacroTextSpec,
    EnvironmentTextSpec,
    SpecialsTextSpec,
    TextConversionState,
    fmt_math_text_style,
    fmt_subsuperscript_text,
    fmt_math_expression_in_delimiters,
    default_math_expression_in,
)

# The JavaScript build is made without the functions that build the default
# specification databases, and ships those databases as modules of their own
# that calling code imports explicitly.  So we import them from where they are
# defined and hand them to every object we build, rather than relying on the
# convenience functions that only the python build has.
from pylatexenc.latexwalker._get_defaultspecs import (
    get_default_latex_context_db as get_latexwalker_default_context_db
)
from pylatexenc.latex2text._get_defaultspecs import (
    get_default_latex_context_db as get_latex2text_default_context_db
)


### BEGIN_TEST_PYLATEXENC_SKIP
import os
import os.path
import shutil
import tempfile
import warnings
### END_TEST_PYLATEXENC_SKIP


# ------------------------------------------------------------------------------
#
# Helpers.
#


def make_l2t(**options):
    r"""A `LatexNodes2Text` object that knows the default text replacements."""
    return LatexNodes2Text(latex_context=get_latex2text_default_context_db(),
                           **options)

def latex_to_text(latex, **options):
    r"""Convert `latex` with the default specifications on both sides: the
    parser needs the latexwalker specifications to know how to read the code,
    and the converter needs the latex2text ones to know what to write."""
    return make_l2t(**options).latex_to_text(
        latex, latex_context=get_latexwalker_default_context_db())


def make_custom_l2t(macros=None, environments=None, specials=None, **options):
    r"""A `LatexNodes2Text` object whose latex context holds only the given text
    replacement specifications, so that a test that is about the replacement
    machinery itself does not depend on the default catalogue."""
    db = macrospec.LatexContextDb()
    db.add_context_category(
        'tests',
        macros=(macros if macros is not None else []),
        environments=(environments if environments is not None else []),
        specials=(specials if specials is not None else []),
    )
    return LatexNodes2Text(latex_context=db, **options)

def make_custom_walker_db(macros=None, environments=None, specials=None):
    r"""The matching latex context for the parser side of `make_custom_l2t()`."""
    db = macrospec.LatexContextDb()
    db.add_context_category(
        'tests',
        macros=(macros if macros is not None else []),
        environments=(environments if environments is not None else []),
        specials=(specials if specials is not None else []),
    )
    return db


#
# The engine writes the letters of a formula, and the argument of the font
# style macros, with the unicode "mathematical alphanumeric symbols".  In most
# editors those look exactly like the ordinary latin letters, so the expected
# values below are built out of plain ASCII with the two tables here instead of
# being spelled out.  The tables are written as literal characters rather than
# computed from code points, so that they do not lean on the very code that is
# being tested; the alphabets themselves are pinned character by character in
# `TestFmtMathTextStyle`.
#

_math_italic_letters = {
    'A': '𝐴', 'B': '𝐵', 'C': '𝐶', 'D': '𝐷', 'E': '𝐸', 'F': '𝐹', 'G': '𝐺',
    'H': '𝐻', 'I': '𝐼', 'J': '𝐽', 'K': '𝐾', 'L': '𝐿', 'M': '𝑀', 'N': '𝑁',
    'O': '𝑂', 'P': '𝑃', 'Q': '𝑄', 'R': '𝑅', 'S': '𝑆', 'T': '𝑇', 'U': '𝑈',
    'V': '𝑉', 'W': '𝑊', 'X': '𝑋', 'Y': '𝑌', 'Z': '𝑍',
    'a': '𝑎', 'b': '𝑏', 'c': '𝑐', 'd': '𝑑', 'e': '𝑒', 'f': '𝑓', 'g': '𝑔',
    'h': 'ℎ', 'i': '𝑖', 'j': '𝑗', 'k': '𝑘', 'l': '𝑙', 'm': '𝑚', 'n': '𝑛',
    'o': '𝑜', 'p': '𝑝', 'q': '𝑞', 'r': '𝑟', 's': '𝑠', 't': '𝑡', 'u': '𝑢',
    'v': '𝑣', 'w': '𝑤', 'x': '𝑥', 'y': '𝑦', 'z': '𝑧',
}

_math_bold_letters = {
    'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆',
    'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍',
    'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔',
    'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
    'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠',
    'h': '𝐡', 'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧',
    'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭', 'u': '𝐮',
    'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳',
}

def mvar(s):
    r"""The plain-ASCII string `s` in math italics, which is the font that the
    letters of a formula are set in by default."""
    return "".join([ _math_italic_letters.get(c, c) for c in s ])

def mbold(s):
    r"""The plain-ASCII string `s` in the bold unicode alphabet, which is what
    ``\textbf{}`` and ``\mathbf{}`` install."""
    return "".join([ _math_bold_letters.get(c, c) for c in s ])



# ------------------------------------------------------------------------------


class TestTextSpecClasses(unittest.TestCase):
    r"""The three specification classes, and in particular the fact that a macro
    is discarded by default while an environment is not."""

    def test_macro_text_spec_fields(self):
        m = MacroTextSpec('foo', simplify_repl='FOO')
        self.assertEqual(m.macroname, 'foo')
        self.assertEqual(m.simplify_repl, 'FOO')
        self.assertIsNone(MacroTextSpec('foo').simplify_repl)

    def test_macro_text_spec_discard_defaults_to_true(self):
        # a macro that we know nothing about is dropped, rather than having its
        # arguments spilled into the output
        self.assertTrue(MacroTextSpec('foo').discard)
        self.assertFalse(MacroTextSpec('foo', discard=False).discard)
        self.assertTrue(MacroTextSpec('foo', discard=True).discard)

    def test_environment_text_spec_fields(self):
        e = EnvironmentTextSpec('bar', simplify_repl='BAR')
        self.assertEqual(e.environmentname, 'bar')
        self.assertEqual(e.simplify_repl, 'BAR')
        self.assertIsNone(EnvironmentTextSpec('bar').simplify_repl)

    def test_environment_text_spec_discard_defaults_to_false(self):
        # an environment we know nothing about still has its body converted
        self.assertFalse(EnvironmentTextSpec('bar').discard)
        self.assertTrue(EnvironmentTextSpec('bar', discard=True).discard)

    def test_specials_text_spec_fields(self):
        s = SpecialsTextSpec('<>', simplify_repl='SPECIAL')
        self.assertEqual(s.specials_chars, '<>')
        self.assertEqual(s.simplify_repl, 'SPECIAL')
        self.assertIsNone(SpecialsTextSpec('<>').simplify_repl)

    def test_macro_discard_in_conversion(self):
        l2t = make_custom_l2t(macros=[ MacroTextSpec('zzz') ])
        wdb = make_custom_walker_db(macros=[ std_macro('zzz', False, 1) ])
        self.assertEqual(l2t.latex_to_text(r'a\zzz{X}b', latex_context=wdb), 'ab')
        # ... and with discard=False the arguments are converted instead
        l2t = make_custom_l2t(macros=[ MacroTextSpec('zzz', discard=False) ])
        self.assertEqual(l2t.latex_to_text(r'a\zzz{X}b', latex_context=wdb), 'aXb')

    def test_environment_discard_in_conversion(self):
        wdb = make_custom_walker_db(environments=[ std_environment('zzz', False, 0) ])
        l2t = make_custom_l2t(environments=[ EnvironmentTextSpec('zzz') ])
        self.assertEqual(
            l2t.latex_to_text(r'a\begin{zzz}X\end{zzz}b', latex_context=wdb), 'aXb')
        # ... and with discard=True the whole environment goes away
        l2t = make_custom_l2t(environments=[ EnvironmentTextSpec('zzz', discard=True) ])
        self.assertEqual(
            l2t.latex_to_text(r'a\begin{zzz}X\end{zzz}b', latex_context=wdb), 'ab')

    def test_unknown_macro_is_discarded(self):
        # a macro with no specification at all behaves like a MacroTextSpec with
        # the default discard=True
        self.assertEqual(latex_to_text(r'a\thereisnosuchmacro b'), 'ab')

    def test_unknown_environment_keeps_its_body(self):
        l2t = make_custom_l2t()
        wdb = make_custom_walker_db(environments=[ std_environment('zzz', False, 0) ])
        self.assertEqual(
            l2t.latex_to_text(r'a\begin{zzz}X\end{zzz}b', latex_context=wdb), 'aXb')

    def test_specials_without_spec_are_left_alone(self):
        l2t = make_custom_l2t()
        wdb = make_custom_walker_db(specials=[ SpecialsSpec('<>') ])
        self.assertEqual(l2t.latex_to_text('a<>b', latex_context=wdb), 'a<>b')



class TestMathModeOption(unittest.TestCase):
    r"""The `math_mode=` option: the values it accepts and the value it rejects."""

    def test_default_is_fancy(self):
        self.assertEqual(make_l2t().math_mode, 'fancy')

    def test_accepted_values(self):
        for value in ('fancy', 'text', 'with-delimiters', 'verbatim', 'remove',):
            self.assertEqual(make_l2t(math_mode=value).math_mode, value)

    def test_rejects_anything_else(self):
        with self.assertRaises(ValueError):
            make_l2t(math_mode='no-such-mode')



class TestMathModeRendering(unittest.TestCase):
    r"""What each math mode makes of an inline formula and of a display formula."""

    def test_fancy(self):
        # the 'fancy' engine ignores the whitespace of the source and puts
        # spaces back where they help the reader; display math is set on lines
        # of its own
        self.assertEqual(latex_to_text(r'a $x+y$ b', math_mode='fancy'),
                         'a ' + mvar('x') + ' + ' + mvar('y') + ' b')
        self.assertEqual(latex_to_text(r'a \[x+y\] b', math_mode='fancy'),
                         'a \n    ' + mvar('x') + ' + ' + mvar('y') + '\n b')
        self.assertEqual(
            latex_to_text(r'a \begin{equation}x+y\end{equation} b',
                          math_mode='fancy'),
            'a \n    ' + mvar('x') + ' + ' + mvar('y') + '\n b')

    def test_text(self):
        # the 'text' engine simply reproduces the contents, whitespace and all
        self.assertEqual(latex_to_text(r'a $x+y$ b', math_mode='text'),
                         'a ' + mvar('x') + '+' + mvar('y') + ' b')
        self.assertEqual(latex_to_text(r'a \[x+y\] b', math_mode='text'),
                         'a \n    ' + mvar('x') + '+' + mvar('y') + '\n b')

    def test_with_delimiters(self):
        # as 'text', but the original delimiters are kept around the contents
        self.assertEqual(latex_to_text(r'a $x+y$ b', math_mode='with-delimiters'),
                         'a $' + mvar('x') + '+' + mvar('y') + '$ b')
        self.assertEqual(latex_to_text(r'a \(x+y\) b', math_mode='with-delimiters'),
                         'a \\(' + mvar('x') + '+' + mvar('y') + '\\) b')
        self.assertEqual(latex_to_text(r'a \[x+y\] b', math_mode='with-delimiters'),
                         'a \\[\n' + mvar('x') + '+' + mvar('y') + '\n\\] b')
        self.assertEqual(
            latex_to_text(r'a \begin{equation}x+y\end{equation} b',
                          math_mode='with-delimiters'),
            'a \\begin{equation}\n' + mvar('x') + '+' + mvar('y')
            + '\n\\end{equation} b')

    def test_verbatim(self):
        # the latex source of the formula is reproduced as it stands
        self.assertEqual(latex_to_text(r'a $x+y$ b', math_mode='verbatim'),
                         'a $x+y$ b')
        self.assertEqual(latex_to_text(r'a \[x+y\] b', math_mode='verbatim'),
                         'a \n\\[x+y\\]\n b')
        self.assertEqual(
            latex_to_text(r'a \begin{equation}x+y\end{equation} b',
                          math_mode='verbatim'),
            'a \n\\begin{equation}x+y\\end{equation}\n b')

    def test_remove(self):
        self.assertEqual(latex_to_text(r'a $x+y$ b', math_mode='remove'), 'a  b')
        self.assertEqual(latex_to_text(r'a \[x+y\] b', math_mode='remove'), 'a  b')
        self.assertEqual(
            latex_to_text(r'a \begin{equation}x+y\end{equation} b',
                          math_mode='remove'),
            'a  b')



class TestOptions(unittest.TestCase):
    r"""The remaining constructor options."""

    # --- keep_comments ---

    def test_comments_are_dropped_by_default(self):
        self.assertEqual(latex_to_text('a % a comment\nb'), 'a \nb')

    def test_keep_comments(self):
        self.assertEqual(latex_to_text('a % a comment\nb', keep_comments=True),
                         'a % a comment\nb')

    def test_keep_comments_false_keeps_the_following_indentation(self):
        # dropping a comment keeps the whitespace that followed it, which
        # preserves the indentation of the next line
        self.assertEqual(latex_to_text('a %c\n   b', keep_comments=False),
                         'a \n   b')

    def test_comments_strict_spaces_drops_the_following_whitespace(self):
        self.assertEqual(
            latex_to_text('a %c\n   b', keep_comments=False,
                          strict_latex_spaces=True),
            'a b')

    def test_keep_comments_strict_spaces_normalizes_to_one_newline(self):
        self.assertEqual(
            latex_to_text('a %c\n   b', keep_comments=True,
                          strict_latex_spaces=True),
            'a %c\nb')

    def test_keep_comments_paragraph_break_after_comment(self):
        # two newlines after a comment are reported as a separate characters
        # node, so the comment itself is followed by nothing
        self.assertEqual(
            latex_to_text('a %c\n\nb', keep_comments=True,
                          strict_latex_spaces=True),
            'a %c\n\nb')

    # --- keep_braced_groups and keep_braced_groups_minlen ---

    def test_braced_groups_are_dropped_by_default(self):
        self.assertEqual(latex_to_text(r'{ab}c'), 'abc')

    def test_keep_braced_groups(self):
        self.assertEqual(latex_to_text(r'{ab}c', keep_braced_groups=True), '{ab}c')

    def test_keep_braced_groups_minlen(self):
        # a group of a single character is not worth keeping the braces for,
        # the default minimum length being two
        self.assertEqual(latex_to_text(r'{a}b', keep_braced_groups=True), 'ab')
        self.assertEqual(
            latex_to_text(r'{a}b', keep_braced_groups=True,
                          keep_braced_groups_minlen=1),
            '{a}b')
        self.assertEqual(
            latex_to_text(r'{abc}d', keep_braced_groups=True,
                          keep_braced_groups_minlen=4),
            'abcd')

    def test_keep_braced_groups_minlen_counts_the_converted_text(self):
        # the length that is compared is that of the text after conversion, not
        # that of the latex source
        self.assertEqual(
            latex_to_text(r"{\'e}tonnant", keep_braced_groups=True),
            'étonnant')
        self.assertEqual(
            latex_to_text(r"{\'etonnant}", keep_braced_groups=True),
            '{étonnant}')

    # --- fill_text ---

    def test_fill_text_option_is_normalized(self):
        # anything false-ish means no filling at all, `True` means the default
        # width of eighty columns, and an integer is the width itself
        self.assertIsNone(make_l2t().fill_text)
        self.assertIsNone(make_l2t(fill_text=False).fill_text)
        self.assertIsNone(make_l2t(fill_text=0).fill_text)
        self.assertEqual(make_l2t(fill_text=True).fill_text, 80)
        self.assertEqual(make_l2t(fill_text=25).fill_text, 25)

    def test_fill_text_reflows_a_paragraph(self):
        self.assertEqual(
            latex_to_text(
                'aaa bbb ccc ddd eee fff ggg hhh iii jjj kkk lll mmm nnn ooo ppp',
                fill_text=20),
            'aaa bbb ccc ddd eee\nfff ggg hhh iii jjj\nkkk lll mmm nnn ooo\nppp')

    def test_fill_text_keeps_paragraph_breaks(self):
        self.assertEqual(
            latex_to_text('one two\n\nthree four', fill_text=10),
            'one two\n\nthree four')

    def test_fill_text_does_not_reflow_short_text(self):
        self.assertEqual(latex_to_text('short text', fill_text=80), 'short text')

    # --- the two font style options ---

    def test_text_fontstyle_defaults_to_upright(self):
        self.assertEqual(latex_to_text(r'plain'), 'plain')

    def test_text_fontstyle_macros_apply_by_default(self):
        self.assertEqual(latex_to_text(r'\textbf{bold} plain'),
                         mbold('bold') + ' plain')

    def test_text_fontstyle_false_switches_the_alphabets_off(self):
        self.assertEqual(
            latex_to_text(r'\textbf{bold} plain', text_fontstyle=False),
            'bold plain')

    def test_text_fontstyle_style_name_applies_outside_the_macros(self):
        # a style name here is the style that text starts out in; the font
        # macros still install their own for their own contents
        self.assertEqual(
            latex_to_text(r'\textbf{bold} plain', text_fontstyle='sans'),
            mbold('bold') + ' 𝗉𝗅𝖺𝗂𝗇')

    def test_math_fontstyle_defaults_to_italic(self):
        self.assertEqual(latex_to_text(r'$x + \mathbf{a}$'),
                         mvar('x') + ' + ' + mbold('a'))

    def test_math_fontstyle_none_leaves_variables_upright(self):
        # this is what pylatexenc 2 did: no alphabet of its own for a formula,
        # but the '\math..{}' macros still installed theirs
        self.assertEqual(
            latex_to_text(r'$x + \mathbf{a}$', math_fontstyle=None),
            'x + ' + mbold('a'))

    def test_math_fontstyle_false_switches_the_alphabets_off(self):
        self.assertEqual(
            latex_to_text(r'$x + \mathbf{a}$', math_fontstyle=False),
            'x + a')

    def test_math_fontstyle_is_the_initial_state_field(self):
        self.assertEqual(make_l2t().state.math_fontstyle, 'italic')
        self.assertEqual(make_l2t(math_fontstyle='bold').state.math_fontstyle,
                         'bold')

    def test_text_fontstyle_is_the_initial_state_field(self):
        self.assertIsNone(make_l2t().state.text_fontstyle)
        self.assertEqual(make_l2t(text_fontstyle='bold').state.text_fontstyle,
                         'bold')



class TestStrictLatexSpacesOption(unittest.TestCase):
    r"""Every accepted form of the `strict_latex_spaces=` option, checked both on
    the dictionary it is parsed into and on what it does to the output."""

    def test_default_is_the_macros_preset(self):
        d = make_l2t().strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertTrue(d['between-latex-constructs'])
        self.assertFalse(d['after-comment'])
        self.assertEqual(d['in-equations'], 'based-on-source')

    def test_none_turns_everything_off(self):
        d = make_l2t(strict_latex_spaces=None).strict_latex_spaces
        self.assertFalse(d['between-macro-and-chars'])
        self.assertFalse(d['between-latex-constructs'])
        self.assertFalse(d['after-comment'])
        self.assertIsNone(d['in-equations'])

    def test_false_is_the_macros_preset(self):
        d = make_l2t(strict_latex_spaces=False).strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertTrue(d['between-latex-constructs'])
        self.assertFalse(d['after-comment'])
        self.assertEqual(d['in-equations'], 'based-on-source')

    def test_true_turns_everything_on(self):
        d = make_l2t(strict_latex_spaces=True).strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertTrue(d['between-latex-constructs'])
        self.assertTrue(d['after-comment'])
        self.assertTrue(d['in-equations'])

    def test_on_is_the_same_as_true(self):
        d = make_l2t(strict_latex_spaces='on').strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertTrue(d['between-latex-constructs'])
        self.assertTrue(d['after-comment'])
        self.assertTrue(d['in-equations'])

    def test_off_is_the_same_as_false(self):
        d = make_l2t(strict_latex_spaces='off').strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertTrue(d['between-latex-constructs'])
        self.assertFalse(d['after-comment'])
        self.assertEqual(d['in-equations'], 'based-on-source')

    def test_preset_based_on_source(self):
        d = make_l2t(strict_latex_spaces='based-on-source').strict_latex_spaces
        self.assertFalse(d['between-macro-and-chars'])
        self.assertFalse(d['between-latex-constructs'])
        self.assertFalse(d['after-comment'])
        self.assertIsNone(d['in-equations'])

    def test_preset_macros(self):
        d = make_l2t(strict_latex_spaces='macros').strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertTrue(d['between-latex-constructs'])
        self.assertFalse(d['after-comment'])
        self.assertEqual(d['in-equations'], 'based-on-source')

    def test_preset_except_in_equations(self):
        d = make_l2t(strict_latex_spaces='except-in-equations').strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertTrue(d['between-latex-constructs'])
        self.assertTrue(d['after-comment'])
        self.assertEqual(d['in-equations'], 'based-on-source')

    def test_explicit_dictionary_fills_in_the_missing_keys(self):
        d = make_l2t(
            strict_latex_spaces={'between-macro-and-chars': True}
        ).strict_latex_spaces
        self.assertTrue(d['between-macro-and-chars'])
        self.assertFalse(d['between-latex-constructs'])
        self.assertFalse(d['after-comment'])
        self.assertIsNone(d['in-equations'])

    def test_explicit_dictionary_in_equations(self):
        d = make_l2t(strict_latex_spaces={'in-equations': True}).strict_latex_spaces
        self.assertTrue(d['in-equations'])

    def test_invalid_preset_name_raises(self):
        with self.assertRaises(ValueError):
            make_l2t(strict_latex_spaces='no-such-preset')

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            make_l2t(strict_latex_spaces=3)

    def test_the_dictionary_is_not_shared_between_instances(self):
        a = make_l2t()
        b = make_l2t()
        a.strict_latex_spaces['after-comment'] = True
        self.assertFalse(b.strict_latex_spaces['after-comment'])

    # --- what the settings do to the output ---

    def test_space_after_a_bare_macro_is_kept_when_not_strict(self):
        self.assertEqual(
            latex_to_text(r'Sk\l odowska', strict_latex_spaces='based-on-source'),
            'Skł odowska')

    def test_space_after_a_bare_macro_is_eaten_by_default(self):
        self.assertEqual(latex_to_text(r'Sk\l odowska'), 'Skłodowska')

    def test_space_between_two_groups_is_kept_by_default(self):
        self.assertEqual(
            latex_to_text(r'\textbf{A} \textbf{B}', text_fontstyle=False),
            'A B')

    def test_space_between_two_groups_is_dropped_when_not_strict(self):
        # a characters node that holds nothing but whitespace is dropped
        self.assertEqual(
            latex_to_text(r'\textbf{A} \textbf{B}', text_fontstyle=False,
                          strict_latex_spaces='based-on-source'),
            'AB')

    def test_strict_spaces_in_equations_follows_the_in_equations_key(self):
        # 'except-in-equations' asks for strict spacing everywhere but inside a
        # formula, where the source whitespace is kept as it was
        self.assertEqual(
            latex_to_text(r'$\alpha b$', math_mode='text', math_fontstyle=None,
                          strict_latex_spaces='except-in-equations'),
            'α b')
        self.assertEqual(
            latex_to_text(r'$\alpha b$', math_mode='text', math_fontstyle=None,
                          strict_latex_spaces=True),
            'αb')



class TestMathExpressionInOption(unittest.TestCase):
    r"""The `math_expression_in=` option and the function that applies it."""

    def test_module_default_is_parens(self):
        self.assertEqual(default_math_expression_in, 'parens')

    def test_default_option_value(self):
        self.assertEqual(make_l2t().math_expression_in, ('(', ')',))

    def test_accepted_values(self):
        self.assertEqual(make_l2t(math_expression_in='braces').math_expression_in,
                         ('{', '}',))
        self.assertEqual(make_l2t(math_expression_in='parens').math_expression_in,
                         ('(', ')',))
        self.assertEqual(
            make_l2t(math_expression_in=('<', '>',)).math_expression_in,
            ('<', '>',))
        self.assertIsNone(make_l2t(math_expression_in=None).math_expression_in)

    def test_unknown_preset_name_raises(self):
        with self.assertRaises(ValueError):
            make_l2t(math_expression_in='no-such-preset')

    def test_a_pair_of_the_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            make_l2t(math_expression_in=('a', 'b', 'c',))
        with self.assertRaises(ValueError):
            make_l2t(math_expression_in=('a',))

    def test_delimiters_around_a_subscript(self):
        self.assertEqual(
            latex_to_text(r'$x_{abc}^2$', math_expression_in='braces'),
            mvar('x') + '_{' + mvar('abc') + '}²')

    def test_custom_delimiters_around_a_subscript(self):
        self.assertEqual(
            latex_to_text(r'$x_{abc}^2$', math_expression_in=('<', '>',)),
            mvar('x') + '_<' + mvar('abc') + '>²')

    def test_no_delimiters_around_a_subscript(self):
        self.assertEqual(
            latex_to_text(r'$x_{abc}^2$', math_expression_in=None),
            mvar('x') + '_' + mvar('abc') + '²')

    def test_delimiters_around_the_parts_of_a_fraction(self):
        self.assertEqual(
            latex_to_text(r'$\frac{a+b}{c+d}$', math_expression_in='braces'),
            '{' + mvar('a') + ' + ' + mvar('b') + '}/{'
            + mvar('c') + ' + ' + mvar('d') + '}')

    def test_fmt_math_expression_in_delimiters(self):
        self.assertEqual(fmt_math_expression_in_delimiters('abc', 'braces'),
                         '{abc}')
        self.assertEqual(fmt_math_expression_in_delimiters('abc', 'parens'),
                         '(abc)')
        self.assertEqual(fmt_math_expression_in_delimiters('abc', ('<', '>',)),
                         '<abc>')
        self.assertEqual(fmt_math_expression_in_delimiters('abc', None), 'abc')

    def test_fmt_math_expression_in_delimiters_short_text(self):
        # a single character shows its own extent, so it is left alone
        self.assertEqual(fmt_math_expression_in_delimiters('a', 'parens'), 'a')
        self.assertEqual(fmt_math_expression_in_delimiters('', 'parens'), '')

    def test_fmt_math_expression_in_delimiters_invalid_values(self):
        with self.assertRaises(ValueError):
            fmt_math_expression_in_delimiters('abc', 'no-such-preset')
        with self.assertRaises(ValueError):
            fmt_math_expression_in_delimiters('abc', ('<', '>', '!',))



class TestTextConversionState(unittest.TestCase):
    r"""The conversion state object and the way a modified one is installed."""

    def test_default_fields(self):
        st = TextConversionState()
        self.assertIsNone(st.strict_latex_spaces)
        self.assertFalse(st.in_math_mode)
        self.assertEqual(st.list_stack, [])
        self.assertEqual(st.math_expression_in, default_math_expression_in)
        self.assertIsNone(st.text_fontstyle)
        self.assertEqual(st.math_fontstyle, 'italic')

    def test_explicit_fields(self):
        st = TextConversionState(in_math_mode=True, text_fontstyle='bold')
        self.assertTrue(st.in_math_mode)
        self.assertEqual(st.text_fontstyle, 'bold')

    def test_list_stack_is_not_shared_between_states(self):
        a = TextConversionState()
        b = TextConversionState()
        a.list_stack.append('x')
        self.assertEqual(b.list_stack, [])

    def test_sub_state_changes_the_given_field(self):
        st = TextConversionState()
        st2 = st.sub_state(in_math_mode=True)
        self.assertTrue(st2.in_math_mode)

    def test_sub_state_keeps_the_other_fields(self):
        st = TextConversionState(text_fontstyle='bold')
        st2 = st.sub_state(in_math_mode=True)
        self.assertEqual(st2.text_fontstyle, 'bold')

    def test_sub_state_leaves_the_original_alone(self):
        st = TextConversionState()
        st2 = st.sub_state(in_math_mode=True)
        self.assertFalse(st.in_math_mode)
        self.assertIsNot(st, st2)

    def test_sub_state_rejects_an_unknown_field(self):
        st = TextConversionState()
        with self.assertRaises(ValueError):
            st.sub_state(no_such_field=1)

    def test_push_state_installs_the_new_state(self):
        l2t = make_l2t()
        with l2t.push_state(in_math_mode=True):
            self.assertTrue(l2t.state.in_math_mode)

    def test_push_state_restores_the_previous_state(self):
        l2t = make_l2t()
        before = l2t.state
        with l2t.push_state(in_math_mode=True):
            self.assertIsNot(l2t.state, before)
        self.assertIs(l2t.state, before)
        self.assertFalse(l2t.state.in_math_mode)

    def test_push_state_nested(self):
        l2t = make_l2t()
        with l2t.push_state(text_fontstyle='bold'):
            self.assertEqual(l2t.state.text_fontstyle, 'bold')
            with l2t.push_state(text_fontstyle='sans'):
                self.assertEqual(l2t.state.text_fontstyle, 'sans')
            self.assertEqual(l2t.state.text_fontstyle, 'bold')
        self.assertIsNone(l2t.state.text_fontstyle)

    def test_strict_latex_spaces_property_reads_the_state(self):
        l2t = make_l2t()
        self.assertIs(l2t.strict_latex_spaces, l2t.state.strict_latex_spaces)

    def test_math_expression_in_property_reads_the_state(self):
        l2t = make_l2t()
        with l2t.push_state(math_expression_in=('<', '>',)):
            self.assertEqual(l2t.math_expression_in, ('<', '>',))

    def test_math_expression_in_can_be_changed_for_one_part_only(self):
        l2t = make_l2t()
        wdb = get_latexwalker_default_context_db()
        with l2t.push_state(math_expression_in='braces'):
            inside = l2t.latex_to_text(r'$x_{abc}^2$', latex_context=wdb)
        outside = l2t.latex_to_text(r'$x_{abc}^2$', latex_context=wdb)
        self.assertEqual(inside, mvar('x') + '_{' + mvar('abc') + '}²')
        self.assertEqual(outside, mvar('x') + '_(' + mvar('abc') + ')²')

    def test_repr_mentions_the_fields(self):
        # the representation is only used in log messages, so we merely check
        # that it names the class and does not blow up
        r = repr(TextConversionState())
        self.assertEqual(r[0:len('TextConversionState(')], 'TextConversionState(')



class TestBasicConversion(unittest.TestCase):
    r"""`latex_to_text()` on an ordinary spread of latex code, and the two
    entry points that accept `None`."""

    def test_nodelist_to_text_of_none(self):
        self.assertEqual(make_l2t().nodelist_to_text(None), '')

    def test_node_to_text_of_none(self):
        self.assertEqual(make_l2t().node_to_text(None), '')

    def test_nodelist_to_text_of_an_empty_list(self):
        self.assertEqual(make_l2t().nodelist_to_text([]), '')

    def test_plain_text_is_left_alone(self):
        self.assertEqual(latex_to_text('Hello, world.'), 'Hello, world.')

    def test_empty_input(self):
        self.assertEqual(latex_to_text(''), '')

    def test_font_style_macros(self):
        self.assertEqual(
            latex_to_text(r'\textbf{Bold} and \textit{italic}.',
                          text_fontstyle=False),
            'Bold and italic.')

    def test_quotes_and_emphasis(self):
        self.assertEqual(
            latex_to_text(r"``Hello,'' \emph{she} said.", text_fontstyle=False),
            '“Hello,” she said.')

    def test_accents(self):
        self.assertEqual(latex_to_text(r"Sant\'e! \`A la v\^otre."),
                         'Santé! À la vôtre.')

    def test_escaped_special_characters(self):
        self.assertEqual(latex_to_text(r'50\% of \$5'), '50% of $5')

    def test_non_breaking_space(self):
        self.assertEqual(latex_to_text('a~b'), 'a\N{NO-BREAK SPACE}b')

    def test_line_and_paragraph_breaks_are_kept(self):
        self.assertEqual(latex_to_text('x\ny'), 'x\ny')
        self.assertEqual(latex_to_text('para one\n\npara two'),
                         'para one\n\npara two')

    def test_group_contents_are_converted(self):
        self.assertEqual(latex_to_text(r'{\textbf{a}b}c', text_fontstyle=False),
                         'abc')

    def test_macros_with_arguments(self):
        self.assertEqual(latex_to_text(r'\url{http://example.org}'),
                         '<http://example.org>')
        self.assertEqual(latex_to_text(r'\href{http://example.org}{link}'),
                         'link <http://example.org>')
        self.assertEqual(latex_to_text(r'\footnote{note}'), '[note]')

    def test_center_environment(self):
        self.assertEqual(latex_to_text(r'\begin{center}centered\end{center}'),
                         '\ncentered\n')

    def test_verbatim_environment_is_not_interpreted(self):
        self.assertEqual(
            latex_to_text('\\begin{verbatim}\n\\textbf{x} $y$\n\\end{verbatim}'),
            '\\textbf{x} $y$\n')

    def test_nodelist_to_text_accepts_an_explicit_state(self):
        l2t = make_l2t()
        wdb = get_latexwalker_default_context_db()
        nodelist = LatexWalker('abc', latex_context=wdb).parse_content(
            latexnodes_parsers.LatexGeneralNodesParser()
        )[0]
        state = l2t.state.sub_state(text_fontstyle='bold')
        self.assertEqual(l2t.nodelist_to_text(nodelist, state=state), mbold('abc'))
        # ... and the state is put back afterwards
        self.assertIsNone(l2t.state.text_fontstyle)



class TestApplySimplifyRepl(unittest.TestCase):
    r"""`apply_simplify_repl()`, in all the shapes a `simplify_repl` may take.

    The specifications are built here rather than taken from the default
    catalogue, so that these tests say nothing about which macros exist and
    everything about how a replacement is applied."""

    def convert(self, latex, macros=None, environments=None, specials=None,
                walker_macros=None, walker_environments=None,
                walker_specials=None, **options):
        l2t = make_custom_l2t(macros=macros, environments=environments,
                              specials=specials, **options)
        wdb = make_custom_walker_db(macros=walker_macros,
                                    environments=walker_environments,
                                    specials=walker_specials)
        return l2t.latex_to_text(latex, latex_context=wdb)

    # --- string replacements ---

    def test_plain_string(self):
        self.assertEqual(
            self.convert(r'x\aaa y',
                         macros=[ MacroTextSpec('aaa', simplify_repl='AAA') ],
                         walker_macros=[ std_macro('aaa', False, 0) ]),
            'xAAAy')

    def test_string_with_percent_s(self):
        # a single '%s' takes the text of the macro's single argument
        self.assertEqual(
            self.convert(r'\aaa{arg}',
                         macros=[ MacroTextSpec('aaa', simplify_repl='<%s>') ],
                         walker_macros=[ std_macro('aaa', False, 1) ]),
            '<arg>')

    def test_string_with_numbered_placeholders(self):
        self.assertEqual(
            self.convert(r'\aaa{one}{two}',
                         macros=[ MacroTextSpec('aaa',
                                                simplify_repl='[%(2)s|%(1)s]') ],
                         walker_macros=[ std_macro('aaa', False, 2) ]),
            '[two|one]')

    def test_numbered_placeholder_may_be_used_more_than_once(self):
        self.assertEqual(
            self.convert(r'\aaa{X}',
                         macros=[ MacroTextSpec('aaa',
                                                simplify_repl='%(1)s%(1)s') ],
                         walker_macros=[ std_macro('aaa', False, 1) ]),
            'XX')

    def test_environment_body_with_percent_s(self):
        self.assertEqual(
            self.convert(r'\begin{eee}body\end{eee}',
                         environments=[ EnvironmentTextSpec('eee',
                                                            simplify_repl='<%s>') ],
                         walker_environments=[ std_environment('eee', False, 0) ]),
            '<body>')

    def test_environment_body_placeholder(self):
        # in an environment the body is reached with '%(body)s', and the
        # arguments keep their numbers
        self.assertEqual(
            self.convert(r'\begin{eee}{arg}body\end{eee}',
                         environments=[
                             EnvironmentTextSpec('eee',
                                                 simplify_repl='[%(1)s: %(body)s]')
                         ],
                         walker_environments=[ std_environment('eee', False, 1) ]),
            '[arg: body]')

    def test_a_lone_percent_sign_is_literal(self):
        self.assertEqual(
            self.convert(r'\aaa',
                         macros=[ MacroTextSpec('aaa', simplify_repl='%') ],
                         walker_macros=[ std_macro('aaa', False, 0) ]),
            '%')

    def test_a_doubled_percent_sign_is_one_percent_sign(self):
        self.assertEqual(
            self.convert(r'\aaa',
                         macros=[ MacroTextSpec('aaa',
                                                simplify_repl='100%% sure') ],
                         walker_macros=[ std_macro('aaa', False, 0) ]),
            '100% sure')

    def test_a_failed_substitution_falls_back_on_the_raw_string(self):
        # there is no second argument to fill '%(9)s' with, so the replacement
        # text is used as it is (and a warning is logged)
        self.assertEqual(
            self.convert(r'\aaa{X}',
                         macros=[ MacroTextSpec('aaa', simplify_repl='%(9)s') ],
                         walker_macros=[ std_macro('aaa', False, 1) ]),
            '%(9)s')

    def test_a_failed_percent_s_substitution_falls_back_too(self):
        # '%s' takes a single value, so two arguments cannot be substituted
        self.assertEqual(
            self.convert(r'\aaa{one}{two}',
                         macros=[ MacroTextSpec('aaa', simplify_repl='<%s>') ],
                         walker_macros=[ std_macro('aaa', False, 2) ]),
            '<%s>')

    def test_specials_string_replacement(self):
        self.assertEqual(
            self.convert('a<>b',
                         specials=[ SpecialsTextSpec('<>', simplify_repl='SP') ],
                         walker_specials=[ SpecialsSpec('<>') ]),
            'aSPb')

    # --- callable replacements ---

    def test_callable_with_the_node_only(self):
        def repl(node):
            return node.macroname.upper()
        self.assertEqual(
            self.convert(r'\aaa',
                         macros=[ MacroTextSpec('aaa', simplify_repl=repl) ],
                         walker_macros=[ std_macro('aaa', False, 0) ]),
            'AAA')

    def test_callable_with_l2tobj(self):
        def repl(node, l2tobj):
            return '<' + l2tobj.node_arg_to_text(node, 0) + '>'
        self.assertEqual(
            self.convert(r'\aaa{zz}',
                         macros=[ MacroTextSpec('aaa', simplify_repl=repl) ],
                         walker_macros=[ std_macro('aaa', False, 1) ]),
            '<zz>')

    def test_callable_with_l2tstate(self):
        # the state that is handed over is the one that applies where the node
        # sits, i.e. the converter's current state
        outcome = []
        def repl(node, l2tobj, l2tstate):
            outcome.append(l2tstate is l2tobj.state)
            return ''
        self.convert(r'\aaa',
                     macros=[ MacroTextSpec('aaa', simplify_repl=repl) ],
                     walker_macros=[ std_macro('aaa', False, 0) ])
        self.assertEqual(outcome, [ True ])

    def test_callable_with_macroname(self):
        def repl(node, macroname):
            return 'M:' + macroname
        self.assertEqual(
            self.convert(r'\aaa',
                         macros=[ MacroTextSpec('aaa', simplify_repl=repl) ],
                         walker_macros=[ std_macro('aaa', False, 0) ]),
            'M:aaa')

    def test_callable_with_environmentname(self):
        def repl(node, environmentname):
            return 'E:' + environmentname
        self.assertEqual(
            self.convert(r'\begin{eee}body\end{eee}',
                         environments=[ EnvironmentTextSpec('eee',
                                                            simplify_repl=repl) ],
                         walker_environments=[ std_environment('eee', False, 0) ]),
            'E:eee')

    def test_callable_with_specials_chars(self):
        def repl(node, specials_chars):
            return 'S:' + specials_chars
        self.assertEqual(
            self.convert('a<>b',
                         specials=[ SpecialsTextSpec('<>', simplify_repl=repl) ],
                         walker_specials=[ SpecialsSpec('<>') ]),
            'aS:<>b')

    def test_callable_with_several_declared_arguments(self):
        def repl(node, l2tobj, l2tstate, macroname):
            return macroname + ':' + l2tobj.node_arg_to_text(node, 0) \
                + ':' + ('math' if l2tstate.in_math_mode else 'text')
        self.assertEqual(
            self.convert(r'\aaa{q}',
                         macros=[ MacroTextSpec('aaa', simplify_repl=repl) ],
                         walker_macros=[ std_macro('aaa', False, 1) ]),
            'aaa:q:text')

    def test_callable_returning_none_gives_the_empty_string(self):
        def repl_none(node):
            return None
        self.assertEqual(
            self.convert(r'x\aaa y',
                         macros=[ MacroTextSpec('aaa', simplify_repl=repl_none) ],
                         walker_macros=[ std_macro('aaa', False, 0) ]),
            'xy')
        def repl_empty(node):
            return ''
        self.assertEqual(
            self.convert(r'x\aaa y',
                         macros=[ MacroTextSpec('aaa', simplify_repl=repl_empty) ],
                         walker_macros=[ std_macro('aaa', False, 0) ]),
            'xy')

    def test_apply_simplify_repl_can_be_called_directly(self):
        # the method is part of the public interface; a `simplify_repl` may be
        # applied to a node by hand
        l2t = make_custom_l2t(macros=[ MacroTextSpec('aaa', simplify_repl='ZZZ') ])
        wdb = make_custom_walker_db(macros=[ std_macro('aaa', False, 0) ])
        nodelist = LatexWalker(r'\aaa', latex_context=wdb).parse_content(
            latexnodes_parsers.LatexGeneralNodesParser()
        )[0]
        self.assertEqual(
            l2t.apply_simplify_repl(nodelist[0], 'ZZZ', what='test'),
            'ZZZ')



class TestApplyTextReplacements(unittest.TestCase):
    r"""The `apply_text_replacements()` compatibility helper."""

    def test_plain_string_pattern(self):
        l2t = make_l2t()
        self.assertEqual(
            l2t.apply_text_replacements('hello world', [ ('world', 'there',) ]),
            'hello there')

    def test_several_replacements_are_applied_in_order(self):
        l2t = make_l2t()
        self.assertEqual(
            l2t.apply_text_replacements('abc', [ ('a', 'b',), ('b', 'c',) ]),
            'ccc')

    def test_compiled_regular_expression_pattern(self):
        l2t = make_l2t()
        self.assertEqual(
            l2t.apply_text_replacements('a1b22c',
                                        [ (re.compile(r'[0-9]+'), '#',) ]),
            'a#b#c')

### BEGIN_TEST_PYLATEXENC_SKIP
    def test_regular_expression_with_a_group_reference(self):
        # not in the JavaScript build: a back-reference in the replacement
        # string is spelled '\\1' in python and '$1' in JavaScript, and the
        # replacement string is handed to the regular expression engine of
        # whichever of the two we are running on
        l2t = make_l2t()
        self.assertEqual(
            l2t.apply_text_replacements('ab', [ (re.compile(r'(a)(b)'),
                                                 r'\2\1',) ]),
            'ba')
### END_TEST_PYLATEXENC_SKIP

    def test_no_replacements_leaves_the_text_alone(self):
        l2t = make_l2t()
        self.assertEqual(l2t.apply_text_replacements('unchanged', []),
                         'unchanged')



class TestFancyMathEngine(unittest.TestCase):
    r"""The 'fancy' math engine: where it puts spaces, and how it writes the
    superscripts and the subscripts."""

    def fancy(self, latex, **options):
        return latex_to_text(latex, math_mode='fancy', **options)

    # --- the spacing rules ---

    def test_binary_operator_gets_spaces(self):
        self.assertEqual(self.fancy(r'$x+y$'),
                         mvar('x') + ' + ' + mvar('y'))

    def test_relation_gets_spaces(self):
        self.assertEqual(self.fancy(r'$x=y$'),
                         mvar('x') + ' = ' + mvar('y'))

    def test_implicit_multiplication_stays_tight(self):
        self.assertEqual(self.fancy(r'$4\pi c$'), '4π' + mvar('c'))

    def test_source_whitespace_is_ignored(self):
        self.assertEqual(self.fancy(r'$4 \pi c$'), self.fancy(r'$4\pi c$'))
        self.assertEqual(self.fancy('$  x  +  y  $'), self.fancy(r'$x+y$'))

    def test_delimiters_hug_what_they_enclose(self):
        self.assertEqual(self.fancy(r'$f(x)$'),
                         mvar('f') + '(' + mvar('x') + ')')

    def test_function_name_is_set_apart(self):
        self.assertEqual(self.fancy(r'$\sin x$'), 'sin ' + mvar('x'))

    def test_function_name_hugs_an_opening_delimiter(self):
        self.assertEqual(self.fancy(r'$\sin(x)$'),
                         'sin(' + mvar('x') + ')')

    def test_punctuation_is_followed_by_a_space(self):
        self.assertEqual(self.fancy(r'$a, b$'),
                         mvar('a') + ', ' + mvar('b'))

    def test_adjacent_digits_from_separate_items_are_separated(self):
        # the braces are what makes the two digits separate items in the first
        # place; a single number stays a single number
        self.assertEqual(self.fancy(r'${1}2$'), '1 2')
        self.assertEqual(self.fancy(r'$12$'), '12')

    def test_open_ended_rendering_is_set_apart(self):
        self.assertEqual(self.fancy(r'$\frac{a}{b}c$'),
                         mvar('a') + '/' + mvar('b') + ' ' + mvar('c'))

    def test_unary_minus_binds_tightly(self):
        self.assertEqual(self.fancy(r'$-x$'), '-' + mvar('x'))
        self.assertEqual(self.fancy(r'$x = -y$'),
                         mvar('x') + ' = -' + mvar('y'))

    def test_binary_minus_still_gets_its_spaces(self):
        self.assertEqual(self.fancy(r'$a-b$'),
                         mvar('a') + ' - ' + mvar('b'))

    def test_text_fragment_is_opaque(self):
        self.assertEqual(self.fancy(r'$\text{a+b}$'), 'a+b')

    def test_text_fragment_keeps_its_own_spaces(self):
        # the space that '\text{if }' brings along is enough; the engine does
        # not add one of its own next to it
        self.assertEqual(self.fancy(r'$\text{if } x > 0$'),
                         'if ' + mvar('x') + ' > 0')

    # --- superscripts and subscripts ---

    def test_superscript_uses_the_unicode_character(self):
        self.assertEqual(self.fancy(r'$x^2$'), mvar('x') + '²')

    def test_subscript_uses_the_unicode_character(self):
        self.assertEqual(self.fancy(r'$x_i$'), mvar('x') + 'ᵢ')

    def test_superscript_of_several_characters(self):
        self.assertEqual(self.fancy(r'$x^{abc}$'), mvar('x') + 'ᵃᵇᶜ')

    def test_superscript_falls_back_on_the_latex_notation(self):
        # unicode has no superscript 'q'
        self.assertEqual(self.fancy(r'$x^q$'), mvar('x') + '^' + mvar('q'))

    def test_latex_notation_script_is_padded_on_both_sides(self):
        self.assertEqual(self.fancy(r'$4\pi c x^q p$'),
                         '4π' + mvar('c') + ' ' + mvar('x') + '^' + mvar('q')
                         + ' ' + mvar('p'))

    def test_unicode_script_needs_no_padding(self):
        self.assertEqual(self.fancy(r'$4\pi c x^2 p$'),
                         '4π' + mvar('c') + mvar('x') + '²' + mvar('p'))

    def test_a_superscript_followed_by_a_subscript_is_swapped(self):
        # the subscript attaches to the base first, so that the two scripts do
        # not run together
        self.assertEqual(self.fancy(r'$x^a_b$'), mvar('x') + '_' + mvar('b') + 'ᵃ')

    def test_delimiters_only_where_they_are_needed(self):
        # nothing follows, so a bare subscript is unambiguous
        self.assertEqual(self.fancy(r'$x_{abc}$'),
                         mvar('x') + '_' + mvar('abc'))
        # a space is enough to show where it ends
        self.assertEqual(self.fancy(r'$x_{abc} p$'),
                         mvar('x') + '_' + mvar('abc') + ' ' + mvar('p'))
        # a second script attaches to the same base, and only delimiters can
        # tell the two apart
        self.assertEqual(self.fancy(r'$x_{abc}^2$'),
                         mvar('x') + '_(' + mvar('abc') + ')²')

    def test_large_operator_with_a_subscript(self):
        self.assertEqual(self.fancy(r'$\sum_i y$'), '∑ᵢ ' + mvar('y'))

    def test_square_root(self):
        self.assertEqual(self.fancy(r'$\sqrt{x}$'), '√' + mvar('x'))

    def test_display_math_is_set_on_lines_of_its_own(self):
        self.assertEqual(self.fancy(r'\[x+y\]'),
                         '\n    ' + mvar('x') + ' + ' + mvar('y') + '\n')

    def test_upright_letters_are_a_function_name_only_when_italicized(self):
        # a run of upright letters stands out as the name of a function only
        # because the variables around it are italic; switching the alphabets
        # off takes that clue away
        self.assertEqual(self.fancy(r'$2xy$'), '2' + mvar('xy'))
        self.assertEqual(self.fancy(r'$2xy$', math_fontstyle=False), '2xy')

    def test_nested_font_styles_across_math_mode(self):
        # '\text{}' restores the text font that the excursion into math mode
        # never disturbed
        self.assertEqual(
            self.fancy(r'\textit{ab $\mathbf{c+\text{[d]}}$}'),
            mvar('ab ') + mbold('c') + ' + [' + mvar('d') + ']')



class TestMakeMathPiece(unittest.TestCase):
    r"""`make_math_piece()`, the way a `simplify_repl` says how its rendering
    wants to be joined to its neighbours."""

    def test_text_and_default_class(self):
        p = make_l2t().make_math_piece(text='ABC')
        self.assertEqual(str(p), 'ABC')
        self.assertEqual(p.cls_left, 'ord')
        self.assertEqual(p.cls_right, 'ord')

    def test_a_single_class_applies_to_both_edges(self):
        p = make_l2t().make_math_piece(text='ABC', cls='op')
        self.assertEqual(p.cls_left, 'op')
        self.assertEqual(p.cls_right, 'op')

    def test_a_pair_of_classes(self):
        p = make_l2t().make_math_piece(text='ABC', cls=('open', 'close',))
        self.assertEqual(p.cls_left, 'open')
        self.assertEqual(p.cls_right, 'close')

    def test_an_invalid_class_is_rejected(self):
        with self.assertRaises(ValueError):
            make_l2t().make_math_piece(text='ABC', cls='no-such-class')
        with self.assertRaises(ValueError):
            make_l2t().make_math_piece(text='ABC',
                                       cls=('ord', 'ord', 'ord',))

    def test_an_inconsistent_call_is_rejected(self):
        with self.assertRaises(ValueError):
            make_l2t().make_math_piece(text='ABC', inner_text='abc')
        with self.assertRaises(ValueError):
            make_l2t().make_math_piece(text='ABC', prefix='^')

    def test_wrappable_piece_shows_its_contents_bare_on_its_own(self):
        p = make_l2t().make_math_piece(inner_text='abc', prefix='^')
        self.assertEqual(str(p), '^abc')

    def test_wrappable_piece_wraps_when_another_script_follows(self):
        p = make_l2t().make_math_piece(inner_text='abc', prefix='^',
                                       cls=('script', 'openend',))
        text, cls_left, cls_right = p.realize(cls_right_neighbor='script')
        self.assertEqual(text, '^(abc)')
        self.assertEqual(cls_left, 'script')
        self.assertEqual(cls_right, 'close')

    def test_wrappable_piece_stays_bare_when_nothing_follows(self):
        p = make_l2t().make_math_piece(inner_text='abc', prefix='^',
                                       cls=('script', 'openend',))
        text, cls_left, cls_right = p.realize(cls_right_neighbor=None)
        self.assertEqual(text, '^abc')
        self.assertEqual(cls_right, 'openend')

    def test_the_atom_class_decides_the_spacing_around_the_piece(self):
        # an ordinary atom is joined tightly to its neighbours ...
        self.assertEqual(self.render_with_piece_class('ord'),
                         '2OP' + mvar('x'))
        # ... a large operator and a relation are set apart ...
        self.assertEqual(self.render_with_piece_class('op'),
                         '2 OP ' + mvar('x'))
        self.assertEqual(self.render_with_piece_class('rel'),
                         '2 OP ' + mvar('x'))
        # ... and a large object brings its own delimiters, so its neighbours
        # hug it the way they hug a parenthesis
        self.assertEqual(self.render_with_piece_class('block'),
                         '2OP' + mvar('x'))

    def render_with_piece_class(self, cls):
        r"""Render ``$2\mypiece x$`` where '\mypiece' returns a math piece of
        the given atom class, and give back the text."""
        # a plain closure and not a default argument, because a default
        # argument that shadows a name of the enclosing scope does not survive
        # the compilation to JavaScript
        def make_repl(the_cls):
            def repl(node, l2tobj):
                return l2tobj.make_math_piece(text='OP', cls=the_cls)
            return repl
        tdb = get_latex2text_default_context_db()
        tdb.add_context_category(
            'tests',
            macros=[ MacroTextSpec('mypiece', simplify_repl=make_repl(cls)) ],
            prepend=True)
        wdb = get_latexwalker_default_context_db()
        wdb.add_context_category('tests',
                                 macros=[ std_macro('mypiece', False, 0) ],
                                 prepend=True)
        return LatexNodes2Text(latex_context=tdb).latex_to_text(
            r'$2\mypiece x$', latex_context=wdb)



class TestFmtMathTextStyle(unittest.TestCase):
    r"""`fmt_math_text_style()` over every style it knows, including the letters
    that unicode had already given a code point of their own somewhere else."""

    def test_bold(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'bold'), '𝐀𝐙𝐚𝐳')

    def test_italic(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'italic'), '𝐴𝑍𝑎𝑧')
        # the italic 'h' is the planck constant sign
        self.assertEqual(fmt_math_text_style('h', 'italic'), 'ℎ')

    def test_bold_italic(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'bold-italic'), '𝑨𝒁𝒂𝒛')

    def test_script(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'script'), '𝒜𝒵𝒶𝓏')
        self.assertEqual(fmt_math_text_style('BEFHILMRego', 'script'),
                         'ℬℰℱℋℐℒℳℛℯℊℴ')

    def test_bold_script(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'bold-script'), '𝓐𝓩𝓪𝔃')

    def test_fraktur(self):
        # 'Z' is one of the exceptions, so it is not the one of the block
        self.assertEqual(fmt_math_text_style('AZaz', 'fraktur'), '𝔄ℨ𝔞𝔷')
        self.assertEqual(fmt_math_text_style('CHIRZ', 'fraktur'), 'ℭℌℑℜℨ')

    def test_doublestruck(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'doublestruck'), '𝔸ℤ𝕒𝕫')
        self.assertEqual(fmt_math_text_style('CHNPQRZ', 'doublestruck'),
                         'ℂℍℕℙℚℝℤ')

    def test_bold_fraktur(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'bold-fraktur'), '𝕬𝖅𝖆𝖟')

    def test_sans(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'sans'), '𝖠𝖹𝖺𝗓')

    def test_sans_bold(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'sans-bold'), '𝗔𝗭𝗮𝘇')

    def test_sans_italic(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'sans-italic'), '𝘈𝘡𝘢𝘻')

    def test_sans_bold_italic(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'sans-bold-italic'),
                         '𝘼𝙕𝙖𝙯')

    def test_monospace(self):
        self.assertEqual(fmt_math_text_style('AZaz', 'monospace'), '𝙰𝚉𝚊𝚣')

    def test_non_letters_are_left_alone(self):
        self.assertEqual(fmt_math_text_style('a 1.', 'bold'), '𝐚 1.')

    def test_empty_text(self):
        self.assertEqual(fmt_math_text_style('', 'bold'), '')

    def test_an_unknown_style_leaves_the_letters_alone(self):
        self.assertEqual(fmt_math_text_style('abc', 'no-such-style'), 'abc')

    def test_the_helper_tables_of_this_file_agree_with_the_function(self):
        # the two tables at the top of this file are written out by hand; make
        # sure they say the same thing as the function does
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        self.assertEqual(mvar(letters), fmt_math_text_style(letters, 'italic'))
        self.assertEqual(mbold(letters), fmt_math_text_style(letters, 'bold'))



class TestFmtSubsuperscriptText(unittest.TestCase):
    r"""`fmt_subsuperscript_text()`, and the `None` it gives back when unicode
    has nothing to offer."""

    def test_superscript(self):
        self.assertEqual(fmt_subsuperscript_text('123', 'superscript'), '¹²³')
        self.assertEqual(fmt_subsuperscript_text('abc', 'superscript'), 'ᵃᵇᶜ')
        self.assertEqual(fmt_subsuperscript_text('a+b', 'superscript'), 'ᵃ⁺ᵇ')

    def test_subscript(self):
        self.assertEqual(fmt_subsuperscript_text('12', 'subscript'), '₁₂')
        self.assertEqual(fmt_subsuperscript_text('aei', 'subscript'), 'ₐₑᵢ')

    def test_empty_text(self):
        self.assertEqual(fmt_subsuperscript_text('', 'superscript'), '')

    def test_none_when_there_is_no_unicode_version(self):
        # there is no superscript 'q', and no subscript 'b' or 'c'
        self.assertIsNone(fmt_subsuperscript_text('q', 'superscript'))
        self.assertIsNone(fmt_subsuperscript_text('abc', 'subscript'))
        # one missing character gives up on the whole text
        self.assertIsNone(fmt_subsuperscript_text('1q', 'superscript'))

    def test_a_styled_letter_has_no_superscript_by_default(self):
        self.assertIsNone(fmt_subsuperscript_text('𝑛', 'superscript'))

    def test_a_styled_letter_can_be_normalized_first(self):
        self.assertEqual(
            fmt_subsuperscript_text('𝑛', 'superscript',
                                    normalize_math_style_chars=True),
            'ⁿ')

    def test_normalizing_a_plain_letter_changes_nothing(self):
        self.assertEqual(
            fmt_subsuperscript_text('n', 'superscript',
                                    normalize_math_style_chars=True),
            'ⁿ')



class TestListEnvironments(unittest.TestCase):
    r"""The list environments, their item markers and their nesting."""

    def test_itemize(self):
        self.assertEqual(
            latex_to_text(r'\begin{itemize}\item a\item b\end{itemize}'),
            '\n  \N{BULLET} a\n  \N{BULLET} b\n')

    def test_enumerate(self):
        self.assertEqual(
            latex_to_text(r'\begin{enumerate}\item a\item b\end{enumerate}'),
            '\n  1. a\n  2. b\n')

    def test_description(self):
        self.assertEqual(
            latex_to_text(
                r'\begin{description}\item[Foo] a\item[Bar] b\end{description}'),
            '\n  Foo a\n  Bar b\n')

    def test_explicit_item_label(self):
        # an explicit label is used as the marker and does not advance the
        # counter, as in LaTeX
        self.assertEqual(
            latex_to_text(
                r'\begin{enumerate}\item[x] a\item b\end{enumerate}'),
            '\n  x a\n  1. b\n')

    def test_empty_list(self):
        self.assertEqual(latex_to_text(r'\begin{itemize}\end{itemize}'), '\n')

    def test_stray_item_outside_of_any_list(self):
        self.assertEqual(latex_to_text(r'Stray \item here.'),
                         'Stray \n  \N{BULLET} here.')

    def test_item_continuation_lines_are_aligned(self):
        self.assertEqual(
            latex_to_text('\\begin{enumerate}\n\\item first line\nsecond line\n'
                          '\\item another\n\\end{enumerate}'),
            '\n  1. first line\n     second line\n  2. another\n')

    def test_nested_itemize_marker_sequence(self):
        # the markers cycle through bullet, en dash, asterisk and middle dot,
        # and then start over
        self.assertEqual(
            latex_to_text(
                r'\begin{itemize}\item a\begin{itemize}\item b'
                r'\begin{itemize}\item c\begin{itemize}\item d'
                r'\begin{itemize}\item e'
                r'\end{itemize}\end{itemize}\end{itemize}\end{itemize}'
                r'\end{itemize}'),
            '\n  \N{BULLET} a\n    \N{EN DASH} b\n      * c\n'
            '        \N{MIDDLE DOT} d\n          \N{BULLET} e\n')

    def test_nested_enumerate_marker_sequence(self):
        # arabic numbers, lowercase letters in parentheses, lowercase roman
        # numerals, uppercase letters, and then start over
        self.assertEqual(
            latex_to_text(
                r'\begin{enumerate}\item a\begin{enumerate}\item b'
                r'\begin{enumerate}\item c\begin{enumerate}\item d'
                r'\begin{enumerate}\item e'
                r'\end{enumerate}\end{enumerate}\end{enumerate}\end{enumerate}'
                r'\end{enumerate}'),
            '\n  1. a\n     (a) b\n         i. c\n            A. d\n'
            '               1. e\n')

    def test_a_nested_list_of_another_kind_keeps_its_own_marker_depth(self):
        # as in LaTeX, an itemize inside an enumerate is still a first-level
        # itemize
        self.assertEqual(
            latex_to_text(
                r'\begin{enumerate}\item one'
                r'\begin{itemize}\item inner\end{itemize}\end{enumerate}'),
            '\n  1. one\n     \N{BULLET} inner\n')

    def test_text_before_the_first_item_is_kept(self):
        self.assertEqual(
            latex_to_text(r'\begin{itemize}preamble\item a\end{itemize}'),
            '\n  preamble\n  \N{BULLET} a\n')

    def test_enumerate_counter_beyond_ten(self):
        latex = r'\begin{enumerate}' \
            + "".join([ r'\item x' for _ in range(11) ]) \
            + r'\end{enumerate}'
        self.assertTrue(latex_to_text(latex).endswith('\n  11. x\n'))



class TestMatrixEnvironments(unittest.TestCase):
    r"""The matrix and array environments, which are rendered inline."""

    def test_pmatrix(self):
        self.assertEqual(
            latex_to_text(r'$\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}$'),
            '[ 1 2; 3 4 ]')

    def test_bmatrix_with_variables(self):
        self.assertEqual(
            latex_to_text(r'$\begin{bmatrix}a & b\end{bmatrix}$'),
            '[ ' + mvar('a') + ' ' + mvar('b') + ' ]')

    def test_empty_matrix(self):
        self.assertEqual(
            latex_to_text(r'$\begin{pmatrix}\end{pmatrix}$'), '[  ]')

    def test_array_columns_are_padded_to_a_common_width(self):
        self.assertEqual(
            latex_to_text(r'$\begin{array}{cc} 1 & 22 \\ 333 & 4 \end{array}$'),
            '[   1  22; 333   4 ]')

    def test_matrix_outside_of_math_mode(self):
        self.assertEqual(
            latex_to_text(r'\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}'),
            '[ 1 2; 3 4 ]')

    def test_a_matrix_delimits_itself_in_a_formula(self):
        # the brackets show where the object begins and ends, so a neighbour
        # hugs it
        self.assertEqual(
            latex_to_text(r'$2\begin{pmatrix}1&2\end{pmatrix}$'),
            '2[ 1 2 ]')

    def test_matrix_rendering_does_not_depend_on_the_math_mode(self):
        self.assertEqual(
            latex_to_text(r'$\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}$',
                          math_mode='text'),
            '[ 1 2; 3 4 ]')


### BEGIN_TEST_PYLATEXENC_SKIP

class TestDeprecatedModuleHelpers(unittest.TestCase):
    r"""The module-level helpers that `pylatexenc 1` offered.

    These call the deprecation machinery, which needs the `warnings` module, so
    they cannot run in the JavaScript build; they may also end up guarded out of
    that build altogether along with the rest of the legacy support code."""

    def convert(self, fn, *args, **kwargs):
        # the deprecation warnings are the point of these functions; silence
        # them so that they do not drown the test output
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return fn(*args, **kwargs)

    def test_latex2text_helper(self):
        self.assertEqual(
            self.convert(latex2text.latex2text, r'\textbf{Hi} $x+y$ there'),
            'Hi x+y there')

    def test_latex2text_helper_keep_inline_math(self):
        self.assertEqual(
            self.convert(latex2text.latex2text, r'\textbf{Hi} $x+y$',
                         keep_inline_math=True),
            'Hi $x+y$')

    def test_latex2text_helper_keep_comments(self):
        self.assertEqual(
            self.convert(latex2text.latex2text, 'a %c\nb', keep_comments=True),
            'a %c\nb')

    def test_latex2text_helper_drops_comments_by_default(self):
        self.assertEqual(self.convert(latex2text.latex2text, 'a %c\nb'),
                         'a \nb')

    def test_latexnodes2text_helper(self):
        nodelist = LatexWalker(r'\textit{ab}').parse_content(
            latexnodes_parsers.LatexGeneralNodesParser()
        )[0]
        self.assertEqual(self.convert(latex2text.latexnodes2text, nodelist), 'ab')

    def test_envdef_helper(self):
        e = self.convert(latex2text.EnvDef, 'foo', simplify_repl='X')
        self.assertEqual(e.environmentname, 'foo')
        # the pylatexenc 1 attribute name is provided as well
        self.assertEqual(e.envname, 'foo')
        self.assertEqual(e.simplify_repl, 'X')
        self.assertFalse(e.discard)

    def test_macrodef_helper(self):
        m = self.convert(latex2text.MacroDef, 'bar', simplify_repl='Y')
        self.assertEqual(m.macroname, 'bar')
        # the pylatexenc 1 attribute name is provided as well
        self.assertEqual(m.macname, 'bar')
        self.assertEqual(m.simplify_repl, 'Y')
        self.assertTrue(m.discard)

    def test_macrodef_helper_keeps_the_macro_discard_default(self):
        self.assertTrue(self.convert(latex2text.MacroDef, 'bar').discard)

    def test_envdef_helper_keeps_the_environment_discard_default(self):
        self.assertFalse(self.convert(latex2text.EnvDef, 'foo').discard)


class TestTexInputDirectory(unittest.TestCase):
    r"""``\input``, and the two methods that decide where its argument is looked
    for.  These reach the file system, so they cannot run in the JavaScript
    build."""

    def setup_input_tree(self):
        r"""Build a temporary directory holding an input file and a
        subdirectory, and give back the pair of paths."""
        root = tempfile.mkdtemp()
        with open(os.path.join(root, 'included.tex'), 'w') as f:
            f.write('included contents\n')
        subdir = os.path.join(root, 'sub')
        os.mkdir(subdir)
        return root, subdir

    def test_input_is_ignored_without_an_input_directory(self):
        self.assertEqual(latex_to_text(r'a \input{included.tex} b'), 'a  b')

    def test_read_input_file_returns_nothing_without_an_input_directory(self):
        self.assertEqual(make_l2t().read_input_file('included.tex'), '')

    def test_read_input_file_reads_the_file(self):
        root, subdir = self.setup_input_tree()
        try:
            l2t = make_l2t()
            l2t.set_tex_input_directory(root)
            self.assertEqual(l2t.read_input_file('included.tex'),
                             'included contents\n')
        finally:
            shutil.rmtree(root)

    def test_input_macro_includes_the_file(self):
        root, subdir = self.setup_input_tree()
        try:
            l2t = make_l2t()
            l2t.set_tex_input_directory(root)
            self.assertEqual(
                l2t.latex_to_text(r'a \input{included.tex} b',
                                  latex_context=get_latexwalker_default_context_db()),
                'a included contents\n b')
        finally:
            shutil.rmtree(root)

    def test_input_macro_adds_the_tex_extension(self):
        root, subdir = self.setup_input_tree()
        try:
            l2t = make_l2t()
            l2t.set_tex_input_directory(root)
            self.assertEqual(
                l2t.latex_to_text(r'a \input{included} b',
                                  latex_context=get_latexwalker_default_context_db()),
                'a included contents\n b')
        finally:
            shutil.rmtree(root)

    def test_strict_input_refuses_to_leave_the_input_directory(self):
        root, subdir = self.setup_input_tree()
        try:
            l2t = make_l2t()
            l2t.set_tex_input_directory(subdir)
            self.assertEqual(
                l2t.latex_to_text(r'a \input{../included.tex} b',
                                  latex_context=get_latexwalker_default_context_db()),
                'a  b')
        finally:
            shutil.rmtree(root)

    def test_without_strict_input_the_parent_directory_is_reachable(self):
        root, subdir = self.setup_input_tree()
        try:
            l2t = make_l2t()
            l2t.set_tex_input_directory(subdir, strict_input=False)
            self.assertEqual(
                l2t.latex_to_text(r'a \input{../included.tex} b',
                                  latex_context=get_latexwalker_default_context_db()),
                'a included contents\n b')
        finally:
            shutil.rmtree(root)

    def test_set_tex_input_directory_stores_its_arguments(self):
        l2t = make_l2t()
        l2t.set_tex_input_directory('/some/where',
                                    latex_walker_init_args={'tolerant_parsing': True},
                                    strict_input=False)
        self.assertEqual(l2t.tex_input_directory, '/some/where')
        self.assertEqual(l2t.latex_walker_init_args, {'tolerant_parsing': True})
        self.assertFalse(l2t.strict_input)

    def test_read_input_file_can_be_overridden(self):
        # the documented way of plugging in a lookup mechanism of one's own.
        # Note that `set_tex_input_directory()` is still called here even
        # though the overriding method does not use the directory: it is what
        # sets up the parse options that the inclusion machinery reads.
        class MyNodes2Text(LatexNodes2Text):
            def read_input_file(self, fn):
                return 'from ' + fn

        l2t = MyNodes2Text(latex_context=get_latex2text_default_context_db())
        l2t.set_tex_input_directory(None)
        self.assertEqual(
            l2t.latex_to_text(r'a \input{whatever} b',
                              latex_context=get_latexwalker_default_context_db()),
            'a from whatever b')

### END_TEST_PYLATEXENC_SKIP



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
