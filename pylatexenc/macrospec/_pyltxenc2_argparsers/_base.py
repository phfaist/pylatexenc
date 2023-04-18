from __future__ import print_function, unicode_literals


from ...latexnodes import (
    LatexWalkerError,
)
from ...latexnodes import ParsedArguments as ParsedMacroArgs
from ...latexnodes.nodes import (
    LatexCharsNode,
)


# for Py3
_basestring = str

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
## End Py2 support code




class MacroStandardArgsParser(object):
    r"""
    Parses the arguments to a LaTeX macro.

    .. deprecated:: 3.0

       This class is part of `pylatexenc 2.x`'s macro argument parsing API.
       Starting with `pylatexenc 3.0`, each macro/environment/specials argument
       is parsed with an individual macro parser.  See
       :py:class:`pylatexenc.latexnodes.LatexArgumentSpec`,
       :py:class:`pylatexenc.latexnodes.parsers.LatexStandardArgumentParser`.
       (You can also check out the lower-level
       :py:class:`pylatexenc.macrospec.LatexMacroCallParser`,
       :py:class:`pylatexenc.macrospec.LatexEnvironmentCallParser`, and
       :py:class:`pylatexenc.macrospec.LatexSpecialsCallParser`.)

    This class parses a simple macro argument specification with a specified
    arrangement of optional and mandatory arguments.

    This class also serves as base class for more advanced argument parsers
    (e.g. for a ``\verb+...+`` macro argument parser).  In such cases,
    subclasses should attempt to provide the most suitable `argspec` (and
    `argnlist` for the corresponding :py:class:`ParsedMacroArgs`) for their use,
    if appropriate, or set them to `None`.

    Arguments:

      - `argspec`: must be a string in which each character corresponds to an
        argument.  The character '{' represents a mandatory argument (single
        token or LaTeX group) and the character '[' denotes an optional argument
        delimited by braces.  The character '\*' denotes a possible star char at
        that position in the argument list, a corresponding
        ``latexwalker.LatexCharsNode('*')`` (or `None` if no star) will be
        inserted in the argument node list.  For instance, the string '\*{[[{'
        would be suitable to specify the signature of the '\\newcommand' macro.

        Currently, the argspec string may only contain the characters '\*', '{'
        and '['.

        The `argspec` may also be `None`, which is the same as specifying an
        empty string.

      - `optional_arg_no_space`: If set to `True`, then an optional argument
        cannot have any whitespace between the preceeding tokens and the '['
        character.  Set this to `True` in cases such as for ``\\`` in AMS-math
        environments, where AMS apparently introduced a patch to prevent a
        bracket on a new line after ``\\`` from being interpreted as the
        optional argument to ``\\``.
    
      - `args_math_mode`: Either `None`, or a list of the same length as
        `argspec`.  If a list is given, then each item must be `True`, `False`,
        or `None`.  The corresponding argument (cf. `argspec`) is then
        respectively parsed in math mode (`True`), in text mode (`False`), or
        with the mode unchanged (`None`).  If `args_math_mode` is `None`, then
        all arguments are parsed in the same mode as the current mode.

      - additional unrecognized keyword arguments are passed on to superclasses
        in case of multiple inheritance

    Attributes:

    .. py:attribute:: argspec

       Argument type specification provided to the constructor.

    .. py:attribute:: optional_arg_no_space

       See the corresponding constructor argument.

    .. py:attribute:: args_math_mode

       See the corresponding constructor argument.
    """
    def __init__(self, argspec=None, optional_arg_no_space=False,
                 args_math_mode=None, **kwargs):
        super(MacroStandardArgsParser, self).__init__(**kwargs)
        self.argspec = argspec if argspec else ''
        self.optional_arg_no_space = optional_arg_no_space
        self.args_math_mode = args_math_mode
        # catch bugs, make sure that argspec is a string with only accepted chars
        if not isinstance(self.argspec, _basestring) or \
           not all(x in '*[{' for x in self.argspec):
            raise TypeError(
                "argspec must be a string containing chars '*', '[', '{{' only: {!r}"
                .format(self.argspec)
            )
        # non-documented attribute that makes us ignore any leading '*'.  We use
        # this to emulate pylatexenc 1.x behavior when using the MacrosDef()
        # function explicitly
        self._like_pylatexenc1x_ignore_leading_star = False


    def parse_args(self, w, pos, parsing_state=None):
        r"""
        Parse the arguments encountered at position `pos` in the
        :py:class:`~pylatexenc.latexwalker.LatexWalker` instance `w`.

        You may override this function to provide custom parsing of complicated
        macro arguments (say, ``\verb+...+``).  The method will be called by
        keyword arguments, so the argument names should not be altered.

        The argument `w` is the :py:class:`pylatexenc.latexwalker.LatexWalker`
        object that is currently parsing LaTeX code.  You can call methods like
        `w.get_goken()`, `w.get_latex_expression()` etc., to parse and read
        arguments.

        The argument `parsing_state` is the current parsing state in the
        :py:class:`~pylatexenc.latexwalker.LatexWalker` (e.g., are we currently
        in math mode?).  See doc for
        :py:class:`~pylatexenc.latexwalker.ParsingState`.

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

        if parsing_state is None:
            parsing_state = w.make_parsing_state()

        argnlist = []

        if self.args_math_mode is not None and \
           len(self.args_math_mode) != len(self.argspec):
            raise ValueError("Invalid args_math_mode={!r} for argspec={!r}!"
                             .format(self.args_math_mode, self.argspec))

        def get_inner_parsing_state(j):
            if self.args_math_mode is None:
                return parsing_state
            amm = self.args_math_mode[j]
            if amm is None or amm == parsing_state.in_math_mode:
                return parsing_state
            if amm == True:
                return parsing_state.sub_context(in_math_mode=True)
            return parsing_state.sub_context(in_math_mode=False)

        p = pos

        if self._like_pylatexenc1x_ignore_leading_star:
            # ignore any leading '*' character
            tok = w.get_token(p)
            if tok.tok == 'char' and tok.arg == '*':
                p = tok.pos + tok.len

        for j, argt in enumerate(self.argspec):
            if argt == '{':
                (node, np, nl) = w.get_latex_expression(
                    p,
                    strict_braces=False,
                    parsing_state=get_inner_parsing_state(j)
                )
                p = np + nl
                argnlist.append(node)

            elif argt == '[':

                if self.optional_arg_no_space and p < len(w.s) and w.s[p].isspace():
                    # don't try to read optional arg, we don't allow space
                    argnlist.append(None)
                    continue

                optarginfotuple = w.get_latex_maybe_optional_arg(
                    p,
                    parsing_state=get_inner_parsing_state(j)
                )
                if optarginfotuple is None:
                    argnlist.append(None)
                    continue
                (node, np, nl) = optarginfotuple
                p = np + nl
                argnlist.append(node)

            elif argt == '*':
                # possible star.
                tok = w.get_token(p)
                if tok.tok == 'char' and tok.arg.startswith('*'):
                    # has star
                    argnlist.append(
                        w.make_node(LatexCharsNode,
                                    parsing_state=get_inner_parsing_state(j),
                                    chars='*', pos=tok.pos, len=1)
                    )
                    p = tok.pos + 1
                else:
                    argnlist.append(None)

            else:
                raise LatexWalkerError(
                    "Unknown macro argument kind for macro: {!r}".format(argt)
                )

        parsed = ParsedMacroArgs(
            argspec=self.argspec,
            argnlist=argnlist,
        )

        return (parsed, pos, p-pos)


    def __repr__(self):
        return '{}(argspec={!r}, optional_arg_no_space={!r}, args_math_mode={!r})'.format(
            self.__class__.__name__, self.argspec, self.optional_arg_no_space,
            self.args_math_mode
        )
    
