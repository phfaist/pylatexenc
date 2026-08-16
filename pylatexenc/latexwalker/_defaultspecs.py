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


# Internal module. May change without notice.

from ..latexnodes import (
    LatexArgumentSpec,
    ParsingStateDeltaEnterMathMode,
    ParsingStateDeltaLeaveMathMode,
)
from ..latexnodes.nodes import (
    LatexCharsNode,
)
from ..latexnodes.parsers import (
    LatexStandardArgumentParser,
    LatexExpressionParser,
    LatexCharsGroupParser,
    LatexDelimitedVerbatimParser,
    LatexVerbatimEnvironmentContentsParser,
)

from ..macrospec import (
    std_macro,
    std_environment,
    std_specials,
    MacroSpec, EnvironmentSpec, SpecialsSpec,
    LatexSpecialsCallParser,
    # MacroStandardArgsParser,
)


class _SubSuperscriptSpec(SpecialsSpec):
    r"""
    The '^' and '_' specials, which pick up an argument in math mode but which
    are ordinary characters in text mode.

    In math mode, the argument is a single token, exactly as TeX reads it: in
    ``x^12`` only the ``1`` is superscripted.  A group ``x^{12}`` is picked up in
    its entirety, and so is a macro along with its own arguments, as in
    ``x_\mathrm{initial}``.

    In text mode, ``^`` and ``_`` don't pick up any argument at all.  (They are
    in fact errors in LaTeX there.)  This keeps for instance the file name in
    ``\input{my_file.tex}`` in one piece.
    """
    def __init__(self, specials_chars, argname):
        super(_SubSuperscriptSpec, self).__init__(
            specials_chars,
            arguments_spec_list=[
                LatexArgumentSpec(
                    LatexExpressionParser(parse_callable_arguments=True,
                                          return_full_node_list=False),
                    argname=argname,
                ),
            ],
        )
        # the spec to use in text mode: the same specials characters, but
        # without any arguments
        self.text_mode_spec = SpecialsSpec(specials_chars)

    def get_node_parser(self, token, parsing_state):
        if parsing_state.in_math_mode:
            return super(_SubSuperscriptSpec, self).get_node_parser(token, parsing_state)
        # NOTE: a call parser is bound to the token it is given---the node's
        # `pos` and `pos_end` are taken from it---so it has to be created for
        # each call rather than stored once and for all on this spec object.
        return LatexSpecialsCallParser(token, self.text_mode_spec)


def _arg_mathmode(parser):
    return LatexArgumentSpec(parser, parsing_state_delta=ParsingStateDeltaEnterMathMode())

def _arg_textmode(parser):
    return LatexArgumentSpec(parser, parsing_state_delta=ParsingStateDeltaLeaveMathMode())

def _arg_charsname(argname):
    r"""
    An argument that is a name rather than LaTeX code: a file name, a label
    name, and the like.

    The contents are read as plain characters, so that a character which would
    otherwise be picked up as a specials or as a macro stays part of the name.
    Without this, the underscore in ``\input{my_file.tex}`` is reported as its
    own specials node and a caller that reassembles the argument from its chars
    nodes ends up with ``myfile.tex``.
    """
    return LatexArgumentSpec(LatexCharsGroupParser(), argname=argname)


def _make_verbatim_environment_body_parser(token, nodeargd, arg_parsing_state_delta):
    r"""
    Body parser factory for environments whose contents are to be read
    verbatim, up to the matching ``\end{...}``.
    """
    return LatexVerbatimEnvironmentContentsParser(environment_name=token.arg)


def _verbatim_chars_of(nodelist):
    r"""
    Return the concatenated characters of the chars nodes in `nodelist`, or
    `None` if there is no node list at all (e.g. because the verbatim contents
    could not be parsed).
    """
    if nodelist is None:
        return None
    chars = ''
    for n in nodelist:
        if n is not None and n.isNodeType(LatexCharsNode):
            chars += n.chars
    return chars


def _finalize_verb_macro_node(node):
    r"""
    Expose the verbatim content of a ``\verb`` call on its parsed-arguments
    object as `verbatim_text` and `verbatim_delimiters`, the way `pylatexenc 2`
    did.  The content itself lives in the argument group node.
    """
    verbatim_text, verbatim_delimiters = None, None

    argnlist = node.nodeargd.argnlist
    if argnlist and argnlist[0] is not None:
        verbatim_group_node = argnlist[0]
        verbatim_text = _verbatim_chars_of(verbatim_group_node.nodelist)
        verbatim_delimiters = verbatim_group_node.delimiters

    node.nodeargd.verbatim_text = verbatim_text
    node.nodeargd.verbatim_delimiters = verbatim_delimiters

    return node


def _finalize_verbatim_environment_node(node):
    r"""
    Same as :py:func:`_finalize_verb_macro_node()`, for verbatim environments.
    Here the content is the environment body, and there are no delimiters.
    """
    node.nodeargd.verbatim_text = _verbatim_chars_of(node.nodelist)
    node.nodeargd.verbatim_delimiters = None

    return node


def _finalize_lstlisting_environment_node(node):
    r"""
    Same as :py:func:`_finalize_verbatim_environment_node()`, plus the
    `lstlisting_text` attribute that `pylatexenc 2` provided in addition on
    ``lstlisting`` environments.
    """
    node = _finalize_verbatim_environment_node(node)
    node.nodeargd.lstlisting_text = node.nodeargd.verbatim_text

    return node



specs = [
    #
    # CATEGORY: latex-paragraph
    #
    ('latex-paragraph', {
        'macros': [],
        'environments': [],
        'specials': [
            std_specials('\n\n'), # paragraph break
        ],
    }),

    #
    # CATEGORY: latex-base
    #
    ('latex-base', {
        'macros': [

            MacroSpec('documentclass', arguments_spec_list=[
                '[', _arg_charsname('classname') ]),
            MacroSpec('usepackage', arguments_spec_list=[
                '[', _arg_charsname('packagename') ]),
            MacroSpec('RequirePackage', arguments_spec_list=[
                '[', _arg_charsname('packagename') ]),
            std_macro('selectlanguage', True, 1),
            std_macro('setlength', True, 2),
            std_macro('addlength', True, 2),
            std_macro('setcounter', True, 2),
            std_macro('addcounter', True, 2),
            std_macro('newcommand', "*{[[{"),
            std_macro('renewcommand', "*{[[{"),
            std_macro('providecommand', "*{[[{"),
            std_macro('newenvironment', "*{[[{{"),
            std_macro('renewenvironment', "*{[[{{"),
            std_macro('provideenvironment', "*{[[{{"),

            std_macro('DeclareMathOperator', '*{{'),
            # \operatorname{tr} and \operatorname*{ess\,sup}, for a function
            # name that has no macro of its own
            std_macro('operatorname', '*{'),

            std_macro('hspace', '*{'),
            std_macro('vspace', '*{'),

            MacroSpec('mbox', arguments_spec_list=[ _arg_textmode('{') ]),

            # \title, \author, \date.
            #
            # The standard classes (article, report, book) declare these with a
            # single mandatory argument.  A number of widely used classes add a
            # leading optional argument that holds a short form of the field,
            # meant for running heads and similar places:
            #
            #     \title[Short title]{The full and rather long title}
            #
            # beamer does this for all three commands; the AMS classes (amsart,
            # amsbook, amsproc — and acmart, which is built on amsart) do it for
            # \title and \author.  Documents that use the standard classes
            # simply never have the optional argument present, so declaring it
            # here costs them nothing while letting the common non-standard
            # forms parse correctly.
            MacroSpec('title', '[{'),
            MacroSpec('author', '[{'),
            MacroSpec('date', '[{'),

            # (Note: single backslash) end of line with optional no-break ('*') and
            # additional vertical spacing, e.g. \\*[2mm]
            #
            # Special for this command: don't allow an optional spacing argument
            # [2mm] to be separated by spaces from the rest of the macro.  This
            # emulates the behavior in AMS environments, and avoids some errors;
            # e.g. in "\begin{align} A=0 \\ [C,D]=0 \end{align}" the "[C,D]"
            # does not get captured as an optional macro argument.
            MacroSpec('\\', arguments_spec_list=[
                LatexArgumentSpec('*'),
                LatexArgumentSpec(LatexStandardArgumentParser('[', allow_pre_space=False)),
            ]),

            std_macro('item', True, 0),

            # \input{someotherfile}
            MacroSpec('input', arguments_spec_list=[ _arg_charsname('filename') ]),
            MacroSpec('include', arguments_spec_list=[ _arg_charsname('filename') ]),

            MacroSpec('includegraphics', arguments_spec_list=[
                '[',
                _arg_charsname('filename'),
            ]),

            std_macro('part', '*[{'),
            std_macro('chapter', '*[{'),
            std_macro('section', '*[{'),
            std_macro('subsection', '*[{'),
            std_macro('subsubsection', '*[{'),
            std_macro('paragraph', '*[{'),
            std_macro('subparagraph', '*[{'),

            MacroSpec('bibliography', arguments_spec_list=[ _arg_charsname('filename') ]),
            # \bibitem[label]{citekey}, in a {thebibliography} environment
            MacroSpec('bibitem', arguments_spec_list=[
                '[', _arg_charsname('citekey') ]),


            std_macro('emph', False, 1),
            MacroSpec('textrm', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('textit', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('textbf', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('textmd', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('textsc', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('textsf', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('textsl', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('texttt', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('textup', arguments_spec_list=[ _arg_textmode('{') ]),
            MacroSpec('text',   arguments_spec_list=[ _arg_textmode('{') ]),
            std_macro('mathrm', False, 1), # only allowed in math mode anyway
            std_macro('mathbb', False, 1), # only allowed in math mode anyway
            std_macro('mathbf', False, 1),
            std_macro('mathit', False, 1),
            std_macro('mathsf', False, 1),
            std_macro('mathtt', False, 1),
            std_macro('mathcal', False, 1),
            std_macro('mathscr', False, 1),
            std_macro('mathfrak', False, 1),

            MacroSpec('label', arguments_spec_list=[ _arg_charsname('label') ]),
            MacroSpec('ref', arguments_spec_list=[ _arg_charsname('label') ]),
            MacroSpec('autoref', arguments_spec_list=[ _arg_charsname('label') ]),
            MacroSpec('cref', arguments_spec_list=[ _arg_charsname('label') ]),
            MacroSpec('Cref', arguments_spec_list=[ _arg_charsname('label') ]),
            MacroSpec('eqref', arguments_spec_list=[ _arg_charsname('label') ]),
            MacroSpec('href', arguments_spec_list=[
                LatexArgumentSpec(
                    LatexDelimitedVerbatimParser(delimiters=('{','}'),),
                    argname='url',
                ),
                '{'
            ]),
            MacroSpec('url', arguments_spec_list=[
                LatexArgumentSpec(
                    LatexDelimitedVerbatimParser(delimiters=('{','}'),),
                    argname='url',
                ),
            ]),
            std_macro('hypersetup', False, 1),
            std_macro('footnote', True, 1),

            std_macro('keywords', False, 1),

            std_macro('hphantom', True, 1),
            std_macro('vphantom', True, 1),

            std_macro("'", False, 1),
            std_macro("`", False, 1),
            std_macro('"', False, 1),
            std_macro("c", False, 1),
            std_macro("^", False, 1),
            std_macro("~", False, 1),
            std_macro("H", False, 1),
            std_macro("k", False, 1),
            std_macro("=", False, 1),
            std_macro("b", False, 1),
            std_macro(".", False, 1),
            std_macro("d", False, 1),
            std_macro("r", False, 1),
            std_macro("u", False, 1),
            std_macro("v", False, 1),

            MacroSpec('ensuremath', arguments_spec_list=[ _arg_mathmode('{') ]),

            std_macro("not", False, 1),

            std_macro("vec", False, 1),
            std_macro("dot", False, 1),
            std_macro("hat", False, 1),
            std_macro("check", False, 1),
            std_macro("breve", False, 1),
            std_macro("acute", False, 1),
            std_macro("grave", False, 1),
            std_macro("tilde", False, 1),
            std_macro("bar", False, 1),
            std_macro("ddot", False, 1),

            std_macro('frac', False, 2),
            std_macro('nicefrac', False, 2),
            std_macro('textfrac', False, 2),

            std_macro('sqrt', True, 1),

            # the modulo constructs that take the modulus as an argument;
            # '\bmod' is the infix operator and takes none
            MacroSpec('pmod', '{'),
            MacroSpec('mod', '{'),

            MacroSpec('overline', '{'),
            MacroSpec('underline', '{'),
            MacroSpec('widehat', '{'),
            MacroSpec('widetilde', '{'),
            MacroSpec('wideparen', '{'),
            MacroSpec('overleftarrow', '{'),
            MacroSpec('overrightarrow', '{'),
            MacroSpec('overleftrightarrow', '{'),
            MacroSpec('underleftarrow', '{'),
            MacroSpec('underrightarrow', '{'),
            MacroSpec('underleftrightarrow', '{'),
            MacroSpec('overbrace', '{'),
            MacroSpec('underbrace', '{'),
            MacroSpec('overgroup', '{'),
            MacroSpec('undergroup', '{'),
            MacroSpec('overbracket', '{'),
            MacroSpec('underbracket', '{'),
            MacroSpec('overlinesegment', '{'),
            MacroSpec('underlinesegment', '{'),
            MacroSpec('overleftharpoon', '{'),
            MacroSpec('overrightharpoon', '{'),

            MacroSpec('xleftarrow', '[{'),
            MacroSpec('xrightarrow', '[{'),

            std_macro('ket', False, 1),
            std_macro('bra', False, 1),
            std_macro('braket', False, 2),
            std_macro('ketbra', False, 2),

            std_macro('texorpdfstring', False, 2),

            # xcolor commands
            MacroSpec('definecolor', '[{{{'),
            MacroSpec('providecolor', '[{{{'),
            MacroSpec('colorlet', '[{[{'),
            MacroSpec('color', '[{'),
            MacroSpec('textcolor', '[{{'),
            MacroSpec('pagecolor', '[{'),
            MacroSpec('nopagecolor', ''),
            MacroSpec('colorbox', '[{{'),
            MacroSpec('fcolorbox', '[{[{{'),
            MacroSpec('boxframe', '{{{'),
            MacroSpec('rowcolors', '*[{{{'),
        ],
        'environments': [
            # NOTE: Starred variants (as in \begin{equation*}) are not specified as
            # for macros with an argspec='*'.  Rather, we need to define a separate
            # spec for the starred variant as the star really is part of the
            # environment name.  If you specify argspec='*', the parser will try to
            # look for an expression of the form '\begin{equation}*'

            std_environment('figure', '['),
            std_environment('figure*', '['),
            std_environment('table', '['),
            std_environment('table*', '['),

            std_environment('abstract', None),
            
            std_environment('tabular', '{'),
            std_environment('tabular*', '{{'),
            std_environment('tabularx', '{[{'),

            std_environment('array', '[{'),

            std_environment('equation', None, is_math_mode=True),
            std_environment('equation*', None, is_math_mode=True),
            std_environment('eqnarray', None, is_math_mode=True),
            std_environment('eqnarray*', None, is_math_mode=True),
        
            # AMS environments
            std_environment('align', None, is_math_mode=True),
            std_environment('align*', None, is_math_mode=True),
            std_environment('gather', None, is_math_mode=True),
            std_environment('gather*', None, is_math_mode=True),
            std_environment('flalign', None, is_math_mode=True),
            std_environment('flalign*', None, is_math_mode=True),
            std_environment('multline', None, is_math_mode=True),
            std_environment('multline*', None, is_math_mode=True),
            std_environment('alignat', '{', is_math_mode=True),
            std_environment('alignat*', '{', is_math_mode=True),
            std_environment('split', None, is_math_mode=True),
        ],
        'specials': [
            std_specials('&'),

            _SubSuperscriptSpec('^', 'superscript'),
            _SubSuperscriptSpec('_', 'subscript'),
        ]}),


    #
    # CATEGORY: nonascii-specials
    #
    ('nonascii-specials', {
        'macros': [],
        'environments': [],
        'specials': [
            std_specials("~"),
            
            # cf. https://tex.stackexchange.com/a/439652/32188 "fake ligatures":
            std_specials('``'),
            std_specials("''"),
            std_specials("--"),
            std_specials("---"),
            std_specials("!`"),
            std_specials("?`"),
        ]}),


    #
    # CATEGORY: verbatim
    #
    ('verbatim', {
        'macros': [
            MacroSpec('verb',
                      arguments_spec_list=[
                          LatexArgumentSpec(
                              LatexDelimitedVerbatimParser(),
                              argname='verbatim_content',
                          ),
                      ],
                      finalize_node=_finalize_verb_macro_node),
            ],
        'environments': [
            EnvironmentSpec('verbatim',
                            arguments_spec_list=[],
                            make_body_parser=_make_verbatim_environment_body_parser,
                            finalize_node=_finalize_verbatim_environment_node),
        ],
        'specials': [
            # optionally users could include the specials "|" like in latex-doc
            # for verbatim |\like \this|...
        ]}),

    #
    # CATEGORY: lstlisting
    #
    ('lstlisting', {
        'macros': [],
        'environments': [
            EnvironmentSpec('lstlisting',
                            arguments_spec_list=[
                                LatexArgumentSpec(
                                    # a ‘[’ that doesn't immediately follow
                                    # \begin{lstlisting} is verbatim content,
                                    # not an optional argument
                                    LatexStandardArgumentParser(
                                        '[', allow_pre_space=False),
                                    argname='lstlisting_options',
                                ),
                            ],
                            make_body_parser=_make_verbatim_environment_body_parser,
                            finalize_node=_finalize_lstlisting_environment_node),
        ],
        'specials': [
            # optionally users could include the specials "|" like in latex-doc
            # for lstlisting |\like \this|...
        ]}),

    #
    # CATEGORY: theorems
    #
    ('theorems', {
        'macros': [],
        'environments': [
            std_environment('theorem', '['),
            std_environment('proposition', '['),
            std_environment('lemma', '['),
            std_environment('corollary', '['),
            std_environment('definition', '['),
            std_environment('conjecture', '['),
            std_environment('remark', '['),
            #
            std_environment('proof', '['),
            # short names
            std_environment('thm', '['),
            std_environment('prop', '['),
            std_environment('lem', '['),
            std_environment('cor', '['),
            std_environment('conj', '['),
            std_environment('rem', '['),
            std_environment('defn', '['),
        ],
        'specials': [
        ]}),

    #
    # CATEGORY: enumitem
    #
    ('enumitem', {
        'macros': [],
        'environments': [
            std_environment('enumerate', '['),
            std_environment('itemize', '['),
            std_environment('description', '['),
        ],
        'specials': [
        ]}),

    #
    # CATEGORY: natbib
    #
    ('natbib', {
        'macros': [
            # The final mandatory argument of these is a list of citation keys,
            # not latex code.
            MacroSpec('cite', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citet', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citep', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citealt', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citealp', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citeauthor', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citefullauthor', arguments_spec_list=[
                '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citeyear', arguments_spec_list=[
                '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citeyearpar', arguments_spec_list=[
                '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('Citet', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('Citep', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('Citealt', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('Citealp', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('Citeauthor', arguments_spec_list=[
                '*', '[', '[', _arg_charsname('citekey') ]),

            # \citetext{...} is the exception here: its argument is the text to
            # place within the citation delimiters, not a key.
            std_macro('citetext', '{'),
            MacroSpec('citenum', arguments_spec_list=[ _arg_charsname('citekey') ]),

            # \defcitealias{key}{text that replaces the citation}
            MacroSpec('defcitealias', arguments_spec_list=[
                _arg_charsname('citekey'), '{' ]),
            MacroSpec('citetalias', arguments_spec_list=[
                '[', '[', _arg_charsname('citekey') ]),
            MacroSpec('citepalias', arguments_spec_list=[
                '[', '[', _arg_charsname('citekey') ]),
        ],
        'environments': [
        ],
        'specials': [
        ]}),


    #
    # CATEGORY: latex-ethuebung
    #
    ('latex-ethuebung', {
        'macros': [
            # ethuebung
            std_macro('UebungLoesungFont', False, 1),
            std_macro('UebungHinweisFont', False, 1),
            std_macro('UebungExTitleFont', False, 1),
            std_macro('UebungSubExTitleFont', False, 1),
            std_macro('UebungTipsFont', False, 1),
            std_macro('UebungLabel', False, 1),
            std_macro('UebungSubLabel', False, 1),
            std_macro('UebungLabelEnum', False, 1),
            std_macro('UebungLabelEnumSub', False, 1),
            std_macro('UebungSolLabel', False, 1),
            std_macro('UebungHinweisLabel', False, 1),
            std_macro('UebungHinweiseLabel', False, 1),
            std_macro('UebungSolEquationLabel', False, 1),
            std_macro('UebungTipsLabel', False, 1),
            std_macro('UebungTipsEquationLabel', False, 1),
            std_macro('UebungsblattTitleSeries', False, 1),
            std_macro('UebungsblattTitleSolutions', False, 1),
            std_macro('UebungsblattTitleTips', False, 1),
            std_macro('UebungsblattNumber', False, 1),
            std_macro('UebungsblattTitleFont', False, 1),
            std_macro('UebungTitleCenterVSpacing', False, 1),
            std_macro('UebungAttachedSolutionTitleTop', False, 1),
            std_macro('UebungAttachedSolutionTitleFont', False, 1),
            std_macro('UebungAttachedSolutionTitle', False, 1),
            std_macro('UebungTextAttachedSolution', False, 1),
            std_macro('UebungDueByLabel', False, 1),
            std_macro('UebungDueBy', False, 1),
            std_macro('UebungLecture', False, 1),
            std_macro('UebungProf', False, 1),
            std_macro('UebungLecturer', False, 1),
            std_macro('UebungSemester', False, 1),
            std_macro('UebungLogoFile', False, 1),
            std_macro('UebungLanguage', False, 1),
            std_macro('UebungStyle', False, 1),
            #
            std_macro('uebung', '{['),
            std_macro('exercise', '{['),
            std_macro('keywords', False, 1),
            std_macro('subuebung', False, 1),
            std_macro('subexercise', False, 1),
            std_macro('pdfloesung', True, 1),
            std_macro('pdfsolution', True, 1),
            std_macro('exenumfulllabel', False, 1),
            std_macro('hint', False, 1),
            std_macro('hints', False, 1),
            std_macro('hinweis', False, 1),
            std_macro('hinweise', False, 1),
        ],
        'environments': [
        ],
        'specials': [
        ]
    }),
]





