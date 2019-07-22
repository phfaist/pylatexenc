============
 Change Log
============

pylatexenc 2.0
==============

- Improvements to LaTeX parser and its API (:py:mod:`pylatexenc.latexwalker`):

  - More powerful and versatile way of providing a "latex context" with a
    collection of known macros, environment definitions, and "latex specials"
    provided by the :py:mod:`pylatexenc.macrospec` module.

  - Support for arbitrary sequences of characters that have a special meaning in
    LaTeX, such as '&', '#', '``', which are referred to as "latex specials".  A
    new node type (:py:class:`~pylatexenc.latexwalker.LatexSpecialsNode`)
    represents such sequences of characters;

  - Support for arbitrary macro arguments & formats via custom parsing code.
    The groundwork is laid, for instance, to support ``\verb+...+``\ -type
    constructs;

  - Better parsing of math mode, and support for display math modes;

  - Parsed LaTeX nodes (:py:class:`~pylatexenc.latexwalker.LatexNode`\ 's) now
    retain information about which part of the original string they represent,
    and therefore what their verbatim latex representation is;

- Improvements to the :py:mod:`~pylatexenc.latex2text`:

  - Renamed macro specification classes `MacroDef` → `MacroTextSpec` etc.,
    include support for "latex specials";

  - New flag `math_mode=` specifying how to convert math mode to text;

  - Adapted for the updated `latexwalker` API.

- New interface for :py:mod:`pylatexenc.latexencode`, with
  :py:class:`~pylatexenc.latexencode.UnicodeToLatexEncoder` and
  :py:func:`~pylatexenc.latexencode.unicode_to_latex()`.

  The earlier function :py:func:`pylatexenc.latexencode.utf8tolatex()` was
  poorly named, given that its argument was a python unicode string, not a
  `utf-8`-encoded string.  The old function is still provided as is to keep code
  that was designed for `pylatexenc 1.x` working.

- Improvements to the parser may mean that the results might differ slightly
  from earlier versions.

  For instance, `latexwalker` now recognizes ``--`` and ``---`` as "latex
  specials", and by default `latex2text` substitutes the corresponding unicode
  characters for en-dash and em-dash, respecitively.  You can disable this
  behavior by filtering out the 'nonascii-specials' category from the default
  latex context database in `latex2text`::

    latex_context = latex2text.get_default_latex_context_db().filter_context(
        exclude_categories=['nonascii-specials']
    )
    l2t = latex2text.LatexNodes2Text(latex_context=latex_context, ...)
    ...

- The three main modules can now be used in command-line: `latex2text`,
  `latexencode` and `latexwalker`.  Run with ``--help`` for information about
  usage and options.



**API Changes that might affect existing code:**

With the important changes introduced in `pylatexenc 2.0`, some parts of the API
were improved and are not necessarily 100% source compatible with `pylatexenc
1.x`.  Code that uses the high-level features of `pylatexenc 1.x` should run
without any modification required.  However if you use some advanced features of
`pylatexenc`, you might have to make some small changes to your code to adapt to
the new API.

- The specification of known macros, environments, and latex specials for both
  :py:class:`~pylatexenc.latexwalker.LatexWalker` and
  :py:class:`~pylatexenc.latex2text.LatexNodes2Text` are organized into
  categories and stored into a :py:class:`~pylatexenc.macrospec.LatexContextDb`
  object (one for each of these modules).

  Previously, to introduce a custom macro in `latexwalker`, one could write::

    >>> from pylatexenc.latexwalker import LatexWalker, MacrosDef, default_macro_dict
    >>> my_macros = dict(default_macro_dict)
    >>> my_macros['mymacro'] = MacrosDef('mymacro', True, 2)
    >>> w = LatexWalker(r'Text with \mymacro[yes]{one}{two}.', macro_dict=my_macros)
    >>> (nodelist, pos, len_) = w.get_latex_nodes()
    >>> nodelist[1].nodeoptarg
    LatexGroupNode(nodelist=[LatexCharsNode(chars='yes')])

  This code still works in `pylatexenc 2.0`, so *it's not strictly necessary to
  change your code.*  Simply, the new interface is more powerful and is henceforth
  recommended (see doc of :py:mod:`pylatexenc.macrospec`).  The above example
  would now be written as::

    >>> from pylatexenc.latexwalker import LatexWalker, get_default_latex_context_db
    >>> from pylatexenc.macrospec import MacroSpec
    >>> latex_context = get_default_latex_context_db()
    >>> latex_context.add_context_category('mymacros', macros=[ MacroSpec('mymacro', '[{{') ])
    >>> w = LatexWalker(r'Text with \mymacro[yes]{one}{two}.', latex_context=latex_context)
    >>> (nodelist, pos, len_) = w.get_latex_nodes()
    >>> nodelist[1].nodeoptarg
    LatexGroupNode(pos=18, len=5, nodelist=[LatexCharsNode(pos=19, len=3, chars='yes')])

  The same holds for `latex2text`.

  The `pylatexenc.latexwalker.MacrosDef` class in `pylatexenc 1.x` was rewritten
  and renamed :py:class:`pylatexenc.macrospec.MacroSpec`, and corresponding
  classes :py:class:`pylatexenc.macrospec.EnvironmentSpec` and
  :py:class:`pylatexenc.macrospec.SpecialsSpec` were introduced.
  [:py:func:`pylatexenc.latexwalker.MacrosDef` is now a function that returns a
  :py:class:`~pylatexenc.macrospec.MacroSpec`; but the field names of the
  constructed class might have changed.]  The `pylatexenc.latex2text.MacroDef`
  and `pylatexenc.latex2text.EnvDef` were rewritten and renamed
  :py:class:`pylatexenc.latex2text.MacroTextSpec` and
  :py:class:`pylatexenc.latex2text.EnvironmentTextSpec`, and the class
  :py:class:`pylatexenc.latex2text.SpecialsTextSpec` was introduced.  [The
  earlier classes are now functions that return instances of the new classes;
  but the field names of the constructed class might have changed.]

  For :py:class:`~pylatexenc.latexwalker.LatexWalker`, macro, environment, and
  latex specials syntax specifications are provided as
  :py:class:`pylatexenc.macrospec.MacroSpec`,
  :py:class:`pylatexenc.macrospec.EnvironmentSpec`, and
  :py:class:`pylatexenc.macrospec.SpecialsSpec` objects, which extend and
  completely replace the `MacrosDef` object in `pylatexenc 1.x`.

  For :py:class:`~pylatexenc.latex2text.LatexNodes2Text`, specification of
  replacement texts for macros, environments, and latex specials are provided as
  :py:class:`pylatexenc.latex2text.MacroTextSpec`,
  :py:class:`pylatexenc.latex2text.EnvironmentTextSpec`, and
  :py:class:`pylatexenc.latex2text.SpecialsTextSpec` objects, which replace
  replace the `MacroDef` and `EnvironmentDef` objects in `pylatexenc 1.x`.

  If you used custom `text_replacements=` in
  :py:class:`~pylatexenc.latex2text.LatexNodes2Text`, then you will have to
  change::

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

  as a quick fix.  It is recommended however to treat text replacements instead
  as "latex specials".  (Otherwise the brutal text replacements might act on
  text generated from macros and environments and give unwanted results.)  See
  :py:class:`pylatexenc.macrospec.SpecialsSpec` and
  :py:class:`pylatexenc.latex2text.SpecialsTextSpec`.


- The `keep_inline_math=` option was deprecated for both in
  :py:class:`~pylatexenc.latexwalker.LatexWalker` and
  :py:class:`~pylatexenc.latex2text.LatexNodes2Text`  (see `Issue #14
  <https://github.com/phfaist/pylatexenc/issues/14>`_).  Instead, you
  should set the option `math_mode=`  in
  :py:class:`~pylatexenc.latex2text.LatexNodes2Text`.

  The design choice was made in `pylatexenc 2.0` to have
  :py:class:`~pylatexenc.latexwalker.LatexWalker` always parse math modes, and
  have the textual representation be altered not by a parser option but by an
  option in :py:class:`~pylatexenc.latex2text.LatexNodes2Text`.

  Both :py:class:`~pylatexenc.latexwalker.LatexWalker` and
  :py:class:`~pylatexenc.latex2text.LatexNodes2Text` accept the
  `keep_inline_math=` keyword argument to avoid breaking code designed for
  `pylatexenc 1.x`; the former ignores it entirely and the latter attempts to
  set `math_mode=` to a suitable value.

  The result might differ when you run the same code with `pylatexenc 2.0`.
  However you can restore the required behavior by simply replacing the
  following idioms as follows::

    LatexNodes2Text(keep_inline_math=True).latex_to_text(..., keep_inline_math=True)
    -->
    LatexNodes2Text(math_mode='verbatim').latex_to_text(...)

    LatexNodes2Text(keep_inline_math=True).latex_to_text(..., keep_inline_math=False)
    -->
    LatexNodes2Text(math_mode='with-delimiters').latex_to_text(...)

    LatexNodes2Text(keep_inline_math=False).latex_to_text(..., keep_inline_math=True|False)
    -->
    LatexNodes2Text(math_mode='text').latex_to_text(...)

  [Note that the keyword argument to `latex_to_text()` is the option passed to
  the constructor of the `LatexWalker` object.

- The node structure classes were changed to allow macros, environments and
  latex specials to have arbitrarily complicated, non-standard arguments.  If
  you relied on the details of the
  :py:class:`~pylatexenc.latexwalker.LatexNode`\ 's returned by
  :py:class:`~pylatexenc.latexwalker.LatexWalker`, then you might have to adjust
  your code to the API changes.  See documentation of
  :py:class:`~pylatexenc.latexwalker.LatexNode` and friends.




pylatexenc 1.x
==============

See description of updates and changes on the `github releases page
<https://github.com/phfaist/pylatexenc/releases>`_.
