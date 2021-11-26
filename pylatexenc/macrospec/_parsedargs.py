# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2019 Philippe Faist
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




class ParsedMacroArgs(object):
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

        The difference between `argnlist` and the legacy `nodeargs` is that all
        options, regardless of optional or mandatory, are stored in the list
        `argnlist` with possible `None`\ 's at places where optional arguments
        were not provided.  Previously, whether a first optional argument was
        included in `nodeoptarg` or `nodeargs` depended on how the macro
        specification was given.

      - `argspec` is a string or a list that describes how each corresponding
        argument in `argnlist` represents.  If the macro arguments are too
        complicated to store in a list, leave this as `None`.  For standard
        macros and parsed arguments this is a string with characters '*', '[',
        '{' describing an optional star argument, an optional
        square-bracket-delimited argument, and a mandatory argument.

    Attributes:

    .. py:attribute:: argnlist

       The list of latexwalker nodes that was provided to the constructor

    .. py:attribute:: argspec

       Argument type specification provided to the constructor

    .. py:attribute:: legacy_nodeoptarg_nodeargs

       A tuple `(nodeoptarg, nodeargs)` that should be exposed as properties in
       :py:class:`~pylatexenc.latexwalker.LatexMacroNode` to provide (as best as
       possible) compatibility with pylatexenc < 2.

       This is either `(<1st optional arg node>, <list of remaining args>)` if
       the first argument is optional and all remaining args are mandatory; or
       it is `(None, <list of args>)` for any other argument structure.
    """
    def __init__(self, argnlist=[], argspec='', **kwargs):
        super(ParsedMacroArgs, self).__init__(**kwargs)
        
        self.argnlist = argnlist
        self.argspec = argspec

        # for LatexMacroNode to provide some kind of compatibility with pylatexenc < 2
        self.legacy_nodeoptarg_nodeargs = \
            self._get_legacy_attribs(self.argspec, self.argnlist)

    def _get_legacy_attribs(self, argspec, argnlist):
        nskip = 0
        while argspec.startswith('*'):
            argspec = argspec[1:]
            nskip += 1
        if argspec[0:1] == '[' and all(x == '{' for x in argspec[1:]):
            return ( argnlist[nskip], argnlist[nskip+1:] )
        else:
            return (None, argnlist)

    def to_json_object(self):
        r"""
        Called when we export the node structure to JSON when running latexwalker in
        command-line.

        Return a representation of the current parsed arguments in an object,
        typically a dictionary, that can easily be exported to JSON.  The object
        may contain latex nodes and other parsed-argument objects, as we use a
        custom JSON encoder that understands these types.

        Subclasses may
        """

        return dict(
            argspec=self.argspec,
            argnlist=self.argnlist,
        )

    def __repr__(self):
        return "{}(argspec={!r}, argnlist={!r})".format(
            self.__class__.__name__, self.argspec, self.argnlist
        )

