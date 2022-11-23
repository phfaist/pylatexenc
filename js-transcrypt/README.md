# Building a Javascript version of pylatexenc.latexnodes library via *transcrypt*

You can use the fantastic [Transcrypt](http://www.transcrypt.org/) tool ([also
on github](https://github.com/QQuick/Transcrypt)) for converting parts of the
pylatexenc code base into JavaScript to make a JavaScript-based parser for
simple LaTeX code.

This procedure is very much still in alpha stage.  Don't rely too much on it!

To use commands listed here, make sure you installed the optional poetry
dependency group "buildjslib":

    > poetry install --with=buildjslib


## The build script

To generate the JS python sources simply run in this folder:

    # generates pylatexenc-js/
    > poetry run ./generate_pylatexenc_js.py
    
(Make sure you've removed the `pylatexenc-js` folder from any previous run, or
pass the `--delete-target-dir` option to the generator script.)

To compile the tests along with the library, in its own folder:

    # generates both pylatexenc-js/ and test-pylatexenc-js/
    > poetry run ./generate_pylatexenc_js.py --compile-tests

To run the tests using `node`, do:

    > node test-pylatexenc-js/runtests.js


## Steps handled by the build script

These are broadly the steps that the build script will apply.

### Preprocessing the pylatexenc library in preparation for transcrypt:

The script will first preprocess the pylatexenc source code to make it suitable
for use with transcrypt.  You can also do this manually with

    > export PYLATEXENC_SRC_DIR=/path/to/root/folder/of/pylatexenc/
    > export PREPROCESS_LIB_OUTPUT_DIR=pp-tmp/ # or some other temporary folder
    > poetry run python ../tools/preprocess_lib.py  preprocesslib-pylatexenc.config.yaml
    
### Run Transcrypt to generate the Javascript sources

We need to enable a lot of features in transcrypt, some of which are disabled by
default.  The build script basically follows the following commands.

Transcrypt is called with the `import_pylatexenc_modules.py` module as entry
point.  This python module simply imports the subset of the `pylatexenc` library
that we'll be compiling to JavaScript.  The command to run is essentially:

    > poetry run transcrypt import_pylatexenc_modules.py --dassert --dext --ecom --gen --tconv --sform --kwargs --keycheck --opov --xreex --nomin --build --anno --parent .none -u .auto -xp 'pp-tmp$libpatches' -od pylatexenc-js
    
The JavaScript files are output in the `pylatexenc-js` folder.

### Final touches

The build script will then apply some additional steps and patches:

- Create a `package.json` file that defines a module, so that you can import the
  sources using for instance:
  
      // js code
      import { Symbol1 [, ...] } from './pylatexenc-js/pylatexenc.latexnodes.js'

- Create a `py.js` module that exports the functions `$$kw` and `repr`, exposing
  the keyword-argument functionality as well as python's `repr()` function.
  You can pass keywords to transcrypted functions as follows:
  
      // js code
      call_function_from_transcrypt(arg1, arg2, $$kw({ keywordarg1: value1,
                                                       keywordarg2: value2 }))

- Patch Transcrypt's internal runtime methods to add some missing support for
  additional functionality (see `transcrypt_runtime_patches.js`)
  
