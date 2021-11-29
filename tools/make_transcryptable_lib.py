import re
import os
import os.path



source_dir = os.path.join(os.path.dirname(__file__), '..')


target_dir = os.path.join(os.path.dirname(__file__), 'transcryptable_output')

if not os.path.isdir(target_dir):
    os.makedirs(target_dir)


#
# Process our source files to make them usable with Transcrypt (-> to create a
# JavaScript library)
#


include_sources = [
    (['pylatexenc'], '__init__.py'),
    (['pylatexenc'], '_util.py'),
    (['pylatexenc'], 'version.py'),
    (['pylatexenc','macrospec'], '__init__.py'),
    (['pylatexenc','macrospec'], '_parsedargs.py'),
    (['pylatexenc','macrospec'], '_argparsers.py'),
    (['pylatexenc','macrospec'], '_specclasses.py'),
    (['pylatexenc','macrospec'], '_latexcontextdb.py'),
    (['pylatexenc','latexwalker'], '__init__.py'),
    (['pylatexenc','latexwalker'], '_types.py'),
    (['pylatexenc','latexwalker'], '_walker.py'),
]

accept_list_modules = [
    'pylatexenc._util',
    'pylatexenc.version',
    'pylatexenc.macrospec',
    'pylatexenc.macrospec._parsedargs',
    'pylatexenc.macrospec._argparsers',
    'pylatexenc.macrospec._specclasses',
    'pylatexenc.macrospec._latexcontextdb',
    'pylatexenc.latexwalker',
    'pylatexenc.latexwalker._types',
    'pylatexenc.latexwalker._walker',
]


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



_rx_py2supportcode = re.compile(
    r"""
    ^import [ \t]+ sys \s*

    ^if [ ]+ sys[.]version_info[.]major [ ]* == [ ]* 2 [ ]* : \s*[\n]

    ( ^[ \t]+.*[\n] )+     # greedy capturing of lines with indentation

    """,
    flags=re.MULTILINE | re.VERBOSE
)


# remove arguments to super() calls
_rx_super = re.compile(
    r"""
    super\s*
    \(
      \s*
      (?P<clsname> [A-Za-z0-9_]+ )
      \s*
      ,
      \s*
      (?P<self> self )
      \s*
    \)
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



# logger = logging.getLogger(...)  at module level
_rx_logger_defn = re.compile(
    r"""
    ^
    logger
    [ \t]+
    =
    [ \t]+
    .*
    $
    """,
    re.MULTILINE | re.VERBOSE
)
# logger.debug|warn|...
_rx_logger_use = re.compile(
    r"""
    \b
    logger
    [ \t]*
    [.]
    [ \t]*
    (?P<logger_method>
      debug
      |
      info
      |
      warning
      |
      error
      |
      critical
    )
    """,
    re.MULTILINE | re.VERBOSE
)

# 'bisect_right_nodupl = ..."
_rx_bisect_defn = re.compile(
    r"""
    ^
    bisect_right_nodupl
    [ \t]+
    =
    [ \t]+
    .*
    $
    """,
    re.MULTILINE | re.VERBOSE
)

_rx_construct_dict_with_generator = re.compile(
    r"""
    \b
    dict\b
    \(
    (?P<contents>
      [^\[\n]+
      \b for \b
      .*
    )
    \)
    """,
    re.MULTILINE | re.VERBOSE
)



def process_source_file(relative_dir_items, filename_py):
    
    # a bunch of hacks onto the source file to make it compatible with
    # transcrypt to generate a simple JS "latex-markup" parser

    # remove any 'from __future__ import ...' line

    print(f"Processing {relative_dir_items=}  {filename_py=}")

    def _comment_out_text(text):
        return '###> ' + text.replace('\n', '\n###> ') + '\n'

    def _comment_out_match(m):
        return '###> ' + m.group().replace('\n', '\n###> ') + '\n'

    def _repl_from_import(m):
        
        pkg_where = m.group('pkg_where')
        import_targets = m.group('import_targets')
        import_name = m.group('import_name')
        import_as = m.group('import_as')
        more_import_names = m.group('more_import_names')

        group = m.group()
        if group[-1] == '\n':
            group = group[:-1]

        def _comment_out():
            return _comment_out_text(group)

        if pkg_where == '__future__':
            # special '__future__' import, leave it out
            return _comment_out()

        # translate into module name that is imported
        mod_path = pkg_where.split('.')
        if mod_path[0]: # and os.path.isdir(os.join(source_dir, *mod_path)):
            # found absolute import, all fine
            pass
        else:
            # mod_path[0] is empty
            if not mod_path[-1]: # 'from ".." import zz' -> three empty sections in mod_path
                mod_path = mod_path[:-1]
            r = list(relative_dir_items)
            print(f"relative import: {r=}, {mod_path=}")
            mod_path = mod_path[1:]
            while mod_path and not mod_path[0]:
                r = r[:-1]
                mod_path = mod_path[1:]
                print(f"resolved up one level: {r=}, {mod_path=}")
            mod_path = r + mod_path
        
        # mod_path is relative path of the package that is referenced
        imported_sub_module = False
        if os.path.isdir( os.path.join(source_dir, *mod_path) ) \
           and os.path.isfile( os.path.join(source_dir, *mod_path, '__init__.py') ) :
            # it's a directory -> a pythonb package, so we need to look at
            # import_name ("from pylatexenc import latexwalker" -> mod_path
            # should resolve to ['pylatexenc', 'latexwalker'])
            if not import_name:
                raise ValueError(f"Could not parse import statement, I need a single "
                                 f"module to import please: ‘{group}’ ({mod_path=!r})")
            mod_path = mod_path + [ import_name ]
            imported_sub_module = True

        mod_dotname = '.'.join(mod_path)
        mod_fname = os.path.join(source_dir, *mod_path)

        if not os.path.isfile( mod_fname + '.py' ) \
           and not os.path.isfile( os.path.join(mod_fname, '__init__.py') ):
            raise ValueError(f"Could not find module: ‘{group}’ "
                             f"({mod_fname=!r} {mod_dotname=!r})")
        
        # check if the module is accept-listed
        if mod_dotname not in accept_list_modules:
            print(f"Removing import ‘{group}’, not in accept-list")
            return _comment_out()

        # tweak in different form
        if imported_sub_module:
            if more_import_names:
                raise ValueError(
                    f"More names specified, can only handle one sub-module: ‘{group}’"
                )
            if import_as:
                return f'import {mod_dotname} as {import_as}\n'
            return f'import {mod_dotname} as {import_name}\n'

        # transform into simple absolute from X import Y statement
        return f'from {mod_dotname} import {import_targets}'

    def _repl_import(m):

        pkg_name = m.group('pkg_name')
        group = m.group()

        if pkg_name in ('logging', 'bisect',):
            return _comment_out_text(group)

        return group

    def _repl_dict_generator(m):
        
        contents = m.group('contents')
        group = m.group()

        repl = 'dict([ ' + contents + ' ])'

        print(
            "*** replacing suspected dict construction from a generator "
            "comprehension by explicit list: ***\n"
            f"  ‘{group}’  -->\n"
            f"     ‘{repl}’\n"
        )

        return repl

        
    with open(os.path.join(source_dir, *relative_dir_items, filename_py)) as f:
        source_content = f.read()

    final_source_content = source_content

    # remove Py2 support code
    final_source_content = _rx_py2supportcode.sub(
        lambda m: _comment_out_text(m.group()),
        final_source_content)

    # fix "from ... import ..." imports
    final_source_content = _rx_from_import.sub(_repl_from_import, final_source_content)

    # find imports and selectively keep them --- e.g., remove 'logging'
    final_source_content = _rx_import.sub(_repl_import, final_source_content)
    
    # replace logger = logging.getLogger(...) as well as logger.XXX(...) -> console.log
    final_source_content = _rx_logger_defn.sub(_comment_out_match, final_source_content)
    final_source_content = _rx_logger_use.sub('console.log', final_source_content)

    # super(SuperClass, self)  -->  super()
    final_source_content = _rx_super.sub(
        'super()',
        final_source_content
    )

    # dict( x for x in zzz )  --> dict([ x for x in zzz ])
    final_source_content = _rx_construct_dict_with_generator.sub(
        _repl_dict_generator,
        final_source_content
    )

    # custom implementation for bisect
    custom_bisect = r"""
def bisect_right_nodupl(a, x):
    # find the first index of a that is > pos

    lo = 0
    hi = len(a)
    mid = None

    while True:
        if a[lo] > x:
            return lo
        if a[hi-1] <= x:
            return hi
        if hi - lo <= 2:
            if a[lo+1] > x:
                return lo
            else: #if a[lo+2] > x:
                return lo+1
        mid = (hi + lo) // 2
        if a[mid] > x:
            hi = mid+1
        elif a[mid] <= x:
            lo = mid
"""
    final_source_content = _rx_bisect_defn.sub(
        lambda m: custom_bisect,
        final_source_content
    )
        



    if not os.path.isdir(os.path.join(target_dir, *relative_dir_items)):
        os.makedirs(os.path.join(target_dir, *relative_dir_items))
        
    with open(os.path.join(target_dir, *relative_dir_items, filename_py), 'w') as fw:
        fw.write(final_source_content)
    


for relative_dir_items, fname in include_sources:
    process_source_file(relative_dir_items, fname)
