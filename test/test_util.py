import unittest

from pylatexenc import _util


class TestLineNumbersCalculator(unittest.TestCase):
    
    def test_simple(self):

        s = """\
one
two
three
four
five
""".lstrip()

        ln = _util.LineNumbersCalculator(s)

        self.assertEqual( ln.pos_to_lineno_colno(0), (1,0) )
        self.assertEqual( ln.pos_to_lineno_colno(1), (1,1) )
        self.assertEqual( ln.pos_to_lineno_colno(2), (1,2) )
        self.assertEqual( ln.pos_to_lineno_colno(3), (1,3) )
        self.assertEqual( ln.pos_to_lineno_colno(4), (2,0) )
        self.assertEqual( ln.pos_to_lineno_colno(5), (2,1) )
        self.assertEqual( ln.pos_to_lineno_colno(6), (2,2) )
        self.assertEqual( ln.pos_to_lineno_colno(7), (2,3) )
        self.assertEqual( ln.pos_to_lineno_colno(8), (3,0) )
        self.assertEqual( ln.pos_to_lineno_colno(9), (3,1) )

        self.assertEqual( ln.pos_to_lineno_colno(23), (5,4) )

    def test_as_dict(self):
        
        s = """\
one
two
three
four
five
""".lstrip()

        ln = _util.LineNumbersCalculator(s)

        self.assertEqual( ln.pos_to_lineno_colno(9, as_dict=True),
                          { 'lineno': 3,
                            'colno': 1 } )
