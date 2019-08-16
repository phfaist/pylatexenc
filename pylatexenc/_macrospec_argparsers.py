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


import sys


if sys.version_info.major > 2:
    # Py3
    def unicode(s): return s
    _basestring = str
    _str_from_unicode = lambda x: x
    _unicode_from_str = lambda x: x
else:
    # Py2
    _basestring = basestring
    _str_from_unicode = lambda x: unicode(x).encode('utf-8')
    _unicode_from_str = lambda x: x.decode('utf-8')



from .macrospec import ParsedMacroArgs, MacroStandardArgsParser


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

    Attributes:

    .. py:attribute:: verbatim_text

       The verbatim text that was provided

    .. py:attribute:: verbatim_delimiters

       If the verbatim text was specified as an argument to ``\verb$...$``, then
       this is set to a 2-item tuple that specifies the begin and end
       delimiters.  Otherwise, the attribute is `None`.
    """
    def __init__(self, verbatim_chars_node, verbatim_delimiters=None,
                 **kwargs):

        # provide argspec/argnlist to the parent class so that any code that is
        # not "verbatim environment-aware" sees this simply as the argument to
        # an empty verbatim environment
        super(ParsedVerbatimArgs, self).__init__(
            argspec='{',
            argnlist=[verbatim_chars_node],
            **kwargs
        )
        
        self.verbatim_text = verbatim_chars_node.chars
        self.verbatim_delimiters = verbatim_delimiters

    def __repr__(self):
        return "{}(verbatim_text={!r}, verbatim_delimiters={!r})".format(
            self.__class__.__name__, self.verbatim_text, self.verbatim_delimiters
        )



class VerbatimArgsParser(MacroStandardArgsParser):
    r"""
    Parses the arguments to various LaTeX "verbatim" constructs such as
    ``\begin{verbatim}...\end{verbatim}`` environment or ``\verb+...+``.

    This class also serves to illustrate how to write custom parsers for
    complicated macro arguments.  See also :py:class:`MacroStandardArgsParser`.

    Arguments:

    .. py:attribute:: verbatim_arg_type

      One of 'verbatim-environment' or 'verb-macro'.
    """
    def __init__(self, verbatim_arg_type, **kwargs):
        super(VerbatimArgsParser, self).__init__(argspec='{', **kwargs)
        self.verbatim_arg_type = verbatim_arg_type

    def parse_args(self, w, pos, parsing_state=None):

        from . import latexwalker

        if self.verbatim_arg_type == 'verbatim-environment':
            # simply scan the string until we find '\end{verbatim}'.  That's
            # exactly how LaTeX processes it.
            endverbpos = w.s.find(r'\end{verbatim}', pos)
            if endverbpos == -1:
                raise latexwalker.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=r"Cannot find matching \end{verbatim}"
                )
            # do NOT include the "\end{verbatim}", latexwalker will expect to
            # see it:
            len_ = endverbpos-pos

            argd = ParsedVerbatimArgs(
                verbatim_chars_node=w.make_node(latexwalker.LatexCharsNode,
                                                parsing_state=parsing_state,
                                                chars=w.s[pos:pos+len_],
                                                pos=pos,
                                                len=len_)
            )
            return (argd, pos, len_)

        if self.verbatim_arg_type == 'verb-macro':
            # read the next nonwhitespace char. This is the delimiter of the
            # argument
            while w.s[pos].isspace():
                pos += 1
                if pos >= len(w.s):
                    raise latexwalker.LatexWalkerParseError(
                        s=w.s,
                        pos=pos,
                        msg=r"Missing argument to \verb command"
                    )
            verbdelimchar = w.s[pos]
            beginpos = pos+1
            endpos = w.s.find(verbdelimchar, beginpos)
            if endpos == -1:
                raise latexwalker.LatexWalkerParseError(
                    s=w.s,
                    pos=pos,
                    msg=r"End of stream reached while reading argument to \verb command"
                )
            
            verbarg = w.s[beginpos:endpos]

            argd = ParsedVerbatimArgs(
                verbatim_chars_node=w.make_node(latexwalker.LatexCharsNode,
                                                parsing_state=parsing_state,
                                                chars=verbarg,
                                                pos=beginpos,
                                                len=endpos-beginpos),
                verbatim_delimiters=(verbdelimchar, verbdelimchar),
            )

            return (argd, pos, endpos+1-pos) # include delimiters in pos/len


    def __repr__(self):
        return '{}(verbatim_arg_type={!r})'.format(
            self.__class__.__name__, self.verbatim_arg_type
        )

