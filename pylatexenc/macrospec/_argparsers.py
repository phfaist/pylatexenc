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


from ..latexwalker import _types as latexwalker_types
from ._parsedargs import ParsedMacroArgs


# for Py3
_basestring = str

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
## End Py2 support code




class MacroStandardArgsParser(object):
    r"""
    Parses the arguments to a LaTeX macro.

    This class parses a simple macro argument specification with a specified
    arrangement of optional and mandatory arguments.

    This class also serves as base class for more advanced argument parsers
    (e.g. for a ``\verb+...+`` macro argument parser).  In such cases,
    subclasses should attempt to provide the most suitable `argspec` (and
    `argnlist` for the corresponding :py:class:`ParsedMacroArgs`) for their use,
    if appropriate, or set them to `None`.

    Arguments:

      - `argspec`: must be a string in which each character corresponds to an
        argument.  The character '{' represents a mandatory argument (single
        token or LaTeX group) and the character '[' denotes an optional argument
        delimited by braces.  The character '\*' denotes a possible star char at
        that position in the argument list, a corresponding
        ``latexwalker.LatexCharsNode('*')`` (or `None` if no star) will be
        inserted in the argument node list.  For instance, the string '\*{[[{'
        would be suitable to specify the signature of the '\\newcommand' macro.

        Currently, the argspec string may only contain the characters '\*', '{'
        and '['.

        The `argspec` may also be `None`, which is the same as specifying an
        empty string.

      - `optional_arg_no_space`: If set to `True`, then an optional argument
        cannot have any whitespace between the preceeding tokens and the '['
        character.  Set this to `True` in cases such as for ``\\`` in AMS-math
        environments, where AMS apparently introduced a patch to prevent a
        bracket on a new line after ``\\`` from being interpreted as the
        optional argument to ``\\``.
    
      - `args_math_mode`: Either `None`, or a list of the same length as
        `argspec`.  If a list is given, then each item must be `True`, `False`,
        or `None`.  The corresponding argument (cf. `argspec`) is then
        respectively parsed in math mode (`True`), in text mode (`False`), or
        with the mode unchanged (`None`).  If `args_math_mode` is `None`, then
        all arguments are parsed in the same mode as the current mode.

      - additional unrecognized keyword arguments are passed on to superclasses
        in case of multiple inheritance

    Attributes:

    .. py:attribute:: argspec

       Argument type specification provided to the constructor.

    .. py:attribute:: optional_arg_no_space

       See the corresponding constructor argument.

    .. py:attribute:: args_math_mode

       See the corresponding constructor argument.
    """
    def __init__(self, argspec=None, optional_arg_no_space=False,
                 args_math_mode=None, **kwargs):
        super(MacroStandardArgsParser, self).__init__(**kwargs)
        self.argspec = argspec if argspec else ''
        self.optional_arg_no_space = optional_arg_no_space
        self.args_math_mode = args_math_mode
        # catch bugs, make sure that argspec is a string with only accepted chars
        if not isinstance(self.argspec, _basestring) or \
           not all(x in '*[{' for x in self.argspec):
            raise TypeError(
                "argspec must be a string containing chars '*', '[', '{{' only: {!r}"
                .format(self.argspec)
            )
        # non-documented attribute that makes us ignore any leading '*'.  We use
        # this to emulate pylatexenc 1.x behavior when using the MacrosDef()
        # function explicitly
        self._like_pylatexenc1x_ignore_leading_star = False

    def parse_args(self, w, pos, parsing_state=None):
        r"""
        Parse the arguments encountered at position `pos` in the
        :py:class:`~pylatexenc.latexwalker.LatexWalker` instance `w`.

        You may override this function to provide custom parsing of complicated
        macro arguments (say, ``\verb+...+``).  The method will be called by
        keyword arguments, so the argument names should not be altered.

        The argument `w` is the :py:class:`pylatexenc.latexwalker.LatexWalker`
        object that is currently parsing LaTeX code.  You can call methods like
        `w.get_goken()`, `w.get_latex_expression()` etc., to parse and read
        arguments.

        The argument `parsing_state` is the current parsing state in the
        :py:class:`~pylatexenc.latexwalker.LatexWalker` (e.g., are we currently
        in math mode?).  See doc for
        :py:class:`~pylatexenc.latexwalker.ParsingState`.

        This function should return a tuple `(argd, pos, len)` where:

        - `argd` is a :py:class:`ParsedMacroArgs` instance, or an instance of a
          subclass of :py:class:`ParsedMacroArgs`.  The base `parse_args()`
          provided here returns a :py:class:`ParsedMacroArgs` instance.

        - `pos` is the position of the first parsed content.  It should be the
          same as the `pos` argument, except if there is whitespace at that
          position in which case the returned `pos` would have to be the
          position where the argument contents start.

        - `len` is the length of the parsed expression.  You will probably want
          to continue parsing stuff at the index `pos+len` in the string.
        """

        if parsing_state is None:
            parsing_state = w.make_parsing_state()

        argnlist = []

        if self.args_math_mode is not None and \
           len(self.args_math_mode) != len(self.argspec):
            raise ValueError("Invalid args_math_mode={!r} for argspec={!r}!"
                             .format(self.args_math_mode, self.argspec))

        def get_inner_parsing_state(j):
            if self.args_math_mode is None:
                return parsing_state
            amm = self.args_math_mode[j]
            if amm is None or amm == parsing_state.in_math_mode:
                return parsing_state
            if amm == True:
                return parsing_state.sub_context(in_math_mode=True)
            return parsing_state.sub_context(in_math_mode=False)

        p = pos

        if self._like_pylatexenc1x_ignore_leading_star:
            # ignore any leading '*' character
            tok = w.get_token(p)
            if tok.tok == 'char' and tok.arg == '*':
                p = tok.pos + tok.len

        for j, argt in enumerate(self.argspec):
            if argt == '{':
                (node, np, nl) = w.get_latex_expression(
                    p,
                    strict_braces=False,
                    parsing_state=get_inner_parsing_state(j)
                )
                p = np + nl
                argnlist.append(node)

            elif argt == '[':

                if self.optional_arg_no_space and p < len(w.s) and w.s[p].isspace():
                    # don't try to read optional arg, we don't allow space
                    argnlist.append(None)
                    continue

                optarginfotuple = w.get_latex_maybe_optional_arg(
                    p,
                    parsing_state=get_inner_parsing_state(j)
                )
                if optarginfotuple is None:
                    argnlist.append(None)
                    continue
                (node, np, nl) = optarginfotuple
                p = np + nl
                argnlist.append(node)

            elif argt == '*':
                # possible star.
                tok = w.get_token(p)
                if tok.tok == 'char' and tok.arg.startswith('*'):
                    # has star
                    argnlist.append(
                        w.make_node(latexwalker_types.LatexCharsNode,
                                    parsing_state=get_inner_parsing_state(j),
                                    chars='*', pos=tok.pos, len=1)
                    )
                    p = tok.pos + 1
                else:
                    argnlist.append(None)

            else:
                raise latexwalker_types.LatexWalkerError(
                    "Unknown macro argument kind for macro: {!r}".format(argt)
                )

        parsed = ParsedMacroArgs(
            argspec=self.argspec,
            argnlist=argnlist,
        )

        return (parsed, pos, p-pos)


    def __repr__(self):
        return '{}(argspec={!r}, optional_arg_no_space={!r}, args_math_mode={!r})'.format(
            self.__class__.__name__, self.argspec, self.optional_arg_no_space,
            self.args_math_mode
        )
    


# ------------------------------------------------------------------------------




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


class VerbatimArgsParser(MacroStandardArgsParser):
    r"""
    Parses the arguments to various LaTeX "verbatim" constructs such as
    ``\begin{verbatim}...\end{verbatim}`` environment or ``\verb+...+``.

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

      When parsing a "specials" form of a verbatim construct (e.g. ``|\begin|
      and |\end| are special \LaTeX\ commands''), specify the opening and
      closing delimiter here.  When parsing the verbatim construct, the closing
      delimiter is searched and its first occurence is used (there is no
      brace/parenthesis matching or anything of the kind).
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
                raise latexwalker_types.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=r"Cannot find matching \end{"+self.verbatim_environment_name+r"}"
                )
            # do NOT include the "\end{verbatim}", latexwalker will expect to
            # see it:
            len_ = endverbpos-pos

            argd = self.verbatim_parsed_args_class(
                verbatim_chars_node=w.make_node(latexwalker_types.LatexCharsNode,
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
                raise latexwalker_types.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=(r"End of stream reached while reading verbatim specials “{!r}...{!r}”"
                         .format(*self.specials_delimiters))
                )
            
            verbarg = w.s[pos:endpos]

            argd = self.verbatim_parsed_args_class(
                verbatim_chars_node=w.make_node(latexwalker_types.LatexCharsNode,
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
                    raise latexwalker_types.LatexWalkerParseError(
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
                raise latexwalker_types.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=r"End of stream reached while reading argument to \verb command"
                )
            
            verbarg = w.s[beginpos:endpos]

            argd = self.verbatim_parsed_args_class(
                verbatim_chars_node=w.make_node(latexwalker_types.LatexCharsNode,
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

class LstListingArgsParser(VerbatimArgsParser):
    def __init__(self):
        super(LstListingArgsParser, self).__init__(
            "verbatim-environment",
            verbatim_environment_name="lstlisting",
            verbatim_argspec='[',
            verbatim_parsed_args_class=ParsedLstListingArgs,
        )


# ------------------------------------------------------------------------------

