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


import logging
logger = logging.getLogger(__name__)


#__pragma__('opov')


_unisafe_arrow_s = '→'
### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _unisafe_arrow_s = '->'
### END_PYTHON2_SUPPORT_CODE



# allowed macro chars by default: [a-zA-Z]
_default_macro_alpha_chars = (
    "".join([
        chr(ord('a')+j) for j in range(26)
    ]) + "".join([
        chr(ord('A')+j) for j in range(26)
    ])
)


### BEGINPATCH_UNIQUE_OBJECT_ID
fn_unique_object_id = id
### ENDPATCH_UNIQUE_OBJECT_ID




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

       .. deprecated:: 3.0

          The `s` attribute is deprecated starting in `pylatexenc 3`.  If you
          have access to a node instance (cf. :py:class:`LatexNode`) and would
          like to find out the original string that was parsed, use
          `node.latex_walker.s` instead of querying the parsing state.  (The
          rationale of removing the `s` attribute from the parsing state is for
          parsing state objects to have a meaning of their own independently of
          any string being parsed or any latex walker instance.)

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

       Doc ............

    .. py:attribute:: latex_inline_math_delimiters

       Doc ............

    .. py:attribute:: latex_display_math_delimiters

       Doc ............

    .. py:attribute:: enable_double_newline_paragraphs

       Doc ............

    .. py:attribute:: enable_environments

       .Doc ...........

    .. py:attribute:: enable_comments

       Doc ............

    .. py:attribute:: macro_alpha_chars

       Doc ............

    .. py:attribute:: macro_escape_char

       Doc ................

    .. py:attribute:: forbidden_characters

       Characters that are simply forbidden to occur as regular characters.  You
       can use this for instance if you'd like to disable some LaTeX-like
       features but cause the corresponding character to raise an error. For
       instance, you can force inline math to be typed as ``\(...\)`` and not as
       ``$...$``, and yet still force users to type ``\$`` for a dollar sign by
       including '$' in the list of forbidden characters.

       The `forbidden_characters` can be a string, or a list of single-character
       strings; this attribute will be used with the syntax ``if (c in
       forbidden_characters): ...``

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
       `enable_environments`, `enable_comments`, `macro_alpha_chars`,
       `macro_escape_char`, and `forbidden_characters` were introduced in
       version 3.

    .. versionadded:: 3.0

       This class was moved to :py:class:`pylatexenc.latexnodes.ParsingState`
       starting in `pylatexenc 3.0`.  In earlier versions, this class was
       located in the :py:mod:`~pylatexenc.latexwalker` module, see
       :py:class:`~pylatexenc.latexwalker.ParsingState`.
    """

    _fields = (
        's',
        'latex_context',
        'in_math_mode',
        'math_mode_delimiter',
        'latex_group_delimiters',
        'latex_inline_math_delimiters',
        'latex_display_math_delimiters',
        'enable_double_newline_paragraphs',
        'enable_macros',
        'enable_environments',
        'enable_comments',
        'enable_groups',
        'enable_specials',
        'enable_math',
        'macro_alpha_chars',
        'macro_escape_char',
        'comment_start',
        'forbidden_characters',
    )

    def __init__(self, **kwargs):
        super(ParsingState, self).__init__()

        # (parent state object, changed kwargs)
        self._parent_parsing_state_info = \
            kwargs.pop('_parent_parsing_state_info', (None, {}))

        self.set_fields(**kwargs)

        self.finalize_state()


    def set_fields(self,
                   s=None,
                   latex_context=None,
                   in_math_mode=False,
                   math_mode_delimiter=None,
                   latex_group_delimiters=None,
                   latex_inline_math_delimiters=None,
                   latex_display_math_delimiters=None,
                   enable_double_newline_paragraphs=True,
                   enable_macros=True,
                   enable_environments=True,
                   enable_comments=True,
                   enable_groups=True,
                   enable_specials=True,
                   enable_math=True,
                   macro_alpha_chars=_default_macro_alpha_chars,
                   macro_escape_char='\\',
                   comment_start='%',
                   forbidden_characters='',
                   ):

        self.s = s

        self.latex_context = latex_context

        self.in_math_mode = in_math_mode
        self.math_mode_delimiter = math_mode_delimiter

        if not self.in_math_mode and self.math_mode_delimiter:
            logger.warning(
                "ParsingState: You set math_mode_delimiter=%r but "
                "in_math_mode is False", self.math_mode_delimiter
            )
            self.math_mode_delimiter = None

        # new fields in pylatexenc 3

        self.latex_group_delimiters = (
            latex_group_delimiters if latex_group_delimiters is not None else
            [ ('{', '}'), ] # must be single characters!
        )

        self.latex_inline_math_delimiters = (
            latex_inline_math_delimiters if latex_inline_math_delimiters is not None else
            [ ('$', '$'), (r'\(', r'\)'), ]
        )
        self.latex_display_math_delimiters = (
            latex_display_math_delimiters if latex_display_math_delimiters is not None else
            [ ('$$', '$$'), (r'\[', r'\]'), ]
        )
        self.enable_double_newline_paragraphs = enable_double_newline_paragraphs
        self.enable_macros = enable_macros
        self.enable_environments = enable_environments
        self.enable_comments = enable_comments
        self.enable_groups = enable_groups
        self.enable_specials = enable_specials
        self.enable_math = enable_math
        self.macro_alpha_chars = macro_alpha_chars

        # !!! at various places in LatexTokenReader, both of these are assumed
        # !!! to be single characters.
        self.macro_escape_char = macro_escape_char # character that introduces a macro
        self.comment_start = comment_start # character that starts a comment

        self.forbidden_characters = forbidden_characters


    def _finalize_state_latex_group_delimiters_info(self, parent, kwargs):

        if parent is not None and 'latex_group_delimiters' not in kwargs:
            # group delimiters were not changed from parent object, re-use
            # cached values there
            self._latex_group_delimchars_by_open = parent._latex_group_delimchars_by_open
            self._latex_group_delimchars_close = parent._latex_group_delimchars_close
            return

        # compute cached info for latex group delimiters --
        a, b = zip(*self.latex_group_delimiters) # a = list of open delims, b = close delims
        self._latex_group_delimchars_by_open = dict(self.latex_group_delimiters)
        self._latex_group_delimchars_close = frozenset(b)


    def _finalize_state_latex_math_delim_info(self, parent, kwargs):

        if parent is not None \
           and 'latex_inline_math_delimiters' not in kwargs \
           and 'latex_display_math_delimiters' not in kwargs:
            # relevant info not changed, reuse parent info
            self._math_delims_info_startchars = parent._math_delims_info_startchars
            self._math_all_delims_by_len = parent._math_all_delims_by_len
            self._math_delims_info_by_open = parent._math_delims_info_by_open
            self._math_delims_close = parent._math_delims_close
            return

        self._math_delims_info_startchars = "".join([
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
        
    def _finalize_state_inmathmode_info(self, parent, kwargs):

        if parent is not None \
           and 'in_math_mode' not in kwargs \
           and 'math_mode_delimiter' not in kwargs:
            # relevant info not changed, reuse parent info
            self._math_expecting_close_delim_info = parent._math_expecting_close_delim_info
            return

        if not self.in_math_mode:
            self._math_expecting_close_delim_info = None
        elif self.math_mode_delimiter in self._math_delims_info_by_open:
            self._math_expecting_close_delim_info = self._math_delims_info_by_open[
                self.math_mode_delimiter
            ]
        else:
            # Normal, can happen in math environments delimited by
            # e.g. \begin{align}...\end{align}
            self._math_expecting_close_delim_info = None

        # logger.debug("set parsing state internal math mode info, "
        #              "self._math_expecting_close_delim_info=%r",
        #              self._math_expecting_close_delim_info)
        

    def finalize_state(self):

        parent, kwargs = self._parent_parsing_state_info

        self._finalize_state_latex_group_delimiters_info(parent, kwargs)
        self._finalize_state_latex_math_delim_info(parent, kwargs)
        self._finalize_state_inmathmode_info(parent, kwargs)
        
        #logger.debug("finalize_state() done. parent=%r; kwargs=%r.", parent, kwargs)


    # ---

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

        #logger.debug("sub_context(%r)", kwargs)

        attrs = self.get_fields()
        kwargs2 = {
            k: v
            for k, v in kwargs.items()
            if not _safe_eq(v, attrs[k])
        }

        attrs.update(kwargs2)

        p = self.__class__(_parent_parsing_state_info=(self, kwargs2),
                           **attrs)

        logger.debug("%s.sub_context(%r): %r --> %r", self.__class__.__name__, kwargs, self, p)

        return p


    def get_fields(self):
        r"""
        Returns the fields and values associated with this `ParsingState` as a
        dictionary.
        """
        return dict([(f, getattr(self, f)) for f in self._fields])



    def __repr__(self):

        # To shorten ParsingState representation strings, we only show diffs
        # with respect to the parent objects, along with object id's.

        clsname = self.__class__.__name__
        pswid = "{}<{:#x}>".format(clsname, fn_unique_object_id(self))

        parent_obj, diff_kwargs = self._parent_parsing_state_info

        if not parent_obj:
            # no parent, simply show ID. the user already knows this parsing
            # state because it's the one they provided at the start
            return pswid

        # show only fields that differ w.r.t. parent.
        return (
            pswid + "(<{:#x}> {} ".format(fn_unique_object_id(parent_obj), _unisafe_arrow_s)
            +  ", ".join([
                "{}={!r}".format(k, v)
                for k, v in diff_kwargs.items()
                if k not in ('s',)
            ]) + ")"
        )


    def to_json_object(self):
        return { k: v
                 for k, v in self.get_fields().items()
                 if k not in ('latex_context','s',) }



def _safe_eq(a, b):
    return ((a is None and b is None) or a == b)
