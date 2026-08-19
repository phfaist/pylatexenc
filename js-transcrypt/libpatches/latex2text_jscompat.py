#
# Replacements for the few things in `pylatexenc.latex2text` that rely on parts
# of the python standard library that Transcrypt does not provide.  Each of
# them is installed in place of a `### BEGINPATCH_…` block of the original
# sources; see `js-transcrypt/preprocesslib-*.config.yaml`.
#

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
#
# In place of the percent-style string substitution, which the python language
# provides as an operator on strings and which JavaScript has nothing like.
#
# Only the conversions that a `simplify_repl` replacement string can sensibly
# use are supported: '%s' and '%(name)s', along with '%%' for a literal percent
# sign.  Anything else raises a ValueError, exactly as an unsupported
# conversion does in python; the caller reports that as a configuration error
# and leaves the replacement string as it is.
#

def apply_percent_substitution(simplify_repl, x):

    is_mapping = isinstance(x, dict)

    result = []
    args_used = 0
    i = 0
    num = len(simplify_repl)

    while i < num:

        c = simplify_repl[i]
        if c != '%':
            result.append(c)
            i = i + 1
            continue

        i = i + 1
        if i >= num:
            raise ValueError("incomplete format")

        if simplify_repl[i] == '%':
            result.append('%')
            i = i + 1
            continue

        key = None
        if simplify_repl[i] == '(':
            j = simplify_repl.find(')', i)
            if j == -1:
                raise ValueError("incomplete format key")
            key = simplify_repl[i+1:j]
            i = j + 1
            if i >= num:
                raise ValueError("incomplete format")

        conversion = simplify_repl[i]
        i = i + 1

        if conversion != 's':
            raise ValueError(
                "unsupported format character '{}'".format(conversion)
            )

        if key is not None:
            if not is_mapping:
                raise TypeError("format requires a mapping")
            if key not in x:
                raise KeyError(key)
            result.append(str(x[key]))
            continue

        if is_mapping:
            # '%s' with a mapping formats the mapping itself, which is never
            # what a replacement string means
            raise TypeError("not enough arguments for format string")

        if args_used >= len(x):
            raise TypeError("not enough arguments for format string")
        result.append(str(x[args_used]))
        args_used = args_used + 1

    if not is_mapping and args_used < len(x):
        raise TypeError("not all arguments converted during string formatting")

    return "".join(result)


# ------------------------------------------------------------------------------
#
# In place of `textwrap.fill()`.
#
# Unlike the python function, this one only ever breaks a line at a space; the
# python one also breaks a hyphenated word at its hyphens.
#

def fill_text_paragraph(text, width, initial_indent=''):

    if width < 1:
        raise ValueError("invalid width {}".format(width))

    # `textwrap` normalizes the whitespace of the text before laying it out,
    # turning every run of whitespace into a single space
    words = text.split()

    lines = []
    cur = initial_indent
    # `textwrap` places the initial indent immediately in front of the first
    # word, with no space in between; a space only ever separates two words
    have_word = False

    for word in words:

        if have_word:
            candidate = cur + ' ' + word
        else:
            candidate = cur + word

        if len(candidate) <= width:
            cur = candidate
            have_word = True
            continue

        if len(word) <= width:
            # the word doesn't fit on this line, but it does fit on a line of
            # its own
            lines.append(cur)
            cur = word
            have_word = True
            continue

        # a word that is longer than a whole line gets broken up, which is what
        # `textwrap.fill()` does by default (`break_long_words=True`).  As much
        # of it as fits stays on the line that is being built.
        space_left = width - len(cur)
        if have_word:
            space_left = space_left - 1
        if space_left > 0:
            if have_word:
                cur = cur + ' ' + word[:space_left]
            else:
                cur = cur + word[:space_left]
            word = word[space_left:]
        lines.append(cur)

        while len(word) > width:
            lines.append(word[:width])
            word = word[width:]
        cur = word
        have_word = (len(cur) > 0)

    if have_word:
        lines.append(cur)

    return "\n".join(lines)


# ------------------------------------------------------------------------------
#
# In place of `unicodedata.normalize('NFC', …)`.  JavaScript strings provide
# the unicode normalization forms themselves.
#

def compose_accented_char(s):
    __pragma__('js', "{}", """
    return s.normalize('NFC');
    """)


# ------------------------------------------------------------------------------
#
# In place of the `datetime`-based rendering of '\today'.
#
# The month names are spelled out here rather than asked of the system, because
# JavaScript's own localized month names depend on the environment the code
# happens to run in, whereas LaTeX's '\today' is in the language of the
# document.  English is what LaTeX itself uses by default.
#

_month_names = (
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
)

def latex_today():
    __pragma__('js', "{}", """
    var now = new Date();
    return _month_names[now.getMonth()] + ' ' + now.getDate() + ', '
        + now.getFullYear();
    """)


# ------------------------------------------------------------------------------
#
# In place of reading a file from the file system upon '\input{}', which the
# JavaScript build has no way of doing.
#

def read_latex_file(tex_input_directory, strict_input, fn):
    logger.warning(
        "Can't read the contents of '%s': reading input files is not supported "
        "in this build of pylatexenc",
        fn
    )
    return ''
