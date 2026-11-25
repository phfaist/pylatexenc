import unittest

from pylatexenc.latexnodes.nodes import (
    LatexCharsNode, LatexCommentNode, LatexNodeList,
)


class TestFilterNone(unittest.TestCase):
    def test_keep_none_while_removing_comments(self):
        text = LatexCharsNode(chars='x', pos=2, pos_end=3)
        comment = LatexCommentNode(comment='c', pos=0, pos_end=2)
        nodes = LatexNodeList([None, comment, text])

        filtered = nodes.filter(skip_none=False, skip_comments=True)

        self.assertEqual(filtered.nodelist, [None, text])
        self.assertEqual(nodes.nodelist, [None, comment, text])

    def test_keep_none_while_removing_whitespace(self):
        space = LatexCharsNode(chars=' ', pos=0, pos_end=1)
        nodes = LatexNodeList([None, space])
        filtered = nodes.filter(
            skip_none=False, skip_whitespace_char_nodes=True)
        self.assertEqual(filtered.nodelist, [None])

    def test_custom_predicate_still_receives_retained_none(self):
        seen = []

        def predicate(node):
            seen.append(node)
            return node is not None

        text = LatexCharsNode(chars='x', pos=0, pos_end=1)
        nodes = LatexNodeList([None, text])
        filtered = nodes.filter(
            predicate, skip_none=False, skip_comments=True,
            skip_whitespace_char_nodes=True)
        self.assertEqual(seen, [None, text])
        self.assertEqual(filtered.nodelist, [text])
