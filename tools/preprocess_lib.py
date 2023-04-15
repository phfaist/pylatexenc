import re
import os
import os.path
import sys

import logging
logger = logging.getLogger(__name__)

import glob
import argparse

import yaml


default_source_dir = os.path.join(os.path.dirname(__file__), '..')

# see js-transcrypt/preprocesslib.config.yaml for an example YAML config


# ------------------------------------------------------------------------------


_rx_guards = re.compile(
    r"""
    #
    # guard begin instruction, on its own line
    #
    ^\#\#\#\s*BEGIN_(?P<guard_name>[A-Za-z0-9_]+)[ \t]*\n

    #
    # contents. look at lines one by one, making sure they do not
    # start with ### (BEGIN|END)
    #
    (?P<contents>
      (^
        (?!\#\#\#).*
      \n) *
    )

    #
    # guard end instruction, on its own line
    #
    ^\#\#\#\s*END_(?P=guard_name)[ \t]*$
    """
    ,
    flags=re.MULTILINE | re.VERBOSE
)
_rx_patches = re.compile(
    r"""
    #
    # guard begin instruction, on its own line
    #
    ^\#\#\#\s*BEGINPATCH_(?P<patch_name>[A-Za-z0-9_]+)[ \t]*\n

    #
    # contents. look at lines one by one, making sure they do not
    # start with ### (BEGIN|END)
    #
    (?P<contents>
      (^
        (?!\#\#\#).*
      \n) *
    )

    #
    # guard end instruction, on its own line
    #
    ^\#\#\#\s*ENDPATCH_(?P=patch_name)[ \t]*$
    """
    ,
    flags=re.MULTILINE | re.VERBOSE
)



# ------------------------------------------------------------------------------


_rx_from_import = re.compile(
    r"""
    ^                                   # beginning of a line
    from
    \s+
    (?P<pkg_where>[a-zA-Z0-9_.]+)       # package path
    \s+
    import
    (?P<import_targets>
      (?P<import_targets_no_parens>
        \s+
        (?P<import_name>[A-Za-z0-9_*]+) # main imported module
        (?:
          [ \t]+ as [ \t]+
          (?P<import_as>[A-Za-z0-9_]+)  # alias import name
        )?
        (?:
          (?:[ \t]*$)
          |
          (?P<more_import_names>        # end of import stmt, or more stuff
            [,\s]+
            (.*\\\n)*                   # contents with backslash at end of line
            (.*[^\\]$)                  # line not ending with a backslash
          )
        )
      )
      |
      (?P<import_targets_with_parens>
        \s*\(
          (?:[A-Za-z0-9_,\s\n]+        # names, commas, whitespace, newlines
            |  [#].*$ )+                # or comments
        \)
        [ \t]*$
      )
    )
    """,
    flags=re.MULTILINE | re.VERBOSE
)


_rx_import = re.compile(
    r"""
    ^
    import
    [ \t]+
    (?P<pkg_name>[a-zA-Z0-9_.]+)        # package name
    [ \t]*
    $
    """,
    flags=re.MULTILINE | re.VERBOSE
)


# remove arguments to super() calls
_rx_super_with_args = re.compile(
    r"""
    super\s*
    \(
      \s*
      (?P<clsname> [A-Za-z0-9_.]+ )
      \s*
      ,
      \s*
      (?P<self> self )
      \s*
    \)
    """,
    flags=re.MULTILINE | re.VERBOSE
)


_rx_construct_dict_with_generator = re.compile(
    r"""
    \b
    dict\b
    \(
    (?P<contents>
      [^\[\n]+
      \s+for\s+
      .*
    )
    \)
    """,
    re.MULTILINE | re.VERBOSE
)


_rx_frozenset = re.compile(
    r"""\b
    frozenset
    \b""",
    re.MULTILINE | re.VERBOSE
)



_rx_logger_debug = re.compile(
    r"""
    # initial line indent
    ^
    (?P<orig_indent>[ \t]*)

    # "logger.debug("
    logger \s* [.] \s* debug \s* \(

    # up till the end of the line
    .*$

    # include any number of lines that are indented by more than the initial
    # line
    (
      \n
      (?P=orig_indent)[ \t]+
      .*
      $
    )*

    # possibly include a single line that is indented like the original line, as
    # long as it only contains closing parentheses or stuff like that
    (
      \n
      (?P=orig_indent)
      [\)\]\}, \t]*
      $
    )?
    """,
    re.MULTILINE | re.VERBOSE
)
# horrible heuristic


# ------------------------------------------------------------------------------


_rx_initial_or_nl_indent = re.compile( r'(?P<newline>^|\n)(?P<indent>[ \t]*)' )

def _comment_out_text(text, *, place_expression=None):
    def subfn(m):
        if not m.group('newline') and place_expression:
            # initial indent & we want to place a custom statement (e.g. "pass")
            return (
                m.group('indent') + place_expression + '\n'
                + m.group('indent') + '###> '
            )
        return m.group('newline') + m.group('indent') + '###> '
    text2 = _rx_initial_or_nl_indent.sub(subfn, text)
    if not text2.endswith('\n'):
        text2 += '\n'
    return text2

def _comment_out_match(m, **kwargs):
    return _comment_out_text(m.group(), **kwargs)

def _comment_out_text_full_lines(text):
    return '###> ' + text.replace('\n', '\n###> ') + '\n'

def _comment_out_match_full_lines(m, **kwargs):
    return _comment_out_text_full_lines(m.group(), **kwargs)



class _Module:
    mod_path = []
    mod_name = None
    source_content = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Preprocess:

    def __init__(self, source_dir, target_dir, module_list,
                 enabled_features, skip_relative_import_prefixes=None):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.enabled_features = enabled_features
        self.module_list = module_list
        if not skip_relative_import_prefixes:
            skip_relative_import_prefixes = []
        self.skip_relative_import_prefixes = skip_relative_import_prefixes

        # expand user and environment variables
        self.source_dir = os.path.expandvars(os.path.expanduser( self.source_dir ))
        self.target_dir = os.path.expandvars(os.path.expanduser( self.target_dir ))

        # process and glob patterns in module_list
        new_module_list = []
        for m in module_list:
            if not ('*' in m or '?' in m):
                new_module_list.append(m)
                continue
            # process pattern
            fn_pattern = m.replace('.', '/') + '.py'
            try:
                mycwd = os.getcwd()
                os.chdir(self.source_dir)
                matches = glob.glob( fn_pattern )
            finally:
                os.chdir(mycwd)
            for mm in matches:
                assert mm.endswith('.py')
                mm = mm[:-3]
                new_module_list.append( mm.replace('/', '.') )

        logging.info(f"Final module list is {new_module_list}")

        self.modules_to_preprocess = set(new_module_list)
        self.modules_preprocessed = set()

        #self.preprocess()

    def preprocess(self):

        os.makedirs(self.target_dir, exist_ok=True)

        while True:

            need_to_preprocess = ( self.modules_to_preprocess - self.modules_preprocessed )

            # logger.debug(f"{self.modules_to_preprocess=}\n{self.modules_preprocessed=}\n"
            #              f" --> {need_to_preprocess}")

            if not len(need_to_preprocess):
                # done!
                return

            # pick a module to preprocess among the remaining ones
            mod_dotname = need_to_preprocess.pop()
            mod_dotpath = mod_dotname.split('.')

            if os.path.isdir( os.path.join(self.source_dir, * mod_dotpath) ):
                mod_path, mod_name = mod_dotpath, "__init__"
            else:
                mod_path, mod_name = mod_dotpath[:-1], mod_dotpath[-1]

            rel_mod_fname = os.path.join(*mod_path, mod_name+'.py')

            with open( os.path.join(self.source_dir, rel_mod_fname), 'r' ) as f:
                source_content = f.read()

            mod = _Module(mod_path=mod_path,
                          mod_name=mod_name,
                          source_content=source_content)

            logger.info(f"Processing ‘{mod_dotname}’ ...")

            # preprocess the module.
            self.preprocess_module(mod)

            # write the module in output dir.
            ofname = os.path.join(self.target_dir, rel_mod_fname)
            #logger.info(f"*** Once I'm confident enough, I'll output to file {ofname} ***")
            os.makedirs( os.path.join(self.target_dir, *mod_path), exist_ok=True )
            with open( ofname, 'w' ) as fw:
                fw.write(mod.source_content)

            logger.info(f"Processed ‘{mod_dotname}’")
            self.modules_preprocessed.add( mod_dotname )




    def preprocess_module(self, mod):

        self.process_add_comment_header(mod)
        self.process_guards(mod)
        self.process_patches(mod)
        self.process_imports(mod)
        self.process_super(mod)
        self.process_dict_generator(mod)
        self.process_frozenset(mod)
        self.process_logger_debug(mod)

    def process_add_comment_header(self, mod):
        mod.source_content = (
            """\
############################################################
### THE CONTENTS OF THIS MODULE WAS PROCESSED USING A    ###
### CUSTOM SCRIPT `preprocess_lib.py`.  THIS IS NOT THE  ###
### ORIGINAL MODULE SOURCE.  DON'T EDIT!                 ###
############################################################
"""
            + mod.source_content
        )

    def process_guards(self, mod):

        enabled_guards = self.enabled_features.get('guards', {})

        def _process_guard(m):
            if enabled_guards.get(m.group('guard_name'), True):
                return m.group() # no change, guard is enabled
            return _comment_out_match_full_lines(m)

        mod.source_content = _rx_guards.sub(_process_guard, mod.source_content)


    def process_patches(self, mod):

        enabled_patches = self.enabled_features.get('patches', {})

        def _process_patch(m):
            patch_name = m.group('patch_name')
            if patch_name not in enabled_patches or not enabled_patches[patch_name]:
                return m.group() # no change, patch is disabled
            return (
                f'\n###<BEGIN PATCH:{patch_name}>\n'
                + enabled_patches[patch_name]
                + f'\n###<END PATCH:{patch_name}>\n'
            )

        mod.source_content = _rx_patches.sub(_process_patch, mod.source_content)


    def process_imports(self, mod):

        def _repl_from_import(m):

            pkg_where = m.group('pkg_where')
            import_targets = m.group('import_targets')
            import_name = m.group('import_name')
            import_as = m.group('import_as')
            more_import_names = m.group('more_import_names')

            group = m.group()
            if group[-1] == '\n':
                group = group[:-1]

            logger.debug(f"Found “from” import: ‘{group}’")

            def _comment_out():
                return _comment_out_text_full_lines(group)

            if pkg_where == '__future__':
                # special '__future__' import, leave it out unless feature is set
                if self.enabled_features.get('keep_future_statements', True):
                    return m.group()
                else:
                    return _comment_out()

            for skip_prefix in self.skip_relative_import_prefixes:
                if pkg_where == skip_prefix or pkg_where.startswith(skip_prefix + '.'):
                    logger.debug(
                        f"skipping “from {pkg_where} import ...” as it begins "
                        f"with prefix {skip_prefix!r}"
                    )
                    return m.group()

            # translate into module name that is imported
            pkgmod_path = pkg_where.split('.')
            if pkgmod_path[0]: # and os.path.isdir(os.join(self.source_dir, *pkgmod_path)):
                # found absolute import, all fine
                pass
            else:
                # pkgmod_path[0] is empty
                if not pkgmod_path[-1]: # 'from ".." import zz' -> three empty
                                        # sections in pkgmod_path
                    pkgmod_path = pkgmod_path[:-1]
                r = list(mod.mod_path)
                logger.debug(f"relative import: {r=}, {pkgmod_path=}")
                pkgmod_path = pkgmod_path[1:]
                while pkgmod_path and not pkgmod_path[0]:
                    r = r[:-1]
                    pkgmod_path = pkgmod_path[1:]
                    logger.debug(f"resolved up one level: {r=}, {pkgmod_path=}")
                pkgmod_path = r + pkgmod_path

            # pkgmod_path is relative path of the package/module that is referenced
            the_mod_path = pkgmod_path
            if os.path.isdir( os.path.join(self.source_dir, *pkgmod_path) ) \
               and os.path.isfile(
                   os.path.join(self.source_dir, *pkgmod_path, '__init__.py')
               ) :
                # it's a directory -> a python package, so we need to look at
                # import_name ("from pylatexenc import latexwalker" -> the_mod_path
                # should resolve to ['pylatexenc', 'latexwalker'])

                if not import_name:
                    logger.warning(
                        f"Could not fully parse import statement, I'm going to "
                        f"assume that all "
                        f"imported names in the following are symbols imported from the "
                        f"package's __init__.py: ‘{group}’"
                    )
                    imported_sub_module = False
                elif os.path.isfile(
                        os.path.join(self.source_dir, *pkgmod_path, import_name+'.py')
                ):
                    if more_import_names:
                        raise ValueError(
                            f"More names specified, can only handle one sub-module: ‘{group}’"
                        )
                    imported_sub_module = True
                    the_mod_path = pkgmod_path + [ import_name ]
                else:
                    imported_sub_module = False
                    
            else:
                # pkgmod_path directly points to the module/file name
                imported_sub_module = False
                the_mod_path = pkgmod_path

            mod_dotname = '.'.join(the_mod_path)
            #mod_fname = os.path.join(self.source_dir, *the_mod_path)

            # ### All OK, this can happen when importing a symbol from the
            # ### __init__ module of a package (e.g.,
            # ### "from pylatexenc.latexnodes import ParsedMacroArgs")
            #
            # if not os.path.isfile( mod_fname + '.py' ) \
            #    and not os.path.isfile( os.path.join(mod_fname, '__init__.py') ):
            #     raise ValueError(f"Could not find module: ‘{group}’ "
            #                      f"({mod_fname=!r} {mod_dotname=!r})")

            # register full module name so that we visit it
            logger.debug(f"Including module ‘{mod_dotname}’ to be processed "
                         f"if not done so already")
            self.modules_to_preprocess.add( mod_dotname )

            if self.enabled_features.get('keep_relative_imports', True):
                # return original from...import... statement as-is if we want to
                # keep relative imports
                return m.group()

            # tweak in different form
            if imported_sub_module:
                if import_as:
                    return f'import {mod_dotname} as {import_as}\n'
                return f'import {mod_dotname} as {import_name}\n'

            # transform into simple absolute from X import Y statement
            return f'from {mod_dotname} import {import_targets}'

        # def _repl_import(m):
        #     # don't replace the text, but register the module name for it to
        #     # be visited.  --> no, assume only external modules are imported
        #     # in this way...
        #     return m.group()

        # fix "from ... import ..." imports
        mod.source_content = _rx_from_import.sub(_repl_from_import, mod.source_content)

        # # find imports and selectively keep them --- e.g., remove 'logging'
        # source_content = _rx_import.sub(_repl_import, source_content)


    def process_dict_generator(self, mod):
        if self.enabled_features.get('keep_dict_with_generator', True):
            return

        def _repl_dict_generator(m):

            contents = m.group('contents')
            group = m.group()

            repl = 'dict([ ' + contents + ' ])'

            logger.info(
                "*** replacing suspected dict construction from a generator "
                "comprehension by explicit list: ***\n"
                f"  ‘{group}’  -->\n"
                f"     ‘{repl}’\n"
            )

            return repl


        # dict( x for x in zzz )  --> dict([ x for x in zzz ])
        mod.source_content = _rx_construct_dict_with_generator.sub(
            _repl_dict_generator,
            mod.source_content
        )


    def process_super(self, mod):
        if self.enabled_features.get('keep_super_arguments', True):
            return

        # super(SuperClass, self)  -->  super()
        mod.source_content = _rx_super_with_args.sub(
            'super()',
            mod.source_content
        )

    def process_frozenset(self, mod):
        if self.enabled_features.get('keep_frozenset', True):
            return

        # frozenset -> set
        mod.source_content = _rx_frozenset.sub(
            'set',
            mod.source_content
        )

    def process_logger_debug(self, mod):
        if self.enabled_features.get('keep_logger_debug', True):
            return

        # logger.debug -> comment out instruction
        mod.source_content = _rx_logger_debug.sub(
            lambda m: _comment_out_match(m, place_expression='pass'),
            mod.source_content
        )




def setup_logging(level):
    try:
        import colorlog
    except ImportError:
        logging.basicConfig(level=level)
        return

    # You should use colorlog >= 6.0.0a4
    handler = colorlog.StreamHandler()
    handler.setFormatter( colorlog.LevelFormatter(
        log_colors={
            "DEBUG": "white",
            "INFO": "",
            "WARNING": "red",
            "ERROR": "bold_red",
            "CRITICAL": "bold_red",
        },
        fmt={
            # emojis we can use: 🐞 🐜 🚨 🚦 ⚙️ 🧨 🧹 ❗️❓‼️ ⁉️ ⚠️ ℹ️ ➡️ ✔️ 〰️
            # 🎶 💭 📣 🔔 ⏳ 🔧 🔩 ✨ 💥 🔥 🐢 👉
            "DEBUG":    "%(log_color)s〰️    %(message)s", #'  [%(name)s]'
            "INFO":     "%(log_color)s✨  %(message)s",
            "WARNING":  "%(log_color)s⚠️   %(message)s", # (%(module)s:%(lineno)d)",
            "ERROR":    "%(log_color)s🚨  %(message)s", # (%(module)s:%(lineno)d)",
            "CRITICAL": "%(log_color)s🚨  %(message)s", # (%(module)s:%(lineno)d)",
        },
        stream=sys.stderr
    ) )

    root = colorlog.getLogger()
    root.addHandler(handler)

    root.setLevel(level)


if __name__ == '__main__':
    try:
        setup_logging(level=logging.INFO) #.DEBUG) #INFO)

        argparser = argparse.ArgumentParser()
        argparser.add_argument("config", nargs='?', default=None)

        args = argparser.parse_args()

        if args.config:
            with open(args.config, 'r', encoding='utf-8') as f:
                options = yaml.safe_load(f)
        else:
            options = default_options

        if 'source_dir' not in options:
            options['source_dir'] = default_source_dir

        pp = Preprocess(**options)
        pp.preprocess()

        logger.info("*** Done.")
    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        import pdb; pdb.post_mortem()
