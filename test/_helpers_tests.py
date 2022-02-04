import logging
logger = logging.getLogger(__name__)


from pylatexenc.latexnodes import (
    LatexWalkerBase,
    LatexGroupNode,
    LatexMathNode,
    LatexMacroNode,
    LatexEnvironmentNode,
    LatexSpecialsNode,
    LatexNodeList,
    LatexNodesCollector,
    LatexContextDbBase,
    CallableSpecBase,
    ParsedMacroArgs,
)



class DummyWalker(LatexWalkerBase):

    def make_node(self, node_class, **kwargs):
        return node_class(**kwargs)

    def make_nodes_collector(self,
                             latex_walker,
                             token_reader,
                             parsing_state,
                             **kwargs):
        return LatexNodesCollector(
            latex_walker,
            token_reader,
            parsing_state,
            **kwargs
        )

    def parse_content(self, parser, token_reader=None, parsing_state=None,
                      open_context=None):

        if open_context is not None:
            what, tok = open_context
            logger.debug("Parsing content -- %s -- (%r)", what, tok)
        else:
            logger.debug("Parsing content (%s) ...", parser.__class__.__name__)

        nodes, carryover_info = parser(latex_walker=self,
                                       token_reader=token_reader,
                                       parsing_state=parsing_state)

        logger.debug("Parsing content done (%s).", parser.__class__.__name__)

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





def make_dummy_macro_node_parser(tok, spec):
    def dummy_macro_node_parser(latex_walker, token_reader, parsing_state, tok=tok, spec=spec):
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
        return n, None

    return dummy_macro_node_parser

class DummyMacroSpec(CallableSpecBase):
    def __init__(self, macroname):
        super(DummyMacroSpec, self).__init__()
        #self.macroname = macroname

    def get_node_parser(self, token):
        return make_dummy_macro_node_parser(token, self)

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
        return self.specs['macros'][macroname]

    def get_environment_spec(self, environmentname):
        return self.specs['environments'][environmentname]

    def get_specials_spec(self, specials_chars):
        return self.specs['specials'][specials_chars]

    def test_for_specials(self, s, pos, parsing_state):
        for spc in self.specials_by_len:
            if s.startswith(spc, pos):
                return self.specs['specials'][spc]
        return None