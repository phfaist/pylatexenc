import unittest
import sys
import logging



from pylatexenc.macrospec._argumentsparser import (
    LatexArgumentSpec,
    LatexNoArgumentsParser,
    LatexArgumentsParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerTokenParseError,
    LatexToken,
    ParsingState
)



class TestLatexArgumentsParser(unittest.TestCase):

    # ............. TODO, need to write good tests .................

    
    pass



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
