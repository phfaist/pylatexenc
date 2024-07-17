import unittest
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes._parsedargsinfo import (
    SingleParsedArgumentInfo,
    ParsedArgumentsInfo,
)

from pylatexenc.latexnodes._parsedargs import (
    LatexArgumentSpec,
    ParsedArguments,
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
)
from pylatexenc.latexnodes.nodes import *

#from ._helpers_tests import (
# DummyWalker,
# DummyLatexContextDb,
#)



class TestSingleParsedArgumentInfo(unittest.TestCase):

    maxDiff = None

    # --

    def test_was_provided_if_provided(self):
        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            chars='Hello world',
                            pos=13,
                            pos_end=13+11, # 11 == len('Hello world')
                        ),
                    ]
                )
            )
        )
        self.assertTrue(arginfo.was_provided())

    def test_was_provided_if_provided_even_with_None_item(self):
        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        None,
                    ]
                )
            )
        )
        self.assertTrue(arginfo.was_provided())

    def test_was_provided_if_not_provided(self):
        arginfo = SingleParsedArgumentInfo(
            None,
        )
        self.assertFalse(arginfo.was_provided())


    def test_get_content_nodelist_with_group(self):
        grpnode = LatexGroupNode(
            delimiters=('{','}'),
            nodelist=LatexNodeList(
                [
                    LatexCharsNode(
                        chars='Hello world',
                        pos=13,
                        pos_end=13+11, # 11 == len('Hello world')
                    ),
                    None,
                    LatexCommentNode(
                        comment=' a comment',
                        pos=13+11,
                        pos_end=13+11+12, # 12 == len('% a comment\n')
                    ),
                ],
            ),
        )

        arginfo = SingleParsedArgumentInfo( grpnode )

        self.assertEqual(arginfo.get_content_nodelist(), grpnode.nodelist)

    def test_get_content_nodelist_with_charsnode(self):
        chrnode = LatexCharsNode(
            chars='Hello world',
            pos=13,
            pos_end=13+11, # 11 == len('Hello world')
        )

        arginfo = SingleParsedArgumentInfo( chrnode )

        self.assertEqual(arginfo.get_content_nodelist(), LatexNodeList([chrnode]))

    def test_get_content_nodelist_with_nodelist(self):
        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='Hello world',
                    pos=13,
                    pos_end=13+11, # 11 == len('Hello world')
                ),
                None,
                LatexCommentNode(
                    comment=' a comment',
                    pos=13+11,
                    pos_end=13+11+12, # 12 == len('% a comment\n')
                ),
            ],
        )

        arginfo = SingleParsedArgumentInfo( nodelist )

        self.assertEqual(arginfo.get_content_nodelist(), nodelist)


    def test_get_content_as_chars(self):
        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            chars='Hello world',
                            pos=13,
                            pos_end=13+11, # 11 == len('Hello world')
                        ),
                        None,
                        LatexCommentNode(
                            comment=' a comment',
                            pos=13+11,
                            pos_end=13+11+12, # 12 == len('% a comment\n')
                        ),
                    ],
                ),
            )
        )

        self.assertEqual(arginfo.get_content_as_chars(),
                         'Hello world')


    def test_get_content_as_chars_single_arg_node(self):
        arginfo = SingleParsedArgumentInfo(
            LatexCharsNode(
                chars='Hello world',
                pos=13,
                pos_end=13+11, # 11 == len('Hello world')
            ),
        )

        self.assertEqual(arginfo.get_content_as_chars(),
                         'Hello world')

        
    def test_get_content_as_chars_fails_with_invalid_node_type(self):

        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            chars='Hello world',
                            pos=13,
                            pos_end=13+11, # 11 == len('Hello world')
                        ),
                        None,
                        LatexMacroNode(
                            macroname='hello',
                            nodeargd=ParsedArguments(),
                            pos=13+11,
                            pos_end=13+11+6, # 6 == len(r'\hello')
                        ),
                        LatexCommentNode(
                            comment=' a comment',
                            pos=13+11+6,
                            pos_end=13+11+6+12, # 12 == len('% a comment\n')
                        ),
                    ],
                ),
            )
        )

        with self.assertRaises(LatexWalkerParseError):
            _ = arginfo.get_content_as_chars()




class TestParsedArgumentsInfo(unittest.TestCase):

    maxDiff = None

    def test_get_all_arguments_info_noargs(self):

        parsed_args = ParsedArguments(
            arguments_spec_list=[
                LatexArgumentSpec('{', argname='content'),
                LatexArgumentSpec('[', argname='an-optional-arg'),
                LatexArgumentSpec('{', argname=None),
            ],
            argnlist=[
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexCharsNode(
                                chars='Hello world',
                                pos=13,
                                pos_end=13+11, # 11 == len('Hello world')
                            ),
                            None,
                            LatexMacroNode(
                                macroname='hello',
                                nodeargd=ParsedArguments(),
                                pos=13+11,
                                pos_end=13+11+6, # 6 == len(r'\hello')
                            ),
                            LatexCommentNode(
                                comment=' a comment',
                                pos=13+11+6,
                                pos_end=13+11+6+12, # 12 == len('% a comment\n')
                            ),
                        ],
                    ),
                ),
                None,
                LatexMacroNode(
                    macroname='Z',
                    nodeargd=ParsedArguments(),
                    pos=13+11+6+12,
                    pos_end=13+11+6+12+1,
                ),
            ]
        )
        
        myall = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info()

        self.assertEqual(
            myall,
            {
                0: SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                'content': SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                1: SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                'an-optional-arg': SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                2: SingleParsedArgumentInfo(parsed_args.argnlist[2]),
            }
        )

    def test_get_all_arguments_info_withallargsbyindex(self):

        parsed_args = ParsedArguments(
            arguments_spec_list=[
                LatexArgumentSpec('{', argname='content'),
                LatexArgumentSpec('[', argname='an-optional-arg'),
                LatexArgumentSpec('{', argname=None),
            ],
            argnlist=[
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexCharsNode(
                                chars='Hello world',
                                pos=13,
                                pos_end=13+11, # 11 == len('Hello world')
                            ),
                            None,
                            LatexMacroNode(
                                macroname='hello',
                                nodeargd=ParsedArguments(),
                                pos=13+11,
                                pos_end=13+11+6, # 6 == len(r'\hello')
                            ),
                            LatexCommentNode(
                                comment=' a comment',
                                pos=13+11+6,
                                pos_end=13+11+6+12, # 12 == len('% a comment\n')
                            ),
                        ],
                    ),
                ),
                None,
                LatexMacroNode(
                    macroname='Z',
                    nodeargd=ParsedArguments(),
                    pos=13+11+6+12,
                    pos_end=13+11+6+12+1,
                ),
            ]
        )
        
        myall = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info(
            [0, 1, 2]
        )

        self.assertEqual(
            myall,
            {
                0: SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                #'content': SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                1: SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                #'an-optional-arg': SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                2: SingleParsedArgumentInfo(parsed_args.argnlist[2]),
            }
        )

    def test_get_all_arguments_info_withallargsbyindex_2(self):

        parsed_args = ParsedArguments(
            arguments_spec_list=[
                LatexArgumentSpec('{', argname='content'),
                LatexArgumentSpec('[', argname='an-optional-arg'),
                LatexArgumentSpec('{', argname=None),
            ],
            argnlist=[
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexCharsNode(
                                chars='Hello world',
                                pos=13,
                                pos_end=13+11, # 11 == len('Hello world')
                            ),
                            None,
                            LatexMacroNode(
                                macroname='hello',
                                nodeargd=ParsedArguments(),
                                pos=13+11,
                                pos_end=13+11+6, # 6 == len(r'\hello')
                            ),
                            LatexCommentNode(
                                comment=' a comment',
                                pos=13+11+6,
                                pos_end=13+11+6+12, # 12 == len('% a comment\n')
                            ),
                        ],
                    ),
                ),
                None,
                LatexMacroNode(
                    macroname='Z',
                    nodeargd=ParsedArguments(),
                    pos=13+11+6+12,
                    pos_end=13+11+6+12+1,
                ),
            ]
        )
        
        myall = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info(
            [0, 1, 2],
            include_unrequested_argnames=True
        )

        self.assertEqual(
            myall,
            {
                0: SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                'content': SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                1: SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                'an-optional-arg': SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                2: SingleParsedArgumentInfo(parsed_args.argnlist[2]),
            }
        )


    def test_get_all_arguments_info_withallargsbynameorindex(self):

        parsed_args = ParsedArguments(
            arguments_spec_list=[
                LatexArgumentSpec('{', argname='content'),
                LatexArgumentSpec('[', argname='an-optional-arg'),
                LatexArgumentSpec('{', argname=None),
            ],
            argnlist=[
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexCharsNode(
                                chars='Hello world',
                                pos=13,
                                pos_end=13+11, # 11 == len('Hello world')
                            ),
                            None,
                            LatexMacroNode(
                                macroname='hello',
                                nodeargd=ParsedArguments(),
                                pos=13+11,
                                pos_end=13+11+6, # 6 == len(r'\hello')
                            ),
                            LatexCommentNode(
                                comment=' a comment',
                                pos=13+11+6,
                                pos_end=13+11+6+12, # 12 == len('% a comment\n')
                            ),
                        ],
                    ),
                ),
                None,
                LatexMacroNode(
                    macroname='Z',
                    nodeargd=ParsedArguments(),
                    pos=13+11+6+12,
                    pos_end=13+11+6+12+1,
                ),
            ]
        )
        
        myall = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info(
            ['content', 1, 2]
        )

        self.assertEqual(
            myall,
            {
                #0: SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                'content': SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                1: SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                #'an-optional-arg': SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                2: SingleParsedArgumentInfo(parsed_args.argnlist[2]),
            }
        )

    def test_get_all_arguments_info_withallargsbynameorindex_b(self):

        parsed_args = ParsedArguments(
            arguments_spec_list=[
                LatexArgumentSpec('{', argname='content'),
                LatexArgumentSpec('[', argname='an-optional-arg'),
                LatexArgumentSpec('{', argname=None),
            ],
            argnlist=[
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexCharsNode(
                                chars='Hello world',
                                pos=13,
                                pos_end=13+11, # 11 == len('Hello world')
                            ),
                            None,
                            LatexMacroNode(
                                macroname='hello',
                                nodeargd=ParsedArguments(),
                                pos=13+11,
                                pos_end=13+11+6, # 6 == len(r'\hello')
                            ),
                            LatexCommentNode(
                                comment=' a comment',
                                pos=13+11+6,
                                pos_end=13+11+6+12, # 12 == len('% a comment\n')
                            ),
                        ],
                    ),
                ),
                None,
                LatexMacroNode(
                    macroname='Z',
                    nodeargd=ParsedArguments(),
                    pos=13+11+6+12,
                    pos_end=13+11+6+12+1,
                ),
            ]
        )
        
        myall = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info(
            ['content', 1, 2],
            include_unrequested_argnames=True
        )

        self.assertEqual(
            myall,
            {
                #0: SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                'content': SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                1: SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                'an-optional-arg': SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                2: SingleParsedArgumentInfo(parsed_args.argnlist[2]),
            }
        )

    def test_get_all_arguments_info_withallargsbynameorindex_c(self):

        parsed_args = ParsedArguments(
            arguments_spec_list=[
                LatexArgumentSpec('{', argname='content'),
                LatexArgumentSpec('[', argname='an-optional-arg'),
                LatexArgumentSpec('{', argname=None),
            ],
            argnlist=[
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexCharsNode(
                                chars='Hello world',
                                pos=13,
                                pos_end=13+11, # 11 == len('Hello world')
                            ),
                            None,
                            LatexMacroNode(
                                macroname='hello',
                                nodeargd=ParsedArguments(),
                                pos=13+11,
                                pos_end=13+11+6, # 6 == len(r'\hello')
                            ),
                            LatexCommentNode(
                                comment=' a comment',
                                pos=13+11+6,
                                pos_end=13+11+6+12, # 12 == len('% a comment\n')
                            ),
                        ],
                    ),
                ),
                None,
                LatexMacroNode(
                    macroname='Z',
                    nodeargd=ParsedArguments(),
                    pos=13+11+6+12,
                    pos_end=13+11+6+12+1,
                ),
            ]
        )
        
        myall = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info(
            ['content', 1, 2],
            include_unrequested_argindices=True
        )

        self.assertEqual(
            myall,
            {
                0: SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                'content': SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                1: SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                #'an-optional-arg': SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                2: SingleParsedArgumentInfo(parsed_args.argnlist[2]),
            }
        )


    def test_get_all_arguments_info_withnotallargs(self):

        parsed_args = ParsedArguments(
            arguments_spec_list=[
                LatexArgumentSpec('{', argname='content'),
                LatexArgumentSpec('[', argname='an-optional-arg'),
                LatexArgumentSpec('{', argname=None),
            ],
            argnlist=[
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexCharsNode(
                                chars='Hello world',
                                pos=13,
                                pos_end=13+11, # 11 == len('Hello world')
                            ),
                            None,
                            LatexMacroNode(
                                macroname='hello',
                                nodeargd=ParsedArguments(),
                                pos=13+11,
                                pos_end=13+11+6, # 6 == len(r'\hello')
                            ),
                            LatexCommentNode(
                                comment=' a comment',
                                pos=13+11+6,
                                pos_end=13+11+6+12, # 12 == len('% a comment\n')
                            ),
                        ],
                    ),
                ),
                None,
                LatexMacroNode(
                    macroname='Z',
                    nodeargd=ParsedArguments(),
                    pos=13+11+6+12,
                    pos_end=13+11+6+12+1,
                ),
            ]
        )
        
        myall = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info(
            ['content', 1],
            allow_additional_arguments=True,
        )

        self.assertEqual(
            myall,
            {
                'content': SingleParsedArgumentInfo(parsed_args.argnlist[0]),
                1: SingleParsedArgumentInfo(parsed_args.argnlist[1]),
                #'an-optional-arg': SingleParsedArgumentInfo(parsed_args.argnlist[1]),
            }
        )

        with self.assertRaises(LatexWalkerParseError):
            _ = ParsedArgumentsInfo(parsed_arguments=parsed_args).get_all_arguments_info(
                ['content', 1],
                allow_additional_arguments=False, # no additional args allowed, failure
            )

        



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
