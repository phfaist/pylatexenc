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


# Internal module. Internal API may move, disappear or otherwise change at any
# time and without notice.

import logging
logger = logging.getLogger(__name__)

from ..latexnodes import (
    CallableSpecBase,
    ParsingStateDeltaEnterMathMode,
    #ParsingStateDeltaLeaveMathMode,
)

from ._argumentsparser import LatexArgumentsParser, LatexNoArgumentsParser
from ._macrocallparser import (
    LatexMacroCallParser, LatexEnvironmentCallParser, LatexSpecialsCallParser
)
from ._environmentbodyparser import LatexEnvironmentBodyContentsParser


_legacy_pyltxenc2_do = lambda *args: None


class _NotSpecified:
    pass


_spec_node_parser_types = {
    'macro': LatexMacroCallParser,
    'environment': LatexEnvironmentCallParser,
    'specials': LatexSpecialsCallParser,
}


class CallableSpec(CallableSpecBase):
    r"""
    Base class for :py:class:`MacroSpec`, :py:class:`EnvironmentSpec` and
    :py:class:`SpecialsSpec` classes regrouping common functionality.

    Constructor arguments:

      - `arguments_spec_list` is the list of arguments that this callable
        accepts.  Each item is either a
        :py:class:`~pylatexenc.latexnodes.LatexArgumentSpec` instance, or a
        string representing a standard argument type (see
        :py:class:`~pylatexenc.latexnodes.parsers.LatexStandardArgumentParser`)
        which is converted into such an instance.  Specify `None` or an empty
        list if the callable does not accept any arguments.

      - `spec_node_parser_type` determines the parser class that
        :py:meth:`get_node_parser()` instantiates in order to parse an
        invocation of this callable.  You can specify the class itself, or one
        of the strings ``'macro'``, ``'environment'`` or ``'specials'``, which
        select :py:class:`LatexMacroCallParser`,
        :py:class:`LatexEnvironmentCallParser`, and
        :py:class:`LatexSpecialsCallParser`, respectively.

      - `macroname`, `environmentname` and `specials_chars` identify the
        callable.  Exactly one of them is relevant for a given callable type,
        and only those that are explicitly specified are set as attributes on
        this object.  (The subclasses :py:class:`MacroSpec`,
        :py:class:`EnvironmentSpec` and :py:class:`SpecialsSpec` each set the
        relevant one.)

      - `make_arguments_parsing_state_delta`, `make_body_parsing_state_delta`,
        `make_after_parsing_state_delta`, `make_body_parser` and
        `finalize_node` are optional callables.  If one of them is specified,
        then the method of the same name on this object will invoke it instead
        of applying its default behavior.  See the documentation of each of
        those methods for the arguments that the callable receives.

      - `body_parsing_state_delta` (keyword argument, for environments) is the
        parsing state delta to use for the environment body contents.  It is
        stored as the attribute of the same name and is what
        :py:meth:`make_body_parsing_state_delta()` returns by default.

    The constructor also still accepts the arguments of the corresponding
    `pylatexenc 2` classes, namely `args_parser=` and `is_math_mode=`.  Those
    two can be used together, but they cannot be combined with any of the
    arguments that were introduced in `pylatexenc 3` (`arguments_spec_list=`,
    `body_parsing_state_delta=`, and the `make_***=` and `finalize_node=`
    callables); attempting to do so raises a `ValueError`.

    One of the main reasons for bringing all the default functionality of the
    :py:class:`MacroSpec`, :py:class:`EnvironmentSpec`, and
    :py:class:`SpecialsSpec` classes together in the same base class is to
    facilitate creating richer derived spec classes.  For instance, the `flm
    <https://github.com/phfaist/flm>`_ project needs to supplement spec classes
    with additional information, e.g., about how to render the node in
    appropriate output formats.  In such cases, it suffices to inherit
    `CallableSpec` to implement the desired functionality, and instantiate such
    classes directly (or recreate lightweight derived versions for macros,
    environments, and specials), rather than have to play around with multiple
    inheritance or other such tricks to simultaneously implement new base
    functionality that is common to macro, environment, and specials parsing.
    """

    def __init__(self,
                 arguments_spec_list,
                 #*,
                 spec_node_parser_type,
                 macroname=_NotSpecified,
                 environmentname=_NotSpecified,
                 specials_chars=_NotSpecified,
                 make_arguments_parsing_state_delta=None,
                 make_body_parsing_state_delta=None,
                 make_after_parsing_state_delta=None,
                 make_body_parser=None,
                 finalize_node=None,
                 # also accepts `body_parsing_state_delta` as kwargs ->
                 **kwargs):

        self.arguments_spec_list = arguments_spec_list

        self.spec_node_parser_type = spec_node_parser_type
        if isinstance(spec_node_parser_type, str):
            self.spec_node_parser_type = _spec_node_parser_types[spec_node_parser_type]

        if macroname is not _NotSpecified:
            self.macroname = macroname
        if environmentname is not _NotSpecified:
            self.environmentname = environmentname
        if specials_chars is not _NotSpecified:
            self.specials_chars = specials_chars

        # Internal convention: if any of the _fn_*** attributes are set, they
        # should NOT be set to None.  They should simply not be set.  We're
        # testing for their presence with hasattr(self, '_fn_***').

        if make_arguments_parsing_state_delta is not None:
            self._fn_make_arguments_parsing_state_delta = make_arguments_parsing_state_delta
        if make_body_parsing_state_delta is not None:
            self._fn_make_body_parsing_state_delta = make_body_parsing_state_delta
        if make_after_parsing_state_delta is not None:
            self._fn_make_after_parsing_state_delta = make_after_parsing_state_delta
        if make_body_parser is not None:
            self._fn_make_body_parser = make_body_parser
        if finalize_node is not None:
            self._fn_finalize_node = finalize_node

        # note, the following might set self._fn_make_***_parsing_state_delta:
        use_legacy_args_parser = _legacy_pyltxenc2_do(
            'CallableSpec_init_from_args_parser', self, arguments_spec_list, kwargs
        )

        # for environments---
        # body_parsing_state_delta is the default delta object if no
        # "make_body_parsing_state_delta" function is provided or overridden
        body_parsing_state_delta = kwargs.pop('body_parsing_state_delta', None)

### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE
        self.is_math_mode = kwargs.pop('is_math_mode', None) # obsolete !
        if self.is_math_mode:
            if body_parsing_state_delta is None:
                body_parsing_state_delta = ParsingStateDeltaEnterMathMode()
            else:
                raise ValueError("You cannot specify both is_math_mode= and "
                                 "body_parsing_state_delta=")
### END_PYLATEXENC2_LEGACY_SUPPORT_CODE

        self.body_parsing_state_delta = body_parsing_state_delta

        super(CallableSpec, self).__init__(**kwargs)

        if not use_legacy_args_parser:
            # use self.arguments_spec_list, and not the arguments_spec_list
            # argument, because the pylatexenc 2 legacy support code above might
            # have set the former from an `args_parser='...'` argument
            if self.arguments_spec_list:
                self.arguments_parser = LatexArgumentsParser(self.arguments_spec_list)
            else:
                self.arguments_parser = LatexNoArgumentsParser()


    def get_node_parser(self, token, parsing_state):
        r"""
        Return a parser instance that is capable of parsing this node
        construct.

        This base class instantiates and returns an object of the type
        `spec_node_parser_type` that was specified to the constructor.  (This
        type is set to :py:class:`LatexMacroCallParser`,
        :py:class:`LatexEnvironmentCallParser`, or
        :py:class:`LatexSpecialsCallParser` by the corresponding subclasses
        :py:class:`MacroSpec`, :py:class:`EnvironmentSpec`, or
        :py:class:`SpecialsSpec`.)  The given type's constructor is assumed to
        accept to positional arguments to which the token object `token` and the
        present spec instance (`self`) are passed.
        """
        return self.spec_node_parser_type(token, self)

### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

    @property
    def args_parser(self):
        return self.arguments_parser

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE


    def finalize_node(self, node):
        r"""
        Called once the node representing this callable's invocation has been fully
        parsed, giving you a chance to inspect it, to attach further information
        to it, or to replace it by another node instance altogether.

        MUST RETURN the new node instance.

        The default implementation invokes the `finalize_node=` callable that
        was specified to the constructor, if any, and returns `node` unchanged
        otherwise.

        This is called from the LatexMacroCallParser instance, i.e., this
        function won't be called by default if you override get_node_parser()
        and return a different parser instance.
        """

        # Transcrypt doesn't seem to like getattr(obj, attrname, default) with
        # default arg, so use hasattr() test
        if hasattr(self, '_fn_finalize_node'): # and self._fn_finalize_node is not None:
            return self._fn_finalize_node(node)

        return node


    def make_arguments_parsing_state_delta(self, token, latex_walker):
        r"""
        If applicable, return a
        :py:class:`~pylatexenc.latexnodes.ParsingStateDelta` object describing
        how the parsing state should be changed in order to parse the arguments
        of this callable.  Return `None` to parse the arguments with the current
        parsing state.

        The `token` is the token instance that introduced this callable (e.g.
        the ``\mymacro`` macro token), and `latex_walker` is the latex walker
        instance that is parsing the code.

        The default implementation invokes the
        `make_arguments_parsing_state_delta=` callable that was specified to the
        constructor, if any, and returns `None` otherwise.

        Note that individual arguments can also request their own parsing state
        changes, see
        :py:attr:`~pylatexenc.latexnodes.LatexArgumentSpec.parsing_state_delta`.

        This method is called from the :py:class:`LatexMacroCallParser`
        instance, i.e., this function won't be called by default if you override
        :py:meth:`get_node_parser()` and return a different parser instance.
        """
        # Transcrypt doesn't seem to like getattr(obj, attrname, default) with
        # default arg, so use hasattr() test
        if (
                hasattr(self, '_fn_make_arguments_parsing_state_delta')
                #and self._fn_make_arguments_parsing_state_delta is not None
        ):
            return self._fn_make_arguments_parsing_state_delta(
                token=token,
                latex_walker=latex_walker
            )
        return None

    def make_body_parsing_state_delta(self,
                                      token,
                                      nodeargd,
                                      arg_parsing_state_delta,
                                      latex_walker):
        r"""
        If applicable, return a
        :py:class:`~pylatexenc.latexnodes.ParsingStateDelta` object describing
        how the parsing state should be changed in order to parse the body
        contents of this environment.  Return `None` to parse the body with the
        current parsing state.

        The `token` is the token instance that introduced this callable (e.g.
        the ``\begin{myenvironment}`` token), `nodeargd` is the
        :py:class:`~pylatexenc.latexnodes.ParsedArguments` instance with the
        arguments that were parsed for this callable, `arg_parsing_state_delta`
        is any parsing state delta that resulted from parsing those arguments,
        and `latex_walker` is the latex walker instance that is parsing the
        code.

        The default implementation invokes the
        `make_body_parsing_state_delta=` callable that was specified to the
        constructor, if any, and returns the `body_parsing_state_delta`
        attribute otherwise.

        This method only makes sense for LaTeX environments.  It's defined in
        the base class :py:class:`CallableSpec` for consistency with the other
        `make_**_parsing_state_delta()` methods.  This base class
        implementation, if no custom body parsing state delta function is set in
        the constructor, relies on `self.body_parsing_state_delta` being available!

        Note: `arg_parsing_state_delta` is always `None` (unless you actually
        went ahead and replaced the the `arguments_parser` attribute, which is a
        :py:class:`LatexArgumentsParser` or :py:class:`LatexNoArgumentsParser`
        instance, by a custom parser).
        """
        if (
                hasattr(self, '_fn_make_body_parsing_state_delta')
                #and self._fn_make_body_parsing_state_delta is not None
        ):
            return self._fn_make_body_parsing_state_delta(
                token=token,
                nodeargd=nodeargd,
                arg_parsing_state_delta=arg_parsing_state_delta,
                latex_walker=latex_walker,
            )

        # default implementation checks the body_parsing_state_delta attribute
        return self.body_parsing_state_delta


    def make_after_parsing_state_delta(self, parsed_node, latex_walker):
        r"""
        If applicable, create a
        :py:class:`~pylatexenc.latexnodes.ParsingStateDelta` class to convey any
        changes in the parsing state after completing this callable node.
        
        The default implementation returns `None`.  You may, but do not have to,
        override this method to customize its behavior.  You can specify a
        custom callable to `make_after_parsing_state_delta=...` in the
        constructor which will be invoked in this method.

        This method is called from the :py:class:`LatexMacroCallParser`
        instance, i.e., this function won't be called by default if you override
        :py:meth:`get_node_parser()` and return a different parser instance.
        """
        if (
                hasattr(self, '_fn_make_after_parsing_state_delta')
                #and self._fn_make_after_parsing_state_delta is not None
        ):
            return self._fn_make_after_parsing_state_delta(
                parsed_node=parsed_node,
                latex_walker=latex_walker,
            )
        return None


    def make_body_parser(self, token, nodeargd, arg_parsing_state_delta):
        r"""
        Return the parser instance that should be used to parse the body contents
        of this environment.

        The `token` is the ``\begin{environmentname}`` token instance that
        introduced the environment, `nodeargd` is the
        :py:class:`~pylatexenc.latexnodes.ParsedArguments` instance with the
        arguments that were parsed for this environment, and
        `arg_parsing_state_delta` is any parsing state delta that resulted from
        parsing those arguments.

        The default implementation invokes the `make_body_parser=` callable that
        was specified to the constructor, if any, and otherwise returns a
        :py:class:`LatexEnvironmentBodyContentsParser` instance for the
        environment name given by the token's argument.

        For environment specs only.  It's defined in the base class
        :py:class:`CallableSpec` alongside the other methods that customize how
        a callable's invocation is parsed.
        """
        if hasattr(self, '_fn_make_body_parser'): # and self._fn_make_body_parser is not None:
            return self._fn_make_body_parser(token, nodeargd, arg_parsing_state_delta)
        return LatexEnvironmentBodyContentsParser(
            environmentname=token.arg,
        )


    def __repr__(self):
        return (
            self.__class__.__name__ + "(" +
            ", ".join([
                "{}={!r}".format(k,v)
                for (k,v) in self.__dict__.items()
                if (not k.startswith("_")
                    and v is not None
                    and k not in ('spec_node_parser_type', ))
            ])
            + ")"
        )
    


class MacroSpec(CallableSpec):
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

       .. deprecated:: 3.0

           The `args_parser` attribute is deprecated since `pylatexenc 3.0`.  Macro,
           environment, and specials specification classes now return more general
           parsers meant to handle the entire macro/environment/specials invocation,
           not only their arguments, via the :meth:`get_node_parser()` method.

           You can still specify `args_parser=` to the constructor, along with
           the other `pylatexenc 2` argument `is_math_mode=`.  You cannot
           combine it, though, with any of the constructor arguments that were
           introduced in `pylatexenc 3`; doing so raises a `ValueError`.
    """
    def __init__(self, macroname, arguments_spec_list=None, **kwargs):
        super(MacroSpec, self).__init__(
            arguments_spec_list=arguments_spec_list,
            spec_node_parser_type=LatexMacroCallParser,
            macroname=macroname,
            **kwargs
        )




class EnvironmentSpec(CallableSpec):
    r"""
    Stores the specification of a LaTeX environment.

    This stores the environment name and instructions on how to parse any
    arguments provided after ``\begin{environment}<args>``.

    .. note::

       Starred variants of environments (as in ``\begin{equation*}``) must not
       be specified using an argspec as for macros (e.g., `argspec='*'`).
       Rather, we need to define a separate environment spec for the starred
       variant with the star in the name itself (``EnvironmentSpec('equation*',
       None)``) because the star really is part of the environment name.  If you
       happened to use ``EnvironmentSpec('equation', '*')``, then the parser
       would recognize the expression ``\begin{equation}*`` but not
       ``\begin{equation*}``.

    .. py:attribute:: environmentname

       The name of the environment, i.e., the argument of ``\begin{...}`` and
       ``\end{...}``.

    .. py:attribute:: body_parsing_state_delta

       The parsing state changes that are set in order to parse the body
       contents of the environment.


    .. py:attribute:: args_parser

       The parser instance that can understand this environment's arguments.
       For standard LaTeX environment this is usually a
       :py:class:`MacroStandardArgsParser` instance.

       If you specify a string, then for convenience this is interpreted as an
       argspec argument for :py:class:`MacroStandardArgsParser` and such an
       instance is automatically created.

       .. deprecated:: 3.0

           The `args_parser` attribute is deprecated since `pylatexenc 3.0`.  Macro,
           environment, and specials specification classes now return more general
           parsers meant to handle the entire macro/environment/specials invocation,
           not only their arguments, via the :meth:`get_node_parser()` method.

           You can still specify `args_parser=` to the constructor, along with
           the other `pylatexenc 2` argument `is_math_mode=`.  You cannot
           combine it, though, with any of the constructor arguments that were
           introduced in `pylatexenc 3`; doing so raises a `ValueError`.

    .. py:attribute:: is_math_mode

       Indicates if the contents is to be interpreted in Math Mode.  This would
       be `True` for environments like ``\begin{equation}``, ``\begin{align}``,
       etc., but is left to `None` for ``\begin{figure}``, etc.

       .. deprecated:: 3.0

          The field `is_math_mode` was deprecated in `pylatexenc 3` in favor of
          the field `body_parsing_state_delta`.  Instead of `is_math_mode=True`,
          use `body_parsing_state_delta=ParsingStateDeltaEnterMathMode()`.
    """
    def __init__(self, environmentname, arguments_spec_list=None, **kwargs):

        super(EnvironmentSpec, self).__init__(
            arguments_spec_list=arguments_spec_list,
            spec_node_parser_type=LatexEnvironmentCallParser,
            environmentname=environmentname,
            **kwargs
        )



class SpecialsSpec(CallableSpec):
    r"""
    Specification of a LaTeX "special char sequence": an active char, a
    ligature, or some other non-macro char sequence that has a special meaning.

    For instance, '&', '~', and '``' are considered as "specials".

    .. py:attribute:: specials_chars
    
       The string (one or several characters) that has a special meaning. E.g.,
       '&', '~', '``', etc.

    .. py:attribute:: args_parser
    
       A parser (e.g. :py:class:`MacroStandardArgsParser`) that is invoked when
       the specials is encountered.  Can/should be set to `None` if the specials
       should not parse any arguments (e.g. '~').

       .. deprecated:: 3.0

           The `args_parser` attribute is deprecated since `pylatexenc 3.0`.  Macro,
           environment, and specials specification classes now return more general
           parsers meant to handle the entire macro/environment/specials invocation,
           not only their arguments, via the :meth:`get_node_parser()` method.

           You can still specify `args_parser=` to the constructor, along with
           the other `pylatexenc 2` argument `is_math_mode=`.  You cannot
           combine it, though, with any of the constructor arguments that were
           introduced in `pylatexenc 3`; doing so raises a `ValueError`.
    """
    def __init__(self, specials_chars, arguments_spec_list=None, **kwargs):
        super(SpecialsSpec, self).__init__(
            arguments_spec_list=arguments_spec_list,
            spec_node_parser_type=LatexSpecialsCallParser,
            specials_chars=specials_chars,
            **kwargs
        )
        #self.specials_chars = specials_chars





### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

from ._argumentsparser import _LegacyPyltxenc2MacroArgsParserWrapper

from ..latexnodes import ParsingStateDeltaReplaceParsingState

from .. import _util

_legacy_pyltxenc2_do = \
    lambda what, *args: globals()['_legacy_pyltxenc2_'+what](*args)


# The options that were introduced in pylatexenc 3, along with the attribute
# that the spec class constructor sets for each of them.  None of them can be
# combined with the pylatexenc 2 style args_parser= option.  (The option
# arguments_spec_list= is checked separately, because the constructor always
# stores it, whether or not it was specified.)
_legacy_pyltxenc2_pylatexenc3_only_options = [
    ('make_arguments_parsing_state_delta', '_fn_make_arguments_parsing_state_delta'),
    ('make_body_parsing_state_delta', '_fn_make_body_parsing_state_delta'),
    ('make_after_parsing_state_delta', '_fn_make_after_parsing_state_delta'),
    ('make_body_parser', '_fn_make_body_parser'),
    ('finalize_node', '_fn_finalize_node'),
]


def _legacy_pyltxenc2_check_no_pylatexenc3_options(spec, kwargs):
    r"""
    Raise a `ValueError` if an option that was introduced in `pylatexenc 3` was
    specified in the same constructor call as the `pylatexenc 2` style
    `args_parser=` option.  Options of the two styles cannot be mixed.  The
    `pylatexenc 2` style options can of course still be used together, e.g.
    `args_parser=` along with `is_math_mode=`.
    """
    bad_option = None
    for optname, attrname in _legacy_pyltxenc2_pylatexenc3_only_options:
        if hasattr(spec, attrname):
            bad_option = optname
            break
    if bad_option is None and kwargs.get('body_parsing_state_delta', None) is not None:
        bad_option = 'body_parsing_state_delta'
    if bad_option is not None:
        raise ValueError(
            "You cannot specify both args_parser= (a pylatexenc 2 style option) and "
            "{}= (a pylatexenc 3 style option); options of the two styles cannot be "
            "combined in the same specification object".format(bad_option)
        )


def _legacy_pyltxenc2_warn_args_parser_option():
    r"""
    Emit the deprecation warning associated with the `pylatexenc 2` style
    `args_parser=` constructor option.  This is called exactly once per
    constructed specification object, and never while parsing.

    The `stacklevel` counts the frames that separate this call from the user's
    own code, namely: this function, the
    `_legacy_pyltxenc2_CallableSpec_init_from_args_parser()` function, the
    `_legacy_pyltxenc2_do()` dispatcher, `CallableSpec.__init__()`, and the
    `__init__()` of the specification subclass that the user instantiated
    (`MacroSpec`, `EnvironmentSpec` or `SpecialsSpec`).
    """
    _util.pylatexenc_deprecated_3(
        "The `args_parser=` option of the macro, environment and specials "
        "specification classes is obsolete since pylatexenc 3.  It'll still "
        "work, but please consider describing the arguments with the "
        "`arguments_spec_list=` option instead.",
        stacklevel=6
    )


def _legacy_pyltxenc2_CallableSpec_init_from_args_parser(spec, arguments_spec_list, kwargs):

    def _make_after_parsing_state_delta(parsed_node, spec=spec, **kwargs):
        new_parsing_state = getattr(parsed_node.nodeargd,
                                    '_legacy_pyltxenc2_new_parsing_state',
                                    None)
        return ParsingStateDeltaReplaceParsingState(set_parsing_state=new_parsing_state)

    def _make_body_parsing_state_delta(token, nodeargd, spec=spec, **kwargs):
        inner_parsing_state = getattr(nodeargd,
                                      '_legacy_pyltxenc2_inner_parsing_state_delta',
                                      None)
        if inner_parsing_state is None:
            # The legacy args parser didn't report any parsing state for the
            # environment body.  Use the spec's own body parsing state delta,
            # e.g. the one that is_math_mode=True set up.
            return spec.body_parsing_state_delta
        return ParsingStateDeltaReplaceParsingState(set_parsing_state=inner_parsing_state)

    def _init_with_legacy_wrapper(args_parser):
        logger.debug("Initializing spec with legacy args parser %r", args_parser)
        spec.arguments_spec_list = list(args_parser.argspec)
        spec.arguments_parser = _LegacyPyltxenc2MacroArgsParserWrapper(args_parser, spec)
        spec._fn_make_body_parsing_state_delta = _make_body_parsing_state_delta
        spec._fn_make_after_parsing_state_delta = _make_after_parsing_state_delta
        return True

    # remember whether the option was given at all, because `args_parser=None`
    # is a legitimate (and deprecated) pylatexenc 2 way of saying "no arguments"
    has_args_parser_option = ('args_parser' in kwargs)

    args_parser = kwargs.pop('args_parser', None)
    if args_parser is None:

        from ._pyltxenc2_argparsers import MacroStandardArgsParser
        if isinstance(arguments_spec_list, MacroStandardArgsParser):
            # a legacy args parser specified as the first positional argument;
            # this is pylatexenc 2 style, too
            _legacy_pyltxenc2_check_no_pylatexenc3_options(spec, kwargs)
            return _init_with_legacy_wrapper(arguments_spec_list)

        if has_args_parser_option:
            # `args_parser=None`; nothing to set up, but still warn about the
            # obsolete option itself
            _legacy_pyltxenc2_warn_args_parser_option()

        return False

    # legacy support
    if spec.arguments_spec_list is not None:
        raise ValueError("You cannot specify both arguments_spec_list= and args_parser=")

    _legacy_pyltxenc2_check_no_pylatexenc3_options(spec, kwargs)

    # only warn once the constructor arguments were found to be consistent, so
    # that an invalid combination reports its error without further noise
    _legacy_pyltxenc2_warn_args_parser_option()

    if isinstance(args_parser, str):
        spec.arguments_spec_list = args_parser
        spec.arguments_parser = LatexArgumentsParser(args_parser)
    else:
        return _init_with_legacy_wrapper(args_parser)

    return False



def _legacy_pyltxenc2_CallableSpec_parse_args(spec, w, pos, parsing_state=None):
    r"""
    .. deprecated:: 3.0

        This method is not recommented starting from `pylatexenc 3`.  You can
        use parser stored as the `arguments_parser` attribute instead.
    """

    token_reader = w.make_token_reader(pos=pos)

    parsed, parsing_state_delta = w.parse_content(
        spec.arguments_parser,
        token_reader=token_reader,
        parsing_state=parsing_state,
    )

    # pylatexenc 2 reported where the arguments started and how many characters
    # they span.  The parsed arguments object doesn't store those positions, so
    # we read where the parser stopped off of the token reader.
    len_ = token_reader.cur_pos() - pos

    if parsing_state_delta is not None:
        return parsed, pos, len_, parsing_state_delta._to_legacy_pyltxenc2_dict()

    return parsed, pos, len_

CallableSpec.parse_args = _legacy_pyltxenc2_CallableSpec_parse_args


### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
