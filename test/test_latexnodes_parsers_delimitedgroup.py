import unittest
import sys
import logging


from pylatexenc.latexnodes.parsers._delimitedgroup import (
    LatexDelimitedExpressionParserInfo,
    LatexDelimitedExpressionParser,
    LatexDelimitedGroupParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
    LatexTokenReader,
    LatexToken,
    ParsingState,
    ParsedMacroArgs,
)
from pylatexenc.latexnodes.nodes import *


from _helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)




# --------------------------------------

class TestLatexDelimitedExpressionParserInfo(unittest.TestCase):
    
    def test_are_the_tests_complete(self):
        return self.assertTrue(False)




# --------------------------------------



class MyHelperTestDEPInfo(LatexDelimitedExpressionParserInfo):
    @classmethod
    def get_group_parsing_state(cls, delimiters, parsing_state):
        # simple test for a different parsing state
        return parsing_state.sub_context(enable_comments=False)
    @classmethod
    def is_opening_delimiter(cls, delimiters, first_token, group_parsing_state):
        if not ( first_token.tok == 'char' and first_token.arg == '<' ):
            logger.debug("is_opening_delimiter: not a '<' char token")
            return False
        if not cls.check_opening_delimiter(delimiters, first_token.arg):
            logger.debug("is_opening_delimiter: not compatible with delimiters = %r",
                         delimiters)
            return False
        return True

    def initialize(self):
        self.parsed_delimiters = ('<', '>')
        # make slightly different contexts so we can tell which is which
        self.contents_parsing_state = self.group_parsing_state.sub_context(
            in_math_mode=True,
        )
        self.child_parsing_state = self.group_parsing_state.sub_context(
            in_math_mode=False,
            enable_environments=False,
        )

    def stop_token_condition(self, token):
        if token.tok == 'char' and token.arg == '>':
            return True
        return False

    def handle_stop_condition_token(self, token,
                                    latex_walker, token_reader, parsing_state):
        # let's try to do nothing simply, token reader will be left on the
        # closing delimiter token
        pass


def helper_make_log_calls_expression_parser_info_class(BaseClass):

    d = {}

    class LogDEPInfo(BaseClass):
        @classmethod
        def get_group_parsing_state(cls, delimiters, parsing_state):
            d['get_group_parsing_state'] = True
            # simple test for a different parsing state
            return BaseClass.get_group_parsing_state(delimiters, parsing_state)
        @classmethod
        def is_opening_delimiter(cls, delimiters, first_token, group_parsing_state):
            d['is_opening_delimiter'] = {'first_token': first_token}
            return BaseClass.is_opening_delimiter(
                delimiters, first_token, group_parsing_state
            )

        def initialize(self):
            d['initialize'] = True
            return super(LogDEPInfo, self).initialize()

        def stop_token_condition(self, token):
            if super(LogDEPInfo, self).stop_token_condition(token):
                d['stop_token_condition'] = {'token': token}
                return True
            return False

        def handle_stop_condition_token(self, token,
                                        latex_walker, token_reader, parsing_state):
            super(LogDEPInfo, self).handle_stop_condition_token(
                token,
                latex_walker, token_reader, parsing_state
            )
            d['handle_stop_condition_token'] = {'token': token}
            return

        def make_child_parsing_state(self, parsing_state, node_class):
            d['make_child_parsing_state'] = {'node_class_is_group_node':
                                             node_class is LatexGroupNode}
            return super(LogDEPInfo, self).make_child_parsing_state(parsing_state, node_class)

        def parse_content(self, latex_walker, token_reader):
            d['parse_content'] = True
            return super(LogDEPInfo, self).parse_content(latex_walker, token_reader)

        def make_group_node_carryover_info(self, latex_walker, token_reader,
                                           nodelist, carryover_info):
            node, carryover_info = super(LogDEPInfo, self).make_group_node_carryover_info(
                latex_walker, token_reader,
                nodelist, carryover_info
            )
            d['make_group_node_carryover_info'] = {'node': node,
                                                   'carryover_info': carryover_info}
            return node, carryover_info

    return LogDEPInfo, d



class TestLatexDelimitedExpressionParser(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_parser_calls_info_important_methods(self):

        latextext = r'''<Hello t{}here>'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        LogDEPInfo, d = helper_make_log_calls_expression_parser_info_class(
            MyHelperTestDEPInfo
        )

        parser = LatexDelimitedGroupParser(
            delimiters=('<','>'),
            delimited_expression_parser_info_class=LogDEPInfo,
        )

        thenodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertTrue(d['get_group_parsing_state'])
        self.assertEqual(d['is_opening_delimiter']['first_token'].arg, '<')
        self.assertTrue(d['initialize'])
        self.assertEqual(d['stop_token_condition']['token'].arg, '>')
        self.assertEqual(d['handle_stop_condition_token']['token'],
                         d['stop_token_condition']['token'])
        self.assertTrue(d['make_child_parsing_state']['node_class_is_group_node'])
        self.assertTrue(d['parse_content'])
        self.assertTrue(d['make_group_node_carryover_info']['node'].isNodeType(
            LatexGroupNode
        ))

        psgroup = thenodes.parsing_state
        pscontents = thenodes.nodelist[0].parsing_state
        pschild = thenodes.nodelist[1].parsing_state

        self.assertEqual(psgroup.enable_comments, False)
        self.assertEqual(pscontents.in_math_mode, True)
        self.assertEqual(pschild.in_math_mode, False)
        self.assertEqual(pschild.enable_environments, False)
        
        testnodes = LatexGroupNode(
                parsing_state=psgroup,
                delimiters=('<','>'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=pscontents,
                            chars='Hello t',
                            pos=1,
                            pos_end=8,
                        ),
                        LatexGroupNode(
                            parsing_state=pschild,
                            delimiters=('{','}'),
                            nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                            pos=8,
                            pos_end=10,
                        ),
                        LatexCharsNode(
                            parsing_state=pscontents,
                            chars='here',
                            pos=10,
                            pos_end=14,
                        ),
                    ],
                    pos=1,
                    pos_end=14,
                ),
                pos=0,
                pos_end=14, # because the token reader wasn't advanced past the last delimiter
            )

        print(thenodes)
        print(testnodes)

        self.assertEqual(
            thenodes,
            testnodes
        )





    def test_are_these_tests_really_complete(self):
        
        # WRITE ME
        self.assertTrue( False )







# --------------------------------------


class TestDelimitedGroupParser(unittest.TestCase):

    def test_simple_1(self):

        latextext = r'''{Hello there}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}')
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
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
        )

    def test_stops_after_group(self):

        latextext = r'''{Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}')
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
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
        )

    def test_optional_and_group_is_present(self):

        latextext = r'''{Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            optional=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
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
        )

    def test_optional_and_group_is_not_present(self):

        latextext = r''' did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            optional=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            None
        )


    def test_automatic_detection_of_delimiters(self):

        latextext = r'''<Hello there> did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext,
                          latex_context=DummyLatexContextDb(),
                          latex_group_delimiters=[('{','}'),('<','>')],
                          )
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(delimiters=None)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('<','>'),
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
        )

    def test_automatic_closing_delimiter(self):

        latextext = r'''[Hello there] did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext,
                          latex_context=DummyLatexContextDb(),
                          latex_group_delimiters=[('{','}'),('[',']')],
                          )
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(delimiters='[')

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('[',']'),
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
        )

    def test_skip_space_albeit_unnecessary(self):

        latextext = r'''{Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            allow_pre_space=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
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
        )

    def test_does_not_skip_space_by_default(self):

        latextext = r'''   {Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
        )

        with self.assertRaises(LatexWalkerParseError):
            nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

    def test_skip_space_and_group_has_pre_space(self):

        latextext = r'''   {Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            allow_pre_space=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        # pre-space simply gets discarded, which is a strong reason not to use
        # this option at all; prefer to use robust argument parsers that can
        # keep spaces & comments between arguments. ...

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1+3,
                            pos_end=36-24+3,
                        ),
                    ],
                    pos=1+3,
                    pos_end=36-24+3,
                ),
                pos=0+3,
                pos_end=37-24+3,
            )
        )



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
