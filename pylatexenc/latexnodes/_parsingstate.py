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


class _StrictAsciiAlphaChars(object):
    def __str__(self):
        return "".join([
            chr(ord('a')+j) for j in range(26)
        ]) + "".join([
            chr(ord('A')+j) for j in range(26)
        ])
    def __repr__(self):
        return repr(self.__str__())
    def __contains__(self, c):
        n = ord(c)
        return (
            (97 <= n <= 122)  # 97 == ord('a'), 122 == ord('z')
            or
            (65 <= n <= 90) # 65, 90 == ord('A'), ord('Z')
        )



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
       initiated the math mode (one of ``'$'``, ``'$$'``, ``r'\('``, ``r'\['``).
       For user-initiated math modes (e.g. by a custom environment definition),
       you can set this string to any custom value EXCEPT any of the core math
       mode delimiters listed above.

       .. note:: The tokenizer/parser relies on the value of the
                 `math_mode_delimiter` attribute to disambiguate two consecutive
                 dollar signs ``...$$...`` into either a display math mode
                 delimiter or two inline math mode delimiters (as in
                 ``$a$$b$``).  You should only set `math_mode_delimiter='$'` if
                 you know what you're doing.


    .. py:attribute:: latex_group_delimiters

       ............

    .. py:attribute:: latex_inline_math_delimiters

       ............

    .. py:attribute:: latex_display_math_delimiters

       ............

    .. py:attribute:: enable_double_newline_paragraphs

       ............

    .. py:attribute:: enable_environments

       ............

    .. py:attribute:: enable_comments

       ............

    .. py:attribute:: macro_alpha_chars

       ............


    .. versionadded:: 2.0
 
       This class was introduced in version 2.0.

    .. versionadded:: 2.7

       The attribute `math_mode_delimiter` was introduced in version 2.7.

    .. versionchanged:: 2.7

       All arguments must now be specified as keyword arguments as of version
       2.7.

    .. versionadded:: 3.0

       The attributes `latex_group_delimiters`, `latex_inline_math_delimiters`,
       `latex_display_math_delimiters`, `enable_double_newline_paragraphs`,
       `enable_environments`, `enable_comments`, and `macro_alpha_chars` were
       introduced in version 3.
    """
    def __init__(self, **kwargs):
        super(ParsingState, self).__init__()

        self.s = None

        self.latex_context = None

        self.in_math_mode = False
        self.math_mode_delimiter = None

        # new in pylatexenc 3
        self.latex_group_delimiters = [ ('{', '}'), ] # must be single characters!
        self.latex_inline_math_delimiters = [ ('$', '$'), (r'\(', r'\)'), ]
        self.latex_display_math_delimiters = [ ('$$', '$$'), (r'\[', r'\]'), ]
        self.enable_double_newline_paragraphs = True
        self.enable_environments = True
        self.enable_comments = True
        self.macro_alpha_chars = _StrictAsciiAlphaChars()

        # set internally by the other fields by _set_fields()
        self._latex_group_delimchars_by_open = {}
        self._latex_group_delimchars_close = frozenset()
        self._math_delims_info_startchars = ''
        self._math_delims_by_len = []
        self._math_delims_info_by_open = {}
        self._math_delims_close = frozenset()
        self._math_expecting_close_delim = None

        self._fields = (
            's',
            'latex_context', 'in_math_mode', 'math_mode_delimiter',
            'latex_group_delimiters',
            'latex_inline_math_delimiters', 'latex_display_math_delimiters',
            'enable_double_newline_paragraphs',
            'enable_environments',
            'enable_comments',
            'macro_alpha_chars',
        )

        do_sanitize = kwargs.pop('_do_sanitize', True)

        self._set_fields(kwargs, do_sanitize=do_sanitize)

    def _set_derivative_fields(self):
        a, b = zip(*self.latex_group_delimiters)
        self._latex_group_delimchars_by_open = dict(self.latex_group_delimiters)
        #self._latex_group_delimchars_open = frozenset(a)
        self._latex_group_delimchars_close = frozenset(b)
        #
        #
        # FIXME: DO NOT RECOMPUTE THESE FIELDS ALL THE TIME WHEN THE DELIMITER
        # LISTS DO NOT CHANGE....
        self._math_delims_info_startchars = frozenset([
            x[:1]
            for pair in (self.latex_inline_math_delimiters
                      + self.latex_display_math_delimiters)
            for x in pair
        ])
        self._math_all_delims_by_len = sorted(
            [
                (delim, tok_type)
                for delimlist, tok_type in (
                        (self.latex_inline_math_delimiters, 'mathmode_inline'),
                        (self.latex_display_math_delimiters, 'mathmode_display'),
                )
                for delim in set([dlm for dlmpair in delimlist for dlm in dlmpair])
            ],
            key=lambda x: len(x[0]),
            reverse=True,
        )
        # self._math_delims_by_len = sorted(
        #     self.latex_inline_math_delimiters + self.latex_display_math_delimiters,
        #     key=lambda x: len(x[0]),
        #     reverse=True,
        # )
        self._math_delims_info_by_open = dict(
            [ (open_delim, dict(close_delim=close_delim, tok='mathmode_inline'))
              for open_delim, close_delim in self.latex_inline_math_delimiters ]
            + [ (open_delim, dict(close_delim=close_delim, tok='mathmode_display'))
              for open_delim, close_delim in self.latex_display_math_delimiters ]
        )
        self._math_delims_close = frozenset([
            info['close_delim']
            for opendelim,info in self._math_delims_info_by_open.items()
        ])
        if not self.in_math_mode:
            self._math_expecting_close_delim_info = None
        else:
            try:
                self._math_expecting_close_delim_info = self._math_delims_info_by_open[
                    self.math_mode_delimiter
                ]
            except KeyError as e:
                # Normal, can happen in math environments delimited by
                # e.g. \begin{align}...\end{align}
                self._math_expecting_close_delim_info = None



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

        #
        # set internal preprocessed values
        #
        self._set_derivative_fields()


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

