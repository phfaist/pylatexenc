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


## Generate the JS pylatexenc subset library

We need to enable a lot of features in transcrypt, some of which are disabled by
default.  Follow the following commands.


We'll direct *transcrypt* to the `import_pylatexenc_modules.py` module, which
simply imports the subset of the `pylatexenc` library that we'll be compiling to
JavaScript.  Run:

    > poetry run transcrypt import_pylatexenc_modules.py --dassert --dext --gen --tconv --sform --kwargs --keycheck --opov --xreex --nomin --build --anno --parent .none -xp 'libpatches' -od pylatexenc-js
    > cp pylatexenc-js-package.json pylatexenc-js/package.json
    
The JavaScript files are output in the `pylatexenc-js` folder.  Now you can try:

Test run with:

    > cd mytestjscode
    > node my_test_js_code.js
    


## Compile a single Python script with transcrypt along with pylatexenc dependencies

Try:

    > poetry run transcrypt my_test_script.py --dassert --dext --gen --tconv --sform --kwargs --keycheck --opov --xreex --nomin --build --anno --parent .none -xp 'libpatches' -od target_js_output
    > echo '{"type":"module"}' >target_js_output/package.json
    
Test run with:

    > node target_js_output/my_test_script.js
    

## Example build tests runner

First need to preprocess the tests as well as the lib:

    > poetry run python ../preprocess_lib.py  preprocesslib_tests.config.yaml
    
Then we need to transcrypt the main `runtests` test runner script:

    > poetry run transcrypt runtests.py --dassert --dext --gen --tconv --sform --kwargs --keycheck --opov --xreex --nomin --build --anno --parent .none -xp 'libpatches$test' -od 'tests_js_output'
    > echo '{"type":"module"}' >tests_js_output/package.json

Then try to run the tests with:

    > node tests_js_output/runtests.js
