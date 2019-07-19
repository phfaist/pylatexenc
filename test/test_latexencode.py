
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


class TestLatexEncode(unittest.TestCase):

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

    def test_basic_2b(self):

        u = UnicodeToLatexEncoder(non_ascii_only=True)
        ascii_chars_convert = " \" # $ % & \\ _ { } ~ "
        self.assertEqual(u.unicode_to_latex(ascii_chars_convert), ascii_chars_convert)

    def test_basic_2c(self):

        u = UnicodeToLatexEncoder(non_ascii_only=False)
        ascii_chars_convert = " \" # $ % & \\ _ { } ~ "
        self.assertEqual(u.unicode_to_latex(ascii_chars_convert),
                         " '' \\# \\$ \\% \\& {\\textbackslash} \\_ \\{ \\} {\\textasciitilde} ")
    def test_basic_3(self):

        # generates warnings -- that's good
        test_bad_chars = "A unicode character: \N{THAI CHARACTER THO THONG}"
        u = UnicodeToLatexEncoder(bad_char_policy='keep')
        self.assertEqual(u.unicode_to_latex(test_bad_chars), test_bad_chars) # unchanged

    def test_basic_3b(self):

        # generates warnings -- that's good
        test_bad_chars = "A unicode character: \N{THAI CHARACTER THO THONG}"
        u = UnicodeToLatexEncoder(bad_char_policy='replace')

        self.assertEqual(u.unicode_to_latex(test_bad_chars),
                         "A unicode character: {\\bfseries ?}")



    def test_rules(self):
        
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

        



class TestUtf8tolatex(unittest.TestCase):

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
        

        # generates warnings -- that's good
        test_bad_chars = "A unicode character: \N{THAI CHARACTER THO THONG}"
        self.assertEqual(utf8tolatex(test_bad_chars, substitute_bad_chars=False),
                         test_bad_chars) # unchanged
        self.assertEqual(utf8tolatex(test_bad_chars, substitute_bad_chars=True),
                         "A unicode character: {\\bfseries ?}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

