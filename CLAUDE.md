# pylatexenc

Python library for parsing LaTeX code, converting LaTeX to plain text, and
encoding unicode characters into LaTeX escape sequences.  Version 3 (alpha).

The parsing layer is also the basis of the [flm](https://github.com/phfaist/flm)
project, and is transcribed to JavaScript for
[zoodb](https://github.com/phfaist/zoodb) / the Error Correction Zoo.

## Public modules

- `pylatexenc.latexnodes` — core parsing infrastructure: token reader, parsing
  state, parsed-argument objects, exceptions.  Node classes live in
  `pylatexenc.latexnodes.nodes`.
- `pylatexenc.latexnodes.parsers` — the library of reusable parser objects.
- `pylatexenc.macrospec` — specifications of macros, environments and specials,
  and the latex context database that collects them.
- `pylatexenc.latexwalker` — main entry point for parsing a LaTeX string into a
  node tree.
- `pylatexenc.latex2text` — converts a node tree (or LaTeX string) to plain text.
- `pylatexenc.latexencode` — unicode → LaTeX escape sequences.

`latexwalker`, `latex2text` and `latexencode` each have a `__main__.py` exposing
a command-line tool of the same name.

**For anything about code structure, class responsibilities, or usage: read the
API documentation in `doc/` (Sphinx sources), published at
<https://pylatexenc.readthedocs.io/>.**  Prefer updating those `.rst` files and
the docstrings they pull in over documenting details here.

## Repository layout

- `pylatexenc/` — the package.
- `test/` — pytest test suite.
- `doc/` — Sphinx documentation sources.
- `tools/` — developer scripts: `preprocess_lib.py` (source preprocessor),
  `utils_transcrypt_generate_js.py`, and generators for the unicode/LaTeX
  mapping tables.
- `js-transcrypt/` — JavaScript build of the library via Transcrypt.

Note: the tree contains many stale editor backup files (`*~`) and build outputs
(`*.pyc`, `dist/`, `js-transcrypt/pp-tmp/`, `js-transcrypt/pylatexenc-js/`).
Ignore them; never edit a `*~` file.

## Commands

This project uses uv (`pyproject.toml`, PEP 621 metadata, hatchling build
backend).  `uv.lock` is committed; keep it in sync with `uv lock`.
The version string lives **only** in `pylatexenc/version.py` — hatchling reads
it from there (see `[tool.hatch.version]`), so bump it in that one place.

Python tests:

    uv run pytest

JavaScript build and tests (needs the `buildjslib` dependency group):

    uv sync --group buildjslib
    cd js-transcrypt
    uv run python ./generate_pylatexenc_js.py --delete-target-dir --compile-tests
    node test-pylatexenc-js/runtests.js

Building and publishing:

    uv build
    uv publish

Dependency groups (PEP 735, in `[dependency-groups]`): `dev` (pytest) is
installed by a plain `uv sync`; `builddoc` (Sphinx) and `buildjslib`
(Transcrypt, PyYAML) are opt-in via `--group`.

The supported python range is declared once, by `requires-python` in
`pyproject.toml` (currently `>=3.6`).  The `tests-ci` workflow matrix actually
exercises 3.8 through 3.13, so the oldest declared versions (3.6 and 3.7) are
not covered by continuous integration.  Python 2 is not supported; do not
reintroduce compatibility shims for it.


## Constraints when editing

**Transcrypt-compatible subset.**  `latexnodes`, `latexnodes.parsers`,
`macrospec`, `latexwalker` and `latexencode` are compiled to JavaScript, so they
use only a restricted subset of Python: no f-strings, no comprehension-heavy
idioms beyond what `tools/preprocess_lib.py` rewrites, etc.  Follow the style of
the surrounding code.  Any change to these modules must be validated by running
the JavaScript build and its tests, not just `pytest`.  (`latex2text` is not
transcribed and is less constrained.)

**Guarded source blocks.**  `tools/preprocess_lib.py` strips regions delimited by

    ### BEGIN_<GUARD_NAME>
    ...
    ### END_<GUARD_NAME>

Guards in use: `PYLATEXENC1_LEGACY_SUPPORT_CODE`,
`PYLATEXENC2_LEGACY_SUPPORT_CODE`, `PYLATEXENC_GET_DEFAULT_SPECS_FN`,
`LATEXWALKER_HELPERS`, and — in test sources — `DEBUG_SET_EQ_ATTRIBUTE` and
`TEST_PYLATEXENC_SKIP`;
`### BEGINPATCH_…` /
`### ENDPATCH_…` mark code substituted for the JavaScript build.  The markers
must sit on their own line and the enclosed lines must not start with `###`.
Which guards are kept is configured per build in
`js-transcrypt/preprocesslib-*.config.yaml`.

**No public API changes and no refactoring** unless explicitly asked.  Bug fixes
and mechanical cleanups should preserve existing patterns.

## Working agreement

- Explain the rationale for changes in plain language, with enough context to
  follow without deep familiarity with the codebase.  Do not use acronyms.
- Ask before opening pull requests.
- Background agents work in worktrees and commit to a local branch; when done,
  ask whether to merge into local `main` or open a pull request.
- Do not guess when making design decisions.  If a feature requires developing
  a new structural pattern (or extending an existing one), always ask the
  user for feedback before doing so.
