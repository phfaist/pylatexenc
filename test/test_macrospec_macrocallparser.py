import unittest
import sys
import logging



from pylatexenc.macrospec._macrocallparser import (
    LatexMacroCallParser,
    LatexEnvironmentCallParser,
    LatexSpecialsCallParser,
)

from pylatexenc.latexnodes import (
    ParsingState
)
from pylatexenc.latexnodes.nodes import *



class TestLatexMacroCallParser(unittest.TestCase):

    # ............. TODO, need to write good tests .................

    
    pass



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
