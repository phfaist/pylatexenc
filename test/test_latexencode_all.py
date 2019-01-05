
from __future__ import unicode_literals

import unittest

import sys
import codecs
import difflib
import unicodedata
import logging


if sys.version_info.major >= 3:
    PY3 = True
else:
    PY3 = False

if PY3:
    def unicode(string): return string
    basestring = str
    unichr = chr
else:
    range = xrange


from pylatexenc.latexencode import utf8tolatex




class TestLatexEncode(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexEncode, self).__init__(*args, **kwargs)

    def test_pythonunicoderange(self):
        self.assertGreater(sys.maxunicode, 0xFFFF+1,
                           "Your python build only supports unicode characters up to U+FFFF."
                           " Tests of unicode coverage will fail.")

    def test_all(self):

        logging.getLogger().setLevel(logging.CRITICAL)

        with codecs.open('_tmp_uni_chars_test.temp.txt', 'w', encoding='utf-8') as testf:
            
            for i in range(0x10FFFF):
                # iter over all valid unicode characters
                try:
                    chrname = unicodedata.name(unichr(i)) # test if valid, i.e., it has a UNICODE NAME
                except ValueError:
                    continue

                line = "0x%04X %-50s    |%s|\n"%(i, '['+chrname+']', unichr(i))

                # try to encode it using utf8tolatex
                try:
                    enc = utf8tolatex(line, fail_bad_chars=True)
                except ValueError:
                    continue
                testf.write(enc)

        with codecs.open('uni_chars_test_previous.txt', 'r', encoding='utf-8') as reff, \
             codecs.open('_tmp_uni_chars_test.temp.txt', 'r', encoding='utf-8') as testf:
            a = reff.readlines()
            b = testf.readlines()
            
        s = difflib.unified_diff(a, b,
                                 fromfile='uni_chars_test_previous.txt',
                                 tofile='_tmp_uni_chars_test.temp.txt')
        diffmsg = "".join(list(s)).strip()
        if diffmsg:
            print(diffmsg)
            raise self.failureException("Unicode coverage tests failed. See full diff above.")


if __name__ == '__main__':
    unittest.main()
#

