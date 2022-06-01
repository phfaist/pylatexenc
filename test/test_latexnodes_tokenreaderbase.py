import unittest
import logging


from pylatexenc.latexnodes._token import (
    LatexToken
)

from pylatexenc.latexnodes._parsingstate import (
    ParsingState
)

from pylatexenc.latexnodes._tokenreaderbase import (
    LatexTokenListTokenReader
)


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
