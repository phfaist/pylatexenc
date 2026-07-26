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
from pylatexenc.latexnodes import parsers

from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
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

    def test_cur_pos_past_end_of_token_list(self):

        tlist = [
            LatexToken(tok='char', arg='a', pos=0, pos_end=1, pre_space=''),
            LatexToken(tok='char', arg='b', pos=1, pos_end=2, pre_space=''),
        ]

        tr = LatexTokenListTokenReader(tlist)

        ps = ParsingState()

        tr.next_token(ps)
        tr.next_token(ps)

        # we're past the last token now.  Reporting the current position must
        # still work (e.g., end-of-stream handlers query the position after
        # having read the last token); it reports the end position.
        self.assertEqual(tr.cur_pos(), 2)
        self.assertEqual(tr.final_pos(), 2)

    def test_cur_pos_empty_token_list(self):

        tr = LatexTokenListTokenReader([])

        self.assertIsNone(tr.cur_pos())

    def test_parse_content_with_exhausted_token_list(self):
        # an end-to-end check: collecting nodes from a token list must return
        # the nodes that were collected, and not choke on the end of the token
        # list
        tlist = [
            LatexToken(tok='char', arg='a', pos=0, pos_end=1, pre_space=''),
            LatexToken(tok='char', arg='b', pos=1, pos_end=2, pre_space=''),
        ]

        tr = LatexTokenListTokenReader(tlist)

        lw = DummyWalker()
        ps = ParsingState(s=None, latex_context=DummyLatexContextDb())

        nodes, parsing_state_delta = lw.parse_content(
            parsers.LatexGeneralNodesParser(),
            token_reader=tr,
            parsing_state=ps,
        )

        self.assertIsNotNone(nodes)
        self.assertEqual(len(nodes.nodelist), 1)
        self.assertEqual(nodes.nodelist[0].chars, 'ab')




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
