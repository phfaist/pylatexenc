# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2018 Philippe Faist
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

r"""
A simplistic, heuristic LaTeX code parser allowing to returns a text-only
approximation.  Suitable, e.g. for indexing tex code in a database for full text
searching.

The main class is :py:class:`LatexNodes2Text`.  For a quick start, try::

    from pylatexenc.latex2text import LatexNodes2Text
    
    latex = "... LaTeX code ..."
    text = LatexNodes2Text(strict_latex_spaces='macros').latex_to_text(latex)

You may also use the command-line version of `latex2text`::

    $ echo '\textit{italic} \`acc\^ented text' | latex2text
    italic àccênted text

"""

from __future__ import print_function #, absolute_import

import os
import logging
import sys
import inspect

if sys.version_info.major >= 3:
    def unicode(string): return string
    basestring = str
    getfullargspec = inspect.getfullargspec
else:
    getfullargspec = inspect.getargspec

import pylatexenc
from . import latexwalker
from . import macrospec
from . import _util

logger = logging.getLogger(__name__)



class MacroTextSpec(object):
    """
    A specification of how to obtain a textual representation of a macro.

    .. py:attribute:: macroname

       The name of the macro (no backslash)

    .. py:attribute:: simplify_repl

       This is Either a string or a callable. The string may contain '%s'
       replacements, in which the macro arguments will be substituted. The
       callable should accept the corresponding
       :py:class:`pylatexenc.latexwalker.LatexMacroNode` as an argument.  If the
       callable expects a second argument named `l2tobj`, then the
       `LatexNodes2Text` object is provided to that argument.

    .. py:attribute:: discard
    
       If set to `True`, then the macro call is discarded, i.e., it is converted
       to an empty string.


    .. versionadded:: 2.0

       The class :py:class:`MacroTextSpec` was introduced in `pylatexenc
       2.0` to succeed to the previously named `MacroDef` class.
    """
    def __init__(self, macroname, simplify_repl=None, discard=None):
        super(MacroTextSpec, self).__init__()
        self.macroname = macroname
        self.discard = True if (discard is None) else discard
        self.simplify_repl = simplify_repl


class EnvironmentTextSpec(object):
    """
    A specification of how to obtain a textual representation of an environment.

    .. py:attribute:: environmentname

       The name of the environment

    .. py:attribute:: simplify_repl

       The replacement text of the environment.  This is either a callable or a
       string.  If it is a callable, it must accept a single argument, the
       :py:class:`pylatexenc.latexwalker.LatexEnvironmentNode` representing the
       LaTeX environment.  If the callable expects a second argument named
       `l2tobj`, then the `LatexNodes2Text` object is provided to that argument.
       If it is a string, it may contain '%s' which will be replaced by the
       environment contents converted to text.

    .. py:attribute:: discard
    
       If set to `True`, then the full environment is discarded, i.e., it is
       converted to an empty string.


    .. versionadded:: 2.0

       The class :py:class:`EnvironmentTextSpec` was introduced in `pylatexenc
       2.0` to succeed to the previously named `EnvDef` class.
    """
    def __init__(self, environmentname, simplify_repl=None, discard=False):
        super(EnvironmentTextSpec, self).__init__()
        self.environmentname = environmentname
        self.simplify_repl = simplify_repl
        self.discard = discard


class SpecialsTextSpec(object):
    """
    A specification of how to obtain a textual representation of latex specials.

    .. py:attribute:: specials_chars
    
       The sequence of special LaTeX characters

    .. py:attribute:: simplify_repl

       The replacement text of the specials.  This is either a callable or a
       string.  If it is a callable, it must accept a single argument, the
       :py:class:`pylatexenc.latexwalker.LatexSpecialsNode` representing the
       LaTeX environment.  If the callable expects a second argument named
       `l2tobj`, then the `LatexNodes2Text` object is provided to that argument.
       If it is a string, it may contain '%s' replacements, in which the macro
       arguments will be substituted.


    .. versionadded:: 2.0

       Latex specials were introduced in `pylatexenc 2.0`.
    """
    def __init__(self, specials_chars, simplify_repl=None):
        super(SpecialsTextSpec, self).__init__()
        self.specials_chars = specials_chars
        self.simplify_repl = simplify_repl



def EnvDef(envname, simplify_repl=None, discard=False):
    r"""
    .. deprecated:: 2.0

       Instantiate a :py:class:`EnvironmentTextSpec` instead.

       Since `pylatexenc 2.0`, `EnvDef` is a function which returns a
       :py:class:`~pylatexenc.macrospec.EnvironmentTextSpec` instance.  In this
       way the earlier idiom ``EnvDef(...)`` still works in `pylatexenc 2`.
    """
    return EnvironmentTextSpec(environmentname=envname, simplify_repl=simplify_repl,
                               discard=discard)

def MacroDef(macname, simplify_repl=None, discard=None):
    r"""
    .. deprecated:: 2.0

       Instantiate a :py:class:`MacroTextSpec` instead.

       Since `pylatexenc 2.0`, `MacroDef` is a function which returns a
       :py:class:`~pylatexenc.macrospec.MacroTextSpec` instance.  In this way
       the earlier idiom ``MacroDef(...)`` still works in `pylatexenc 2`.
    """
    return MacroTextSpec(macroname=macname, simplify_repl=simplify_repl, discard=discard)




def fmt_equation_environment(envnode, l2tobj):
    r"""
    Can be used as callback for display equation environments.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """

    with _PushEquationContext(l2tobj):

        contents = l2tobj.nodelist_to_text(envnode.nodelist).strip()
        # indent equation, separate by newlines
        indent = ' '*4
        return ("\n"+indent + contents.replace("\n", "\n"+indent) + "\n")


def fmt_input_macro(macronode, l2tobj):
    r"""
    This function can be used as callback in :py:class:`MacroTextSpec` for
    ``\input`` or ``\include`` macros.  The `macronode` must be a macro node
    with a single argument.  If :py:meth:`set_tex_input_directory()` was called
    with a nonempty input directory in the :py:class:`LatexNodes2Text` object,
    then this method reads the contents of the file name in the macro argument
    according to the provided settings.  Otherwise, returns an empty string.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """
    return l2tobj._input_node_simplify_repl(macronode)


def placeholder_node_formatter(placeholdertext):
    r"""
    This function returns a callable that can be used in
    :py:class:`MacroTextSpec`, :py:class:`EnvironmentTextSpec`, or
    :py:class:`SpecialsTextSpec` for latex nodes that do not have a good textual
    representation, providing as text replacement the simple placeholder text
    ``'< P L A C E H O L D E R   T E X T >'``.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """
    return lambda pht=placeholdertext: '< ' + " ".join(pht) + ' >'
    
def fmt_placeholder_node(node):
    r"""
    This function can be used as callable in :py:class:`MacroTextSpec`,
    :py:class:`EnvironmentTextSpec`, or :py:class:`SpecialsTextSpec` for latex
    nodes that do not have a good textual representation.  The text replacement
    is the placeholder text
    ``'< N A M E   O F   T H E   M A C R O   O R   E N V I R O N M E N T >'``.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """
    # spaces added so that database indexing doesn't index the word "array" or
    # "pmatrix"
    name = getattr(node, 'macroname',
                   getattr(node, 'environmentname'),
                   getattr(node, 'specials_chars', '<unknown>'))
    return placeholder_node_formatter(name)



def get_default_latex_context_db():
    r"""
    Return a :py:class:`pylatexenc.macrospec.LatexContextDb` instance
    initialized with a collection of text replacements for known macros and
    environments.

    TODO: document categories.

    If you want to add your own definitions, you should use the
    :py:meth:`pylatexenc.macrospec.LatexContextDb.add_context_category()`
    method.  If you would like to override some definitions, use that method
    with the argument `prepend=True`.  See docs for
    :py:meth:`pylatexenc.macrospec.LatexContextDb.add_context_category()`.

    If there are too many macro/environment definitions, or if there are some
    irrelevant ones, you can always filter the returned database using
    :py:meth:`pylatexenc.macrospec.LatexContextDb.filter_context()`.

    .. versionadded:: 2.0
 
       The :py:class:`pylatexenc.macrospec.LatexContextDb` class as well as this
       method, were all introduced in `pylatexenc 2.0`.
    """
    db = macrospec.LatexContextDb()
    
    from ._latex2text_defaultspecs import specs

    for cat, catspecs in specs:
        db.add_context_category(cat,
                                macros=catspecs['macros'],
                                environments=catspecs['environments'],
                                specials=catspecs['specials'])
    
    return db
    



default_macro_dict = _util.LazyDict(
    generate_dict_fn=lambda: dict([
        (m.macroname, m)
        for m in get_default_latex_context_db().iter_macro_specs()
    ])
)
r"""
.. deprecated:: 2.0

   Use :py:func:`get_default_latex_context_db()` instead, or create your own
   :py:class:`pylatexenc.macrospec.LatexContextDb` object.


Provide an access to the default macro text replacement specs for `latex2text`
in a form that is compatible with `pylatexenc 1.x`\ 's `default_macro_dict`
module-level dictionary.

This is implemented using a custom lazy mutable mapping, which behaves just like
a regular dictionary but that loads the data only once the dictionary is
accessed.  In this way the default latex specs into a python dictionary unless
they are actually queried or modified, and thus users of `pylatexenc 2.0` that
don't rely on the default macro/environment definitions shouldn't notice any
decrease in performance.
"""

default_env_dict = _util.LazyDict(
    generate_dict_fn=lambda: dict([
        (m.environmentname, m)
        for m in get_default_latex_context_db().iter_environment_specs()
    ])
)
r"""
.. deprecated:: 2.0

   Use :py:func:`get_default_latex_context_db()` instead, or create your own
   :py:class:`pylatexenc.macrospec.LatexContextDb` object.


Provide an access to the default environment text replacement specs for
`latex2text` in a form that is compatible with `pylatexenc 1.x`\ 's
`default_macro_dict` module-level dictionary.

This is implemented using a custom lazy mutable mapping, which behaves just like
a regular dictionary but that loads the data only once the dictionary is
accessed.  In this way the default latex specs into a python dictionary unless
they are actually queried or modified, and thus users of `pylatexenc 2.0` that
don't rely on the default macro/environment definitions shouldn't notice any
decrease in performance.
"""


default_text_replacements = ( )
r"""
.. deprecated:: 2.0

   Text replacements are deprecated since `pylatexenc 2.0` with the advent of
   "latex specials".
"""


# ------------------------------------------------------------------------------

_strict_latex_spaces_predef = {
    'default': {
        'between-macro-and-chars': False,
        'between-latex-constructs': False,
        'after-comment': False,
        'in-equations': None,
    },
    'macros': {
        'between-macro-and-chars': True,
        'between-latex-constructs': True,
        'after-comment': False,
        'in-equations': False,
    },
    'except-in-equations': {
        'between-macro-and-chars': True,
        'between-latex-constructs': True,
        'after-comment': True,
        'in-equations': False,
    },
}

def _parse_strict_latex_spaces_dict(strict_latex_spaces):
    d = {
        'between-macro-and-chars': False,
        'between-latex-constructs': False,
        'after-comment': False,
        'in-equations': None,
    }
    if strict_latex_spaces is None:
        return d
    elif isinstance(strict_latex_spaces, dict):
        d.update(strict_latex_spaces)
        return d
    elif isinstance(strict_latex_spaces, basestring):
        if strict_latex_spaces == 'on':
            return _parse_strict_latex_spaces_dict(True)
        if strict_latex_spaces == 'off':
            return _parse_strict_latex_spaces_dict(False)
        if strict_latex_spaces not in _strict_latex_spaces_predef:
            raise ValueError("invalid value for strict_latex_spaces preset: {}"
                             .format(strict_latex_spaces))
        return _strict_latex_spaces_predef[strict_latex_spaces]
    else:
        for k in d.keys():
            d[k] = bool(strict_latex_spaces)
        return d


class LatexNodes2Text(object):
    """
    Simplistic Latex-To-Text Converter.

    This class parses a nodes structure generated by the :py:mod:`latexwalker` module,
    and creates a text representation of the structure.

    It is capable of parsing ``\\input`` directives safely, see
    :py:meth:`set_tex_input_directory()` and :py:meth:`read_input_file()`.  By default,
    ``\\input`` and ``\\include`` directives are ignored.

    Arguments to the constructor:

    - `latex_context_db` is a :py:class:`pylatexenc.macrospec.LatexContextDb`
      class storing a collection of rules for converting macros, environments,
      and other latex specials to text.  The `LatexContextDb` should contain
      specifications via :py:class:`MacroTextSpec`,
      :py:class:`EnvironmentTextSpec`, and :py:class:`SpecialsTextSpec` objects.

      The default latex context database can be obtained using
      :py:func:`get_default_latex_context_db()`.

    Additional keyword arguments are flags which may influence the behavior:

    - `math_mode='text'|'with-delimiters'|'verbatim'`: Specify how to treat
      chunks of LaTeX code that correspond to math modes.  If 'text' (the
      default), then the math mode contents is incorporated as normal text.  If
      'with-delimiters', the content is incorporated as normal text but it is
      still included in the original math-mode delimiters, such as '$...$'.  If
      'verbatim', then the math mode chunk is kept verbatim, including the
      delimiters.

    - `keep_comments=True|False`: If set to `True`, then LaTeX comments are kept
      (including the percent-sign); otherwise they are discarded.  (By default
      this is `False`)

    - `strict_latex_spaces=True|False`: If set to `True`, then we follow closely
      LaTeX's handling of whitespace.  For instance, whitespace following a bare
      macro (i.e. w/o any delimiting characters like '{') is consumed/removed.
      If set to `False` (the default), then some liberties are taken with
      respect to whitespace [hopefully making the result slightly more
      aesthetic, but this behavior is mostly there for historical reasons].

      You may also use one of the presets
      `strict_latex_spaces='default'|'macros'|'except-in-equations'`, which
      allow for finer control of how whitespace is handled. The 'default' is the
      same as `False`. Using 'macros' will make macros and other sequences
      of LaTeX constructions obey LaTeX space rules, but will keep indentations
      after comments and more liberal whitespace rules in equations. The
      'except-in-equations' preset goes as you'd expect, setting strict latex
      spacing only outside of equation contexts.

      Finally, the argument `strict_latex_spaces` may also be set to a
      dictionary with keys 'between-macro-and-chars', 'after-comment', and
      'between-latex-constructs', 'in-equations', with individual values either
      `True` or `False`, dictating whitespace behavior in specific cases (`True`
      indicates strict latex behavior).  The value for 'in-equations' may even
      be another dictionary with the same keys to override values in equations.

      In the future, the default value of this setting might change, e.g., to
      'macros'.

    - `keep_braced_groups=True|False`: If set to `True`, then braces delimiting
      a TeX group ``{Like this}`` will be kept in the output, with the contents
      of the group converted to text as usual.  (By default this is `False`)

    - `keep_braced_groups_minlen=<int>`: If `keep_braced_groups` is set to
      `True`, then we keep braced groups only if their contents length (after
      conversion to text) is longer than the given value.  E.g., if
      `keep_braced_groups_minlen=2`, then ``{\'e}tonnant`` still goes to
      ``\N{LATIN SMALL LETTER E WITH ACUTE}tonnant`` but ``{\'etonnant}``
      becomes ``{\N{LATIN SMALL LETTER E WITH ACUTE}tonnant}``.

    .. versionadded: 1.4

       Added the `strict_latex_spaces`, `keep_braced_groups`, and
       `keep_braced_groups_minlen` flags

    Additionally, the following arguments are accepted for backwards compatibility:

    - `keep_inline_math=True|False`: Obsolete since `pylatexenc 2`.  If set to
      `True`, then this is the same as `math_mode='verbatim'`, and if set to
      `False`, this is the same as `math_mode='text'`.

      .. deprecated:: 2.0
    
         The `keep_inline_math=` option is deprecated because it had a weird
         behavior and was poorly implemented, especially given that a similarly
         named option in :py:class:`LatexWalker` had a different effect.  See
         `Issue #14 <https://github.com/phfaist/pylatexenc/issues/14>`_.

    - `text_replacements` this argument is ignored starting from `pylatexenc 2`.

      .. deprecated:: 2.0

         Text replacements are no longer made at the end of the text conversion.
         This feature is replaced by the concept of LaTeX specials---see, e.g.,
         :py:class:`pylatexenc.latexwalker.LatexSpecialsNode`.

         To keep existing code working, add a call to
         :py:meth:`apply_text_replacements()` immediately after
         :py:meth:`nodelist_to_text()` to achieve the same effect as in
         `pylatexenc 1.x`.  See :py:meth:`apply_text_replacements()`.

    - `env_dict`, `macro_dict`: Obsolete since `pylatexenc 2`.  If set, they are
      dictionaries of known environment and macro definitions.  They default to
      :py:data:`default_env_dict` and :py:data:`default_macro_dict`,
      respectively.

      .. deprecated:: 2.0

         You should now use the more powerful option `latex_context_db=`.  You
         cannot specify both `macro_list` (or `env_list`) and
         `latex_context_db`.
    """
    def __init__(self, latex_context=None, **flags):
        super(LatexNodes2Text, self).__init__()

        if latex_context is None:
            if 'macro_dict' in flags or 'env_dict' in flags:
                # LEGACY -- build a latex context using the given macro_dict
                if pylatexenc._settings['deprecation_warnings']:
                    logger.warning(
                        "Deprecated (pylatexenc 2.0): "
                        "The `macro_dict=...` and `env_dict=...` options in LatexNodes2Text() are "
                        "obsolete since pylatexenc 2.  It'll still work, but please consider "
                        "using instead the more versatile option `latex_context=...`."
                    )
                
                macro_dict = flags.pop('macro_dict', [])
                env_dict = flags.pop('env_dict', [])

                latex_context = macrospec.LatexContextDb()
                latex_context.add_context_category('custom',
                                                   macros=macro_dict.values(),
                                                   environments=env_dict.values(),
                                                   specials=[])

            else:
                # default -- use default
                latex_context = get_default_latex_context_db()

        self.latex_context = latex_context

        self.tex_input_directory = None
        self.strict_input = True

        if 'keep_inline_math' in flags:
            if 'math_mode' in flags:
                raise TypeError("Cannot specify both math_mode= and keep_inline_math= "
                                "for LatexNodes2Text()")
            if pylatexenc._settings['deprecation_warnings']:
                logger.warning("Deprecated (pylatexenc 2.0): "
                               "The keep_inline_math=... option in LatexNodes2Text() has been superseded by "
                               "the math_mode=... option.")
            self.math_mode = 'verbatim' if flags.pop('keep_inline_math') else 'text'
        else:
            self.math_mode = flags.pop('math_mode', 'text')

        if self.math_mode not in ('text', 'with-delimiters', 'verbatim'):
            raise ValueError("math_mode= option must be one of 'text', 'with-delimiters', 'verbatim'")

        self.keep_comments = flags.pop('keep_comments', False)

        strict_latex_spaces = flags.pop('strict_latex_spaces', False)
        self.strict_latex_spaces = _parse_strict_latex_spaces_dict(strict_latex_spaces)

        self.keep_braced_groups = flags.pop('keep_braced_groups', False)
        self.keep_braced_groups_minlen = flags.pop('keep_braced_groups_minlen', 2)

        if 'text_replacements' in flags:
            del flags['text_replacements']
            if pylatexenc._settings['deprecation_warnings']:
                logger.warning("Deprecated (pylatexenc 2.0): "
                               "The text_replacements= argument is ignored since pylatexenc 2. "
                               "To keep existing code working, add a call to `apply_text_replacements()`. "
                               "New code should use instead \"latex specials\".")

        if flags:
            # any flags left which we haven't recognized
            logger.warning("LatexNodes2Text(): Unknown flag(s) encountered: %r", list(flags.keys()))
        

    def set_tex_input_directory(self, tex_input_directory, latex_walker_init_args=None,
                                strict_input=True):
        """
        Set where to look for input files when encountering the ``\\input`` or
        ``\\include`` macro.

        Alternatively, you may also override :py:meth:`read_input_file()` to
        implement a custom file lookup mechanism.

        The argument `tex_input_directory` is the directory relative to which to
        search for input files.

        If `strict_input` is set to `True`, then we always check that the
        referenced file lies within the subtree of `tex_input_directory`,
        prohibiting for instance hacks with '..' in filenames or using symbolic
        links to refer to files out of the directory tree.

        The argument `latex_walker_init_args` allows you to specify the parse
        flags passed to the constructor of
        :py:class:`pylatexenc.latexwalker.LatexWalker` when parsing the input
        file.
        """
        self.tex_input_directory = tex_input_directory
        self.latex_walker_init_args = latex_walker_init_args if latex_walker_init_args else {}
        self.strict_input = strict_input



    def read_input_file(self, fn):
        """
        This method may be overridden to implement a custom lookup mechanism when
        encountering ``\\input`` or ``\\include`` directives.

        The default implementation looks for a file of the given name relative
        to the directory set by :py:meth:`set_tex_input_directory()`.  If
        `strict_input=True` was set, we ensure strictly that the file resides in
        a subtree of the reference input directory (after canonicalizing the
        paths and resolving all symlinks).

        You may override this method to obtain the input data in however way you
        see fit.  In that case, a call to `set_tex_input_directory()` may not be
        needed as that function simply sets properties which are used by the
        default implementation of `read_input_file()`.

        This function accepts the referred filename as argument (the argument to
        the ``\\input`` macro), and should return a string with the file
        contents (or generate a warning or raise an error).
        """
        fnfull = os.path.realpath(os.path.join(self.tex_input_directory, fn))
        if self.strict_input:
            # make sure that the input file is strictly within dirfull, and didn't escape with
            # '../..' tricks or via symlinks.
            dirfull = os.path.realpath(self.tex_input_directory)
            if not fnfull.startswith(dirfull):
                logger.warning(
                    "Can't access path '%s' leading outside of mandated directory [strict input mode]",
                    fn
                )
                return ''

        if not os.path.exists(fnfull) and os.path.exists(fnfull + '.tex'):
            fnfull = fnfull + '.tex'
        if not os.path.exists(fnfull) and os.path.exists(fnfull + '.latex'):
            fnfull = fnfull + '.latex'
        if not os.path.isfile(fnfull):
            logger.warning(u"Error, file doesn't exist: '%s'", fn)
            return ''
        
        logger.debug("Reading input file %r", fnfull)

        try:
            with open(fnfull) as f:
                return f.read()
        except IOError as e:
            logger.warning(u"Error, can't access '%s': %s", fn, e)
            return ''


    def _input_node_simplify_repl(self, n):
        #
        # recurse into files upon '\input{}'
        #
        
        if len(n.nodeargs) != 1:
            logger.warning(u"Expected exactly one argument for '\\input' ! Got = %r", n.nodeargs)

        inputtex = self.read_input_file(self.nodelist_to_text([n.nodeargs[0]]).strip())

        return self.nodelist_to_text(
            latexwalker.LatexWalker(inputtex, **self.latex_walker_init_args)
            .get_latex_nodes()[0]
        )


    def latex_to_text(self, latex, **parse_flags):
        """
        Parses the given `latex` code and returns its textual representation.

        The `parse_flags` are the flags to give on to the
        :py:class:`pylatexenc.latexwalker.LatexWalker` constructor.
        """
        return self.nodelist_to_text(latexwalker.LatexWalker(latex, **parse_flags).get_latex_nodes()[0])


    def nodelist_to_text(self, nodelist):
        """
        Extracts text from a node list. `nodelist` is a list of nodes as returned by
        :py:meth:`pylatexenc.latexwalker.LatexWalker.get_latex_nodes()`.

        Turn the node list to text representations of each node.  Basically apply
        `node_to_text()` to each node.  (But not quite actually, since we take
        some care as to where we add whitespace.)
        """

        s = ''
        prev_node = None
        for node in nodelist:
            if self._is_bare_macro_node(prev_node) and node.isNodeType(latexwalker.LatexCharsNode):
                if not self.strict_latex_spaces['between-macro-and-chars']:
                    # after a macro with absolutely no arguments, include
                    # post_space in output by default if there are other chars
                    # that follow.  This is for more breathing space (especially
                    # in equations(?)), and for compatibility with earlier
                    # versions of pylatexenc (<= 1.3).  This is NOT LaTeX'
                    # default behavior (see issue #11), so only do this if the
                    # corresponding `strict_latex_spaces=` flag is set.
                    s += prev_node.macro_post_space
            s += self.node_to_text(node)
            prev_node = node
        return s

    def node_to_text(self, node, prev_node_hint=None):
        """
        Return the textual representation of the given `node`.

        If `prev_node_hint` is specified, then the current node is formatted
        suitably as following the node given in `prev_node_hint`.  This might
        affect how much space we keep/discard, etc.
        """
        if node is None:
            return ""
        
        if node.isNodeType(latexwalker.LatexCharsNode):
            # Unless in strict latex spaces mode, ignore nodes consisting only
            # of empty chars, as this tends to produce too much space...  These
            # have been inserted by LatexWalker() in some occasions to keep
            # track of all relevant pre_space of tokens, such as between two
            # braced groups ("{one} {two}") or other such situations.
            if not self.strict_latex_spaces['between-latex-constructs'] and len(node.chars.strip()) == 0:
                return ""
            return node.chars
        
        if node.isNodeType(latexwalker.LatexCommentNode):
            if self.keep_comments:
                if self.strict_latex_spaces['after-comment']:
                    return '%' + node.comment + '\n'
                else:
                    # default spaces, i.e., keep what spaces were already there after the comment
                    return '%' + node.comment + node.comment_post_space
            else:
                if self.strict_latex_spaces['after-comment']:
                    return ""
                else:
                    # default spaces, i.e., keep what spaces were already there after the comment
                    # This can be useful to preserve e.g. indentation of the next line
                    return node.comment_post_space
        
        if node.isNodeType(latexwalker.LatexGroupNode):
            contents = self._groupnodecontents_to_text(node)
            if self.keep_braced_groups and len(contents) >= self.keep_braced_groups_minlen:
                return node.delimiters[0] + contents + node.delimiters[1]
            return contents

        def apply_simplify_repl(node, simplify_repl, nodelistargs, what):
            if callable(simplify_repl):
                if 'l2tobj' in getfullargspec(simplify_repl)[0]:
                    # callable accepts an argument named 'l2tobj', provide pointer to self
                    return simplify_repl(node, l2tobj=self)
                return simplify_repl(node)
            if '%' in simplify_repl:
                try:
                    return simplify_repl % tuple([self._groupnodecontents_to_text(nn)
                                                  for nn in nodelistargs])
                except (TypeError, ValueError):
                    logger.warning(
                        "WARNING: Error in configuration: {} failed its substitution!".format(what)
                    )
                    return simplify_repl # too bad, keep the percent signs as they are...
            return simplify_repl
            
        
        if node.isNodeType(latexwalker.LatexMacroNode):
            # get macro behavior definition.
            macroname = node.macroname
            mac = self.latex_context.get_macro_spec(macroname)
            if mac is None:
                # default for unknown macros
                mac = MacroTextSpec('', discard=True)

            def get_macro_str_repl(node, macroname, mac):
                if mac.simplify_repl:
                    return apply_simplify_repl(node, mac.simplify_repl, node.nodeargs,
                                               what="macro '%s'"%(macroname))
                if mac.discard:
                    return ""
                a = node.nodeargs
                if (node.nodeoptarg):
                    a.prepend(node.nodeoptarg)
                return "".join([self._groupnodecontents_to_text(n) for n in a])

            macrostr = get_macro_str_repl(node, macroname, mac)
            return macrostr
        
        if node.isNodeType(latexwalker.LatexEnvironmentNode):
            # get environment behavior definition.
            environmentname = node.environmentname
            envdef = self.latex_context.get_environment_spec(environmentname)
            if envdef is None:
                # default for unknown environments
                envdef = EnvironmentTextSpec('', discard=False)

            if envdef.simplify_repl:
                return apply_simplify_repl(node, envdef.simplify_repl, node.nodelist,
                                           what="environment '%s'"%(environmentname))
            if envdef.discard:
                return ""
            return self.nodelist_to_text(node.nodelist)

        if node.isNodeType(latexwalker.LatexSpecialsNode):
            # get macro behavior definition.
            specials_chars = node.specials_chars
            sspec = self.latex_context.get_specials_spec(specials_chars)
            if sspec is None:
                # no corresponding spec, leave the special chars unchanged:
                return specials_chars

            def get_specials_str_repl(node, specials_chars, spec):
                if spec.simplify_repl:
                    argnlist = node.nodeargd.argnlist if node.nodeargd else []
                    return apply_simplify_repl(node, spec.simplify_repl, argnlist,
                                               what="specials '%s'"%(specials_chars))
                if spec.discard:
                    return ""
                a = node.nodeargd.argnlist
                return "".join([self._groupnodecontents_to_text(n) for n in a])

            s = get_specials_str_repl(node, specials_chars, sspec)
            return s

        if node.isNodeType(latexwalker.LatexMathNode):
            if self.math_mode == 'verbatim':
                return node.latex_verbatim()
            elif self.math_mode == 'with-delimiters':
                with _PushEquationContext(self):
                    return (node.delimiters[0] + self.nodelist_to_text(node.nodelist) 
                            + node.delimiters[1])
            elif self.math_mode == 'text':
                with _PushEquationContext(self):
                    return self.nodelist_to_text(node.nodelist)
            else:
                raise RuntimeError("unknown math_mode={} !".format(self.math_mode))
                

        logger.warning("LatexNodes2Text.node_to_text(): Unknown node: %r", node)

        # discard anything else.
        return ""

    def _is_bare_macro_node(self, node):
        return (node is not None and
                node.isNodeType(latexwalker.LatexMacroNode) and 
                node.nodeoptarg is None and 
                len(node.nodeargs) == 0)

    def _groupnodecontents_to_text(self, groupnode):
        if not groupnode.isNodeType(latexwalker.LatexGroupNode):
            return self.node_to_text(groupnode)
        return self.nodelist_to_text(groupnode.nodelist)


    def apply_text_replacements(self, s, text_replacements):
        r"""
        Convenience function for code that used `text_replacements=` in `pylatexenc
        1.x`.

        If you used custom `text_replacements=` in `pylatexenc 1.x` then you
        will have to change::
  
          # pylatexenc 1.x with text_replacements
          text_replacements = ...
          l2t = LatexNodes2Text(..., text_replacements=text_replacements)
          text = l2t.nodelist_to_text(...)
  
        to::
  
          # pylatexenc 2 text_replacements compatibility
          text_replacements = ...
          l2t = LatexNodes2Text(...)
          temp = l2t.nodelist_to_text(...)
          text = l2t.apply_text_replacements(temp, text_replacements)
  
        as a quick fix.  It is recommended however to treat text replacements
        instead as "latex specials".  (Otherwise the brutal text replacements
        might act on text generated from macros and environments and give
        unwanted results.)  See :py:class:`pylatexenc.macrospec.SpecialsSpec`
        and :py:class:`SpecialsTextSpec`.
        """
        
        # perform suitable replacements
        for pattern, replacement in text_replacements:
            if hasattr(pattern, 'sub'):
                s = pattern.sub(replacement, s)
            else:
                s = s.replace(pattern, replacement)

        return s


class _PushEquationContext(latexwalker._PushPropOverride):
    def __init__(self, l2t):

        new_strict_latex_spaces = None
        if l2t.strict_latex_spaces['in-equations'] is not None:
            new_strict_latex_spaces = _parse_strict_latex_spaces_dict(
                l2t.strict_latex_spaces['in-equations']
            )

        super(_PushEquationContext, self).__init__(l2t, 'strict_latex_spaces',
                                                   new_strict_latex_spaces)








# ------------------------------------------------------------------------------



def latex2text(content, tolerant_parsing=False, keep_inline_math=False, keep_comments=False):
    """
    Heuristic conversion of LaTeX content `content` to unicode text.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    (nodelist, tpos, tlen) = latexwalker.get_latex_nodes(content, keep_inline_math=keep_inline_math,
                                                         tolerant_parsing=tolerant_parsing)

    return latexnodes2text(nodelist, keep_inline_math=keep_inline_math, keep_comments=keep_comments)


def latexnodes2text(nodelist, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from a node list. `nodelist` is a list of nodes as returned by
    :py:func:`pylatexenc.latexwalker.get_latex_nodes()`.

    .. deprecated:: 1.0
       Please use :py:class:`LatexNodes2Text` instead.
    """

    return LatexNodes2Text(
        keep_inline_math=keep_inline_math,
        keep_comments=keep_comments
    ).nodelist_to_text(nodelist)




def main(argv=None):
    import fileinput
    import argparse

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()

    group = parser.add_argument_group("LatexWalker options")

    group.add_argument('--parser-keep-inline-math', action='store_const', const=True,
                       dest='parser_keep_inline_math', default=None,
                       help=argparse.SUPPRESS)
    group.add_argument('--no-parser-keep-inline-math', action='store_const', const=False,
                       dest='parser_keep_inline_math',
                       help=argparse.SUPPRESS)

    group.add_argument('--tolerant-parsing', action='store_const', const=True,
                       dest='tolerant_parsing', default=True)
    group.add_argument('--no-tolerant-parsing', action='store_const', const=False,
                       dest='tolerant_parsing',
                       help="Tolerate syntax errors when parsing, and attempt to continue (default yes)")

    group.add_argument('--strict-braces', action='store_const', const=True,
                       dest='strict_braces', default=False)
    group.add_argument('--no-strict-braces', action='store_const', const=False,
                       dest='strict_braces',
                       help="Report errors for mismatching LaTeX braces (default no)")

    group = parser.add_argument_group("LatexNodes2Text options")

    group.add_argument('--text-keep-inline-math', action='store_const', const=True,
                       dest='text_keep_inline_math', default=None,
                       help=argparse.SUPPRESS)
    group.add_argument('--no-text-keep-inline-math', action='store_const', const=False,
                       dest='text_keep_inline_math',
                       help=argparse.SUPPRESS)

    group.add_argument('--math-mode', action='store', dest='math_mode',
                       choices=['text', 'with-delimiters', 'verbatim'], default='text',
                       help="How to handle chunks of math mode LaTeX code. 'text' = convert "
                       "to text like the rest; 'with-delimiters' = same as 'text' but retain "
                       "the original math mode delimiters; 'verbatim' = keep verbatim LaTeX code")

    group.add_argument('--keep-comments', action='store_const', const=True,
                       dest='keep_comments', default=False)
    group.add_argument('--no-keep-comments', action='store_const', const=False,
                       dest='keep_comments',
                       help="Keep LaTeX comments in text output (default no)")

    group.add_argument('--strict-latex-spaces',
                       choices=['off', 'on']+list(_strict_latex_spaces_predef.keys()),
                       dest='strict_latex_spaces', default='macros',
                       help="How to handle whitespace. See documentation for the class "
                       "LatexNodes2Text().")

    group.add_argument('--keep-braced-groups', action='store_const', const=True,
                       dest='keep_braced_groups', default=False)
    group.add_argument('--no-keep-braced-groups', action='store_const', const=False,
                       dest='keep_braced_groups',
                       help="Keep LaTeX {braced groups} in text output (default no)")

    group.add_argument('--keep-braced-groups-minlen', type=int, default=2,
                       dest='keep_braced_groups_minlen',
                       help="Only apply --keep-braced-groups to groups that contain at least"
                       "this many characters")

    parser.add_argument('files', metavar="FILE", nargs='*',
                        help='Input files (if none specified, read from stdandard input)')

    args = parser.parse_args(argv)

    if args.parser_keep_inline_math is not None or args.text_keep_inline_math is not None:
        logger.warning("Options --parser-keep-inline-math and --text-keep-inline-math are "
                       "deprecated and no longer work.  Please consider using "
                       "--math-mode=... instead.")

    latex = ''
    for line in fileinput.input(files=args.files):
        latex += line

    lw = latexwalker.LatexWalker(latex,
                                 tolerant_parsing=args.tolerant_parsing,
                                 strict_braces=args.strict_braces)

    (nodelist, pos, len_) = lw.get_latex_nodes()

    ln2t = LatexNodes2Text(math_mode=args.math_mode,
                           keep_comments=args.keep_comments,
                           strict_latex_spaces=args.strict_latex_spaces,
                           keep_braced_groups=args.keep_braced_groups,
                           keep_braced_groups_minlen=args.keep_braced_groups_minlen)

    print(ln2t.nodelist_to_text(nodelist) + "\n")



def run_main():

    try:

        main()

    except SystemExit:
        raise
    except: # lgtm [py/catch-base-exception]
        import pdb
        import traceback
        traceback.print_exc()
        pdb.post_mortem()




if __name__ == '__main__':

    run_main()
