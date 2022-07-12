# -*- coding: utf-8 -*-

from __future__ import print_function


import logging
logger = logging.getLogger(__name__)


from pylatexenc.latexnodes import (
    LatexWalkerBase,
    LatexNodesCollector,
    LatexContextDbBase,
    CallableSpecBase,
    LatexArgumentSpec,
    ParsedArguments,
    #ParsingStateDelta,
    ParsingStateDeltaEnterMathMode,
    ParsingStateDeltaReplaceParsingState,
    get_updated_parsing_state_from_delta,
)
from pylatexenc.latexnodes.nodes import *


def _class_name(x):
    if hasattr(x, '__class__'):
        return x.__class__.__name__
    return str(x)



class DummyWalker(LatexWalkerBase):
    def __init__(self, **kwargs):
        super(DummyWalker, self).__init__(**kwargs)
        self.mkgroup_assert_delimiters_equals = None
        self.mkmath_assert_delimiters_equals = None

    def make_node(self, node_class, **kwargs):
        return node_class(**kwargs)

    def make_nodelist(self, nodelist, **kwargs):
        return LatexNodeList(nodelist=nodelist, **kwargs)

    def make_nodes_collector(self,
                             token_reader,
                             parsing_state,
                             **kwargs):
        return LatexNodesCollector(
            self,
            token_reader,
            parsing_state,
            **kwargs
        )

    def make_latex_group_parser(self, delimiters):
        # dummy group parser
        if self.mkgroup_assert_delimiters_equals is not None:
            assert delimiters == self.mkgroup_assert_delimiters_equals
        return dummy_empty_group_parser

    def make_latex_math_parser(self, math_mode_delimiters):
        # dummy group parser
        if self.mkmath_assert_delimiters_equals is not None:
            assert math_mode_delimiters == self.mkmath_assert_delimiters_equals
        return dummy_empty_mathmode_parser

    def parse_content(self, parser, token_reader=None, parsing_state=None,
                      open_context=None):

        if open_context is not None:
            what, tok = open_context
        else:
            what, tok = None, None
        logger.debug(":: Parsing content (%s) @ pos %d -- %s -- %r / ::",
                     _class_name(parser), token_reader.cur_pos(), what, tok)


        nodes, parsing_state_delta = parser(latex_walker=self,
                                       token_reader=token_reader,
                                       parsing_state=parsing_state)

        logger.debug(":: Parsing content DONE (%s) @ pos %d -- %s -- %r / ::",
                     _class_name(parser), token_reader.cur_pos(), what, tok)

        return nodes, parsing_state_delta





def dummy_empty_group_parser(latex_walker, token_reader, parsing_state):
    first_token = token_reader.next_token(parsing_state=parsing_state)
    second_token = token_reader.next_token(parsing_state=parsing_state)

    if first_token.tok == 'brace_open' and second_token.tok == 'brace_close':
        # good
        n = latex_walker.make_node(
            LatexGroupNode,
            delimiters=(first_token.arg, second_token.arg),
            nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
            pos=first_token.pos,
            pos_end=second_token.pos_end,
            parsing_state=parsing_state
        )
        return n, None

    raise RuntimeError("dummy empty group parser: expected an empty group.")

def dummy_empty_mathmode_parser(latex_walker, token_reader, parsing_state):
    first_token = token_reader.next_token(parsing_state=parsing_state)
    second_token = token_reader.next_token(parsing_state=parsing_state)

    # --- math mode is only set in the CONTENT of the math node ---
    #
    # math_parsing_state = get_updated_parsing_state_from_delta(
    #     parsing_state,
    #     ParsingStateDeltaEnterMathMode(
    #         math_mode_delimiter=first_token.arg,
    #         trigger_token=first_token,
    #     ),
    #     latex_walker,
    # )

    if first_token.tok in ('mathmode_inline','mathmode_display') \
       and second_token.tok in ('mathmode_inline', 'mathmode_display'):
        # good
        n = latex_walker.make_node(
            LatexMathNode,
            delimiters=(first_token.arg, second_token.arg),
            displaytype=('inline' if first_token.tok == 'mathmode_inline' else 'display'),
            nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
            pos=first_token.pos,
            pos_end=second_token.pos_end,
            parsing_state=parsing_state
        )
        return n, None

    raise RuntimeError("dummy math mode group parser: expected an empty math mode group.")





def make_dummy_macro_node_parser(tok, spec, _mk_parsing_state_delta=None):
    def dummy_macro_node_parser(latex_walker, token_reader, parsing_state):
        n = latex_walker.make_node(
            LatexMacroNode,
            parsing_state=parsing_state,
            macroname=tok.arg,
            spec=spec,
            nodeargd=ParsedArguments(),
            macro_post_space=tok.post_space,
            pos=tok.pos,
            pos_end=tok.pos_end
        )
        coi = None
        if _mk_parsing_state_delta is not None:
            coi = _mk_parsing_state_delta(parsing_state)
        return n, coi

    return dummy_macro_node_parser

class DummyMacroSpec(CallableSpecBase):
    def __init__(self, macroname):
        super(DummyMacroSpec, self).__init__()
        #self.macroname = macroname

    def get_node_parser(self, token):
        return make_dummy_macro_node_parser(token, self)

class DefineMacroZMacroSpec(DummyMacroSpec):
    def get_node_parser(self, token):
        def _mkparsing_state_delta(ps):
            return ParsingStateDeltaReplaceParsingState(
                set_parsing_state=ps.sub_context(latex_context=DummyLatexContextDb2())
            )
        return make_dummy_macro_node_parser(token, self, _mkparsing_state_delta)

def make_dummy_environment_node_parser(tok, spec):
    def dummy_environment_node_parser(latex_walker, token_reader, parsing_state):
        next_token = token_reader.next_token(parsing_state)
        if next_token.tok != 'end_environment' or next_token.arg != tok.arg:
            raise RuntimeError(
                "Expected immediate end of environment in dummy environemnt parser.")

        n = latex_walker.make_node(
            LatexEnvironmentNode,
            parsing_state=parsing_state,
            environmentname=tok.arg,
            spec=spec,
            nodeargd=ParsedArguments(),
            nodelist=LatexNodeList([]),
            pos=tok.pos,
            pos_end=next_token.pos_end
        )
        return n, None

    return dummy_environment_node_parser

class DummyEnvironmentSpec(CallableSpecBase):
    def __init__(self, environmentname):
        super(DummyEnvironmentSpec, self).__init__()
        #self.environmentname = environmentname

    def get_node_parser(self, token):
        return make_dummy_environment_node_parser(token, self)

def make_dummy_specials_node_parser(tok, spec):
    def dummy_specials_node_parser(latex_walker, token_reader, parsing_state):
        n = latex_walker.make_node(
            LatexSpecialsNode,
            parsing_state=parsing_state,
            specials_chars=tok.arg.specials_chars,
            spec=spec,
            nodeargd=ParsedArguments(),
            pos=tok.pos,
            pos_end=tok.pos_end
        )
        return n, None

    return dummy_specials_node_parser

class DummySpecialsSpec(CallableSpecBase):
    def __init__(self, specials_chars):
        super(DummySpecialsSpec, self).__init__()
        self.specials_chars = specials_chars

    def get_node_parser(self, token):
        return make_dummy_specials_node_parser(token, self)






class DummyLatexContextDb(LatexContextDbBase):
    def __init__(self):
        super(DummyLatexContextDb, self).__init__()
        self.specs = dict(
            macros={
                'somemacro': DummyMacroSpec('somemacro'),
                'yourname': DummyMacroSpec('yourname'),
                'definemacroZ': DefineMacroZMacroSpec('definemacroZ'),
            },
            environments={
                'someenv': DummyEnvironmentSpec('someenv'),
            },
            specials={
                '~': DummySpecialsSpec('~')
            }
        )
        self.specials_by_len = sorted(
            self.specs['specials'].keys(),
            key=lambda x: len(x),
            reverse=True
        )

    def get_macro_spec(self, macroname):
        return self.specs['macros'].get(macroname, None)

    def get_environment_spec(self, environmentname):
        return self.specs['environments'].get(environmentname, None)

    def get_specials_spec(self, specials_chars):
        return self.specs['specials'].get(specials_chars, None)

    def test_for_specials(self, s, pos, parsing_state):
        for spc in self.specials_by_len:
            if s.startswith(spc, pos):
                return self.specs['specials'][spc]
        return None



class DummyLatexContextDb2(DummyLatexContextDb):
    def __init__(self):
        super(DummyLatexContextDb2, self).__init__()
        self.specs['macros']['Z'] = DummyMacroSpec('Z')




def add_not_equal_warning_to_object(Obj):

    pass

### BEGIN_DEBUG_SET_EQ_ATTRIBUTE

    if hasattr(Obj, '_old_eq_fn'):
        return

    Obj._old_eq_fn = Obj.__eq__

    def _eq_with_warning(a, b):
        result = a._old_eq_fn(b)
        if not result:
            logger.warning("|a!=b|:\na=%r\nb=%r", a, b)
        return result

    Obj.__eq__ = _eq_with_warning

### END_DEBUG_SET_EQ_ATTRIBUTE





### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE


class HelperProvideAssertEqualsForLegacyTests(object):
    
    def assertEqual(self, a, b, msg=''):

        from pylatexenc import macrospec

        if isinstance(a, LatexNodeList) or isinstance(b, LatexNodeList):
            return self._assert_lists_equal(a, b)
        if isinstance(a, LatexNode) or isinstance(b, LatexNode):
            return self._assert_nodes_equal(a, b)
        if isinstance(a, macrospec.ParsedMacroArgs) \
           or isinstance(b, macrospec.ParsedMacroArgs):
            return self._assert_parsedmacroargs_equal(a, b)
        if isinstance(a, LatexArgumentSpec) \
           or isinstance(b, LatexArgumentSpec):
            return self._assert_latexargumentspec_equal(a, b)
        if isinstance(a, list) or isinstance(b, list):
            return self._assert_lists_equal(a, b)
        if isinstance(a, tuple) or isinstance(b, tuple):
            return self._assert_lists_equal(a, b)

        super(HelperProvideAssertEqualsForLegacyTests, self).assertEqual(a, b, msg=msg)

    def _assert_parsedmacroargs_equal(self, a, b, msg=''):
        for fld in ('arguments_spec_list', 'argnlist'):
            x, y = getattr(a, fld), getattr(b, fld)
            try:
                self.assertEqual(x, y)
            except AssertionError:
                print("------------------------------------------------------------")
                print("In comparing the ‘", fld, "’ fields of", sep='')
                print("    a = \n", repr(a), sep='')
                print("    b = \n", repr(b), sep='')
                print("    a.",fld," = \n", repr(x), sep='')
                print("    b.",fld," = \n", repr(y), sep='')
                print("------------------------------------------------------------")
                raise

    def _assert_latexargumentspec_equal(self, a, b, msg=None):

        from pylatexenc import macrospec

        if isinstance(a, LatexArgumentSpec):
            a = a.parser
        if isinstance(b, LatexArgumentSpec):
            b = b.parser

        return self.assertEqual(a, b, msg=msg)

    def _assert_nodes_equal(self, a, b, msg=''):
        if not (a is not None and b is not None and a.nodeType() is b.nodeType()):
            print("------------------------------------------------------------")
            print("    a = \n", repr(a), sep='')
            print("    b = \n", repr(b), sep='')
            print("------------------------------------------------------------")
            self.fail(msg + "incompatible node types, {at} and {bt}".format(
                at=_class_name(a) if a is not None else None,
                bt=_class_name(b) if b is not None else None
            ))
        
        for fld in a._redundant_fields:
            if fld in ('spec', 'latex_walker'):
                # we just skip some fields, at least for now.
                continue

            x = getattr(a, fld, None)
            y = getattr(b, fld, None)
            try:
                self.assertEqual(x, y)
            except AssertionError as e:
                print("------------------------------------------------------------")
                print("In comparing field", fld, "of node type", _class_name(a))
                print("    a = \n", repr(a), sep='')
                print("    b = \n", repr(b), sep='')
                print("    a.",fld," = \n", repr(x), sep='')
                print("    b.",fld," = \n", repr(y), sep='')
                print("    msg =", msg)
                print("------------------------------------------------------------")
                raise

    def _assert_lists_equal(self, a, b, msg=''):
        if isinstance(a, LatexNodeList):
            a = a.nodelist
        if isinstance(b, LatexNodeList):
            b = b.nodelist

        if len(a) != len(b):
            msg += 'Lists have differing lengths {alen} and {blen}'.format(
                alen=len(a),
                blen=len(b),
            )
            print("------------------------------------------------------------")
            print("    a = \n", pprint.pformat(a), sep='')
            print("    b = \n", pprint.pformat(b), sep='')
            print("------------------------------------------------------------")
            self.fail(msg)

        for j, (x, y) in enumerate(zip(a, b)):
            try:
                self.assertEqual(x, y)
            except AssertionError as e:
                print("------------------------------------------------------------")
                print("In comparing element {j} of nodelists".format(j=j))
                print("    a = \n", repr(a), sep='')
                print("    b = \n", repr(b), sep='')
                print("    a[",j,"] = \n", repr(x), sep='')
                print("    b[",j,"] = \n", repr(y), sep='')
                print("    msg =", msg)
                print("------------------------------------------------------------")
                raise

        return 


### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
