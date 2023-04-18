# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2021 Philippe Faist
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


from ...latexnodes import _exctypes as latexnodes_exctypes
from ...latexnodes import nodes as latexnodes_nodes
from ...latexnodes import ParsedArguments as ParsedMacroArgs


from ._base import MacroStandardArgsParser



class ParsedVerbatimArgs(ParsedMacroArgs):
    r"""
    Parsed representation of arguments to LaTeX verbatim constructs, such as
    ``\begin{verbatim}...\end{verbatim}`` or ``\verb|...|``.

    Instances of `ParsedVerbatimArgs` are returned by the args parser
    :py:class:`VerbatimArgsParser`.

    Arguments:

      - `verbatim_chars_node` --- a properly initialized
        :py:class:`pylatexenc.latexwalker.LatexCharsNode` that stores the
        verbatim text provided.  It is used to initialize the base class
        :py:class:`ParsedMacroArgs` to expose a single mandatory argument with
        the given verbatim text.  The `verbatim_text` attribute is initialized
        from this node, too.

      - `verbatim_delimiters` --- a 2-item tuple of characters used to delimit
        the verbatim arguemnt (in case of a ``\verb+...+`` macro) or `None`.

      - `verbatim_argspec`, `verbatim_argnlist` --- the argspec and node list
        representing any regular (optional or mandatory) argument(s) that the
        construct might have accepted, before the verbatim content.  (E.g.
        ``\begin{lstlisting}[language=Python]``)

    Attributes:

    .. py:attribute:: verbatim_text

       The verbatim text that was provided

    .. py:attribute:: verbatim_delimiters

       If the verbatim text was specified as an argument to ``\verb$...$``, then
       this is set to a 2-item tuple that specifies the begin and end
       delimiters.  Otherwise, the attribute is `None`.

    .. deprecated:: 3.0

       This class was deprecated in `pylatexenc 3`.  Starting from `pylatexenc
       3`, the preferred way to parse verbatim arguments is to use a verbatim
       parser
       (:py:class:`pylatexenc.latexnodes.parsers.LatexDelimitedVerbatimParser`)
       as an argument in a :py:class:`pylatexenc.macrospec.LatexArgumentsParser`
       instance.
    """
    def __init__(self,
                 verbatim_chars_node,
                 verbatim_delimiters=None,
                 verbatim_argspec='',
                 verbatim_argnlist=[],
                 **kwargs):

        # provide argspec/argnlist to the parent class so that any code that is
        # not "verbatim environment-aware" sees this simply as the argument to
        # an empty verbatim environment
        super(ParsedVerbatimArgs, self).__init__(
            argspec=verbatim_argspec + '{',
            argnlist=verbatim_argnlist + [verbatim_chars_node],
            **kwargs
        )
        
        self.verbatim_text = verbatim_chars_node.chars
        self.verbatim_delimiters = verbatim_delimiters


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
            super(ParsedVerbatimArgs, self).to_json_object(),
            verbatim_text=self.verbatim_text,
            verbatim_delimiters=self.verbatim_delimiters,
        )

    def __repr__(self):
        return (
            "{}(verbatim_text={!r}, verbatim_delimiters={!r}) [ {} ]"
            .format(
                self.__class__.__name__,
                self.verbatim_text,
                self.verbatim_delimiters,
                super(ParsedVerbatimArgs, self).__repr__(),
            )
        )

    def __eq__(self, other):
        return (
            super(ParsedVerbatimArgs, self).__eq__(other)
            and self.verbatim_text == other.verbatim_text
            and self.verbatim_delimiters == other.verbatim_delimiters
        )


class VerbatimArgsParser(MacroStandardArgsParser):
    r"""
    Parses the arguments to various LaTeX verbatim constructs such as
    ``\begin{verbatim}...\end{verbatim}`` environment or ``\verb+...+``.

    .. deprecated:: 3.0

       This class is part of `pylatexenc 2.x`'s macro argument parsing API.
       Starting with `pylatexenc 3.0`, each macro/environment/specials argument
       is parsed with an individual macro parser.  (See
       :py:class:`pylatexenc.latexnodes.LatexArgumentSpec`,
       :py:class:`pylatexenc.macrospec.LatexStandardArgumentParser`.)  To parse
       verbatim contents for macro arguments and body contents, see
       :py:class:`pylatexenc.latexnodes.parsers.LatexDelimitedVerbatimParser`
       and
       :py:class:`pylatexenc.latexnodes.parsers.LatexVerbatimEnvironmentContentsParser`.


    This class also serves to illustrate how to write custom parsers for
    complicated macro arguments.  See also :py:class:`MacroStandardArgsParser`.

    Arguments:

    .. py:attribute:: verbatim_arg_type

      One of 'verbatim-environment', 'verb-macro', or 'specials-delimiters'.

    .. py:attribute:: verbatim_environment_name

      Name of the environment which acts as verbatim environment.  This is used
      to find the end of the environment in the document (we simply search for
      ``\end{environment-name}``).

    .. py:attribute:: verbatim_environment_argspec

      Specify any standard macro argument(s) the verbatim environment (or analog
      environment such as the `lstlisting` environment) accepts before their
      verbatim content.

    .. py:attribute:: verbatim_parsed_args_class
    
      The class to use to construct the parsed-arguments object after we parsed
      the verbatim construct.  By default this is
      :py:class:`ParsedVerbatimArgs`.  You can use another class that derives
      from :py:class:`ParsedVerbatimArgs` and that accepts the same keyword
      arguments.

    .. py:attribute:: specials_delimiters

      When parsing a "specials" form of a verbatim construct (e.g.
      ``|\begin| and |\end| are special \LaTeX\ commands``), specify the
      opening and closing delimiter here.  When parsing the verbatim construct,
      the closing delimiter is searched and its first occurence is used (there
      is no brace/parenthesis matching or anything of the kind).
    """
    def __init__(self,
                 verbatim_arg_type,
                 verbatim_environment_name="verbatim",
                 verbatim_argspec='',
                 verbatim_parsed_args_class=ParsedVerbatimArgs,
                 specials_delimiters=('|', '|'),
                 **kwargs):
        super(VerbatimArgsParser, self).__init__(
            argspec=verbatim_argspec+'{',
            **kwargs
        )
        self.verbatim_arg_type = verbatim_arg_type
        self.verbatim_environment_name = verbatim_environment_name
        self.verbatim_argspec = verbatim_argspec
        self.verbatim_parsed_args_class = verbatim_parsed_args_class
        self.specials_delimiters = tuple(specials_delimiters)

        if self.verbatim_argspec:
            self.verbatim_std_arg_parser = MacroStandardArgsParser(
                argspec=self.verbatim_argspec,
                optional_arg_no_space=True, # "[" on new line is not an optional argument
            )
        else:
            self.verbatim_std_arg_parser = None

    def parse_args(self, w, pos, parsing_state=None):

        parsed_args_object_kwargs = {}

        # first, parse any standard arguments
        if self.verbatim_std_arg_parser is not None:
            (argd, ppos, plen) = self.verbatim_std_arg_parser.parse_args(
                w,
                pos,
                parsing_state=parsing_state,
            )
            pos_start = ppos
            pos = ppos+plen
            parsed_args_object_kwargs['verbatim_argspec'] = argd.argspec
            parsed_args_object_kwargs['verbatim_argnlist'] = argd.argnlist
        else:
            # the actual pos of the argument in the string is still to be
            # determined
            pos_start = None

        # parse relevant verbatim construct

        if self.verbatim_arg_type == 'verbatim-environment':
            # the contents start right away, if we didn't have any arguments
            if pos_start is None:
                pos_start = pos
            # simply scan the string until we find '\end{verbatim}'.  That's
            # exactly how LaTeX processes it.
            endverbpos = w.s.find(r'\end{'+self.verbatim_environment_name+r'}', pos)
            if endverbpos == -1:
                raise latexnodes_exctypes.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=r"Cannot find matching \end{"+self.verbatim_environment_name+r"}"
                )
            # do NOT include the "\end{verbatim}", latexwalker will expect to
            # see it:
            len_ = endverbpos-pos

            argd = self.verbatim_parsed_args_class(
                verbatim_chars_node=w.make_node(latexnodes_nodes.LatexCharsNode,
                                                parsing_state=parsing_state,
                                                chars=w.s[pos:pos+len_],
                                                pos=pos,
                                                len=len_),
                **parsed_args_object_kwargs
            )
            return (argd, pos_start, endverbpos - pos_start)

        if self.verbatim_arg_type == 'specials-delimiters':

            if pos_start is None:
                pos_start = pos

            endpos = w.s.find(self.specials_delimiters[1], pos)
            if endpos == -1:
                raise latexnodes_exctypes.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=(r"End of stream reached while reading verbatim specials “{!r}...{!r}”"
                         .format(*self.specials_delimiters))
                )
            
            verbarg = w.s[pos:endpos]

            argd = self.verbatim_parsed_args_class(
                verbatim_chars_node=w.make_node(latexnodes_nodes.LatexCharsNode,
                                                parsing_state=parsing_state,
                                                chars=verbarg,
                                                pos=pos,
                                                len=endpos-pos),
                verbatim_delimiters=self.specials_delimiters,
                **parsed_args_object_kwargs
            )

            return (argd, pos_start, endpos+1-pos_start) # include delimiters in pos/len

        if self.verbatim_arg_type == 'verb-macro':
            # read the next nonwhitespace char. This is the delimiter of the
            # argument
            while w.s[pos].isspace():
                pos += 1
                if pos >= len(w.s):
                    raise latexnodes_exctypes.LatexWalkerParseError(
                        s=w.s,
                        pos=pos,
                        msg=r"Missing argument to \verb command"
                    )
            verbdelimchar = w.s[pos]
            beginpos = pos+1
            if pos_start is None:
                pos_start = beginpos # the argument started here

            endpos = w.s.find(verbdelimchar, beginpos)
            if endpos == -1:
                raise latexnodes_exctypes.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=r"End of stream reached while reading argument to \verb command"
                )
            
            verbarg = w.s[beginpos:endpos]

            argd = self.verbatim_parsed_args_class(
                verbatim_chars_node=w.make_node(latexnodes_nodes.LatexCharsNode,
                                                parsing_state=parsing_state,
                                                chars=verbarg,
                                                pos=beginpos,
                                                len=endpos-beginpos),
                verbatim_delimiters=(verbdelimchar, verbdelimchar),
                **parsed_args_object_kwargs
            )

            return (argd, pos_start, endpos+1-pos_start) # include delimiters in pos/len


    def __repr__(self):
        return (
            '{}(verbatim_arg_type={!r}, verbatim_environment_name={!r}, verbatim_argspec={!r})'
            .format(
                self.__class__.__name__,
                self.verbatim_arg_type,
                self.verbatim_environment_name,
                self.verbatim_argspec,
            )
        )


# --------------------------------------

class ParsedLstListingArgs(ParsedVerbatimArgs):
    r"""
    Parsed representation of arguments to a LaTeX lstlisting environment, i.e.
    ``\begin{lstlisting}...\end{lstlisting}``

    Arguments:

      - `lstlisting_chars_node` --- a properly initialized
        :py:class:`pylatexenc.latexwalker.LatexCharsNode` that stores the
        lstlisting text provided.  It is used to initialize the base class
        :py:class:`ParsedMacroArgs` to expose a single mandatory argument with
        the given lstlisting text.  The `lstlisting_text` attribute is initialized
        from this node, too.

    Attributes:

    .. py:attribute:: lstlisting_text

       The lstlisting text that was provided
    """
    def __init__(self, verbatim_chars_node, **kwargs):

        # provide argspec/argnlist to the parent class so that any code that is
        # not "lstlisting environment-aware" sees this simply as the argument to
        # an empty lstlisting environment
        super(ParsedLstListingArgs, self).__init__(
            verbatim_chars_node=verbatim_chars_node,
            **kwargs
        )
        
        self.lstlisting_text = verbatim_chars_node.chars

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
            super(ParsedLstListingArgs, self).to_json_object(),
            lstlisting_text=self.lstlisting_text
        )

    def __repr__(self):
        return (
            "{}(lstlisting_text={!r}) [ {} ]"
            .format(
                self.__class__.__name__,
                self.lstlisting_text,
                super(ParsedLstListingArgs, self).__repr__()
            )
        )

    def __eq__(self, other):
        return (
            super(ParsedLstListingArgs, self).__eq__(other)
            and self.lstlisting_text == other.lstlisting_text
        )


class LstListingArgsParser(VerbatimArgsParser):
    def __init__(self):
        super(LstListingArgsParser, self).__init__(
            "verbatim-environment",
            verbatim_environment_name="lstlisting",
            verbatim_argspec='[',
            verbatim_parsed_args_class=ParsedLstListingArgs,
        )


# ------------------------------------------------------------------------------

