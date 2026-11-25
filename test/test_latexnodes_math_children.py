import unittest

from pylatexenc.latexnodes.nodes import LatexCharsNode, LatexMathNode


class TestMathChildren(unittest.TestCase):
    def test_new_math_nodes_have_independent_contents(self):
        first = LatexMathNode(displaytype='inline')
        second = LatexMathNode(displaytype='display')
        text = LatexCharsNode(chars='x', pos=0, pos_end=1)
        first.nodelist.append(text)

        self.assertEqual(second.nodelist, [])
        self.assertEqual(LatexMathNode(displaytype='inline').nodelist, [])
        self.assertEqual(first.nodelist, [text])

    def test_explicit_child_lists_are_retained(self):
        children = [LatexCharsNode(chars='x', pos=0, pos_end=1)]
        node = LatexMathNode(displaytype='inline', nodelist=children)
        self.assertTrue(node.nodelist is children)
