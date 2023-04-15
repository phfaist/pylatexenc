import unittest

import logging
logging.basicConfig(level=logging.DEBUG)


import customjspatches
customjspatches.custom_apply_patches()




# a selection of tests to run -->

import test_latexnodes_nodes
import test_latexnodes_nodescollector
import test_latexnodes_parsedargsinfo
import test_latexnodes_parsers_delimited
import test_latexnodes_parsers_generalnodes
import test_latexnodes_parsers_math
import test_latexnodes_parsers_stdarg
import test_latexnodes_parsers_verbatim
import test_latexnodes_tokenreader
import test_latexnodes_tokenreaderbase



my_test_modules = [
    test_latexnodes_nodes,
    test_latexnodes_nodescollector,
    test_latexnodes_parsedargsinfo,
    test_latexnodes_parsers_delimited,
    test_latexnodes_parsers_generalnodes,
    test_latexnodes_parsers_math,
    test_latexnodes_parsers_stdarg,
    test_latexnodes_parsers_verbatim,
    test_latexnodes_tokenreader,
    test_latexnodes_tokenreaderbase,
]



print("Instantiating tests...")

my_test_classes = []

for module in my_test_modules:
    for membername in dir(module):
        if membername.startswith('Test'):
            cls = getattr(module, membername)
            #print("Class is ", cls.__name__)
            instance = cls()
            #print("Instance is ", instance)
            my_test_classes.append( [membername, instance] )


print("About to run all tests...")


unittest.do_run(my_test_classes)

