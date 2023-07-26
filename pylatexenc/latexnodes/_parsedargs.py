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



#from ._exctypes import LatexWalkerParseError





class LatexArgumentSpec(object):
    r"""
    Specify an argument accepted by a callable (a macro, an environment, or
    specials).

    .. py:attribute:: parser

       The parser instance to use to parse an argument to this callable.

       For the constructor you can also specify a string represending a standard
       argument type, such as '{', '[', '*', or also some `xparse`-inspired
       strings.  See
       :py:class:`~pylatexenc.latexnodes.parsers.LatexStandardArgumentParser`.
       In this case, a suitable parser is instanciated and stored in the
       `parser` attribute.

    .. py:attribute:: argname

       A name for the argument (which can be `None`, if the argument is to be
       referred to only by number).

       The name can serve for easier argument lookups and can offer more
       future-proof flexibility: E.g., while adding more optional arguments
       renumbers all arguments, you can refer to them by name to avoid having to
       update all references to argument numbers.

       See :py:class:`ParsedArgumentsInfo` for an interface for looking up
       argument values on a node instance.

    .. py:attribute:: parsing_state_delta

       Specify if this argument should be parsed with a specifically altered
       parsing state (e.g., if the argument should be parsed in math mode).

    .. versionadded:: 3.0

       This class was introduced in `pylatexenc 3`.
    """
    def __init__(self, parser, argname=None, parsing_state_delta=None):

        self.parser = parser

        self.argname = argname

        self.parsing_state_delta = parsing_state_delta

    _fields = ('parser', 'argname', 'parsing_state_delta', )


    def __repr__(self):
        return (
            "{cls}(argname={argname!r}, parser={parser!r}, "
            "parsing_state_delta={parsing_state_delta!r})"
            .format(
                cls=self.__class__.__name__,
                argname=self.argname,
                parser=self.parser,
                parsing_state_delta=self.parsing_state_delta
            )
        )

    def to_json_object(self):
        d = dict(
            parser=self.parser,
            argname=self.argname,
            parsing_state_delta=self.parsing_state_delta,
        )
        return d
        
    def __eq__(self, other):
        return (
            self.parser == other.parser
            and self.argname == other.argname
            and self.parsing_state_delta == other.parsing_state_delta
        )




class ParsedArguments(object):
    r"""
    Parsed representation of macro arguments.

    The base class provides a simple way of storing the arguments as a list of
    parsed nodes.

    This base class can be subclassed to store additional information and
    provide more advanced APIs to access macro arguments for certain categories
    of macros.

    Arguments:

      - `argnlist` is a list of latexwalker nodes that represent macro
        arguments.  If the macro arguments are too complicated to store in a
        list, leave this as `None`.  (But then code that uses the latexwalker
        must be aware of your own API to access the macro arguments.)

        The difference between `argnlist` and the legacy `nodeargs` (in
        `pylatexenc 1.x`) is that all options, regardless of optional or
        mandatory, are stored in the list `argnlist` with possible `None`\ 's at
        places where optional arguments were not provided.  Previously, whether
        a first optional argument was included in `nodeoptarg` or `nodeargs`
        depended on how the macro specification was given.

      - `argspec` is a string or a list that describes how each corresponding
        argument in `argnlist` represents.  If the macro arguments are too
        complicated to store in a list, leave this as `None`.  For standard
        macros and parsed arguments this is a string with characters '*', '[',
        '{' describing an optional star argument, an optional
        square-bracket-delimited argument, and a mandatory argument.

    Attributes:

    .. py:attribute:: argnlist

       The list of latexwalker nodes that was provided to the constructor

    .. py:attribute:: arguments_spec_list

       Argument types, etc. ................

    .. py:attribute:: argspec

       Argument type specification provided to the constructor

       .. deprecated:: 3.0
    
          The attribute `argspec` is deprecated and only read-only starting from
          `pylatexenc 3`.  Use the `arguments_spec_list` attribute instead.

    .. py:attribute:: legacy_nodeoptarg_nodeargs

       A tuple `(nodeoptarg, nodeargs)` that should be exposed as properties in
       :py:class:`~pylatexenc.latexwalker.LatexMacroNode` to provide (as best as
       possible) compatibility with pylatexenc < 2.

       This is either `(<1st optional arg node>, <list of remaining args>)` if
       the first argument is optional and all remaining args are mandatory; or
       it is `(None, <list of args>)` for any other argument structure.

       .. deprecated:: 2.0

          The `legacy_nodeoptarg_nodeargs` might be removed in a future version
          of pylatexenc.

    .. versionchanged:: 3.0

       This class used to be called `ParsedMacroArgs` in `pylatexenc 2`.  It
       provides a mostly backwards-compatible interface to the earlier
       `ParsedMacroArgs` class, and is still exposed as
       `macrospec.ParsedMacroArgs`.
    """
    def __init__(self,
                 argnlist=None,
                 arguments_spec_list=None,
                 #
                 **kwargs):
        argspec = kwargs.pop('argspec', None)
        super(ParsedArguments, self).__init__(**kwargs)

        if arguments_spec_list is None and argspec is not None:
            # support for pylatexenc 2 syntax
            arguments_spec_list = argspec

        self.argnlist = argnlist if argnlist else []

        self.arguments_spec_list = arguments_spec_list if arguments_spec_list else []


    _fields = ( 'arguments_spec_list', 'argnlist' )


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE
    @property
    def argspec(self):
        if getattr(self, '_argspec', None) is None:
            self._argspec = _argspec_from_arguments_spec_list(self.arguments_spec_list)
        return self._argspec

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE


### BEGIN_PYLATEXENC1_LEGACY_SUPPORT_CODE

    @property
    def legacy_nodeoptarg_nodeargs(self):
        argspec = self.argspec
        argnlist = self.argnlist
        nskip = 0
        while argspec.startswith('*'):
            argspec = argspec[1:]
            nskip += 1
        if argspec[0:1] == '[' and all(x == '{' for x in argspec[1:]):
            return ( argnlist[nskip], argnlist[nskip+1:] )
        else:
            return (None, argnlist)

### END_PYLATEXENC1_LEGACY_SUPPORT_CODE

    def accept_node_visitor(self, visitor):
        if self.argnlist is not None:
            for argnode in self.argnlist:
                if argnode is not None:
                    argnode.accept_node_visitor(visitor)
        visitor.visit_parsed_arguments(self)


    def __eq__(self, other):
        return (
            self.arguments_spec_list == other.arguments_spec_list
            and self.argnlist == other.argnlist
        )
 
    def to_json_object(self):
        r"""
        Called when we export the node structure to JSON when running latexwalker in
        command-line.

        Return a representation of the current parsed arguments in an object,
        typically a dictionary, that can easily be exported to JSON.  The object
        may contain latex nodes and other parsed-argument objects, as we use a
        custom JSON encoder that understands these types.
        """

        return dict(
            arguments_spec_list=self.arguments_spec_list,
            argnlist=self.argnlist,
        )

    def __repr__(self):
        return "{}(arguments_spec_list={!r}, argnlist={!r})".format(
            self.__class__.__name__, self.arguments_spec_list, self.argnlist,
        )






### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

def _argspec_from_arguments_spec_list(arguments_spec_list):

    def _argspec_char_for_arg(arg):
        if isinstance(arg, _basestring):
            return arg
        parser = getattr(arg, 'parser', None)
        if parser is not None:
            if isinstance(parser, _basestring):
                return parser
            return getattr(parser, 'arg_spec', '?')
        return '?'

    return "".join([
        _argspec_char_for_arg(arg)
        for arg in arguments_spec_list
    ])

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
