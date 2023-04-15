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


class LatexContextDbBase(object):
    r"""
    Base class for a parsing state's LaTeX context database.

    A full implementation of how to specify macro, environment, and specials
    definitions are actually in the :py:mod:`pylatexenc.macrospec` module.  As
    far as this :py:mod:`latexnodes` is concerned, a latex context database
    object is simply an object that provides the :py:meth:`get_***_spec()`
    family of methods along with :py:meth:`test_for_specials()`, and they return
    relevant spec objects.

    The spec objects returned by :py:meth:`get_***_spec()` and
    :py:meth:`test_for_specials()` are subclasses of
    :py:class:`CallableSpecBase`.


    .. versionadded:: 3.0
    
       The :py:class:`LatexContextDbBase` class was added in `pylatexenc 3.0`.
    """

    def get_macro_spec(self, macroname):
        r"""
        Return the macro spec to use to parse a macro named `macroname`.  The
        `macroname` does not contain the escape character (``\``) itself.

        This method should return the relevant spec object, which should be an
        instance of a subclass of :py:class:`CallableSpecBase`.

        The latex context database object may choose to provide a default spec
        object if `macroname` wasn't formally defined.  As far as the parsers
        are concerned, if `get_macro_spec()` returns a spec object, then the
        parsers know how to parse the given macro and will happily proceed.

        If a macro of name `macroname` should not be considered as defined, and
        the parser should not attempt to parse a macro and raise an error
        instead (or recover from it in tolerant parsing mode), then this method
        should return `None`.
        """
        return None

    def get_environment_spec(self, environmentname):
        r"""
        Like :py:meth:`get_macro_spec()`, but for environments.  The
        `environmentname` is the name of the environment specified between the
        curly braces after the ``\begin`` call.

        This method should return the relevant spec object, which should be an
        instance of a subclass of :py:class:`CallableSpecBase`.

        The latex context database object may choose to provide a default spec
        object if an environment named `environmentname` wasn't somehow formally
        defined.  As far as the parsers are concerned, if
        `get_environment_spec()` returns a spec object, then the parsers know
        how to parse the given environment and will happily proceed.

        If an environment of name `environmentname` should not be considered as
        defined, and the parser should not attempt to parse the environment and
        raise an error instead (or recover from it in tolerant parsing mode),
        then this method should return `None`.
        """
        return None

    def get_specials_spec(self, specials_chars):
        r"""
        Like :py:meth:`get_macro_spec()`, but for specials.  The `specials_chars` is
        the sequence of characters for which we'd like to find if they are a
        specials construct.

        Parsing of specials is different from macros and environments, because
        there is no universal syntax that distinguishes them (macros and
        environments are always initiated with the escape character ``\``).  So
        the token reader will call :py:meth:`test_for_specials()` to see if the
        string at the given position can be matched for specials.

        The result is that :py:meth:`get_specials_spec()` usually doesn't get
        called when parsing tokens.  The :py:meth:`get_specials_spec()` method
        is only called in certain specific situations, such as to get the spec
        object associated with the new paragraph token ``\n\n``.

        This method should return the relevant spec object, which should be an
        instance of a subclass of :py:class:`CallableSpecBase`, or `None` if
        these characters are not to be considered as specials.
        """
        return None

    def test_for_specials(self, s, pos, parsing_state):
        r"""
        Test the string `s` at position `pos` for the presence of specials.

        For instance, if the parser tests the string ``"Eq.~\eqref{eq:xyz}"`` at
        position 3, then the latex context database might want to report the
        character ``~`` as a specials construct and return a specials spec for
        it.

        If specials characters are recognized, then this method should return a
        corresponding spec object.  The spec object should be an instance of a
        :py:class:`CallableSpecBase` subclass.  In addition, the returned spec
        object must expose the attribute :py:attr:`specials_chars`.  That
        attribute should contain the sequence of characters that were recognized
        as special.

        If no specials characters are recongized at exactly the position `pos`,
        then this method should return `None`.
        """
        return None
