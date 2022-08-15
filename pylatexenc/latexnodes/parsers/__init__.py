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
Collection of Parser objects that can parse specific types of LaTeX
constructs.
"""

from ._base import LatexParserBase

from ._generalnodes import (
    LatexGeneralNodesParser,
    LatexSingleNodeParser,
)
from ._delimited import (
    LatexDelimitedExpressionParserInfo,
    LatexDelimitedExpressionParser,
    LatexDelimitedGroupParserInfo,
    LatexDelimitedGroupParser,
    LatexDelimitedExpressionParserOpeningDelimiterNotFound,
)
from ._math import (
    LatexMathParser,
)

from ._expression import (
    LatexExpressionParser,
)

from ._optionals import (
    LatexOptionalSquareBracketsParser,
    LatexOptionalCharsMarkerParser,
)

from ._stdarg import (
    LatexStandardArgumentParser,
    get_standard_argument_parser,
    LatexCharsCommaSeparatedListParser,
    LatexCharsGroupParser,
    LatexTackOnInformationFieldMacrosParser,
)


from ._verbatim import (
    LatexVerbatimBaseParser,
    LatexDelimitedVerbatimParser,
    LatexVerbatimEnvironmentContentsParser,
)
