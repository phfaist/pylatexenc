import os
import os.path
import re
import sys
import argparse
import json

import shutil
import subprocess

import logging
logger = logging.getLogger('generate_pylatexenc_js')

pylatexenc_src_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

def run_main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--pylatexenc-js-output-dir', action='store',
                        default='pylatexenc-js',
                        help="Folder where to output generated JavaScript pylatexenc sources")

    parser.add_argument('--delete-target-dir', action='store_true', default=False,
                        help="With this option, the target directory is removed if it exists "
                        "at the beginning of the script instead of throwing an error.  Will "
                        "also remove the tests target directory if --compile-tests is given.")

    parser.add_argument('--preprocess-lib-output-dir', action='store', default='pp-tmp',
                        help="Temporary folder in which to write intermediate, "
                        "preprocessed sources to be fed into Transcrypt")

    parser.add_argument('--compile-tests', action='store_true', default=False,
                        help="Also compile the pylatexenc tests into a separate "
                        "folder (by default ./test-pylatexenc-js)")

    parser.add_argument('--test-pylatexenc-js-output-dir', action='store',
                        default='test-pylatexenc-js',
                        help="Folder where to output generated JavaScript pylatexenc "
                        "test sources. "
                        "The main entry point for the tests will be the script 'runtests.js'")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    if args.delete_target_dir:
        if os.path.exists(args.pylatexenc_js_output_dir):
            shutil.rmtree(args.pylatexenc_js_output_dir)
        if args.compile_tests:
            if os.path.exists(args.test_pylatexenc_js_output_dir):
                shutil.rmtree(args.test_pylatexenc_js_output_dir)

    os.makedirs(args.preprocess_lib_output_dir, exist_ok=True)

    if os.path.exists(args.pylatexenc_js_output_dir):
        raise RuntimeError(
            f"Target destination ‘{args.pylatexenc_js_output_dir}’ already exists. "
            f"Please remove it first."
        )

    # pick up pylatexenc's generation script tool

    pylatexenc_tools_dir = os.path.join(pylatexenc_src_dir, 'tools')
    logger.info(f"Using pylatexenc_tools_dir = {pylatexenc_tools_dir!r}")
    sys.path.insert(0, pylatexenc_tools_dir)

    import utils_transcrypt_generate_js

    genutils = utils_transcrypt_generate_js.GenUtils(
        pylatexenc_src_dir=pylatexenc_src_dir,
        preprocess_lib_output_dir=args.preprocess_lib_output_dir,
    )

    # preprocess both pylatexenc & pylatexenc libraries to prepare them for Transcrypt -->
    genutils.preprocess_pylatexenc_lib()
    if args.compile_tests:
        genutils.preprocess_lib('preprocesslib-tests.config.yaml')

    # run Transcrypt pylatexenc lib now -->
    genutils.run_transcrypt(
        'import_pylatexenc_modules.py',
        output_dir=args.pylatexenc_js_output_dir,
    )
    # final tweaks to finalize the JS package
    genutils.finalize_transcrypt_package(
        args.pylatexenc_js_output_dir,
        package_name='pylatexenc-js',
        package_version='0.0.1',
        package_description=\
            'Automatically transliterated Javascript version of the pylatexenc sources'
    )


    if args.compile_tests:

        # Generate the test runner script
        runtests_py = genutils.generate_runtests_script(
            os.path.join(pylatexenc_src_dir, 'test'),
            test_file_patterns=[
                # these are regexes that are matched as ^( <...> )[.]py$
                'test_latexnodes_.*',
                'test_macrospec_.*',
                'test_latexwalker_.*',
                'test_util',
            ]
        )

        # Transcrypt it
        genutils.run_transcrypt(
            runtests_py,
            add_import_paths=[
                os.path.join(args.preprocess_lib_output_dir, 'test')
            ],
            output_dir=args.test_pylatexenc_js_output_dir,
        )
        genutils.finalize_transcrypt_package(
            args.test_pylatexenc_js_output_dir,
            package_name='test-pylatexenc-js',
        )

        logger.info("Compiled the tests. To run them, try ‘node {}/runtests.js’"
                    .format(args.test_pylatexenc_js_output_dir))

    logger.info(f"Done!")







if __name__ == '__main__':
    run_main()
