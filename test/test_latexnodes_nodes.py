# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import unittest
import re
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes.nodes import *

from pylatexenc.latexnodes import (
    LatexArgumentSpec,
    ParsedArguments,
)






class TestLatexNodeClasses(unittest.TestCase):

    maxDiff = None

    def test_methods_display_str(self):
        
        self.assertEqual(
            LatexCharsNode(
                chars='Hello world',
                pos=13,
                pos_end=13+11, # 11 == len('Hello world')
            ).display_str(),
            r"chars ‘Hello world’"
        )
        # abbreviates whenever necessary
        self.assertEqual(
            LatexCharsNode(
                chars='01234567890123456789012345678901234567890123456789', # 50 chars
                pos=13,
                pos_end=13+11, # 11 == len('Hello world')
            ).display_str(),
            r"chars ‘01234567890123456789012345678901234567…’"
        )

        self.assertEqual(
            LatexMacroNode(
                macroname='cref',
                pos=45,
                pos_end=55,
            ).display_str(),
            r"macro ‘\cref’"
        )

        self.assertEqual(
            LatexEnvironmentNode(
                environmentname='itemize',
                nodelist=[ LatexCharsNode(chars='fooba', pos=40, pos_end=45) ],
                pos=33,
                pos_end=99,
            ).display_str(),
            r"environment ‘{itemize}’"
        )

        self.assertEqual(
            LatexSpecialsNode(
                specials_chars='``',
                pos=45,
                pos_end=47,
            ).display_str(),
            r"specials ‘``’"
        )

        self.assertEqual(
            LatexCommentNode(
                comment=' this is a comment',
                comment_post_space='\n  ',
                pos=45,
                pos_end=67, # or whatever
            ).display_str(),
            r"comment ‘this is a comment’"
        )
        self.assertEqual(
            LatexCommentNode(
                comment='  01234567890123456789012345678901234567890123456789',
                comment_post_space='\n',
                pos=45,
                pos_end=150,
            ).display_str(),
            r"comment ‘01234567890123456789012345678901234567…’"
        )

        self.assertEqual(
            LatexGroupNode(
                delimiters=(r'{', r'}'),
                nodelist=[ LatexCharsNode(chars='fooba', pos=40, pos_end=45) ],
                pos=38,
                pos_end=47,
            ).display_str(),
            r"group ‘{…}’"
        )
        # don't fail on sketchy delimiters argument
        self.assertEqual(
            LatexGroupNode(
                delimiters=None,
                nodelist=[ LatexCharsNode(chars='fooba', pos=40, pos_end=45) ],
                pos=38,
                pos_end=47,
            ).display_str(),
            r"group ‘<??>…<??>’"
        )
        self.assertEqual(
            LatexGroupNode(
                delimiters=('', None),
                nodelist=[ LatexCharsNode(chars='fooba', pos=40, pos_end=45) ],
                pos=38,
                pos_end=47,
            ).display_str(),
            r"group ‘…’"
        )

        self.assertEqual(
            LatexMathNode(
                displaytype='inline',
                delimiters=(r'\(', r'\)'),
                nodelist=[ LatexCharsNode(chars='a+b=c', pos=40, pos_end=45) ],
                pos=38,
                pos_end=47,
            ).display_str(),
            r"inline math ‘\(…\)’"
        )


class TestLatexNodeList(unittest.TestCase):

    maxDiff = None

    def test_picks_pos_correctly(self):

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='Hello world',
                    pos=13,
                    pos_end=13+11, # 11 == len('Hello world')
                ),
                LatexCommentNode(
                    comment=' a comment',
                    pos=13+11,
                    pos_end=13+11+12, # 12 == len('% a comment\n')
                ),
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)

    def test_picks_pos_correctly_with_None_at_beginning(self):

        nodelist = LatexNodeList(
            [
                None,
                LatexCharsNode(
                    chars='Hello world',
                    pos=13,
                    pos_end=13+11, # 11 == len('Hello world')
                ),
                LatexCommentNode(
                    comment=' a comment',
                    pos=13+11,
                    pos_end=13+11+12, # 12 == len('% a comment\n')
                ),
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)

    def test_picks_pos_correctly_with_None_at_end(self):

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
                None,
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)


    def test_picks_pos_correctly_with_None_at_beginning_and_end(self):

        nodelist = LatexNodeList(
            [
                None,
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
                None,
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)



    def test_split_at_chars_1(self):

        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=10,
            pos_end=15,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=6,
            pos_end=15,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='a,b,,c',
                    pos=0,
                    pos_end=6,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=15,
                    pos_end=17,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=False),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=0,
                        pos_end=1,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='b',
                        pos=2,
                        pos_end=3,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=15,
                        pos_end=16,
                    ),
                ]),
            ]
        )


    def test_split_at_chars_keepempty(self):


        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=10,
            pos_end=15,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=6,
            pos_end=15,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='a,b,,c',
                    pos=0,
                    pos_end=6,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=15,
                    pos_end=17,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=True),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=0,
                        pos_end=1,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='b',
                        pos=2,
                        pos_end=3,
                    ),
                ]),
                LatexNodeList([], pos=4, pos_end=4),
                LatexNodeList([
                    LatexCharsNode(
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=15,
                        pos_end=16,
                    ),
                ]),
                LatexNodeList([], pos=17, pos_end=17),
            ]
        )



    def test_split_at_chars_edges_nokeepempty(self):

        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=6,
            pos_end=11,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=2,
            pos_end=11,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars=',a',
                    pos=0,
                    pos_end=2,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=11,
                    pos_end=13,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=False),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=1,
                        pos_end=2,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=11,
                        pos_end=12,
                    ),
                ]),
            ]
        )

    def test_split_at_chars_edges_keepempty(self):

        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=6,
            pos_end=11,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=2,
            pos_end=11,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars=',a',
                    pos=0,
                    pos_end=2,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=11,
                    pos_end=13,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=True),
            [
                LatexNodeList([], pos=0, pos_end=0),
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=1,
                        pos_end=2,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=11,
                        pos_end=12,
                    ),
                ]),
                LatexNodeList([], pos=13, pos_end=13),
            ]
        )


    def test_split_at_chars_callable(self):

        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=10,
            pos_end=15,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=6,
            pos_end=15,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='a,b//c',
                    pos=0,
                    pos_end=6,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=15,
                    pos_end=17,
                ),
            ],
        )

        # let's say we seek either ',' or '//'
        rx = re.compile(r'(,|//)')
        def find_sep_fn(chars, pos):
            m = rx.search(chars[pos:]) # chars[pos:] for Transcrypt ??
            if m is None:
                return None
            return pos+m.start(), pos+m.end()

        self.assertEqual(
            nodelist.split_at_chars(find_sep_fn, keep_empty=False),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=0,
                        pos_end=1,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='b',
                        pos=2,
                        pos_end=3,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=15,
                        pos_end=16,
                    ),
                ]),
            ]
        )


    def test_split_at_chars_rx(self):

        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=10,
            pos_end=15,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=6,
            pos_end=15,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='a,b//c',
                    pos=0,
                    pos_end=6,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=15,
                    pos_end=17,
                ),
            ],
        )

        # let's say we seek either ',' or '//'
        rx = re.compile(r'(,|//)')

        self.assertEqual(
            nodelist.split_at_chars(rx, keep_empty=False),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=0,
                        pos_end=1,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='b',
                        pos=2,
                        pos_end=3,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=15,
                        pos_end=16,
                    ),
                ]),
            ]
        )


    def test_parse_keyval_content(self):

        charsnode = LatexCharsNode(
            chars='X=one,YY=two,Z',
            pos=0,
            pos_end=14,
        )

        nodelist = LatexNodeList(
            [
                charsnode,
            ],
        )

        self.assertEqual(
            nodelist.parse_keyval_content(),
            {
                'X': LatexNodeList([
                    LatexCharsNode(
                        chars='one',
                        pos=2,
                        pos_end=5,
                    ),
                ]),
                'YY': LatexNodeList([
                    LatexCharsNode(
                        chars='two',
                        pos=9,
                        pos_end=12,
                    ),
                ]),
                'Z': LatexNodeList([
                    None
                ]),
            }
        )

    def test_parse_keyval_content(self):

        # 'X={on{\macro}},,Z'
        Xargcontentnodes = LatexNodeList(
            [
                LatexCharsNode(
                    chars='on',
                    pos=3,
                    pos_end=5,
                ),
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            LatexMacroNode(
                                macroname='macro',
                                nodeargd=None,
                                pos=6,
                                pos_end=11,
                            ),
                        ],
                        pos=6,
                        pos_end=11,
                    ),
                    pos=5,
                    pos_end=12,
                ),
            ],
            pos=3,
            pos_end=13,
        )
        nodes = LatexNodeList(
            [
                LatexCharsNode(
                    chars='X=',
                    pos=0,
                    pos_end=2,
                ),
                LatexGroupNode(
                    delimiters=('{','}'),
                    nodelist=Xargcontentnodes,
                    pos=2,
                    pos_end=14,
                ),
                LatexCharsNode(
                    chars=',,Z',
                    pos=14,
                    pos_end=17,
                )
            ],
            pos=0,
            pos_end=17,
        )

        kv = nodes.parse_keyval_content()
        
        self.assertEqual(
            kv,
            {
                'X': Xargcontentnodes,
                'Z': LatexNodeList([
                    None
                ]),
            }
        )












# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
