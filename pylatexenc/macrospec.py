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


# Internal module. May change without notice.  See
# `latexwalker.get_default_defs()` for access to stuff here.

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

      - `legacy_nodeoptarg_nodeargs` is a tuple `(nodeoptarg, nodeargs)` that
        should be exposed as properties in
        :py:class:`~latexwalker.LatexMacroNode` to provide (as best as possible)
        compatibility with pylatexenc < 2.

        This is to be used in cases where the macro arguments structure is
        relatively standard.  The first tuple item `nodeoptarg` should be a
        possible first optional value, or `None` and the second item `nodeargs`
        is a list of nodes that represents subsequent arguments (optional or
        mandatory).
    """
    def __init__(self, argnlist=[], legacy_nodeoptarg_nodeargs=None,
                 **kwargs):
        super(ParsedMacroArgs, self).__init__(**kwargs)
        
        self.argnlist = argnlist
        self.legacy_nodeoptarg_nodeargs = legacy_nodeoptarg_nodeargs
        
    def to_json_object(self):
        r"""
        Return a representation of the current parsed arguments in an object that
        our main JSON exporter (:py:class:`latexwalker.LatexNodesJSONEncoder`)
        can understand and export to JSON.

        Called when we export the node structure to JSON (e.g., latexwalker in
        command-line).
        """
        legacystuff = {}
        if self.legacy_nodeoptarg_nodeargs:
            legacystuff['nodeoptarg'] = self.legacy_nodeoptarg_nodeargs[0]
            legacystuff['nodeargs'] = self.legacy_nodeoptarg_nodeargs[1]

        return dict(
            argnlist=self.argnlist,
            # stuff for compatibility with pylatexenc < 2
            **legacystuff
        )

    def __repr__(self):
        return "ParsedMacroArgs(argnlist={!r})".format(self.argnlist)



class MacroSpec(object):
    r"""
    Parses the arguments to a LaTeX macro.

    This base class parses a simple macro argument specification with a
    specified arrangement of optional and mandatory arguments.

    Arguments:

      - `macroname`: the name of the macro, without the leading backslash.

      - `argspec`: must be a string in which each character corresponds to an
        argument.  The character '{' represents a mandatory argument (single
        token or LaTeX group) and the character '[' denotes an optional argument
        delimited by braces.  The character '*' denotes a possible star char at
        that position in the argument list, a corresponding
        ``latexwalker.LatexCharsNode('*')`` (or `None` if no star) will be
        inserted in the argument node list.  For instance, the string '*{[{'
        would be suitable to specify the signature of the '\newcommand' macro.

        Currently, the argspec string may only contain the characters '*', '{'
        and '['.

        The `argspec` may also be `None`, which is the same as specifying an
        empty string.

      - additional unrecognized keyword arguments are passed on to superclasses
        in case of multiple inheritance
    """
    def __init__(self, macroname, argspec=None, **kwargs):
        super(MacroSpec, self).__init__(**kwargs)
        self.macroname = macroname
        self.argspec = argspec if argspec else ''
        # catch bugs, make sure that argspec is a string with only accepted chars
        if not isinstance(self.argspec, _basestring) or \
           not all(x in '*[{' for x in self.argspec):
            raise TypeError(
                "argspec must be a string containing chars '*', '[', '{{' only: {!r}"
                .format(self.argspec)
            )

    def parse_args(self, w, pos):
        r"""
        Parse the arguments encountered at position `pos` in the LatexWalker
        instance `w`.

        The argument `w` is the `latexwalker.LatexWalker` object that is
        currently parsing LaTeX code.  You can call methods like
        `w.get_goken()`, `w.get_latex_expression()` etc., to parse and read
        arguments.

        This function should return a tuple `(argd, pos, len)` where:

        - `argd` is a :py:class:`ParsedMacroArgs` instance (or a subclass
          instance).

        - `pos` is the position of the first parsed content.  It should be the
          same as the `pos` argument, except if there is whitespace at that
          position in which case the returned `pos` would have to be the
          position where the argument contents start.

        - `len` is the length of the parsed expression.  You will probably want
          to continue parsing stuff at the index `pos+len` in the string.
        """

        from . import latexwalker

        argnlist = []

        p = pos

        for argt in self.argspec:
            if argt == '{':
                (node, np, nl) = w.get_latex_expression(p, strict_braces=False)
                p = np + nl
                argnlist.append(node)

            elif argt == '[':
                optarginfotuple = w.get_latex_maybe_optional_arg(p)
                if optarginfotuple is None:
                    argnlist.append(None)
                    continue
                (node, np, nl) = optarginfotuple
                p = np + nl
                argnlist.append(node)

            elif argt == '*':
                # possible star.
                tok = w.get_token(p)
                if tok.tok == 'char' and tok.arg.lstrip().startswith('*'):
                    # has star
                    argnlist.append(latexwalker.LatexCharsNode('*'))
                    p = tok.pos + 1
                else:
                    argnlist.append(None)

            else:
                raise LatexWalkerError(
                    "Unknown macro argument kind for macro {}: {!r}".format(
                        self.macroname,
                        argt
                    )
                )

        # for LatexMacroNode to provide some kind of compatibility with pylatexenc < 2
        (legacy_nodeoptarg, legacy_nodeargs) = (None, argnlist)
        if self.argspec[0:1] == '[' and all(x == '{' for x in self.argspec[1:]):
            legacy_nodeoptarg = argnlist[0]
            legacy_nodeargs = argnlist[1:]

        parsed = ParsedMacroArgs(
            argnlist,
            legacy_nodeoptarg_nodeargs=(legacy_nodeoptarg, legacy_nodeargs),
        )

        return (parsed, pos, p-pos)


def std_macro(macname, *args):
    r"""
    Return a parser for the given macro.  Syntax::

      spec = std_macro(macname, argspec)
      #  or
      spec = std_macro(macname, optarg, numargs)
      #  or
      spec = std_macro( (macname, argspec), )
      #  or
      spec = std_macro( (macname, optarg, numargs), )

    - `macname` is the name of the macro, without the leading backslash.

    - `argspec` is a string either characters "*", "{" or "[", in which star
      indicates an optional asterisk character (e.g. starred macro variants),
      each curly brace specifies a mandatory argument and each square bracket
      specifies an optional argument in square brackets.  For example, "{{*[{"
      expects two mandatory arguments, then an optional star, an optional
      argument in square brackets, and then another mandatory argument.

      `argspec` may also be `None`, which is the same as ``argspec=''``.

    - `optarg` may be one of `True`, `False`, or `None`, corresponding to these
      possibilities:

      + if `True`, the macro expects as first argument an optional argument in
        square brackets. Then, `numargs` specifies the number of additional
        mandatory arguments to the command, given in usual curly braces (or
        simply as one TeX token like a single macro)

      + if `False`, the macro only expects a number of mandatory arguments given
        by `numargs`. The mandatory arguments are given in usual curly braces
        (or simply as one TeX token like a single macro)

      + if `None`, then `numargs` is a string like `argspec` above.  I.e.,
        ``std_macro(macname, None, argspec)`` is the same as
        ``std_macro(macname, argspec)``.

    - `numargs`: depends on `optarg`, see above.
    """

    if isinstance(macname, tuple):
        if len(args) != 0:
            raise TypeError("No positional arguments expected if first argument is a tuple")
        args = macname
    
    if len(args) == 1:
        # std_macro(macname, argspec)
        argspec = args[0]
    elif len(args) != 2:
        raise TypeError(
            "Wrong number of arguments for std_macro, macname={!r}, args={!r}".format(
                macname, args
            ))
    elif not args[0] and isinstance(args[1], _basestring):
        # argspec given in numargs
        argspec = args[1]
    else:
        argspec = ''
        if args[0]:
            argspec = '['
        argspec += '{'*args[1]

    return MacroSpec(macname, argspec)




class MacroSpecDb(object):
    r"""
    Store a list of macro specifications (stored as :py:class:`MacroSpec`
    objects), organized by categories.

    This class is used to store the default list of known latex macros and
    environments.
    """
    def __init__(self, d, **kwargs):
        super(MacroSpecDb, self).__init__(**kwargs)
        self._d = d

    def categories(self):
        r"""
        Return a list of valid category names that can be used as arguments to,
        e.g., :py:meth:`specs()`.
        """
        return list(self._d.keys())
    
    def specs(self, cat=None):
        r"""
        Return the macro specs corresponding to all macros in the given categories.

        If `cat` is `None`, then the known macro specs from *all* categories are
        returned in one long list.  Otherwise, `cat` should be a list of
        category names (e.g., 'latex-base') of macro specs to return.

        The macro specs from the different categories specified are concatenated
        into one long list which is returned.
        """
        return list(self.iter_specs(cat))

    def iter_specs(self, cat=None):
        r"""
        Yield the macro specs corresponding to all macros in the given categories.

        If `cat` is `None`, then the known macro specs from *all* categories are
        provided in one long iterable sequence.  Otherwise, `cat` should be a
        list of category names (e.g., 'latex-base') of macro specs to return.

        The macro specs from the different categories specified are concatenated
        into one long sequence which is yielded spec by spec.
        """

        if cat is None:
            cat = self._d.keys()

        for c in cat:
            if c not in self._d:
                raise ValueError("Invalid latex macro spec db category: {!r} (Expected one of {!r})"
                                 .format(c, list(self._d.keys())))
            for spec in self._d[c]:
                yield spec
    

macro_spec_db = MacroSpecDb({
    'latex-base': [
        std_macro('documentclass', True, 1),
        std_macro('usepackage', True, 1),
        std_macro('selectlanguage', True, 1),
        std_macro('setlength', True, 2),
        std_macro('addlength', True, 2),
        std_macro('setcounter', True, 2),
        std_macro('addcounter', True, 2),
        std_macro('newcommand', "*{[{"),
        std_macro('renewcommand', "*{[{"),
        std_macro('providecommand', "*{[{"),
        std_macro('newenvironment', "*{[{{"),
        std_macro('renewenvironment', "*{[{{"),
        std_macro('provideenvironment', "*{[{{"),

        std_macro('DeclareMathOperator', '*{{'),

        std_macro('hspace', False, 1),
        std_macro('vspace', False, 1),

        # (Note: single backslash) end of line with optional no-break ('*') and
        # additional vertical spacing, e.g. \\*[2mm]
        std_macro('\\', '*['),

        std_macro('item', True, 0),

        # \input{someotherfile}
        std_macro('input', False, 1),
        std_macro('include', False, 1),

        std_macro('includegraphics', True, 1),

        std_macro('chapter', '*[{'),
        std_macro('section', '*[{'),
        std_macro('subsection', '*[{'),
        std_macro('subsubsection', '*[{'),
        std_macro('pagagraph', '*[{'),
        std_macro('subparagraph', '*[{'),


        std_macro('emph', False, 1),
        std_macro('textit', False, 1),
        std_macro('textbf', False, 1),
        std_macro('textsc', False, 1),
        std_macro('textsl', False, 1),
        std_macro('text', False, 1),
        std_macro('mathrm', False, 1),

        std_macro('label', False, 1),
        std_macro('ref', False, 1),
        std_macro('eqref', False, 1),
        std_macro('url', False, 1),
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

        std_macro('sqrt', True, 1),

        std_macro('ket', False, 1),
        std_macro('bra', False, 1),
        std_macro('braket', False, 2),
        std_macro('ketbra', False, 2),

        std_macro('texorpdfstring', False, 2),
    ],

    'latex-ethuebung': [
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
    ]
})


environment_spec_db = MacroSpecDb({
    'latex-base': [
        std_macro('figure', '['),
        std_macro('table', '['),

        std_macro('abstract', None),

        std_macro('tabular', '{'),

        std_macro('array', '[{'),
        std_macro('alignat', '{'),
        
    ],
    'enumitem': [
        std_macro('enumerate', '['),
        std_macro('itemize', '['),
        std_macro('description', '['),
    ]
})
