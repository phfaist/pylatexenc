import re
import sys
import os
import os.path
import json

import subprocess

import logging
logger = logging.getLogger(__name__)


default_transcrypt_options = (
    '--dassert --dext --gen --tconv --sform --kwargs --keycheck --xreex '
    '--opov ' # let's hope we can get away w/o this one sometime in the future....
    '--nomin --build --anno --parent .none -u .auto'.split()
)


class GenUtils:
    def __init__(self, *, pylatexenc_src_dir, preprocess_lib_output_dir, env=None):
        super().__init__()

        self.python = sys.executable

        self.transcrypt_options = list(default_transcrypt_options)

        self.preprocess_lib_output_dir = preprocess_lib_output_dir

        if pylatexenc_src_dir is None:
            pylatexenc_src_dir = os.path.normpath(
                os.path.join(os.getcwd(), '..', os.path.dirname(__file__))
            )
        self.setpaths(pylatexenc_src_dir)

        self.env = env
        if self.env is None:
            self.env = {}


    def setpaths(self, pylatexenc_src_dir):
        self.pylatexenc_src_dir = pylatexenc_src_dir

        self.preprocess_lib_py = os.path.join(
            self.pylatexenc_src_dir, 'tools', 'preprocess_lib.py'
        )

        self.pylatexenc_js_transcrypt_dir = \
            os.path.join(self.pylatexenc_src_dir, 'js-transcrypt')

        self.libpatches_dir = \
            os.path.join(self.pylatexenc_js_transcrypt_dir, 'libpatches')

        self.transcrypt_runtime_patches_file = \
            os.path.join(self.pylatexenc_js_transcrypt_dir, 'transcrypt_runtime_patches.js' )



    def run_cmd(self, cmd, *, add_env=None):

        env = dict(self.env, PYLATEXENC_SRC_DIR=self.pylatexenc_src_dir)

        if add_env:
            env.update(add_env)

        logger.info(f"Running {cmd}")
        subprocess.run(cmd, env=env, check=True, stdout=None, stderr=None,)


    def preprocess_pylatexenc_lib(self, *, preprocess_lib_output_dir=None, config_yaml=None):

        if preprocess_lib_output_dir is None:
            preprocess_lib_output_dir = self.preprocess_lib_output_dir

        if config_yaml is None:
            config_yaml = os.path.join(self.pylatexenc_js_transcrypt_dir,
                                       'preprocesslib-pylatexenc.config.yaml')

        self.preprocess_lib(config_yaml, preprocess_lib_output_dir=preprocess_lib_output_dir)
        

    def preprocess_lib(self, config_yaml, *, preprocess_lib_output_dir=None, add_env=None):

        if preprocess_lib_output_dir is None:
            preprocess_lib_output_dir = self.preprocess_lib_output_dir

        do_add_env = {}
        if preprocess_lib_output_dir is not None:
            do_add_env['PREPROCESS_LIB_OUTPUT_DIR'] = preprocess_lib_output_dir
        if add_env:
            do_add_env.update(add_env)

        self.run_cmd([self.python, self.preprocess_lib_py, config_yaml],
                     add_env=do_add_env)


    def run_transcrypt(self, source, *, output_dir,
                       add_import_paths=None, add_transcrypt_options=None):

        #
        # get the import path list
        #
        all_import_paths = []
        if add_import_paths:
            all_import_paths += add_import_paths
        if self.preprocess_lib_output_dir is not None:
            all_import_paths.append(self.preprocess_lib_output_dir)
        if self.libpatches_dir:
            all_import_paths.append(self.libpatches_dir)
        # combine with '$' separator, see transcrypt --help
        import_path_arg = "$".join(all_import_paths)

        transcrypt_options = list(self.transcrypt_options)
        if add_transcrypt_options:
            transcrypt_options += add_transcript_options

        self.run_cmd([
            self.python, '-m', 'transcrypt',
            source,
            *transcrypt_options,
            '-xp', import_path_arg,
            # abspath() because otherwise the output is interpreted relative to
            # the source script
            '-od', os.path.abspath(output_dir),
        ])
        
    def finalize_transcrypt_package(
            self,
            output_dir,
            *,
            package_name,
            package_version='0.0.1',
            package_description='Some automatically Transcrypt-ed sources',
            package_info_dict=None,
            create_py_js=True,
            js_patches=True,
            js_transcrypt_runtime_add_code=None,
    ):

        #
        # Create package.json
        #
        logger.info(f"Creating package.json ...")
        pkginfo = {
            'name': package_name,
            'type': 'module',
            'version': package_version,
            'description': package_description,
        }
        if package_info_dict:
            pkginfo.update(package_info_dict)

        with open( os.path.join(output_dir, 'package.json'), 'w' ) as fw:
            json.dump(pkginfo, fw)

        if create_py_js:
            #
            # Simple interface for some python constructs that can be exposed to any
            # code that imports this library.  E.g., to specify kwargs as " $$kw({
            # arg1: value1 ...}) "
            #
            logger.info(f"Installing shortcuts to python runtime tricks ...")
            with open( os.path.join(output_dir, 'py.js'), 'w' ) as fw:
                fw.write(r"""
import {__kwargtrans__, repr} from "./org.transcrypt.__runtime__.js";
const $$kw = __kwargtrans__;
export { $$kw, repr };
""")

        if js_patches:
            logger.info(f"Applying some patches to Transcrypt's JS runtime ...")

            with open( self.transcrypt_runtime_patches_file ) as f:
                patches_code = f.read()
                
            runtimejs_fname = os.path.join(output_dir, 'org.transcrypt.__runtime__.js')
            with open( runtimejs_fname ) as f:
                runtimejs = f.read()

            # apply our base JS patches
            runtimejs += "\n\n"

            # apply our additional JS patches
            runtimejs += "\n\n" + patches_code

            with open( runtimejs_fname, 'w' ) as f:
                f.write(runtimejs)



    def generate_runtests_script(self, test_dir, *, script_file_name=None,
                                 test_file_patterns=['test_.*']):

        if script_file_name is None:
            script_file_name = 'runtests.py'
            if self.preprocess_lib_output_dir is not None:
                script_file_name = \
                    os.path.join(self.preprocess_lib_output_dir, script_file_name)

        logger.info(f"Creating test runner script ...")
        with open( script_file_name, 'w' ) as fw:
            fw.write(r"""
import logging
logging.basicConfig(level=logging.DEBUG)

import unittest
""")
            testmodnames = []
            for testpyname in os.listdir(test_dir):
                m = re.match('^(?P<testmodname>'
                             + '|'.join(test_file_patterns)
                             + r')[.]py$', testpyname)
                if m is not None:
                    testmodnames.append( m.group('testmodname') )
            
            fw.write("\n".join([ f"import {mod}" for mod in testmodnames ]) + "\n")
            fw.write(r"""my_test_modules = [ """ + "\n".join([
                f"{x}, " for x in testmodnames
            ]) + " ]\n")
            fw.write(r"""

print("About to run all tests...")

unittest.do_run_test_modules(my_test_modules)

print("Done! All tests succeeded.")
""")

        return script_file_name
