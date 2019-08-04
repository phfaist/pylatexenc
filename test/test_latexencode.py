# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import unittest
import sys
import re
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

from pylatexenc.latexencode import UnicodeToLatexEncoder, utf8tolatex
from pylatexenc import latexencode 


class _DummyContextMgr(object):
    def __enter__(self, *args, **kwargs):
        pass
    def __exit__(self, *args, **kwargs):
        pass

class ProvideAssertCmds(object):
    def assertLogs(self, *args, **kwargs):
        logging.getLogger(__name__).warning(
            "Can't check if logger generates correct warnings, skipping this check.")
        return _DummyContextMgr()


class TestLatexEncode(unittest.TestCase, ProvideAssertCmds):

    def __init__(self, *args, **kwargs):
        super(TestLatexEncode, self).__init__(*args, **kwargs)

    def test_basic_0(self):
        u = UnicodeToLatexEncoder()
        input = "\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "''\\`A votre sant\\'e!'' s'exclama le ma{\\^\\i}tre de maison \\`a 100\\%.")

    def test_basic_1(self):
        u = UnicodeToLatexEncoder(non_ascii_only=True, replacement_latex_protection='braces-all')
        input = "\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "\"{\\`A} votre sant{\\'e}!\" s'exclama le ma{\\^\\i}tre de maison {\\`a} 100%.")
        
    def test_basic_2(self):
        u = UnicodeToLatexEncoder(replacement_latex_protection='braces-after-macro')
        input = "\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "''\\`A votre sant\\'e!'' s'exclama le ma\\^\\i{}tre de maison \\`a 100\\%.")

    def test_basic_2b(self):
        u = UnicodeToLatexEncoder(replacement_latex_protection='none')
        input = "\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "''\\`A votre sant\\'e!'' s'exclama le ma\\^\\itre de maison \\`a 100\\%.")

    def test_basic_2c(self):
        u = UnicodeToLatexEncoder(non_ascii_only=True)
        ascii_chars_convert = " \" # $ % & \\ _ { } ~ "
        self.assertEqual(u.unicode_to_latex(ascii_chars_convert), ascii_chars_convert)

    def test_basic_2d(self):
        u = UnicodeToLatexEncoder(non_ascii_only=False)
        ascii_chars_convert = " \" # $ % & \\ _ { } ~ "
        self.assertEqual(u.unicode_to_latex(ascii_chars_convert),
                         " '' \\# \\$ \\% \\& {\\textbackslash} \\_ \\{ \\} {\\textasciitilde} ")

    def test_basic_3(self):
        test_unknown_chars = "A unicode character: \N{THAI CHARACTER THO THONG}"
        # generates warnings -- that's good
        with self.assertLogs(logger='pylatexenc.latexencode', level='WARNING') as cm:
            u = UnicodeToLatexEncoder(unknown_char_policy='keep')
            self.assertEqual(u.unicode_to_latex(test_unknown_chars), test_unknown_chars) # unchanged

    def test_basic_3b(self):
        test_unknown_chars = "A unicode character: \N{THAI CHARACTER THO THONG}"
        # generates warnings -- that's good
        with self.assertLogs(logger='pylatexenc.latexencode', level='WARNING') as cm:
            u = UnicodeToLatexEncoder(unknown_char_policy='replace')
            self.assertEqual(u.unicode_to_latex(test_unknown_chars),
                             "A unicode character: {\\bfseries ?}")

    def test_basic_3c(self):
        test_unknown_chars = "A unicode character: \N{THAI CHARACTER THO THONG}"
        u = UnicodeToLatexEncoder(unknown_char_policy='unihex', unknown_char_warning=False)

        self.assertEqual(u.unicode_to_latex(test_unknown_chars),
                         "A unicode character: \\ensuremath{\\langle}\\texttt{U+0E18}\\ensuremath{\\rangle}")



    def test_rules_00(self):
        
        def acallable(s, pos):
            if s[pos] == "\N{LATIN SMALL LETTER E WITH ACUTE}":
                return (1, r"{\'{e}}")
            if s.startswith('...', pos):
                return (3, r"\ldots")
            return None

        u = UnicodeToLatexEncoder(conversion_rules=[
            latexencode.UnicodeToLatexConversionRule(latexencode.RULE_DICT, {
                ord("\N{LATIN CAPITAL LETTER A WITH GRAVE}"): r"{{\`{A}}}",
                ord("%"): r"\textpercent",
            }),
            latexencode.UnicodeToLatexConversionRule(latexencode.RULE_REGEX, [
                (re.compile('v(otre)'), r'n\1'),
                (re.compile("s'exclama", flags=re.I), r"s'exprima"),
                (re.compile('\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}'), r"{\^i}"),
            ]),
        ] + latexencode.get_builtin_conversion_rules('defaults') + [
            latexencode.UnicodeToLatexConversionRule(latexencode.RULE_CALLABLE, acallable),
        ])
        input = "\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison ... \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "''{{\\`{A}}} notre sant\\'e!'' s'exprima le ma{\\^i}tre de maison {\\ldots} \\`a 100{\\textpercent}.")

    def test_rules_01(self):
        
        def acallable(s, pos):
            if s[pos] == "\N{LATIN SMALL LETTER E WITH ACUTE}":
                return (1, r"{\'{e}}")
            if s.startswith('...', pos):
                return (3, r"\ldots")
            return None

        u = UnicodeToLatexEncoder(conversion_rules=[
            latexencode.UnicodeToLatexConversionRule(latexencode.RULE_DICT, {
                ord("\N{LATIN CAPITAL LETTER A WITH GRAVE}"): r"{{\`{A}}}",
                ord("%"): r"\textpercent",
            }),
            latexencode.UnicodeToLatexConversionRule(latexencode.RULE_REGEX, [
                (re.compile('v(otre)'), r'n\1'),
                (re.compile("s'exclama", flags=re.I), r"s'exprima"),
                (re.compile('\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}'), r"{\^i}"),
            ]),
            'unicode-xml', # expand built-in rule names
            latexencode.UnicodeToLatexConversionRule(latexencode.RULE_CALLABLE, acallable),
        ])
        input = "\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison ... \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "\"{{\\`{A}}} notre sant\\'{e}!\" s'exprima le ma{\\^i}tre de maison {\\ldots} \\`{a} 100{\\textpercent}.")

    def test_rules_02(self):
        # based on test_basic_0()
        u = UnicodeToLatexEncoder(conversion_rules=['defaults'])
        #u = UnicodeToLatexEncoder()
        input = "* \"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama\N{SUPERSCRIPT TWO} le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "* ''\\`A votre sant\\'e!'' s'exclama{\\texttwosuperior} le ma{\\^\\i}tre de maison \\`a 100\\%.")

    def test_rules_03(self):
        u = UnicodeToLatexEncoder(conversion_rules=['unicode-xml'])
        input = "* \"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama\N{SUPERSCRIPT TWO} le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(u.unicode_to_latex(input),
                         "{\\ast} \"\\`{A} votre sant\\'{e}!\" s{\\textquotesingle}exclama{^2} le ma\\^{\\i}tre de maison \\`{a} 100\\%.")


    def test_issue_no21(self):
        # test for https://github.com/phfaist/pylatexenc/issues/21
        
        def capitalize_acronyms(s, pos):
            if s[pos] in ('{', '}'):
                # preserve existing braces
                return (1, s[pos])
            m = re.compile(r'\b[A-Z]{2,}\w*\b').match(s, pos)
            if m is None:
                return None
            return (m.end()-m.start(), "{" + m.group() + "}")

        u = UnicodeToLatexEncoder(
            conversion_rules=[
                latexencode.UnicodeToLatexConversionRule(latexencode.RULE_CALLABLE, capitalize_acronyms),
            ] + latexencode.get_builtin_conversion_rules('defaults')
        )
        input = "Title with {Some} ABC acronyms LIKe this."
        self.assertEqual(
            u.unicode_to_latex(input),
            "Title with {Some} {ABC} acronyms {LIKe} this."
        )

        u = UnicodeToLatexEncoder(
            conversion_rules=[
                latexencode.UnicodeToLatexConversionRule(
                    latexencode.RULE_REGEX,
                    [ (re.compile(r'([{}])'), r'\1'), # keep existing braces
                      (re.compile(r'\b([A-Z]{2,}\w*)\b'), r'{\1}'), ]
                ),
            ] + latexencode.get_builtin_conversion_rules('defaults')
        )
        input = "Title with {Some} ABC acronyms LIKe this."
        self.assertEqual(
            u.unicode_to_latex(input),
            "Title with {Some} {ABC} acronyms {LIKe} this."
        )



    def test_latex_string_class(self):
        
        class LatexChunkList:
            def __init__(self):
                self.chunks = []

            def __iadd__(self, s):
                self.chunks.append(s)
                return self

        u = UnicodeToLatexEncoder(latex_string_class=LatexChunkList,
                                  replacement_latex_protection='none')
        result = u.unicode_to_latex("A é → α")
        # result is an object of custom type LatexChunkList
        self.assertEqual(
            result.chunks,
            ['A', ' ', r'\'e', ' ', r'\textrightarrow', ' ', r'\ensuremath{\alpha}']
        )



class TestUtf8tolatex(unittest.TestCase, ProvideAssertCmds):

    def __init__(self, *args, **kwargs):
        super(TestUtf8tolatex, self).__init__(*args, **kwargs)


    def test_basic(self):

        input = "\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(utf8tolatex(input),
                         "''{\\`A} votre sant{\\'e}!'' s'exclama le ma{\\^\\i}tre de maison {\\`a} 100{\\%}.")

        self.assertEqual(utf8tolatex(input, non_ascii_only=True),
                         "\"{\\`A} votre sant{\\'e}!\" s'exclama le ma{\\^\\i}tre de maison {\\`a} 100%.")
        
        # TODO: in the future, be clever and avoid breaking macros like this ("\itre"):
        self.assertEqual(utf8tolatex(input, brackets=False),
                         "''\\`A votre sant\\'e!'' s'exclama le ma\\^\\itre de maison \\`a 100\\%.")

        ascii_chars_convert = " \" # $ % & \\ _ { } ~ "
        self.assertEqual(utf8tolatex(ascii_chars_convert, non_ascii_only=True),
                         ascii_chars_convert)
        self.assertEqual(utf8tolatex(ascii_chars_convert, non_ascii_only=False),
                         " '' {\\#} {\\$} {\\%} {\\&} {\\textbackslash} {\\_} {\\{} {\\}} {\\textasciitilde} ")
        

        test_bad_chars = "A unicode character: \N{THAI CHARACTER THO THONG}"
        # generates warnings -- that's good
        with self.assertLogs(logger='pylatexenc.latexencode', level='WARNING') as cm:
            self.assertEqual(utf8tolatex(test_bad_chars, substitute_bad_chars=False),
                             test_bad_chars) # unchanged
        with self.assertLogs(logger='pylatexenc.latexencode', level='WARNING') as cm:
            self.assertEqual(utf8tolatex(test_bad_chars, substitute_bad_chars=True),
                             "A unicode character: {\\bfseries ?}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

