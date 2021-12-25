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


import logging
logger = logging.getLogger(__name__)



class ParsingState(object):
    r"""
    Stores some information about the current parsing state, such as whether we
    are currently in a math mode block.

    One of the ideas of `pylatexenc` is to make the parsing of LaTeX code mostly
    state-independent mark-up parsing (in contrast to a full TeX engine, whose
    state constantly changes and whose parsing behavior is altered dynamically
    while parsing).  However a minimal state of the context might come in handy
    sometimes.  Perhaps some macros or specials should behave differently in
    math mode than in text mode.

    This class also stores some essential information that is associated with
    :py:class:`LatexNode`\ 's and which provides a context to better understand
    the node structure.  For instance, we store the original parsed string, and
    each node refers to which part of the string they represent.
    
    .. py:attribute:: s

       The string that is parsed by the :py:class:`LatexWalker`

    .. py:attribute:: latex_context

       The latex context (with macros/environments specifications) that was used
       when parsing the string `s`.  This is a
       :py:class:`pylatexenc.macrospec.LatexContextDb` object.

    .. py:attribute:: in_math_mode

       Whether or not we are in a math mode chunk of LaTeX (True or False).
       This can be inline or display, and can be caused by an equation
       environment.

    .. py:attribute:: math_mode_delimiter

       Information about the kind of math mode we are currently in, if
       `in_math_mode` is `True`.  This is a string which can be set to aid the
       parser.  The parser sets this field to the math mode delimiter that
       initiated the math mode (one of ``'$'``, ``'$$'``, ``r'\('``, ``r'\)'``).
       For user-initiated math modes (e.g. by a custom environment definition),
       you can set this string to any custom value EXCEPT any of the core math
       mode delimiters listed above.

       .. note:: The tokenizer/parser relies on the value of the
                 `math_mode_delimiter` attribute to disambiguate two consecutive
                 dollar signs ``...$$...`` into either a display math mode
                 delimiter or two inline math mode delimiters (as in
                 ``$a$$b$``).  You should only set `math_mode_delimiter='$'` if
                 you know what you're doing.

    .. versionadded:: 2.0
 
       This class was introduced in version 2.0.

    .. versionadded:: 2.7

       The attribute `math_mode_delimiter` was introduced in version 2.7.

    .. versionchanged:: 2.7

       All arguments must now be specified as keyword arguments as of version
       2.7.
    """
    def __init__(self, **kwargs):
        super(ParsingState, self).__init__()
        self.s = None
        self.latex_context = None
        self.in_math_mode = False
        self.math_mode_delimiter = None

        # new in pylatexenc 3
        self.latex_group_delimiters = [ ('{', '}'), ]
        self.latex_inline_math_delimiters = [ ('$', '$'), (r'\(', r'\)'), ]
        self.latex_display_math_delimiters = [ ('$$', '$$'), (r'\[', r'\]'), ]
        self.enable_environments = True
        self.enable_comments = True
        self.enable_nlnl_paragraph = True

        self._fields = ('s', 'latex_context', 'in_math_mode', 'math_mode_delimiter', )

        do_sanitize = kwargs.pop('_do_sanitize', True)

        self._set_fields(kwargs, do_sanitize=do_sanitize)

    def sub_context(self, **kwargs):
        r"""
        Return a new :py:class:`ParsingState` instance that is a copy of the current
        parsing state, but where the given properties keys have been set to the
        corresponding values (given as keyword arguments).

        This makes it easy to create a sub-context in a given parser.  For
        instance, if we enter math mode, we might write::

           parsing_state_inner = parsing_state.sub_context(in_math_mode=True)

        If no arguments are provided, this returns a copy of the present parsing
        context object.
        """
        p = self.__class__(_do_sanitize=False, **self.get_fields())

        p._set_fields(kwargs)

        return p

    def get_fields(self):
        r"""
        Returns the fields and values associated with this `ParsingState` as a
        dictionary.
        """
        return dict([(f, getattr(self, f)) for f in self._fields])


    def _set_fields(self, kwargs, do_sanitize=True):

        for k, v in kwargs.items():
            if k not in self._fields:
                raise ValueError("Invalid field for ParsingState: {}={!r}".format(k, v))
            setattr(self, k, v)

        if do_sanitize:
            # Do some sanitization.  If we set in_math_mode=False, then we should
            # clear any math_mode_delimiter.
            self._sanitize(given_fields=kwargs)

    def _sanitize(self, given_fields):
        """
        Sanitize the parsing state.  E.g., clear any `math_mode_delimiter` if
        `in_math_mode` is `False`.

        The argument `given_fields` is what fields the user required to set;
        this is used to generate warnings if incompatible field configurations
        were explicitly required to be set.
        """
        if not self.in_math_mode and self.math_mode_delimiter:
            self.math_mode_delimiter = None
            if 'math_mode_delimiter' in given_fields:
                logger.warning(
                    "ParsingState: You set math_mode_delimiter=%r but "
                    "in_math_mode is False", self.math_mode_delimiter
                )

