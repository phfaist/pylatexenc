# -*- coding: utf-8 -*-

from __future__ import print_function


import logging
logger = logging.getLogger(__name__)


from pylatexenc.latexnodes import (
    LatexWalkerBase,
    LatexNodesCollector,
    LatexContextDbBase,
    CarryoverInformation,
    CallableSpecBase,
    ParsedMacroArgs,
)
from pylatexenc.latexnodes.nodes import *



class DummyWalker(LatexWalkerBase):

    def make_node(self, node_class, **kwargs):
        return node_class(**kwargs)

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

    def parse_content(self, parser, token_reader=None, parsing_state=None,
                      open_context=None):

        if open_context is not None:
            what, tok = open_context
        else:
            what, tok = None, None
        logger.debug(":: Parsing content (%s) @ pos %d -- %s -- %r / ::",
                     parser.__class__.__name__, token_reader.cur_pos(), what, tok)


        nodes, carryover_info = parser(latex_walker=self,
                                       token_reader=token_reader,
                                       parsing_state=parsing_state)

        logger.debug(":: Parsing content DONE (%s) @ pos %d -- %s -- %r / ::",
                     parser.__class__.__name__, token_reader.cur_pos(), what, tok)

        return nodes, carryover_info





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





def make_dummy_macro_node_parser(tok, spec, _mkcarryoverinfo=None):
    def dummy_macro_node_parser(latex_walker, token_reader, parsing_state,
                                tok=tok, spec=spec, _mkcarryoverinfo=_mkcarryoverinfo):
        n = latex_walker.make_node(
            LatexMacroNode,
            parsing_state=parsing_state,
            macroname=tok.arg,
            spec=spec,
            nodeargd=ParsedMacroArgs(),
            macro_post_space=tok.post_space,
            pos=tok.pos,
            pos_end=tok.pos_end
        )
        coi = None
        if _mkcarryoverinfo is not None:
            coi = _mkcarryoverinfo(parsing_state)
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
        def _mkcarryover_info(ps):
            return CarryoverInformation(
                set_parsing_state=ps.sub_context(latex_context=DummyLatexContextDb2())
            )
        return make_dummy_macro_node_parser(token, self, _mkcarryover_info)

def make_dummy_environment_node_parser(tok, spec):
    def dummy_environment_node_parser(latex_walker, token_reader, parsing_state,
                                      tok=tok, spec=spec,):
        next_token = token_reader.next_token(parsing_state)
        if next_token.tok != 'end_environment' or next_token.arg != tok.arg:
            raise RuntimeError(
                "Expected immediate end of environment in dummy environemnt parser.")

        n = latex_walker.make_node(
            LatexEnvironmentNode,
            parsing_state=parsing_state,
            environmentname=tok.arg,
            spec=spec,
            nodeargd=ParsedMacroArgs(),
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
    def dummy_specials_node_parser(latex_walker, token_reader, parsing_state,
                                   tok=tok, spec=spec):
        n = latex_walker.make_node(
            LatexSpecialsNode,
            parsing_state=parsing_state,
            specials_chars=tok.arg.specials_chars,
            spec=spec,
            nodeargd=ParsedMacroArgs(),
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
        if isinstance(a, macrospec.LatexArgumentSpec) \
           or isinstance(b, macrospec.LatexArgumentSpec):
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

        if isinstance(a, macrospec.LatexArgumentSpec):
            a = a.parser
        if isinstance(b, macrospec.LatexArgumentSpec):
            b = b.parser

        return self.assertEqual(a, b, msg=msg)

    def _assert_nodes_equal(self, a, b, msg=''):
        if not (a is not None and b is not None
                and a.isNodeType(b.__class__) and b.isNodeType(a.__class__)):
            print("------------------------------------------------------------")
            print("    a = \n", repr(a), sep='')
            print("    b = \n", repr(b), sep='')
            print("------------------------------------------------------------")
            self.fail(msg + "incompatible node types, {at} and {bt}".format(
                at=a.__class__.__name__ if a is not None else None,
                bt=b.__class__.__name__ if b is not None else None
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
                print("In comparing field", fld, "of node type", a.__class__.__name__)
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
