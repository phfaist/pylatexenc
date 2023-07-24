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
.. versionadded:: 3.0

   The `latexnodes` module was introduced in `pylatexenc` 3.

"""


from ._exctypes import *

from ._token import LatexToken

from ._nodescollector import (
    LatexNodesCollector
)

from ._parsingstate import (
    ParsingState
)

from ._parsingstatedelta import (
    ParsingStateDelta,
    ParsingStateDeltaReplaceParsingState,
    ParsingStateDeltaChained,
    ParsingStateDeltaWalkerEvent,
    ParsingStateDeltaEnterMathMode,
    ParsingStateDeltaLeaveMathMode,
    get_updated_parsing_state_from_delta,
)
from ._parsedargs import (
    LatexArgumentSpec,
    ParsedArguments,
)

from ._tokenreaderbase import (
    LatexTokenReaderBase,
    LatexTokenListTokenReader,
)
from ._tokenreader import (
    LatexTokenReader,
)

from ._callablespecbase import (
    CallableSpecBase
)

from ._walkerbase import (
    LatexWalkerParsingStateEventHandler,
    LatexWalkerBase,
)

from ._latexcontextdbbase import (
    LatexContextDbBase
)

from ._parsedargsinfo import (
    ParsedArgumentsInfo,
    SingleParsedArgumentInfo,
)

