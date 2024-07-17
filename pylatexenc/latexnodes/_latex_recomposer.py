import logging
logger = logging.getLogger(__name__)

from .nodes import LatexNodesVisitor

class LatexNodesLatexRecomposer(LatexNodesVisitor):
    r"""
    Reconstruct the LaTeX code that gave rise to a given node structure.

    This recomposition works by traversing the node tree and reproducing the
    latex code that is associated with the information stored in each node.

    Note that parsing the recomposed latex code is NOT guaranteed to give you
    the same node tree, because parsing state settings or on-fly changes cannot
    be guaranteed to be followed in the same way.

    Usage::

        node = ... # say, a LatexNodeList or LatexNode instance
        recomposer = LatexNodesLatexRecomposer()
        
        latex = recomposer.latex_recompose(node)
    """

    def latex_recompose(self, node):
        
        return self.start(node)


    # ----


    def recompose_chars(self, chars, n):
        if not chars:
            chars = '' # not None or other stuff
        return str(chars)

    def recompose_nodelist(self, recomposed_list, n):
        return "".join([
            recomposed for recomposed in recomposed_list
            if recomposed is not None
        ])

    def recompose_delimited_nodelist(self, delimiters, recomposed_list, n):
        if not delimiters:
            delimiters = ('', '')
        return (delimiters[0] + self.recompose_nodelist(recomposed_list, n)
                + delimiters[1])
    
    def recompose_comment(self, comment, comment_post_space, n):
        if not comment:
            comment = ''
        if not comment_post_space:
            comment_post_space = ''
        return n.parsing_state.comment_start + comment + comment_post_space

    def recompose_macro_call(self, macroname, macro_post_space, recomposed_arguments_str, n):
        #logger.debug('recompose_macro_call:  recomposed_arguments_str=%r', recomposed_arguments_str)
        if not recomposed_arguments_str:
            recomposed_arguments_str = ''
        return '\\' + macroname + macro_post_space + recomposed_arguments_str

    def recompose_environment_call(
            self, environmentname, recomposed_arguments_str, recomposed_body_list, n
    ):
        if not recomposed_arguments_str:
            recomposed_arguments_str = ''
        return (
            '\\begin{' + str(environmentname) + '}' + recomposed_arguments_str
            + self.recompose_nodelist(recomposed_body_list, n)
            + '\\end{' + str(environmentname) + '}'
        )

    def recompose_specials_call(self, specials_chars, recomposed_arguments_str, n):
        if not recomposed_arguments_str:
            recomposed_arguments_str = ''
        return specials_chars + recomposed_arguments_str

    def recompose_math_content(self, delimiters, recomposed_list, n):
        return self.recompose_delimited_nodelist(delimiters, recomposed_list, n)

    def recompose_parsed_arguments(self, recomposed_list, pa):
        #logger.debug('recompose_parsed_arguments:  %r', recomposed_list)
        return self.recompose_nodelist(recomposed_list, pa)


    def recompose_unknown(self, node):
        return '<<< UNKNOWN NODE: ' + repr(node) + ' >>>'


    # ---

    def visit_chars_node(self, node, **kwargs):
        return self.recompose_chars(node.chars, node)

    def visit_group_node(self, node, visited_results_nodelist, **kwargs):
        return self.recompose_delimited_nodelist(
            node.delimiters, visited_results_nodelist, node
        )

    def visit_comment_node(self, node, **kwargs):
        return self.recompose_comment(node.comment, node.comment_post_space, node)

    def visit_macro_node(self, node, visited_results_arguments, **kwargs):
        return self.recompose_macro_call(
            node.macroname, node.macro_post_space, visited_results_arguments, node
        )

    def visit_environment_node(self, node, visited_results_arguments,
                               visited_results_body, **kwargs):
        return self.recompose_environment_call(
            node.environmentname, visited_results_arguments, visited_results_body, node
        )

    def visit_specials_node(self, node, visited_results_arguments, **kwargs):
        return self.recompose_specials_call(
            node.specials_chars, visited_results_arguments, node
        )

    def visit_math_node(self, node, visited_results_nodelist, **kwargs):
        return self.recompose_math_content(node.delimiters, visited_results_nodelist, node)

    def visit_node_list(self, nodelist, visited_results_nodelist, **kwargs):
        return self.recompose_nodelist(visited_results_nodelist, nodelist)

    def visit_parsed_arguments(self, parsed_args, visited_results_argnlist, **kwargs):
        return self.recompose_parsed_arguments(visited_results_argnlist, parsed_args)


    def visit_unknown_node(self, node, **kwargs):
        r"""
        Called when visiting a node whose type is unknown.
        """
        return self.recompose_unknown(node)
