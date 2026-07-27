What's new in `pylatexenc 3`
============================

Wow, a *lot* of stuff has changed in the `latexwalker` and `macrospec` modules.
There's even a new `latexnodes` module.  I don't know where to start!

The good news is, if you're simply using the latex-to-unicode and
unicode-to-latex conversion tools, your code depending on `pylatexenc 2` should
run without any changes.  The *text* that comes out might look a little
different here and there, though — see below.  You might get some deprecation
warnings which you can silence using python's warnings filter management (e.g.,
``python -W 'ignore::DeprecationWarning'`` or using
:py:func:`warnings.simplefilter`).  We did our best to make the API as
backwards-compatible as reasonably possible, so there's a good chance your code
continues to run as-is (or with minor tweaks).

Compatibility with Python 2 was dropped.  We'll try to remain compatible with
Python ≥ 3.6 moving forward.

The parser-related modules have seen a number of changes, including:

- New parsing mechanism in a new `latexnodes` module — everything gets delegated
  to "parser objects" that are specialized in parsing a specific construct.  See
  :py:class:`pylatexenc.latexnodes.parsers.LatexParserBase`.

- The parser has new enhanced handling of macro, environment, and specials
  arguments.  Arguments can be named for easier lookup when traversing the node
  tree.

- Lists of latex node objects
  (:py:class:`~pylatexenc.latexnodes.nodes.LatexNode`) are now wrapped in a
  special object for node lists →
  :py:class:`pylatexenc.latexnodes.nodes.LatexNodeList`.

- Macro, environment and specials arguments are now stored in a
  :py:class:`pylatexenc.latexnodes.ParsedArguments` object.  (The name
  `macrospec.ParsedMacroArgs` still refers to that same class, so existing
  `isinstance()` tests keep working.)  Use
  :py:class:`pylatexenc.latexnodes.ParsedArgumentsInfo` to look up arguments
  comfortably, including by name.

- New standard argument parsers for custom type arguments: You can now declare
  macros, environments, and specials that take arguments with extended syntax
  such as ``\mymacro<One>{Two}[Optional three]``.  The argument specification is
  inspired by LaTeX' `xparse` package specification.  For a full list of
  argument types, see :py:class:`~pylatexenc.macrospec.MacroSpec` and
  :py:class:`~pylatexenc.latexnodes.parsers.LatexStandardArgumentParser`.

- Errors got their own little hierarchy.  `LatexWalkerParseError` now derives
  from a new
  :py:class:`~pylatexenc.latexnodes.LatexWalkerLocatedError`, and the walker
  actually raises the more specific
  :py:class:`~pylatexenc.latexnodes.LatexWalkerNodesParseError` and
  :py:class:`~pylatexenc.latexnodes.LatexWalkerTokenParseError`.  Catching
  `LatexWalkerParseError` still works; matching on the error *message* doesn't,
  because the messages and the "open blocks" trace were rewritten.

- :py:class:`~pylatexenc.macrospec.LatexContextDb` objects have a lifecycle
  now: you build them with `add_context_category()`, then `freeze()` them, and
  then you can derive new ones with `filtered_context()` (which replaces
  `filter_context()`) and `extended_with()`.  Note `extended_with()` insists
  that the object be frozen first.

- Two new tools you might enjoy:
  :py:class:`~pylatexenc.latexnodes.LatexNodesLatexRecomposer` turns a node
  tree back into latex code, and
  :py:class:`~pylatexenc.latexnodes.nodes.LatexNodesVisitor` (along with
  ``node.accept_node_visitor()``) gives you a visitor pattern for walking a
  tree.

- The `len` attribute in node objects is replaced by a `pos_end` attribute.  The
  `len` attribute can still be accessed as a read-only computed attribute for
  compatibility with existing code using pylatexenc 2.

- Node objects carry more information than they used to (the parsing state, the
  latex walker, the spec object, ...), so ``repr(node)`` is now *much* longer
  than in `pylatexenc 2`, and the JSON export produced by ``latexwalker
  --output-format=json`` changed shape accordingly.  If you were comparing
  reprs in doctests or scraping them from logs, you'll want to look at the node
  fields directly instead.


The `latex2text` module was improved:

- :py:mod:`~pylatexenc.latex2text` now keeps track of the surroundings in which
  a node is being converted, in a
  :py:class:`pylatexenc.latex2text.TextConversionState` object available as
  :py:attr:`LatexNodes2Text.state <pylatexenc.latex2text.LatexNodes2Text.state>`.

- :py:mod:`~pylatexenc.latex2text` renders list environments
  (``{itemize}``, ``{enumerate}``, ``{description}``) properly, including nested
  lists: items are numbered where relevant, the item marker style follows the
  nesting depth as it does in LaTeX, and the contents of an item that spans
  several lines is aligned with the item text.  Note the default bullet for
  ``\item`` is now ``•`` and no longer ``*``.

- Support for unicode alphabets for bold and italic text.

- There is a new renderer for math content, ``math_mode='fancy'``.  It is now
  the default.  It tries to make the plain text look like the
  formula LaTeX would typeset, so that ``$4 \pi c\sin(x+y)$`` gives
  ``4π𝑐 sin(𝑥 + 𝑦)`` using unicode alphabets.   (Use ``math_mode='text'`` to
  restore pylatexenc-v2's behavior.)  Relevant options: ``math_mode=``,
  ``math_fontstyle=``, ``math_expression_in=`` (see
  :py:class:`~pylatexenc.latex2text.LatexNodes2Text`).

- Subscripts and superscripts are now rendered with unicode characters whenever
  there are suitable ones: ``$x^2$`` gives ``x²``, ``$H_2O$`` gives ``H₂O``,
  and ``$\sum_{i=1}^n x_i$`` gives ``∑ᵢ₌₁ⁿ xᵢ``.  Same for ``\sqrt``, which
  gives ``√`` and ``∛``.


The `latexencode` module has barely changed.





.. _new-in-pylatexenc-3-possible-pitfall-changes:

A couple things to look out for
-------------------------------

- :py:class:`~pylatexenc.latex2text.LatexNodes2Text` renders formulas with the
  new ``math_mode='fancy'`` engine by default, so its output now contains the
  unicode mathematical alphanumeric characters where `pylatexenc 2` produced
  plain ASCII letters: ``$x+y$`` gives ``𝑥 + 𝑦``, and ``\textbf{bold}`` gives
  ``𝐛𝐨𝐥𝐝``.  Those characters are outside the Basic Multilingual Plane, and a
  font that does not cover them shows a placeholder box.  If you are indexing
  the output, comparing it against stored strings, or feeding it to a program
  that expects ASCII, pass ``math_mode='text'`` to get the `pylatexenc 2`
  rendering back, or keep the new rendering and only drop the unicode
  alphabets with ``text_fontstyle=False, math_fontstyle=False``.  The
  command-line tool takes ``--math-mode=text``, or ``--text-fontstyle=off
  --math-fontstyle=off``, for the same purposes.

- Paragraph breaks (``\n\n``) as well as ``^`` and ``_`` are now reported as
  their own *specials* nodes.  This means that text which used to come back as
  a single :py:class:`~pylatexenc.latexnodes.nodes.LatexCharsNode` is now split
  into several nodes::

    'para one\n\npara two'   pylatexenc 2:  chars('para one\n\npara two')
                             pylatexenc 3:  chars('para one') +
                                            specials('\n\n') +
                                            chars('para two')

  If you were looking for ``"\n\n"`` inside ``node.chars`` to split paragraphs,
  or simply concatenating the ``chars`` of every chars node in a list, you'll
  need to handle those specials nodes as well.  This is probably the change
  that's most likely to bite you, because it doesn't require using any fancy
  feature — reading ``node.chars`` is enough.

- The default macro and environment database learned a few new definitions,
  including ``\href`` (which takes two arguments), ``\part``, ``\paragraph``
  (which was misspelled in the `pylatexenc 2` database, and hence unknown), and
  the ``{lstlisting}`` environment.  When a macro becomes known, the ``{...}``
  groups that follow it are parsed as its *arguments* instead of remaining
  sibling group nodes, so the shape of the node tree changes for documents that
  use them.

- If you created a :py:class:`~pylatexenc.macrospec.LatexContextDb` database
  from scratch, you might suddenly get errors about unknown macros.  The default
  initialization for unknown macro, environment and specials specification
  objects for :py:class:`~pylatexenc.macrospec.LatexContextDb` was, and remains,
  `None`.  What has changed is the interpretation of this `None`: Now, the latex
  walker (more precisely,
  :py:class:`~pylatexenc.latexnodes.LatexNodesCollector`) reports an error,
  whereas previously, the parser would simply assume the macro doesn't accept
  any arguments.  To restore the earlier behavior, simply set the spec objects
  for unknown macro/environment/specials in your latex context db object::

    latex_context_db = macrospec.LatexContextDb()
    # ...
    latex_context_db.add_context_category( ... )
    # ...
    latex_context_db.set_unknown_macro_spec(macrospec.MacroSpec(''))
    latex_context_db.set_unknown_environment_spec(macrospec.EnvironmentSpec(''))
    #
    # unknown macros and environments are now accepted and are assumed
    # not to take any arguments
    #

- Node lists are now encapsulated in a
  :py:class:`~pylatexenc.latexnodes.nodes.LatexNodeList`.  It behaves very much
  like a list in all respects (indexing, slicing, etc.), except that it does not
  satisfy ``isinstance(nodelist, list)``.  If you relied on such tests, you'll
  need to update them to the liking of ``isinstance(nodelist, (LatexNodeList,
  list))``.

- Verbatim arguments to `\verb` are now reported with a ``LatexGroupNode`` that
  contains a chars node, rather than a ``LatexCharsNode`` directly.  Note also
  that ``isinstance(node.nodeargd, ParsedVerbatimArgs)`` is no longer true for
  ``\verb``; the `verbatim_text` attribute still works as before.

- We've introduced a new entry point interface for parsing:
  :py:meth:`LatexWalker.parse_content()
  <pylatexenc.latexwalker.LatexWalker.parse_content>`, with a suitable parser
  object from :py:mod:`pylatexenc.latexnodes.parsers` (such as
  :py:class:`~pylatexenc.latexnodes.parsers.LatexGeneralNodesParser`).  The new
  interface returns ``(nodes, parsing_state_delta)`` — the node list along with
  any information about state changes that occurred during the parsing.
  The earlier interface exposed by `pylatexenc 2`, using
  :py:class:`~pylatexenc.latexwalker.LatexWalker` — `get_latex_nodes()`,
  `get_token()`, `get_latex_expression()`, `get_latex_braced_group()`,
  `get_latex_environment()` and `get_latex_maybe_optional_arg()` keeps working
  as it did.

- Building macro specifications with the `pylatexenc 2` `args_parser=` argument
  still works, but it is deprecated and now warns.  You can't mix it with the
  `pylatexenc 3` options (`arguments_spec_list=`, `body_parsing_state_delta=`,
  …) in the same call.



Some bug fixes in behavior
--------------------------

- The :py:mod:`~pylatexenc.latex2text` 's ``\paragraph{...}`` output
  was fixed to produce simply ``"Paragraph Title\nBody"``.  (Pylatexenc 2
  didn't get the newlines quite right.)

- The ``verbatim`` and ``lstlisting`` environments no longer report the newline
  that immediately follows ``\begin{...}`` as part of their contents, mirroring
  what LaTeX itself does.

- An unterminated ``lstlisting`` environment no longer loses its parsed
  arguments in tolerant parsing mode; ``nodeargd`` used to be `None` there.

- Fixes for latex2text: ``\href{...}{...}`` and ``\url{...}``; ``{verbatim}``
  and ``{lstlisting}``.

- ``{enumerate}`` items are numbered, and ``\frac{a}`` (with a missing second
  argument) no longer emits the literal replacement string ``'%s/%s'``.

- More extensive support for math operators and symbols in latex2text.

- Several bug fixes, especially in tolerant parsing mode.

- You might notice other fixes that we forgot to include here.


Details that v3 might get different
-----------------------------------

Pylatexenc v3's behavior might get some minor things a bit differently.  We don't
expect these to lead to downstream issues, but we're listing the ones we're aware
of here for completeness:

- The :py:mod:`~pylatexenc.latexencode` module no longer uses the dotless
  ``\i`` command when encoding the accented characters ‘ì’, ‘í’, ‘î’ and ‘ï’
  (U+00EC–U+00EF), producing ``\'i`` instead of ``{\'\i}``.  This follows
  a long-standing change in LaTeX where ``\i`` is no longer needed for such
  accented characters.  (If you prefer to keep braces around your replacement,
  remember to use a "latex replacement protection" option, see
  :py:attr:`pylatexenc.latexencode.UnicodeToLatexEncoder.replacement_latex_protection`.)

- Parse error messages were rewritten, and the reported column can be off by one
  compared with `pylatexenc 2`.  The exception *classes* are still the ones you
  know (see above), so code that catches them is fine; code that matches on the
  message text isn't.

- Recomposing a node tree back to latex code with
  :py:class:`~pylatexenc.latexnodes.LatexNodesLatexRecomposer` normalizes the
  white space around a paragraph break to exactly ``\n\n``, because that's what
  the specials node records.  E.g. ``'a\n\n\n\nb'`` comes back as ``'a\n\nb'``.


- You might notice other differences that we forgot to include here.
