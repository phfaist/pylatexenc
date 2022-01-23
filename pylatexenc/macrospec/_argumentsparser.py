
from ..latexnodes import get_standard_argument_parser


class LatexArgumentSpec(object):
    def __init__(self, spec, argname=None):

        self.spec = spec

        if isinstance(spec, _basestring):
            self.arg_node_parser = get_standard_argument_parser(spec)
        else:
            self.arg_node_parser = spec # it's directly the parser instance.

        self.argname = argname



class LatexArgumentsParser(LatexParserBase):

    def __init__(self,
                 arguments_spec_list,
                 **kwargs
                 ):
        super(LatexArgumentsParser, self).__init__(**kwargs)

        if arguments_spec_list is None:
            arguments_spec_list = []

        self.arguments_spec_list = [
            (LatexArgumentSpec(arg) if isinstance(arg, _basestring) else arg)
            for arg in arguments_spec_list
        ]


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        argnlist = []

        pos_start_default = token_reader.cur_pos()
        pos_start = None
        last_arg_node = None

        for argno, arg in enumerate(self.arguments_spec_list):
            arg_node_parser = arg.arg_node_parser
            argnodes, carryover_info = latex_walker.parse_content(
                arg_node_parser,
                token_reader,
                parsing_state,
                open_context=(
                    "Argument #{}".format(argno),
                    token_reader.cur_pos()
                )
            )
            if carryover_info is not None:
                logger.warning(
                    "Parsing carry-over information (%r) ignored when parsing arguments!",
                    carryover_info
                )
            argnlist.append( argnodes )

            if argnodes is not None:
                if pos_start is None:
                    pos_start = argnodes.pos
                last_arg_node = argnodes

        if pos_start is not None and last_arg_node is not None:
            pos = pos_start
            len_ = last_arg_node.pos + last_arg_node.len - pos_start
        else:
            pos = pos_start_default
            len_ = 0

        parsed = ParsedMacroArgs(
            arguments_spec_list=self.arguments_spec_list,
            argnlist=argnlist,
            pos=pos,
            len=len_
        )

        return parsed, None


# ------------------------------------------------------------------------------

### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

class _LegacyMacroArgsParserWrapper(LatexParserBase):
    def __init__(self, args_parser, spec_object):
        super(_LegacyMacroArgsParserWrapper, self).__init__()

        self.args_parser = args_parser
        self.spec_object = spec_object


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        argsresult = spec.parse_args(w=latex_walker,
                                     pos=token_reader.cur_pos(),
                                     parsing_state=p.parsing_state)

        if len(argsresult) == 4:
            (nodeargd, apos, alen, adic) = argsresult
        else:
            (nodeargd, apos, alen) = argsresult
            adic = {}

        pos_end = apos + alen
        token_reader.move_to_pos_chars(pos_end)

        # if nodeargd is not None and nodeargd.legacy_nodeoptarg_nodeargs:
        #     legnodeoptarg = nodeargd.legacy_nodeoptarg_nodeargs[0]
        #     legnodeargs = nodeargd.legacy_nodeoptarg_nodeargs[1]
        # else:
        #     legnodeoptarg, legnodeargs = None, []

        new_parsing_state = adic.get('new_parsing_state', None)
        inner_parsing_state = adic.get('inner_parsing_state', None)

        carryover_info_kw = {}

        if new_parsing_state is not None:
            carryover_info_kw['set_parsing_state'] = new_parsing_state

        if inner_parsing_state is not None:
            carryover_info_kw['inner_parsing_state'] = inner_parsing_state

        if carryover_info_kw:
            carryover_info = CarryoverInformation(**carryover_info_kw)
        else:
            carryover_info = None

        return node, carryover_info



### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
