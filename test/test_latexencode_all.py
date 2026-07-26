
import unittest

import codecs
import difflib
import unicodedata
import logging
import os.path


from pylatexenc.latexencode import UnicodeToLatexEncoder




class TestLatexEncodeAll(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexEncodeAll, self).__init__(*args, **kwargs)

    def test_all(self):

        loglevel = logging.getLogger().level
        logging.getLogger().setLevel(logging.CRITICAL)

        u = UnicodeToLatexEncoder(unknown_char_policy='fail',
                                  replacement_latex_protection='braces-almost-all')

        def fn(x, bdir=os.path.realpath(os.path.abspath(os.path.dirname(__file__)))):
            return os.path.join(bdir, x)

        with codecs.open(fn('_tmp_uni_chars_test.temp.txt'), 'w', encoding='utf-8') as testf:
            
            for i in range(0x10FFFF):
                # iter over all valid unicode characters
                try:
                    chrname = unicodedata.name(chr(i)) # test if valid, i.e., it has a UNICODE NAME
                except ValueError:
                    continue

                line = "0x%04X %-50s    |%s|\n"%(i, '['+chrname+']', chr(i))

                # try to encode it using our unicode_to_latex routines
                try:
                    enc = u.unicode_to_latex(line)
                except ValueError:
                    continue
                testf.write(enc)

        with codecs.open(fn('uni_chars_test_previous.txt'), 'r', encoding='utf-8') as reff, \
             codecs.open(fn('_tmp_uni_chars_test.temp.txt'), 'r', encoding='utf-8') as testf:
            a = reff.readlines()
            b = testf.readlines()
            
        logging.getLogger().setLevel(loglevel)

        s = difflib.unified_diff(a, b,
                                 fromfile='uni_chars_test_previous.txt',
                                 tofile='_tmp_uni_chars_test.temp.txt')
        diffmsg = "".join(list(s)).strip()
        if diffmsg:
            print(diffmsg)
            raise self.failureException("Unicode coverage tests failed. See full diff above.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

