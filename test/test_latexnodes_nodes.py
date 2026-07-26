# -*- coding: utf-8 -*-

import unittest
import re
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes.nodes import *

from pylatexenc.latexnodes import (
    LatexArgumentSpec,
    ParsedArguments,
    ParsingState,
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

    def test_eq_returns_false_and_does_not_raise(self):
        # comparing to None, or to an object of a different type, must simply
        # report that the objects are not equal

        self.assertFalse( LatexNodeList([]) == None )
        self.assertFalse( LatexNodeList([]) == 'not a node list' )
        self.assertFalse( ParsedArguments() == None )
        self.assertFalse( LatexArgumentSpec('{') == None )

        # a node list is still comparable to a plain list of nodes
        self.assertTrue( LatexNodeList([]) == [] )

        # this happens in everyday use: a macro node has an empty
        # ParsedArguments instance by default, whereas a specials node has
        # nodeargd=None by default
        self.assertFalse(
            LatexMacroNode(macroname='a', nodeargd=ParsedArguments())
            == LatexMacroNode(macroname='a', nodeargd=None)
        )
        self.assertFalse(
            LatexMacroNode(macroname='a', nodeargd=None)
            == LatexMacroNode(macroname='a', nodeargd=ParsedArguments())
        )

### BEGIN_TEST_PYLATEXENC_SKIP
    def test_environment_node_legacy_optargs_args(self):
        # the deprecated pylatexenc 2 attributes `optargs` and `args` are still
        # readable (and the corresponding constructor keyword arguments are
        # still accepted)

        optarg_node = LatexGroupNode(
            delimiters=('[',']'),
            nodelist=LatexNodeList([ LatexCharsNode(chars='h!') ]),
        )
        arg_node = LatexGroupNode(
            delimiters=('{','}'),
            nodelist=LatexNodeList([ LatexCharsNode(chars='ccc') ]),
        )

        n = LatexEnvironmentNode(environmentname='center',
                                 nodelist=LatexNodeList([]))
        self.assertEqual(n.envname, 'center')
        self.assertEqual(n.optargs, [None])
        self.assertEqual(n.args, [])

        n2 = LatexEnvironmentNode(
            environmentname='figure',
            nodelist=LatexNodeList([]),
            nodeargd=ParsedArguments(argspec='[', argnlist=[optarg_node]),
        )
        self.assertEqual(n2.optargs, [optarg_node])
        self.assertEqual(n2.args, [])

        n3 = LatexEnvironmentNode(
            environmentname='tabular',
            nodelist=LatexNodeList([]),
            nodeargd=ParsedArguments(argspec='{', argnlist=[arg_node]),
        )
        self.assertEqual(n3.optargs, [None])
        self.assertEqual(n3.args, [arg_node])

        n4 = LatexEnvironmentNode(
            environmentname='figure',
            nodelist=LatexNodeList([]),
            optargs=[optarg_node],
            args=[arg_node],
        )
        self.assertEqual(n4.optargs, [optarg_node])
        self.assertEqual(n4.args, [arg_node])
### END_TEST_PYLATEXENC_SKIP


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


    def test_split_at_chars_max_split(self):

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='a,b,c,d',
                    pos=0,
                    pos_end=7,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', max_split=2),
            [
                LatexNodeList([
                    LatexCharsNode(chars='a', pos=0, pos_end=1,),
                ]),
                LatexNodeList([
                    LatexCharsNode(chars='b', pos=2, pos_end=3,),
                ]),
                LatexNodeList([
                    LatexCharsNode(chars='c,d', pos=4, pos_end=7,),
                ]),
            ]
        )

    def test_split_at_chars_max_split_counts_splits_not_parts(self):
        # `max_split` limits how many times we split, regardless of whether or
        # not the resulting chunks are empty (empty chunks are only collected if
        # keep_empty=True).  Here the first separator is at the very beginning
        # of the string, so that the single allowed split produces an empty
        # first chunk that is dropped; the remaining separator must be left
        # alone.

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars=',a,b',
                    pos=0,
                    pos_end=4,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', max_split=1),
            [
                LatexNodeList([
                    LatexCharsNode(chars='a,b', pos=1, pos_end=4,),
                ]),
            ]
        )

    def test_copy_constructor_uses_keyword_arguments(self):

        parsing_state = ParsingState()

        nodelist = LatexNodeList(
            [
                LatexCharsNode(chars='Hello world', pos=13, pos_end=13+11,),
            ],
        )

        # copying a node list without any keyword arguments keeps all the
        # attributes of the object that is being copied
        nodelist_copy = LatexNodeList(nodelist)
        self.assertEqual(nodelist_copy.pos, 13)
        self.assertEqual(nodelist_copy.pos_end, 13+11)
        self.assertIsNone(nodelist_copy.parsing_state)

        # keyword arguments that are given override the corresponding attributes
        nodelist_copy2 = LatexNodeList(nodelist, pos=0, pos_end=99,
                                       parsing_state=parsing_state)
        self.assertEqual(nodelist_copy2.pos, 0)
        self.assertEqual(nodelist_copy2.pos_end, 99)
        self.assertIs(nodelist_copy2.parsing_state, parsing_state)

    def test_parse_keyval_content_more(self):

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

    def test_parse_keyval_content_repeated_key(self):

        # 'X=one,X=two'
        nodes = LatexNodeList(
            [
                LatexCharsNode(
                    chars='X=one,X=two',
                    pos=0,
                    pos_end=11,
                ),
            ],
            pos=0,
            pos_end=11,
        )

        # whichever aggregation action is used, the values are always node lists

        kv_first = nodes.parse_keyval_content(repeated_key_aggregate_action='first')
        self.assertTrue( isinstance(kv_first['X'], LatexNodeList) )
        self.assertEqual( kv_first['X'].get_content_as_chars(), 'one' )

        kv_last = nodes.parse_keyval_content(repeated_key_aggregate_action='last')
        self.assertTrue( isinstance(kv_last['X'], LatexNodeList) )
        self.assertEqual( kv_last['X'].get_content_as_chars(), 'two' )

        kv_concat = nodes.parse_keyval_content(repeated_key_aggregate_action='concatenate')
        self.assertTrue( isinstance(kv_concat['X'], LatexNodeList) )
        self.assertEqual( kv_concat['X'].get_content_as_chars(), 'onetwo' )

    def test_parse_keyval_content_repeated_key_custom_callable(self):

        # 'X=one,X=two'
        nodes = LatexNodeList(
            [
                LatexCharsNode(
                    chars='X=one,X=two',
                    pos=0,
                    pos_end=11,
                ),
            ],
            pos=0,
            pos_end=11,
        )

        seen_values = []

        def aggregate_fn(key, prev_value, new_value, result_keyvals=None):
            seen_values.append(prev_value)
            seen_values.append(new_value)
            return new_value

        kv = nodes.parse_keyval_content(repeated_key_aggregate_action=aggregate_fn)

        # the callable is handed node lists, both for the value we already had
        # and for the new value
        self.assertEqual(len(seen_values), 2)
        self.assertTrue( isinstance(seen_values[0], LatexNodeList) )
        self.assertTrue( isinstance(seen_values[1], LatexNodeList) )
        self.assertEqual( seen_values[0].get_content_as_chars(), 'one' )
        self.assertEqual( seen_values[1].get_content_as_chars(), 'two' )
        self.assertEqual( kv['X'].get_content_as_chars(), 'two' )












# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
