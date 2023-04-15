import unittest
import logging
logger = logging.getLogger(__name__)


from pylatexenc.latexnodes._tokenreaderbase import (
    LatexTokenReaderBase,
    LatexTokenListTokenReader,
)

from pylatexenc.latexnodes import (
    LatexWalkerEndOfStream,
    LatexToken,
    ParsingState,
)




class TestTokenReaderBase(unittest.TestCase):

    def test_make_token(self):
        tb = LatexTokenReaderBase()
        
        self.assertEqual(
            tb.make_token(tok='char', arg='*', pos=3),
            LatexToken(tok='char', arg='*', pos=3)
        )

    def test_peek_token_or_none(self):

        class MyTokenReader(LatexTokenReaderBase):
            def __init__(self, at_end=False):
                super(MyTokenReader, self).__init__()
                self.at_end = at_end

            def peek_token(self, parsing_state):
                if not self.at_end:
                    return self.make_token(tok='char', arg='-', pos=5)
                raise LatexWalkerEndOfStream()

        ps = ParsingState()

        tb = MyTokenReader(False)
        self.assertEqual( tb.peek_token_or_none(ps),
                          LatexToken(tok='char', arg='-', pos=5) )
        tb = MyTokenReader(True)
        self.assertIsNone( tb.peek_token_or_none(ps) )



class TestTokenReaderTokenList(unittest.TestCase):

    def test_reads_tokens(self):
        
        tlist = [
            LatexToken(tok='char', arg='a', pos=0, pos_end=1, pre_space=''),
            LatexToken(tok='char', arg='b', pos=1, pos_end=1+2, pre_space=''),
            LatexToken(tok='macro', arg='relax', pos=2, pos_end=2+2+len(r'\relax'),
                       pre_space='', post_space='\t '),
        ]

        tr = LatexTokenListTokenReader(tlist)
        
        ps = ParsingState()

        self.assertEqual(tr.peek_token(ps), tlist[0])
        self.assertEqual(tr.peek_token(ps), tlist[0])

        self.assertEqual(tr.cur_pos(), tlist[0].pos)

        self.assertEqual(tr.next_token(ps), tlist[0])

        self.assertEqual(tr.peek_token(ps), tlist[1])
        self.assertEqual(tr.peek_token(ps), tlist[1])
        
        self.assertEqual(tr.next_token(ps), tlist[1])
        
        self.assertEqual(tr.next_token(ps), tlist[2])

        tr.move_to_token(tlist[1])

        self.assertEqual(tr.next_token(ps), tlist[1])
        
        tr.move_past_token(tlist[0])

        self.assertEqual(tr.next_token(ps), tlist[1])

        self.assertEqual(tr.cur_pos(), tlist[2].pos)




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
