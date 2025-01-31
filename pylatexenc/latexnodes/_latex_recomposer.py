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
        r"""
        Recompose a node into a corresponding latex code representation.

        Returns the recomposed string.
        """

        return self.start(node)


    # ----


    def recompose_chars(self, chars, n):
        r"""
        Produce latex code for the given chars from a chars node.
        """
        if not chars:
            chars = '' # not None or other stuff
        return str(chars)

    def recompose_nodelist(self, nodelist, n):
        r"""
        Produce latex code for a node list.

        The nodes in the list have not been recomposed yet, and should be done
        so in the course of this method by calling `node.accept_node_visitor()`
        or using a helper function such as `self.descend_into_nodelist()`.
        """
        recomposed_list = self.descend_into_nodelist(nodelist)
        return "".join([
            recomposed for recomposed in recomposed_list
            if recomposed is not None
        ])

    def recompose_delimited_nodelist(self, delimiters, nodelist, n):
        r"""
        Produce latex code for a node list enclosed by delimiters.

        The nodes in the list have not been recomposed yet, and should be done
        so in the course of this method by calling `node.accept_node_visitor()`
        or using a helper function such as `self.descend_into_nodelist()`.

        The delimiters are specified as a tuple (opening delimiter, closing
        delimiter).
        """
        if not delimiters:
            delimiters = ('', '')
        return (delimiters[0] + self.recompose_nodelist(nodelist, n)
                + delimiters[1])
    
    def recompose_comment(self, comment, comment_post_space, n):
        r"""
        Produce latex code for a comment.
        """
        if not comment:
            comment = ''
        if not comment_post_space:
            comment_post_space = ''
        return n.parsing_state.comment_start + comment + comment_post_space

    def recompose_macro_call(self, macroname, macro_post_space, parsed_arguments, n):
        r"""
        Produce latex code for macro call, including the macro call and
        arguments.

        The nodes in `parsed_arguments` list have not been recomposed yet, and
        should be done so in the course of this method by calling
        `node.accept_node_visitor()` or using a helper function such as
        `self.descend_into_nodelist()`.
        """
        recomposed_arguments = self.descend_into_parsed_arguments(parsed_arguments)
        return (
            '\\' + macroname + macro_post_space
            + recomposed_arguments
        )

    def recompose_environment_call(
            self, environmentname, parsed_arguments, body_node_list, n
    ):
        r"""
        Produce latex code for a latex environment, including the begin/end
        calls, arguments, and the body contents.

        The nodes in the lists `parsed_arguments` and `body_node_list` have not
        been recomposed yet, and should be done so in the course of this method
        by calling `node.accept_node_visitor()` or using a helper function such
        as `self.descend_into_nodelist()`.
        """

        recomposed_arguments = self.descend_into_parsed_arguments(parsed_arguments)
        recomposed_body = self.recompose_nodelist(body_node_list, n)

        return (
            '\\begin{' + str(environmentname) + '}'
            + recomposed_arguments
            + recomposed_body
            + '\\end{' + str(environmentname) + '}'
        )

    def recompose_specials_call(self, specials_chars, parsed_arguments, n):
        r"""
        Produce latex code for latex specials call, including the specials
        chars and possible arguments.

        The nodes in the list `parsed_arguments` have not been recomposed
        yet, and should be done so in the course of this method by calling
        `node.accept_node_visitor()` or using a helper function such as
        `self.descend_into_nodelist()`.
        """
        recomposed_arguments = self.descend_into_parsed_arguments(parsed_arguments)
        return specials_chars + recomposed_arguments

    def recompose_math_content(self, delimiters, nodelist, n):
        r"""
        Produce latex code for a latex math construt (e.g., `$...$`),
        including delimiters and content.  

        The nodes in the list `node_list` have not been recomposed yet, and
        should be done so in the course of this method by calling
        `node.accept_node_visitor()` or using a helper function such as
        `self.descend_into_nodelist()`.
        """
        return self.recompose_delimited_nodelist(delimiters, nodelist, n)

    def recompose_parsed_arguments(self, parsed_arguments):
        r"""
        Produce latex code for a sequence of arguments provided to a macro,
        environment, or specials call.
        
        The nodes in the list `parsed_arguments` have not been recomposed yet,
        and should be done so in the course of this method by calling
        `node.accept_node_visitor()` or using a helper function such as
        `self.descend_into_nodelist()`.
        """

        ### FIXME: At this point, we should have a node or at least a
        ### parsing_state that we can pass over to recompose_nodelist????

        return self.recompose_nodelist(parsed_arguments.argnlist, None)


    def recompose_unknown(self, node):
        r"""
        Produce something for an unknown node.
        """
        return '<<< UNKNOWN NODE: ' + repr(node) + ' >>>'



    # ---

    def node_standard_process_chars(self, node):
        return self.recompose_chars(node.chars, node)

    def node_standard_process_group(self, node):
        return self.recompose_delimited_nodelist(
            node.delimiters,
            node.nodelist,
            node
        )

    def node_standard_process_comment(self, node):
        return self.recompose_comment(node.comment, node.comment_post_space, node)

    def node_standard_process_macro(self, node):
        return self.recompose_macro_call(
            node.macroname,
            node.macro_post_space,
            node.nodeargd,
            node
        )

    def node_standard_process_environment(self, node):
        return self.recompose_environment_call(
            node.environmentname,
            node.nodeargd,
            node.nodelist,
            node
        )

    def node_standard_process_specials(self, node):
        return self.recompose_specials_call(
            node.specials_chars,
            node.nodeargd,
            node
        )

    def node_standard_process_math(self, node):
        return self.recompose_math_content(
            node.delimiters,
            node.nodelist,
            node
        )

    def node_standard_process_list(self, nodelist):
        return self.recompose_nodelist(
            nodelist.nodelist,
            nodelist
        )

    def node_standard_process_parsed_arguments(self, parsed_arguments):
        return self.recompose_parsed_arguments(parsed_arguments)



    # handle something we don't recognize

    def visit(self, node, **kwargs):
        return self.recompose_unknown(node)
