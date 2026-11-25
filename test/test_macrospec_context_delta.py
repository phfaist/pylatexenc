import unittest

from pylatexenc.latexnodes import ParsingState
from pylatexenc.macrospec import (
    LatexContextDb, MacroSpec, ParsingStateDeltaExtendLatexContextDb,
)


class TestContextDelta(unittest.TestCase):
    def test_extend_the_context_selected_by_set_attributes(self):
        original = LatexContextDb()
        original.add_context_category('old', macros=[MacroSpec('old')])
        original.freeze()
        selected_macro = MacroSpec('selected')
        selected = LatexContextDb()
        selected.add_context_category('selected', macros=[selected_macro])
        selected.freeze()
        added = MacroSpec('added')
        state = ParsingState(latex_context=original)
        delta = ParsingStateDeltaExtendLatexContextDb(
            extend_latex_context={'macros': [added]},
            set_attributes={'latex_context': selected, 'in_math_mode': True},
        )

        result = delta.get_updated_parsing_state(state, None)

        self.assertTrue(result.latex_context.get_macro_spec('selected') is selected_macro)
        self.assertTrue(result.latex_context.get_macro_spec('added') is added)
        self.assertEqual(result.latex_context.get_macro_spec('old'), None)
        self.assertTrue(result.in_math_mode)
        self.assertTrue(result.latex_context.frozen)
        self.assertTrue(state.latex_context is original)
        self.assertFalse(state.in_math_mode)
        self.assertEqual(selected.get_macro_spec('added'), None)
        self.assertEqual(original.get_macro_spec('added'), None)

    def test_no_changes_keep_the_original_state(self):
        state = ParsingState()
        delta = ParsingStateDeltaExtendLatexContextDb(extend_latex_context={})
        self.assertTrue(delta.get_updated_parsing_state(state, None) is state)
