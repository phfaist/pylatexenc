import unittest
import sys
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

from pylatexenc.latexencode import utf8tolatex


class TestLatexEncode(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexEncode, self).__init__(*args, **kwargs)

    def test_basic(self):

        input = u"\"\N{LATIN CAPITAL LETTER A WITH GRAVE} votre sant\N{LATIN SMALL LETTER E WITH ACUTE}!\" s'exclama le ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre de maison \N{LATIN SMALL LETTER A WITH GRAVE} 100%."
        self.assertEqual(utf8tolatex(input),
                         u"''{\\`A} votre sant{\\'e}!'' s'exclama le ma{\\^\\i}tre de maison {\\`a} 100{\\%}.")

        self.assertEqual(utf8tolatex(input, non_ascii_only=True),
                         u"\"{\\`A} votre sant{\\'e}!\" s'exclama le ma{\\^\\i}tre de maison {\\`a} 100%.")
        
        # TODO: in the future, be clever and avoid breaking macros like this ("\itre"):
        self.assertEqual(utf8tolatex(input, brackets=False),
                         u"''\\`A votre sant\\'e!'' s'exclama le ma\\^\\itre de maison \\`a 100\%.")

        ascii_chars_convert = u" \" # $ % & \\ _ { } ~ "
        self.assertEqual(utf8tolatex(ascii_chars_convert, non_ascii_only=True),
                         ascii_chars_convert)
        self.assertEqual(utf8tolatex(ascii_chars_convert, non_ascii_only=False),
                         u" '' {\\#} {\\$} {\\%} {\\&} {\\textbackslash} {\\_} {\\{} {\\}} {\\textasciitilde} ")
        

        # generates warnings -- that's good
        test_bad_chars = u"A unicode character: \N{THAI CHARACTER THO THONG}"
        self.assertEqual(utf8tolatex(test_bad_chars, substitute_bad_chars=False),
                         test_bad_chars) # unchanged
        self.assertEqual(utf8tolatex(test_bad_chars, substitute_bad_chars=True),
                         u"A unicode character: {\\bfseries ?}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

