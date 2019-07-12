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


# ------------------------------------------------------------------------------


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


class MacroStandardArgsParser(object):
    r"""
    Parses the arguments to a LaTeX macro.

    This class parses a simple macro argument specification with a specified
    arrangement of optional and mandatory arguments.

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
    def __init__(self, argspec=None, **kwargs):
        super(MacroStandardArgsParser, self).__init__(**kwargs)
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
                    "Unknown macro argument kind for macro: {!r}".format(argt)
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



# ------------------------------------------------------------------------------

class MacroSpec(object):
    r"""
    Stores the specification of a macro.

    This stores the macro name and instructions on how to parse the macro
    arguments.

    .. py:attribute:: macroname

       The name of the macro, without the leading backslash.

    .. py:attribute:: args_parser

       The parser instance that can understand this macro's arguments.  For
       standard LaTeX macros this is usually a
       :py:class:`MacroStandardArgsParser` instance.

       If you specify a string, then for convenience this is interpreted as an
       argspec argument for :py:class:`MacroStandardArgsParser` and such an
       instance is automatically created.
    """
    def __init__(self, macroname, args_parser=MacroStandardArgsParser(), **kwargs):
        super(MacroSpec, self).__init__(**kwargs)
        self.macroname = macroname
        if isinstance(args_parser, _basestring):
            self.args_parser = MacroStandardArgsParser(args_parser)
        else:
            self.args_parser = args_parser

    def parse_args(self, *args, **kwargs):
        r"""
        Shorthand for calling the :py:attr:`args_parser`\ 's `parse_args()` method.
        See :py:class:`MacroStandardArgsParser`.
        """
        return self.args_parser.parse_args(*args, **kwargs)




class EnvironmentSpec(object):
    r"""
    Stores the specification of a LaTeX environment.

    This stores the environment name and instructions on how to parse any
    arguments provided after ``\begin{environment}<args>``.

    .. py:attribute:: environmentname

       The name of the environment, i.e., the argument of ``\begin{...}`` and
       ``\end{...}``.

    .. py:attribute:: args_parser

       The parser instance that can understand this environment's arguments.
       For standard LaTeX environment this is usually a
       :py:class:`MacroStandardArgsParser` instance.

    .. py:attribute:: is_math_mode

       A boolean that indicates whether or not the contents is to be interpreted
       in Math Mode.  This would be True for environments like
       ``\begin{equation}``, ``\begin{align}``, etc., but False for
       ``\begin{figure}``, etc.

    .. note::

       Starred variants of environments (as in ``\begin{equation*}``) must not
       be specified using an argspec as for macros (e.g., `argspec='*'`).
       Rather, we need to define a separate environment spec for the starred
       variant with the star in the name itself (``EnvironmentSpec('equation*',
       None)``) because the star really is part of the environment name.  If you
       happened to use ``EnvironmentSpec('equation', '*')``, then the parser
       would recognize the expression ``\begin{equation}*`` but not
       ``\begin{equation*}``.
    """
    def __init__(self, environmentname, args_parser=MacroStandardArgsParser(),
                 is_math_mode=False, **kwargs):
        super(EnvironmentSpec, self).__init__(**kwargs)
        self.environmentname = environmentname
        self.args_parser = args_parser
        self.is_math_mode = is_math_mode

    def parse_args(self, *args, **kwargs):
        r"""
        Shorthand for calling the :py:attr:`args_parser`\ 's `parse_args()` method.
        See :py:class:`MacroStandardArgsParser`.
        """
        return self.args_parser.parse_args(*args, **kwargs)





# ------------------------------------------------------------------------------


def std_macro(macname, *args, **kwargs):
    r"""
    Return a macro specification for the given macro.  Syntax::

      spec = std_macro(macname, argspec)
      #  or
      spec = std_macro(macname, optarg, numargs)
      #  or
      spec = std_macro( (macname, argspec), )
      #  or
      spec = std_macro( (macname, optarg, numargs), )
      #  or
      spec = std_macro( spec ) # spec is already a `MacroSpec` -- no-op

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
    
    To make environment specifications (:py:class:`EnvironmentSpec`) instead of
    a macro specification, use the function :py:func:`std_environment()`
    instead.

    The helper function :py:func:`std_environment()` is a shorthand for calling
    this function with additional keyword arguments.  An optional keyword
    argument `make_environment_spec=True` to the present function may be
    specified to return an `EnvironmentSpec` instead of a `MacroSpec`.  In this
    case, you can further specify the `environment_is_math_mode=True|False` to
    specify whether of not the environment represents a math mode.
    """

    if isinstance(macname, tuple):
        if len(args) != 0:
            raise TypeError("No positional arguments expected if first argument is a tuple")
        args = macname

    if isinstance(macname, MacroSpec):
        if len(args) != 0:
            raise TypeError("No positional arguments expected if first argument is a MacroSpec")
        return macname
    
    if isinstance(macname, EnvironmentSpec):
        if len(args) != 0:
            raise TypeError("No positional arguments expected if first argument is a EnvironmentSpec")
        return macname

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

    if kwargs.get('make_environment_spec', False):
        return EnvironmentSpec(macname, args_parser=MacroStandardArgsParser(argspec),
                               is_math_mode=kwargs.get('environment_is_math_mode', False))
    return MacroSpec(macname, args_parser=MacroStandardArgsParser(argspec))


def std_environment(envname, *args, **kwargs):
    r"""
    Return an environment specification for the given environment.  Syntax::

      spec = std_environment(envname, argspec, is_math_mode=True|False)
      #  or
      spec = std_environment(envname, optarg, numargs, is_math_mode=True|False)
      #  or
      spec = std_environment( (envname, argspec), is_math_mode=True|False)
      #  or
      spec = std_environment( (envname, optarg, numargs), is_math_mode=True|False)
      #  or
      spec = std_environment( spec ) # spec is already a `EnvironmentSpec` -- no-op

    - `envname` is the name of the environment, i.e., the argument to
      ``\begin{...}``.

    - `argspec` is a string either characters "*", "{" or "[", in which star
      indicates an optional asterisk character (e.g. starred environment variants),
      each curly brace specifies a mandatory argument and each square bracket
      specifies an optional argument in square brackets.  For example, "{{*[{"
      expects two mandatory arguments, then an optional star, an optional
      argument in square brackets, and then another mandatory argument.

      `argspec` may also be `None`, which is the same as ``argspec=''``.

    .. note::

       See :py:class:`EnvironmentSpec` for an important remark about starred
       variants for environments.  TL;DR: a starred verison of an environment is
       defined as a separate `EnvironmentSpec` with the star in the name and
       *not* using an ``argspec='*'``.

    - `optarg` may be one of `True`, `False`, or `None`, corresponding to these
      possibilities:

      + if `True`, the environment expects as first argument an optional argument in
        square brackets. Then, `numargs` specifies the number of additional
        mandatory arguments to the command, given in usual curly braces (or
        simply as one TeX token like a single environment)

      + if `False`, the environment only expects a number of mandatory arguments given
        by `numargs`. The mandatory arguments are given in usual curly braces
        (or simply as one TeX token like a single environment)

      + if `None`, then `numargs` is a string like `argspec` above.  I.e.,
        ``std_environment(envname, None, argspec)`` is the same as
        ``std_environment(envname, argspec)``.

    - `numargs`: depends on `optarg`, see above.

    - `is_math_mode`: if set to True, then the environment represents a math
      mode environment (e.g., 'equation', 'align', 'gather', etc.), i.e., whose
      contents should be parsed in an appropriate math mode.  Note that
      `is_math_mode` *must* be given as a keyword argument, in contrast to all
      other arguments which must be positional (non-keyword) arguments.
    """
    is_math_mode = kwargs.pop('is_math_mode', False)
    kwargs2 = dict(kwargs)
    kwargs2.update(make_environment_spec=True,
                   environment_is_math_mode=is_math_mode)
    return std_macro(envname, *args, **kwargs2)




# ------------------------------------------------------------------------------




class LatexContextDb(object):
    r"""
    Store a database of macro specifications (stored as :py:class:`MacroSpec`
    objects), environment specifications (stored as :py:class:`EnvironSpec`, a
    subclass of :py:class:`MacroSpec`), each organized in different categories.
    
    TODO: In the future, this class will also store special/active/ligature
    chars, etc.

    See :py:func:`default_latex_context()` for the default latex context with a
    default collection of known latex macros and environments.
    """
    def __init__(self, **kwargs):
        super(LatexContextDb, self).__init__(**kwargs)

        self.category_list = []
        self.d = {}

        self.unknown_macro_spec = MacroSpec('')
        self.unknown_environment_spec = EnvironmentSpec('')
        
    def add_context_category(self, category, macros, environments, prepend=False):
        r"""
        Register a category of macro and environment specifications in the context
        database.

        The category name `category` must not already exist in the database.

        The argument `macros` is an iterable (e.g., a list) of
        :py:class:`MacroSpec` objects.  The argument `environments` is an
        iterable (e.g., a list) of :py:class:`EnvironmentSpec` objects.

        If you specify `prepend=True`, then macro and environment lookups will
        prioritize this category over other categories.  Categories are normally
        searched for in the order they are registered to the database; if you
        specify `prepend=True`, then the new category is prepended to the
        existing list so that it is searched first.
        """
        
        if category in self.category_list:
            raise ValueError("Category {} is already registered in the context database"
                             .format(category))

        if prepend:
            self.category_list.prepend(category)
        else:
            self.category_list.append(category)

        self.d[category] = {
            'macros': dict( (m.macroname, m) for m in macros ),
            'environments': dict( (e.environmentname, e) for e in environments),
        }

    def set_unknown_macro_spec(self, macrospec):
        r"""
        Set the macro spec (a `MacroSpec` instance) to use when encountering a macro
        that is not in the database.
        """
        self.unknown_macro_spec = macrospec

    def set_unknown_environment_spec(self, environmentspec):
        r"""
        Set the environment spec (a `EnvironmentSpec` instance) to use when
        encountering a LaTeX environment that is not in the database.
        """
        self.unknown_environment_spec = environmentspec

    def categories(self):
        r"""
        Return a list of valid category names that are registered in the current
        database context.
        """
        return self.category_list

    def get_macro_spec(self, macroname):
        r"""
        Look up a macro specification by macro name.  The macro name is searched for
        in all categories one by one and the first match is returned.

        Returns a :py:class:`MacroSpec` instance.  If the macro name was not
        found, we return a default macro specification or the one set by
        :py:meth:`set_unknown_macro_spec()`.
        """
        for cat in self.category_list:
            # search categories in the given order
            if macroname in self.d[cat]['macros']:
                return self.d[cat]['macros'][macroname]
        return self.unknown_macro_spec
    
    def get_environment_spec(self, environmentname):
        r"""
        Look up an environment specification by environment name.  The environment
        name is searched for in all categories one by one and the first match is
        returned.

        Returns a :py:class:`EnvironmentSpec` instance.  If the environment name
        was not found, we return a default environment specification or the one
        set by :py:meth:`set_unknown_environment_spec()`.
        """
        for cat in self.category_list:
            # search categories in the given order
            if environmentname in self.d[cat]['environments']:
                return self.d[cat]['environments'][environmentname]
        return self.unknown_environment_spec

    def iter_macro_specs(self, categories=None):
        r"""
        Yield the macro specs corresponding to all macros in the given categories.

        If `categories` is `None`, then the known macro specs from all
        categories are provided in one long iterable sequence.  Otherwise,
        `categories` should be a list or iterable of category names (e.g.,
        'latex-base') of macro specs to return.

        The macro specs from the different categories specified are concatenated
        into one long sequence which is yielded spec by spec.
        """

        if categories is None:
            categories = self.category_list

        for c in categories:
            if c not in self.category_list:
                raise ValueError("Invalid latex macro spec db category: {!r} (Expected one of {!r})"
                                 .format(c, self.category_list))
            for spec in self.d[c]['macros'].values():
                yield spec

    def iter_environment_specs(self, categories=None):
        r"""
        Yield the environment specs corresponding to all environments in the given
        categories.

        If `categories` is `None`, then the known environment specs from all
        categories are provided in one long iterable sequence.  Otherwise,
        `categories` should be a list or iterable of category names (e.g.,
        'latex-base') of environment specs to return.

        The environment specs from the different categories specified are
        concatenated into one long sequence which is yielded spec by spec.
        """

        if categories is None:
            categories = self.category_list

        for c in categories:
            if c not in self.category_list:
                raise ValueError("Invalid latex environment spec db category: {!r} (Expected one of {!r})"
                                 .format(c, self.category_list))
            for spec in self.d[c]['environments'].values():
                yield spec


    def filter_context(self, keep_categories=[], exclude_categories=[],
                       keep_which=[]):
        r"""
        Return a new :py:class:`LatexContextDb` instance where we only keep
        certain categories of macro and environment specifications.
        
        If `keep_categories` is set to a nonempty list, then the returned
        context will not contain any definitions that do not correspond to the
        specified categories.

        If `exclude_categories` is set to a nonempty list, then the returned
        context will not contain any definitions that correspond to the
        specified categories.

        The argument `keep_which`, if non-empty, specifies which definitions to
        keep.  It should be a subset of the list ['macros', 'environments'].
        
        The returned context will make a copy of the dictionaries that store the
        macro and environment specifications, but the specification classes (and
        corresponding argument parsers) might correspond to the same instances.
        I.e., the returned context is not a full deep copy.
        """
        
        new_context = LatexContextDb()

        new_context.unknown_macro_spec = self.unknown_macro_spec
        new_context.unknown_environment_spec = self.unknown_environment_spec

        keep_macros = not keep_which or 'macros' in keep_which
        keep_environments = not keep_which or 'environments' in keep_which

        for cat in self.category_list:
            if keep_categories and cat not in keep_categories:
                continue
            if exclude_categories and cat in exclude_categories:
                continue

            # include this category
            new_context.add_context_category(
                cat,
                self.d[cat]['macros'].values() if keep_macros else [],
                self.d[cat]['environments'].values() if keep_environments else [],
            )

        return new_context




def get_default_latex_context_db():
    db = LatexContextDb()
    
    from ._macrospec_defaults import specs

    for cat, catspecs in specs:
        db.add_context_category(cat, catspecs['macros'], catspecs['environments'])
    
    return db
    


legacy_default_macro_dict = dict([
    (m.macroname, m)
    for m in get_default_latex_context_db().iter_macro_specs()
])
