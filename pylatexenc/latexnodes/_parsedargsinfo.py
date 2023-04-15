# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2022 Philippe Faist
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


# Internal module. Internal API may move, disappear or otherwise change at any
# time and without notice.

from __future__ import print_function, unicode_literals


# for Py3
_basestring = str

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
### END_PYTHON2_SUPPORT_CODE



import logging
logger = logging.getLogger(__name__)

from .nodes import *
from ._exctypes import LatexWalkerParseError



class SingleParsedArgumentInfo(object):
    r"""
    Helper class to retrieve information about a given argument that was
    specified and parsed to a latex callable object (macro, environment, or
    specials).

    You normally won't have to instantiate this object yourself, rather,
    instances are returned by :py:meth:`ParsedArgumentsInfo.get_argument_info()`
    and :py:meth:`ParsedArgumentsInfo.get_all_arguments_info()`.

    .. versionadded:: 3.0

       This class was introduced in `pylatexenc 3`.
    """
    def __init__(self, argument_node_object):
        super(SingleParsedArgumentInfo, self).__init__()
        self.argument_node_object = argument_node_object

    def was_provided(self):
        r"""
        Return `True` if the given argument was provided to the macro (or
        environment/specials) call, `False` if the argument was not provided.
        This only makes sense for optional arguments and will always return
        `True` for a mandatory argument that was provided.
        
        Checks that the given node object `argument_node_object` is not `None`.
        """
        return (self.argument_node_object is not None)

    def get_content_nodelist(self):
        r"""
        Return a node list with the contents of the argument.  The returned object
        is always a :py:class:`LatexNodeList` instance.

        If the argument node is a :py:class:`LatexGroupNode` instance (e.g., a
        mandatory argument delimited by braces as in ``\textbf{Hello world}``),
        then we return the node list contents of that group node.  If the
        argument is a single node instance of a type other than a group node,
        then we return a new node list containing that single node.  If an
        optional argument was not provided, then we return a node list that
        contains a single `None` item.
        """
        argument_node_object = self.argument_node_object
        if argument_node_object is None:
            return LatexNodeList([None])

        if isinstance(argument_node_object, LatexNodeList):
            return argument_node_object

        if argument_node_object.isNodeType(LatexGroupNode):
            return argument_node_object.nodelist

        return LatexNodeList([argument_node_object])


    def get_content_as_chars(self):
        r"""
        Return the argument contents as a single character string.

        The argument must be such that only character nodes (and possibly
        comment nodes) were given, and an error will be raised otherwise.  The
        content might still be contained in a single group node.

        This method first extracts the content node list with
        :py:meth:`get_content_nodelist()`.  Then, it iterates through the node
        list, ignoring `None` items and comment nodes, while concatenating
        strings in character nodes. Any other node type causes a
        `LatexWalkerParseError` to be raised.

        This method is useful to extract character arguments from macro calls
        with an argument that requires a single string, such as
        ``\label{my-label}`` or ``\href{https://example.com/}{...}``.

        If the argument consists of a group which contains character and comment
        nodes (as happens with arguments delimited by braces), the group
        delimiters are not included in the returned string.
        """
        nodelist = self.get_content_nodelist()
        return nodelist.get_content_as_chars()


    def __repr__(self):
        return (
            "{}(argument_node_object={!r})"
            .format(
                self.__class__.__name__,
                self.argument_node_object,
            )
        )

    def __eq__(self, other):
        return (
            (self.argument_node_object is None and other.argument_node_object is None)
            or self.argument_node_object == other.argument_node_object
        )





class ParsedArgumentsInfo(object):
    r"""
    Utility class that can gather information about the arguments stored in a
    :py:class:`ParsedArguments` instance.
    """
    def __init__(self, parsed_arguments=None, node=None):
        super(ParsedArgumentsInfo, self).__init__()
        self.parsed_arguments = parsed_arguments
        self.node = node
        if self.node is not None:
            self.node_pos = self.node.pos
            if self.parsed_arguments is None and hasattr(self.node, 'nodeargd'):
                self.parsed_arguments = self.node.nodeargd
            else:
                self.parsed_arguments = None
        else:
            self.node_pos = None

        if self.parsed_arguments is None and self.node is None:
            logger.warning("You created ParsedArgumentsInfo with both node=None "
                           "and parsed_arguments=None, might be a bug in your code?")

    def get_argument_info(self, arg):
        r"""
        Return some information about an argument.

        If `arg` is an integer, then it is interpreted as an index in the list
        of arguments.  If it is a string, then it is interpreted as a named
        argument, and a corresponding :py:class:`LatexArgumentSpec` will be
        sought with a matching `argname` attribute.

        The returned object is a :py:class:`SingleParsedArgumentInfo` instance.
        """

        if self.parsed_arguments is None:
            raise LatexWalkerParseError(
                "Cannot get argument information, there were no arguments specified",
                pos=self.node_pos
            )

        arg_i = arg
        if isinstance(arg_i, _basestring):
            # find index by looking up the argument name
            argname = arg_i
            for j, arg_spec in enumerate(self.parsed_arguments.arguments_spec_list):
                if arg_spec.argname == argname:
                    arg_i = j
                    break
            else:
                raise LatexWalkerParseError(
                    "Cannot find argument named ‘{}’".format(argname),
                    pos=self.node_pos
                )

        # arg_i is the index in the list of arguments
        return SingleParsedArgumentInfo( self.parsed_arguments.argnlist[arg_i] )

    def get_all_arguments_info(self, args=None,
                               #*,
                               allow_additional_arguments=False,
                               skip_nonexistent_arguments=False,
                               return_argnames_only=True):
        r"""
        A helper function to return info objects for all arguments.
    
        Here, `args` specifies which arguments to retrieve information for.  If
        `args=None`, then information about all known arguments are returned.
        Otherwise, you can specify a list wherein each item is an argument name
        or an argument index.

        This method returns a dictionary of argument names to
        :py:class:`ParsedArgumentInfo` instances.  (Unless you set
        `return_argnames_only=False`, in which case the returned dictionary keys
        match exactly what you specified in `args` if the latter is non-`None`.)

        The `allow_additional_arguments` flag sets the behavior to adopt if an
        argument was found in the present argument list that is not in `args`.
        If `False`, then a parse error is raised complaining about an unexpected
        argument.  If `True`, it is ignored.

        The `skip_nonexistent_arguments` flag defines the behavior to adopt if
        an argument requested in `args` does not appear in the present argument
        list.  If `False`, then a parse error is raised complaining about a
        missing argument.  If `True`, the error is ignored and the returned
        dictionary will not include an entry for that argument.
        """

        if self.parsed_arguments is None:
            if skip_nonexistent_arguments:
                return {}
            msg = "Missing arguments"
            if self.node is not None:
                msg = "Missing arguments to {!r}".format(self.node)
            raise LatexWalkerParseError(
                msg,
                self.node_pos
            )

        args_info = {}

        arg_names_seen = set()
        arg_i_seen = set()

        for j, arg_spec in enumerate(self.parsed_arguments.arguments_spec_list):
            
            argument_node_object = self.parsed_arguments.argnlist[j]

            arg_requested = False
            arg_requested_by = None
            if args is not None:
                if arg_spec.argname in args:
                    arg_requested = True
                    arg_requested_by = arg_spec.argname
                    arg_names_seen.add(arg_spec.argname)
                elif j in args:
                    arg_requested = True
                    arg_requested_by = j
                    arg_i_seen.add(j)
            else:
                arg_requested = True

            if not arg_requested:
                if not allow_additional_arguments:
                    raise LatexWalkerParseError(
                        "Got unexpected argument ‘{}’".format(arg_spec.argname),
                        pos=(argument_node_object.pos
                             if argument_node_object is not None
                             else None)
                    )
                continue

            arg_info = SingleParsedArgumentInfo( argument_node_object )

            if not return_argnames_only and arg_requested_by is not None:
                args_info[arg_requested_by] = arg_info
            elif arg_spec.argname:
                args_info[arg_spec.argname] = arg_info
            else:
                args_info[j] = arg_info

        if not skip_nonexistent_arguments and args is not None:
            # if there's an argument in args that wasn't seen, that's an error
            for arg_x in args:
                if arg_x not in arg_names_seen and arg_x not in arg_i_seen:
                    raise ValueError(
                        "Missing argument {}"
                        .format( ( '‘'+arg_x+'’'
                                   if isinstance(arg_x, _basestring)
                                   else str(arg_x) ) )
                    )
                
        return args_info

        
