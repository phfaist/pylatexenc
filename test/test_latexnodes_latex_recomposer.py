import unittest
import logging
logger = logging.getLogger(__name__)


from pylatexenc.latexnodes._latex_recomposer import (
    LatexNodesLatexRecomposer
)

from pylatexenc.latexnodes import (
    ParsingState, ParsedArguments
)
from pylatexenc.latexnodes.nodes import (
    LatexCharsNode, LatexGroupNode, LatexMacroNode, LatexEnvironmentNode, LatexSpecialsNode,
    LatexCommentNode, LatexMathNode, LatexNodeList
)

from ._helpers_tests import (
    #DummyWalker,
    DummyLatexContextDb,
)



class TestLatexNodesLatexRecomposer(unittest.TestCase):

    def test_recompose_simple(self):

        ps = ParsingState(s=None, latex_context=DummyLatexContextDb())

        node = LatexGroupNode(
            parsing_state=ps,
            delimiters=('{','}'),
            nodelist=LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='Hello there',
                        pos=1,
                        pos_end=36-24,
                    ),
                ],
                pos=1,
                pos_end=36-24,
            ),
            pos=0,
            pos_end=37-24,
        )

        self.assertEqual(
            LatexNodesLatexRecomposer().latex_recompose(node),
            r"{Hello there}"
        )

    def test_ribufg9eoihwuabjfdks(self):

        ps = ParsingState(s=None, latex_context=DummyLatexContextDb())

        nodelist = LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars=' \n \t ',
                        pos=0,
                        pos_end=5,
                    ),
                    LatexGroupNode(
                        parsing_state=ps,
                        nodelist=LatexNodeList(
                            [
                                LatexCharsNode(
                                    parsing_state=ps,
                                    chars='char',
                                    pos=6,
                                    pos_end=10,
                                ),
                            ],
                            parsing_state=ps,
                        ),
                        delimiters=('{','}'),
                        pos=5,
                        pos_end=11,
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='acters',
                        pos=11,
                        pos_end=17,
                    ),
                ],
            )

        self.assertEqual(
            LatexNodesLatexRecomposer().latex_recompose(nodelist),
            ' \n \t {char}acters'
        )


    def test_ribufgfdsafds9eoihwuabjfdks(self):
 
        ps = ParsingState(s=None, latex_context=DummyLatexContextDb())
        psm = ps.sub_context(in_math_mode=True)

        nodelist = LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='Hello, ',
                    ),
                    LatexMacroNode(
                        parsing_state=ps,
                        macroname='myname',
                        nodeargd=ParsedArguments(argspec='<', argnlist=[
                            LatexGroupNode(
                                parsing_state=ps,
                                delimiters=('<', '>'),
                                nodelist=[
                                    LatexCharsNode(parsing_state=ps, chars='NAME',)
                                ],)
                        ]),
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='.'
                    ),
                    LatexSpecialsNode(
                        parsing_state=ps,
                        specials_chars='\n\n',
                        nodeargd=None
                    ),
                    LatexEnvironmentNode(
                        parsing_state=ps,
                        environmentname='figure',
                        nodeargd=ParsedArguments(argspec='[', argnlist=[
                            LatexGroupNode(
                                parsing_state=ps,
                                delimiters=('[', ']'),
                                nodelist=[
                                    LatexCharsNode(parsing_state=ps, chars='h!',)
                                ],)
                        ]),
                        nodelist=LatexNodeList([
                            LatexCharsNode(
                                parsing_state=ps,
                                chars='\nSome math: ',
                            ),
                            LatexMathNode(
                                parsing_state=ps,
                                displaytype='inline',
                                delimiters=(r'\(', r'\)'),
                                nodelist=[
                                    LatexMacroNode(
                                        parsing_state=psm,
                                        macroname='vec',
                                        macro_post_space=' ',
                                        nodeargd=ParsedArguments(
                                            argspec='{',
                                            argnlist=[
                                                LatexCharsNode(
                                                    parsing_state=psm,
                                                    chars='b',
                                                )
                                            ]),
                                    )
                                ]),
                        ]),
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='\n',
                    ),
                    LatexCommentNode(
                        parsing_state=ps,
                        comment='%% this is a comment',
                        comment_post_space='\n',
                    ),
                    LatexMacroNode(
                        parsing_state=ps,
                        macroname=r'mymacro',
                        macro_post_space='\n',
                        nodeargd=ParsedArguments(
                                            argspec='*',
                                            argnlist=[
                                                None
                                            ]),
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars="That's all, folks!\n",
                    ),
                ],
            )

        self.assertEqual(
            LatexNodesLatexRecomposer().latex_recompose(nodelist),
            r"""
Hello, \myname<NAME>.

\begin{figure}[h!]
Some math: \(\vec b\)\end{figure}
%%% this is a comment
\mymacro
That's all, folks!
""".lstrip()
        )






if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
