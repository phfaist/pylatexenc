# Building a Javascript version of pylatexenc.latexnodes library via *transcrypt*

You can use the fantastic [transcrypt](http://www.transcrypt.org/) tool ([also
on github](https://github.com/QQuick/Transcrypt)) for converting parts of the
pylatexenc code base into JavaScript to make a JavaScript-based parser for
simple LaTeX code.

This procedure is very much still in alpha stage.  Don't rely on it!


To use commands listed here, make sure you installed the optional poetry extras
"buildjslib":

    > poetry install -E buildjslib


## Preprocessing the pylatexenc library in preparation for transcrypt:

We first need to preprocess the pylatexenc source code to make it suitable for
use with transcrypt.

    > poetry run python ../preprocess_lib.py  preprocesslib.config.yaml
    
We can also run a few tests to see that the preprocessed lib works as intended:

    > PYTHONPATH


## Example build with transcrypt command

Note that we need to enable a lot of features in transcrypt, some of which are
disabled by default.  Here's an example compilation line that will convert the
script called `my_test_script.py`, along with the relevant `pylatexenc` modules,
into a folder named `__target__`:

    > poetry run transcrypt my_test_script.py --dassert --dext --gen --tconv --sform --kwargs --keycheck --opov --xreex --nomin --build --anno --parent .none -xp 'libpatches' -od 'target_js_output'
    > echo '{"type":"module"}' >>target_js_output/package.json
    
Test run with:

    > node target_js_output/my_test_script.js
    



## Example build tests runner

First need to preprocess the tests as well as the lib:

    > poetry run python ../preprocess_lib.py  preprocesslib_tests.config.yaml
    
Then we need to transcrypt the main `runtests` test runner script:

    > poetry run transcrypt runtests.py --dassert --dext --gen --tconv --sform --kwargs --keycheck --opov --xreex --nomin --build --anno --parent .none -xp 'libpatches$test' -od 'tests_js_output'
    > echo '{"type":"module"}' >>tests_js_output/package.json

Then try to run the tests with:

    > node tests_js_output/runtests.js
