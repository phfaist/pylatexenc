import re
import os
import os.path
import sys

import logging


logger = logging.getLogger(__name__)


options = {

    'enabled_features': {
        'keep_future_statements': False,
        'keep_relative_imports': False,
        'keep_super_arguments': False,
        'keep_dict_with_generator': False,
        'keep_frozenset': False,
        'guards': {
            'PYTHON2_SUPPORT_CODE': False,
            'PYLATEXENC1_LEGACY_SUPPORT_CODE': False,
            'PYLATEXENC2_LEGACY_SUPPORT_CODE': False,
            'PYLATEXENC_GET_DEFAULT_SPECS_FN': False,
            'LATEXWALKER_HELPERS': False,
        }
    },

    'source_dir': os.path.join(os.path.dirname(__file__), '..'),

    'target_dir': os.path.join(os.path.dirname(__file__), 'transcryptable_output'),

    # which modules to preprocess
    'module_list': [
        'pylatexenc.latexnodes',
        'pylatexenc.macrospec',
        'pylatexenc.latexwalker',
    ],
}



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


# ------------------------------------------------------------------------------


def _comment_out_text(text):
    return '###> ' + text.replace('\n', '\n###> ') + '\n'

def _comment_out_match(m):
    return '###> ' + m.group().replace('\n', '\n###> ') + '\n'



class _Module:
    mod_path = []
    mod_name = None
    source_content = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Preprocess:

    def __init__(self, source_dir, target_dir, module_list, enabled_features):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.enabled_features = enabled_features
        self.module_list = module_list

        self.modules_to_preprocess = set(module_list)
        self.modules_preprocessed = set()

        self._preprocess()

    def _preprocess(self):

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

        self.process_guards(mod)
        self.process_imports(mod)
        self.process_super(mod)
        self.process_dict_generator(mod)
        self.process_frozenset(mod)


    def process_guards(self, mod):

        enabled_guards = self.enabled_features['guards']

        def _process_guard(m):
            if enabled_guards[m.group('guard_name')]:
                return m.group() # no change, guard is enabled
            return _comment_out_match(m)

        mod.source_content = _rx_guards.sub(_process_guard, mod.source_content)


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

            logger.debug(f"Found import: ‘{group}’")

            def _comment_out():
                return _comment_out_text(group)

            if pkg_where == '__future__':
                # special '__future__' import, leave it out unless feature is set
                if self.enabled_features['keep_future_statements']:
                    return m.group()
                else:
                    return _comment_out()

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
            mod_fname = os.path.join(self.source_dir, *the_mod_path)

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

            if self.enabled_features['keep_relative_imports']:
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
        if self.enabled_features['keep_dict_with_generator']:
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
        if self.enabled_features['keep_super_arguments']:
            return;

        # super(SuperClass, self)  -->  super()
        mod.source_content = _rx_super_with_args.sub(
            'super()',
            mod.source_content
        )

    def process_frozenset(self, mod):
        if self.enabled_features['keep_frozenset']:
            return;

        # frozenset -> set
        mod.source_content = _rx_frozenset.sub(
            'set',
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
        Preprocess(**options)
        logger.info("*** Done.")
    except Exception as e:
        logger.error(f"Exception: {e}", exc_info=True)
        import pdb; pdb.post_mortem()
