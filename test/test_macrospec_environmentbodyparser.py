import unittest


from pylatexenc.macrospec._environmentbodyparser import (
    LatexEnvironmentBodyContentsParser,
)

from pylatexenc.latexnodes import (
    LatexTokenReader,
    LatexArgumentSpec,
    ParsedArguments,
)
from pylatexenc.latexnodes.nodes import *
from pylatexenc.macrospec import (
    LatexContextDb,
    MacroSpec,
    ParsingStateDeltaExtendLatexContextDb,
)
from pylatexenc.latexwalker import LatexWalker

# from ._helpers_tests import (
# )



class TestEnvironmentBodyContentsParser(unittest.TestCase):

    maxDiff = None

    def test_simple_1(self):
        
        # \begin{environment}
        latextext = r'''a+b=c\end{environment}'''

        tr = LatexTokenReader(latextext)
        lw = LatexWalker(latextext, latex_context=LatexContextDb())
        ps = lw.make_parsing_state()

        print("ps = ", ps)

        parser = LatexEnvironmentBodyContentsParser('environment')
        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        latex_walker=lw,
                        chars='a+b=c',
                        pos=0,
                        pos_end=5,
                    ),
                ],
                pos=0,
                pos_end=5,
            )
        )

    def test_contents_and_child_parsing_state_delta(self):
        
        # \begin{enumerate}
        latextext = r'''
\item A \textbf{\localcommand}\end{enumerate}'''.lstrip()

        latex_context = LatexContextDb()
        latex_context.add_context_category(
            'main-context-category',
            macros=[
                MacroSpec("textbf", '{')
            ]
        )

        tr = LatexTokenReader(latextext)
        lw = LatexWalker(latextext, latex_context=latex_context, tolerant_parsing=False)
        ps = lw.make_parsing_state()

        print("ps = ", ps)

        ps_content_delta = ParsingStateDeltaExtendLatexContextDb(
            extend_latex_context=dict(
                macros=[
                    MacroSpec("item", ''),
                ]
            )
        )
        ps_child_delta = ParsingStateDeltaExtendLatexContextDb(
            extend_latex_context=dict(
                macros=[
                    MacroSpec("localcommand", ''),
                ]
            )
        )

        parser = LatexEnvironmentBodyContentsParser(
            'enumerate',
            contents_parsing_state_delta=ps_content_delta,
            child_parsing_state_delta=ps_child_delta,
        )
        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        ps_content = nodes[1].parsing_state
        ps_child = nodes[0].parsing_state
        
        print("ps_content =", ps_content)
        print("ps_child =", ps_child)

        nodes_expected = LatexNodeList(
            [
                LatexMacroNode(
                    parsing_state=ps_child,
                    latex_walker=lw,
                    macroname='item',
                    spec=ps_content.latex_context.get_macro_spec('item'),
                    nodeargd=ParsedArguments(argnlist=LatexNodeList([]),),
                    pos=0,
                    pos_end=6,
                    macro_post_space=' ',
                ),
                LatexCharsNode(
                    parsing_state=ps_content,
                    latex_walker=lw,
                    chars='A ',
                    pos=6,
                    pos_end=8,
                ),
                LatexMacroNode(
                    parsing_state=ps_child,
                    latex_walker=lw,
                    macroname='textbf',
                    spec=ps.latex_context.get_macro_spec('textbf'),
                    nodeargd=ParsedArguments(
                        argnlist=[
                            LatexGroupNode(
                                parsing_state=ps_child,
                                latex_walker=lw,
                                delimiters=('{','}'),
                                nodelist=LatexNodeList(
                                    [
                                        LatexMacroNode(
                                            parsing_state=ps_child,
                                            latex_walker=lw,
                                            spec=ps_child.latex_context \
                                                .get_macro_spec('localcommand'),
                                            macroname='localcommand',
                                            nodeargd=ParsedArguments(
                                                argnlist=LatexNodeList([]),
                                            ),
                                            pos=16,
                                            pos_end=29,
                                            macro_post_space='',
                                        ),
                                    ],
                                    pos=16,
                                    pos_end=29,
                                ),
                                pos=15,
                                pos_end=30,
                            )
                        ],
                        arguments_spec_list=[
                            LatexArgumentSpec(argname=None, parser='{'),
                        ],
                    ),
                    pos=8,
                    pos_end=30,
                    macro_post_space='',
                ),
            ],
            pos=0,
            pos_end=30,
        )

        print(nodes)
        print(nodes_expected)

        self.assertIsNotNone( ps_content.latex_context.get_macro_spec('item') )
        self.assertIsNone( ps_content.latex_context.get_macro_spec('localcommand') )

        self.assertIsNone( ps_child.latex_context.get_macro_spec('item') )
        self.assertIsNotNone( ps_child.latex_context.get_macro_spec('localcommand') )


        self.assertEqual(
            nodes,
            nodes_expected
        )

if __name__ == '__main__':
    unittest.main()
