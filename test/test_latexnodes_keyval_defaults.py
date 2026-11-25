import unittest

from pylatexenc.latexnodes.nodes import LatexCharsNode, LatexNodeList


def chars_nodes(text):
    return LatexNodeList([LatexCharsNode(chars=text, pos=0, pos_end=len(text))])


class TestKeyvalDefaults(unittest.TestCase):
    def test_explicit_empty_value_does_not_use_the_default(self):
        nodes = chars_nodes('empty=,bare,valued=ok')
        result = nodes.parse_keyval_content(
            default_value_nodelist=chars_nodes('fallback'))

        self.assertEqual(result['empty'].get_content_as_chars(), '')
        self.assertEqual(result['bare'].get_content_as_chars(), 'fallback')
        self.assertEqual(result['valued'].get_content_as_chars(), 'ok')

    def test_plain_default_node_list_is_not_nested(self):
        default_nodes = chars_nodes('fallback').nodelist
        result = chars_nodes('bare').parse_keyval_content(
            default_value_nodelist=default_nodes)

        self.assertEqual(result['bare'].get_content_as_chars(), 'fallback')
        self.assertEqual(result['bare'].nodelist, default_nodes)

    def test_a_single_default_node_is_still_supported(self):
        default_node = LatexCharsNode(chars='fallback', pos=0, pos_end=8)
        result = chars_nodes('bare').parse_keyval_content(
            default_value_nodelist=default_node)
        self.assertEqual(result['bare'].get_content_as_chars(), 'fallback')
