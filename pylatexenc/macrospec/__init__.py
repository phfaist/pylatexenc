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

r"""
Provides classes and helper functions to describe a LaTeX context of known
macros and environments, specifying how they should be parsed by
:py:mod:`pylatexenc.latexwalker`.

.. versionadded:: 2.0

   The entire module :py:mod:`pylatexenc.macrospec` was introduced in
   `pylatexenc 2.0`.
"""


from ._specclasses import (
    CallableSpec,
    MacroSpec,
    EnvironmentSpec,
    SpecialsSpec,
)

### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE
from ._spechelpers import std_macro, std_environment, std_specials
### END_PYLATEXENC2_LEGACY_SUPPORT_CODE


from ._latexcontextdb import (
    LatexContextDb,
    ParsingStateDeltaExtendLatexContextDb,
)

from ._argumentsparser import (
    LatexArgumentsParser,
    LatexNoArgumentsParser,
)

from ._environmentbodyparser import (
    LatexEnvironmentBodyContentsParserInfo,
    LatexEnvironmentBodyContentsParser
)

from ._macrocallparser import (
    LatexMacroCallParser,
    LatexEnvironmentCallParser,
    LatexSpecialsCallParser
)


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE
from ..latexnodes import ParsedArguments as ParsedMacroArgs
from ._pyltxenc2_argparsers import (
    MacroStandardArgsParser,
    ParsedVerbatimArgs,
    VerbatimArgsParser,
    ParsedLstListingArgs,
    LstListingArgsParser,
)
### END_PYLATEXENC2_LEGACY_SUPPORT_CODE

