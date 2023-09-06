# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2019 Philippe Faist
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


# Internal module. Internal API may move, disappear or otherwise change at any
# time and without notice.

from __future__ import print_function, unicode_literals

from ._exctypes import LatexWalkerParseError
from ._parsedargs import ParsedArguments


# for Py3
_unicode_from_str = lambda x: x

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _unicode_from_str = lambda x: x.decode('utf-8')
### END_PYTHON2_SUPPORT_CODE



def _display_abbrev_str(s, maxlen=40):
    if not maxlen or maxlen < 2: # also catches None
        maxlen = 2
    if len(s) < maxlen:
        return s
    return s[:maxlen-2] + '…'


def _display_str_delimiters(delimiters):

    open_delim = '<??>'
    close_delim = '<??>'

    try:
        open_delim, close_delim = delimiters
    except: # Transcrypt-friendly
        pass

    if open_delim is None:
        open_delim = ''
    if close_delim is None:
        close_delim = ''

    return open_delim, close_delim


#
# see __all__ defined at the bottom of this module.
#


# ------------------------------------------------------------------------------



class LatexNode(object):
    """
    Represents an abstract 'node' of the latex document.

    Use :py:meth:`nodeType()` to figure out what type of node this is, and
    :py:meth:`isNodeType()` to test whether it is of a given type.

    You should use :py:meth:`LatexWalker.make_node()` to create nodes, so that
    the latex walker has the opportunity to do some additional setting up.

    .. versionchanged: 3.0
    
       This class (along with its canonical subclasses) is located in the module
       :py:mod:`pylatexenc.latexnodes.nodes` starting in `pylatexenc 3.0`.  It
       is aliased in :py:mod:`pylatexenc.latexwalker` for backwards
       compatibility.


    All nodes have the following attributes:

    .. py:attribute:: parsing_state

       The parsing state at the time this node was created.  This object stores
       additional context information for this node, such as whether or not this
       node was parsed in a math mode block of LaTeX code.

       See also the :py:meth:`LatexWalker.make_parsing_state()` and the
       `parsing_state` argument of :py:meth:`LatexWalker.get_latex_nodes()`.

    .. py:attribute:: pos

       The position in the parsed string that this node represents.  If you're
       using the :py:class:`LatexWalker` walker class, then the parsed string
       can normally be recovered as `node.latex_walker.s`, see
       :py:attr:`LatexWalker.s` and the :py:attr:`latex_walker` attribute.

    .. py:attribute:: pos_end

       The position in the parsed string that is immediately after the present
       node.  If you're using the :py:class:`LatexWalker` walker class, then the
       parsed string can normally be recovered as `node.latex_walker.s`, see
       :py:attr:`LatexWalker.s` and the :py:attr:`latex_walker` attribute.

    .. py:attribute:: len

       (Read-only attribute.)  How many characters in the parsed string this
       node represents, starting at position `pos`.  If you're using the
       :py:class:`LatexWalker` walker class, then the parsed string can normally
       be recovered as `node.latex_walker.s`, see :py:attr:`LatexWalker.s` and
       the :py:attr:`latex_walker` attribute.

       Starting from `pylatexenc 3.0`, the `pos_end` attribute is primarily set
       and used instead of the `len` field.  The `len` field becomes a computed
       read-only attribute that computes `pos_end - pos`.

    .. versionadded:: 2.0
       
       The attributes `parsing_state`, `pos` and `len` were added in
       `pylatexenc 2.0`.

    .. py:attribute:: latex_walker

       The :py:class:`LatexWalker` instance used to create this node.

       .. versionadded:: 3.0

          The attribute latex_walker was added in `pylatexenc 3`.
    """
    def __init__(self, _fields, _redundant_fields=None,
                 parsing_state=None, pos=None, pos_end=None, latex_walker=None,
                 **kwargs):

        len_ = kwargs.pop('len', None)

        # Important: subclasses must specify a list of fields they set in the
        # `_fields` argument.  They should only specify base (non-redundant)
        # fields; if they have "redundant" fields, specify the additional fields
        # in _redundant_fields=...
        super(LatexNode, self).__init__(**kwargs)

        self.parsing_state = parsing_state
        self.latex_walker = latex_walker
        self.pos = pos
        self.pos_end = pos_end

        if pos_end is None and len_ is not None:
            self.pos_end = self.pos + len_

        self._fields = tuple(['pos', 'pos_end', 'parsing_state', 'latex_walker']
                             + list(_fields))
        if _redundant_fields is not None:
            self._redundant_fields = tuple(list(self._fields) + ['len']
                                           + list(_redundant_fields))
        else:
            self._redundant_fields = tuple(list(self._fields) + ['len'])

    def nodeType(self):
        """
        Returns the class which corresponds to the type of this node.  This is a
        Python class object, that is one of
        :py:class:`~pylatexenc.latexwalker.LatexCharsNode`,
        :py:class:`~pylatexenc.latexwalker.LatexGroupNode`, etc.
        """
        return LatexNode

    def isNodeType(self, t):
        """
        Returns `True` if the current node is of the given type.  The argument `t`
        must be a Python class such as,
        e.g. :py:class:`~pylatexenc.latexwalker.LatexGroupNode`.
        """
        return isinstance(self, t)

    @property
    def len(self):
        if self.pos is None or self.pos_end is None:
            return None
        return self.pos_end - self.pos

    def latex_verbatim(self):
        r"""
        Return the chunk of LaTeX code that this node represents.

        This is a shorthand for ``node.latex_walker.s[node.pos:node.pos_end]``.
        """
        if self.latex_walker is None:
            raise TypeError("Can't use latex_verbatim() on node because we don't "
                            "have any latex_walker set")
        return self.latex_walker.s[self.pos : self.pos_end]

    def __eq__(self, other):
        return (
            other is not None  and
            isinstance(other, LatexNode) and
            self.nodeType() is other.nodeType()  and
            other.parsing_state is self.parsing_state  and
            other.latex_walker is self.latex_walker  and
            # the "pos is None and other.pos is None" checks on top of equality
            # comparison are there for transcrypt ...
            ((other.pos is None and self.pos is None) or other.pos == self.pos)  and
            ((other.pos_end is None and self.pos_end is None)
             or other.pos_end == self.pos_end)  and
            all(
                (
                    ( (getattr(self, f) is None and getattr(other, f) is None)
                      or getattr(self, f) == getattr(other, f) )
                    for f in self._fields
                )
            )
        )

    # see https://docs.python.org/3/library/constants.html#NotImplemented
    def __ne__(self, other): return NotImplemented

    __hash__ = None

    def __unicode__(self):
        return _unicode_from_str(self.__str__())
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return (
            self.nodeType().__name__ + "(" +
            ", ".join([ "{}={!r}".format(k,getattr(self,k))  for k in self._fields ]) +
            ")"
            )

    def display_str(self):
        return r'<UNKNOWN NODE TYPE>: ' + repr(self)

    def accept_node_visitor(self, visitor):
        visitor.visit_unknown_node(self)

    def to_json_object_with_latexwalker(self, latexwalker):
        # Prepare a dictionary with the correct keys and values.
        d = {
            'nodetype': self.__class__.__name__,
        }
        #redundant_fields = getattr(n, '_redundant_fields', n._fields)
        for fld in self._fields:
            if fld == 'spec':
                # TODO: maybe do something smarter here in the future
                d[fld] = repr(self.spec)
            elif fld == 'latex_walker':
                # skip
                pass
            else:
                d[fld] = getattr(self, fld)
        d.update(latexwalker.pos_to_lineno_colno(self.pos, as_dict=True))
        return d

    def format_pos(self):
        if self.latex_walker is not None:
            return self.latex_walker.format_pos(self.pos)
        return '[@ pos {}]'.format(repr(self.pos))


class LatexCharsNode(LatexNode):
    """
    A string of characters in the LaTeX document, without any special LaTeX
    code.

    .. py:attribute:: chars

       The string of characters represented by this node.
    """
    def __init__(self, chars, **kwargs):
        super(LatexCharsNode, self).__init__(
            _fields = ('chars',),
            **kwargs
        )
        self.chars = chars

    def nodeType(self):
        return LatexCharsNode

    def display_str(self):
        return 'chars ‘' + _display_abbrev_str(self.chars) + '’'

    def accept_node_visitor(self, visitor):
        visitor.visit_chars_node(self)



class LatexGroupNode(LatexNode):
    r"""
    A LaTeX group delimited by braces, ``{like this}``.

    Note: in the case of an optional macro or environment argument, this node is
    also used to represents a group delimited by square braces instead of curly
    braces.

    .. py:attribute:: nodelist

       A list of nodes describing the contents of the LaTeX braced group.  Each
       item of the list is a :py:class:`LatexNode`.
    
       This attribute is normally a :py:class:`LatexNodeList`.

    .. py:attribute:: delimiters

       A 2-item tuple that stores the delimiters for this group node.  Usually
       this is `('{', '}')`, except for optional macro arguments where this
       might be for instance `('[', ']')`.

       .. versionadded:: 2.0

          The `delimiters` field was added in `pylatexenc 2.0`.
    """
    def __init__(self, nodelist, **kwargs):
        delimiters = kwargs.pop('delimiters', ('{', '}'))
        super(LatexGroupNode, self).__init__(
            _fields=('nodelist','delimiters',),
            **kwargs
        )
        self.nodelist = nodelist
        self.delimiters = delimiters

    def nodeType(self):
        return LatexGroupNode

    def display_str(self):
        open_delim, close_delim = _display_str_delimiters(self.delimiters)
        return "group ‘" + open_delim + "…" + close_delim + "’"

    def accept_node_visitor(self, visitor):
        if self.nodelist is not None:
            for node in self.nodelist:
                if node is not None:
                    node.accept_node_visitor(visitor)
        visitor.visit_group_node(self)


class LatexCommentNode(LatexNode):
    r"""
    A LaTeX comment, delimited by a percent sign until the end of line.

    .. py:attribute:: comment

       The comment string, not including the '%' sign nor the following newline

    .. py:attribute:: comment_post_space

       The newline that terminated the comment possibly followed by spaces
       (e.g., indentation spaces of the next line)

    """
    def __init__(self, comment, **kwargs):
        comment_post_space = kwargs.pop('comment_post_space', '')

        super(LatexCommentNode, self).__init__(
            _fields = ('comment', 'comment_post_space', ),
            **kwargs
        )

        self.comment = comment
        self.comment_post_space = comment_post_space

    def nodeType(self):
        return LatexCommentNode

    def display_str(self):
        return "comment ‘" + _display_abbrev_str(self.comment.strip()) + "’"

    def accept_node_visitor(self, visitor):
        visitor.visit_comment_node(self)


class LatexMacroNode(LatexNode):
    r"""
    Represents a macro type node, e.g. ``\textbf``

    .. py:attribute:: macroname

       The name of the macro (string), *without* the leading backslash.

    .. py:attribute:: spec

       The specification object for this macro (a :py:class:`MacroSpec`
       instance).

       .. versionadded:: 3.0

          The `spec` attribute was introduced in `pylatexenc 3`.

    .. py:attribute:: nodeargd

       The :py:class:`pylatexenc.latexnodes.ParsedArguments` object that
       represents the macro arguments.

       For macros that do not accept any argument, this is an empty
       :py:class:`~pylatexenc.latexnodes.ParsedArguments` instance.  The
       attribute `nodeargd` can be `None` even for macros that accept arguments,
       in the situation where :py:meth:`LatexWalker.get_latex_expression()`
       encounters the macro when reading a single expression.

       Arguments must be declared in the latex context passed to the
       :py:class:`LatexWalker` constructor, using a suitable
       :py:class:`pylatexenc.macrospec.MacroSpec` object.  Some known macros are
       already declared in the default latex context.

       .. versionadded:: 2.0

          The `nodeargd` attribute was introduced in `pylatexenc 2`.

    .. py:attribute:: macro_post_space

       Any spaces that were encountered immediately after the macro.

    The following attributes are obsolete since `pylatexenc 2.0`.

    .. py:attribute:: nodeoptarg

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in `pylatexenc 2`.  Accessing
          the argument `nodeoptarg` will still give a first optional argument
          for standard latex macros, for backwards compatibility.

       If non-`None`, this corresponds to the optional argument of the macro.

    .. py:attribute:: nodeargs

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in pylatexenc 2.  Accessing
          the argument `nodeargs` will still provide a list of argument nodes
          for standard latex macros, for backwards compatibility.

       A list of arguments to the macro. Each item in the list is a
       :py:class:`LatexNode`.
    """
    def __init__(self, macroname, **kwargs):
        nodeargd = kwargs.pop('nodeargd', ParsedArguments())
        macro_post_space = kwargs.pop('macro_post_space', '')
        spec = kwargs.pop('spec', None)

        super(LatexMacroNode, self).__init__(
            _fields = ('macroname','spec','nodeargd','macro_post_space'),
            _redundant_fields = ('nodeoptarg','nodeargs'),
            **kwargs)

        self.macroname = macroname
        self.spec = spec
        self.nodeargd = nodeargd
        self.macro_post_space = macro_post_space

    def nodeType(self):
        return LatexMacroNode

    def display_str(self):
        return "macro ‘\\" + self.macroname + "’"

    def accept_node_visitor(self, visitor):
        if self.nodeargd is not None:
            self.nodeargd.accept_node_visitor(visitor)
        visitor.visit_macro_node(self)


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE
    @property
    def nodeoptarg(self):
        if not hasattr(self, '_nodeoptarg'):
            self._nodeoptarg, self._nodeargs = \
                getattr(self.nodeargd, 'legacy_nodeoptarg_nodeargs', (None,None))
        return self._nodeoptarg

    @property
    def nodeargs(self):
        if not hasattr(self, '_nodeargs'):
            self._nodeoptarg, self._nodeargs = \
                getattr(self.nodeargd, 'legacy_nodeoptarg_nodeargs', (None,None))
        return self._nodeargs

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE



class LatexEnvironmentNode(LatexNode):
    r"""
    A LaTeX Environment Node, i.e. ``\begin{something} ... \end{something}``.

    .. py:attribute:: environmentname

       The name of the environment ('itemize', 'equation', ...)

    .. py:attribute:: spec

       The specification object for this macro (an :py:class:`EnvironmentSpec`
       instance).

       .. versionadded:: 3.0

       The `spec` attribute was introduced in `pylatexenc 3`.

    .. py:attribute:: nodelist

       A list of :py:class:`LatexNode`'s that represent all the contents between
       the ``\begin{...}`` instruction and the ``\end{...}`` instruction.

       This attribute is normally a :py:class:`LatexNodeList`.

    .. py:attribute:: nodeargd

       The :py:class:`pylatexenc.latexnodes.ParsedArguments` object that
       represents the arguments passed to the environment.  These are arguments
       that are present after the ``\begin{xxxxxx}`` command, as in
       ``\begin{tabular}{ccc}`` or ``\begin{figure}[H]``.  Arguments must be
       declared in the latex context passed to the :py:class:`LatexWalker`
       constructor, using a suitable
       :py:class:`pylatexenc.macrospec.EnvironmentSpec` object.  Some known
       environments are already declared in the default latex context.

       .. versionadded:: 2.0

          The `nodeargd` attribute was introduced in `pylatexenc 2`.

    The following attributes are available, but they are obsolete since
    `pylatexenc 2.0`.

    .. py:attribute:: envname

       .. deprecated:: 2.0

          This attribute was renamed `environmentname` for consistency with the
          rest of the package.

    .. py:attribute:: optargs

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in `pylatexenc 2`.  Accessing
          the argument `optargs` will still give a list of initial optional
          arguments for standard latex macros, for backwards compatibility.

    .. py:attribute:: args

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in `pylatexenc 2`.  Accessing
          the argument `args` will still give a list of curly-brace-delimited
          arguments for standard latex macros, for backwards compatibility.
    """
    
    def __init__(self, environmentname, nodelist, **kwargs):
        nodeargd = kwargs.pop('nodeargd', ParsedArguments())
        spec = kwargs.pop('spec', None)
        # # legacy:
        # optargs = kwargs.pop('optargs', [])
        # args = kwargs.pop('args', [])

        super(LatexEnvironmentNode, self).__init__(
            _fields = ('environmentname','spec','nodelist','nodeargd',),
            _redundant_fields = ('envname', 'optargs','args',),
            **kwargs)

        self.environmentname = environmentname
        self.spec = spec
        self.nodelist = nodelist
        self.nodeargd = nodeargd
        # legacy:
        #self.envname = environmentname
        #self.optargs = optargs
        #self.args = args


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE
    @property
    def envname(self):
        # Obsolete, don't use.
        return self.environmentname

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE

    def nodeType(self):
        return LatexEnvironmentNode

    def display_str(self):
        return "environment ‘{" + self.environmentname + "}’"

    def accept_node_visitor(self, visitor):
        if self.nodeargd is not None:
            self.nodeargd.accept_node_visitor(visitor)
        if self.nodelist is not None:
            for node in self.nodelist:
                if node is not None:
                    node.accept_node_visitor(visitor)
        visitor.visit_environment_node(self)



class LatexSpecialsNode(LatexNode):
    r"""
    Represents a specials type node, e.g. ``&`` or ``~``

    .. py:attribute:: specials_chars

       The name of the specials (string), *without* the leading backslash.

    .. py:attribute:: spec

       The specification object for this macro (a :py:class:`SpecialsSpec`
       instance).

       .. versionadded:: 3.0

       The `spec` attribute was introduced in `pylatexenc 3`.

    .. py:attribute:: nodeargd

       If the specials spec (cf. :py:class:`~pylatexenc.macrospec.SpecialsSpec`)
       has `args_parser=None` then the attribute `nodeargd` is set to `None`.
       If `args_parser` is specified in the spec, then the attribute `nodeargd`
       is a :py:class:`pylatexenc.latexnodes.ParsedArguments` instance that 
       represents the arguments to the specials.

       The `nodeargd` attribute can also be `None` even if the specials expects
       arguments, in the special situation where
       :py:meth:`LatexWalker.get_latex_expression()` encounters this specials.

       Arguments must be declared in the latex context passed to the
       :py:class:`LatexWalker` constructor, using a suitable
       :py:class:`pylatexenc.macrospec.SpecialsSpec` object.  Some known latex
       specials are already declared in the default latex context.

    .. versionadded:: 2.0

       Latex specials were introduced in `pylatexenc 2.0`.
    """
    def __init__(self, specials_chars, **kwargs):

        spec = kwargs.pop('spec', None)
        nodeargd = kwargs.pop('nodeargd', None)

        super(LatexSpecialsNode, self).__init__(
            _fields = ('specials_chars','spec','nodeargd'),
            **kwargs)

        self.specials_chars = specials_chars
        self.spec = spec
        self.nodeargd = nodeargd

    def nodeType(self):
        return LatexSpecialsNode

    def display_str(self):
        return "specials ‘" + self.specials_chars + "’"

    def accept_node_visitor(self, visitor):
        if self.nodeargd is not None:
            self.nodeargd.accept_node_visitor(visitor)
        visitor.visit_specials_node(self)


class LatexMathNode(LatexNode):
    r"""
    A Math node type.

    .. py:attribute:: displaytype

       Either 'inline' or 'display', to indicate an inline math block or a
       display math block. (Note that math environments such as
       ``\begin{equation}...\end{equation}``, are reported as
       :py:class:`LatexEnvironmentNode`'s, and not as
       :py:class:`LatexMathNode`'s.)

    .. py:attribute:: delimiters

       A 2-item tuple containing the begin and end delimiters used to delimit
       this math mode section.

       .. versionadded:: 2.0

          The `delimiters` attribute was introduced in `pylatexenc 2`.

    .. py:attribute:: nodelist
    
       The contents of the environment.  This attribute is normally a
       :py:class:`LatexNodeList`.
    """
    def __init__(self, displaytype, nodelist=[], **kwargs):
        delimiters = kwargs.pop('delimiters', (None, None))

        super(LatexMathNode, self).__init__(
            _fields = ('displaytype','nodelist','delimiters'),
            **kwargs
        )

        self.displaytype = displaytype
        self.nodelist = nodelist
        self.delimiters = delimiters

    def nodeType(self):
        return LatexMathNode

    def display_str(self):
        open_delim, close_delim = _display_str_delimiters(self.delimiters)
        return self.displaytype + " math ‘" + open_delim + "…" + close_delim + "’"

    def accept_node_visitor(self, visitor):
        if self.nodelist is not None:
            for node in self.nodelist:
                if node is not None:
                    node.accept_node_visitor(visitor)
        visitor.visit_math_node(self)



# ------------------------------------------------------------------------------



class LatexNodeList(object):
    r"""
    Represents a list of nodes, along with the spanning position and length.

    You can use a :py:class:`LatexNodeList` pretty much like a python `list` of
    nodes, including as an argument to `len()` and with indexing as in `obj[i]`.

    .. py:attribute:: nodelist

       A list of node instances.

    .. py:attribute:: pos
    
       The position in the parsed string where this node list starts, assuming
       that the `nodelist` represents a single continuous sequence of nodes in
       the latex string.

    .. py:attribute:: pos_end

       The position in the parsed string immediately after this node list ends,
       assuming that the `nodelist` represents a single continuous sequence of
       nodes in the latex string.

    .. py:attribute:: parsing_state

       The parsing state used to parse this node list.

    .. py:attribute:: latex_walker

       The latex walker instance used to parse this node list.


    .. py:attribute:: len

       (Read-only attribute.)  The total length spanned by this node list,
       assuming that the `nodelist` represents a single continuous sequence of
       nodes in the latex string.

    .. versionadded: 3.0

       The `LatexNodeList` class was introduced in `pylatexenc 3.0`.
    """
    def __init__(self, nodelist, **kwargs):

        if isinstance(nodelist, LatexNodeList):
            obj = nodelist
            self.nodelist = obj.nodelist
            self.parsing_state = obj.parsing_state
            self.latex_walker = obj.latex_walker
            self.pos = obj.pos
            self.pos_end = obj.pos_end
            return

        self.nodelist = nodelist

        if self.nodelist is None:
            logger.warning("You're creating a LatexNodeList with nodelist=None. That's "
                           "likely to cause crashes!")

        self.parsing_state = kwargs.pop('parsing_state', None)
        self.latex_walker = kwargs.pop('latex_walker', None)
        self.pos = kwargs.pop('pos', None)
        self.pos_end = kwargs.pop('pos_end', None)

        if len(kwargs): # len() for Transcrypt
            raise ValueError("Unexpected keyword arguments to LatexNodeList: "
                             + repr(kwargs))

        self.pos, self.pos_end = \
            _update_posposend_from_nodelist(self.pos, self.pos_end, self.nodelist)


    _fields = ('nodelist', 'parsing_state', 'latex_walker', 'pos', 'pos_end',)


    @property
    def len(self):
        if self.pos is None or self.pos_end is None:
            return None
        return self.pos_end - self.pos

    # needed for Transcrypt apparently, on top of __getitem__.
    def __iter__(self):
        if self.nodelist is None:
            return iter([])
        return iter(self.nodelist)


    def __getitem__(self, index):
        # supports slicing, too, and returns a simple list in such cases

        #
        # Provide supporting code that is only visible to Transcrypt -->
        #

        #__pragma__('ecom')

        # Transcrypt supports slices by passing an array [lower,upper,step] as
        # "index" parameter.

        """?
        try:
            if len(index) == 3:
                lower, upper, step = index
                return self.nodelist[lower:upper:step]
        except:
            pass
        ?"""

        # Negative indexing does not seem to be always supported in Transcrypt?
        """?
        if isinstance(index, int) and index < 0:
            index = len(self.nodelist) + index
        ?"""

        return self.nodelist[index]


    def __len__(self):
        return len(self.nodelist)
    
    
    def latex_verbatim(self):
        r"""
        Return the chunk of LaTeX code that this node represents.

        This is a shorthand for concatenating all the `latex_verbatim()`
        representation of all the nodes in the list.
        """
        return "".join([
            n.latex_verbatim()
            for n in self.nodelist
            if n is not None
        ])


    def display_str(self):
        r"""
        Return a string that is not too long
        """
        if self.nodelist is None:
            list_len = 'null list'
            list_preview = ''
        else:
            list_len = len(self.nodelist)
            list_preview = (
                ": "
                + ", ".join([
                    n.display_str() if n is not None else 'None'
                    for n in self.nodelist[:2]
                ])
                + (" …" if list_len > 2 else '')
            )
        return "list of nodes (" + str(list_len) + ")" + list_preview

    def accept_node_visitor(self, visitor):
        if self.nodelist is not None:
            for node in self.nodelist:
                if node is not None:
                    node.accept_node_visitor(visitor)
        visitor.visit_node_list(self)


    def filter(self, node_predicate_fn=None,
               skip_none=True, skip_comments=False, skip_whitespace_char_nodes=False):

        if self.latex_walker is not None:
            make_nodelist = self.latex_walker.make_nodelist
        else:
            make_nodelist = lambda nl, **kwargs: LatexNodeList(nl, **kwargs)
        
        def filter_full_predicate_fn(n):
            if skip_none and n is None:
                return False
            if skip_comments and n.isNodeType(LatexCommentNode):
                return False
            if skip_whitespace_char_nodes and n.isNodeType(LatexCharsNode) \
               and len(n.chars.strip()) == 0:
                return False
            if node_predicate_fn is not None:
                return node_predicate_fn(n)
            return True

        filtered_nodes = [
            n
            for n in self.nodelist
            if filter_full_predicate_fn(n)
        ]

        return make_nodelist(
            filtered_nodes,
            parsing_state=self.parsing_state,
            # give a meaningful pos/pos_end, both equal to our own pos_end, in
            # case no nodes satisfied the predicates
            pos=(None if len(filtered_nodes) else self.pos_end),
            pos_end=(None if len(filtered_nodes) else self.pos_end),
        )
    

    def split_at_node(self, node_predicate_fn, skip_none=True, keep_separators=False,
                      max_split=None):

        nodelists_list = [ [] ]

        if max_split is not None and max_split == 0:
            no_more_splits = True
        else:
            no_more_splits = False

        for n in self.nodelist:
            if skip_none and n is None:
                continue
            if not no_more_splits and node_predicate_fn(n):
                if keep_separators:
                    nodelists_list.append([n])
                else:
                    nodelists_list.append([])
                    
                if max_split is not None and len(nodelists_list) >= max_split:
                    no_more_splits = True
            else:
                nodelists_list[len(nodelists_list)-1].append(n)
        
        if self.latex_walker is not None:
            make_latex_node_list = self.latex_walker.make_nodelist
        else:
            make_latex_node_list = lambda nl, **kwargs: LatexNodeList(nl, **kwargs)

        return [
            make_latex_node_list(nl, parsing_state=self.parsing_state)
            for nl in nodelists_list
        ]

    def split_at_chars(self, sep_chars, max_split=None, keep_empty=False, skip_none=True):
        r"""
        Split the node list into multiple node lists corresponding to chunks
        delimited by the given `sep_chars`.

        More precisely, this method iterates over the node list, collecting
        nodes as they are iterated over.  In simple character nodes, every
        occurrence of `sep_chars` causes a new list to be initiated.

        This method is useful to split arguments delimited by tokens, e.g.::

            \cite{key1,key2,my{special,key},keyN}

        In the above example, splitting the argument of the ``\cite`` command
        with the ``,`` separator yields four node lists ``[ (node for "key1")
        ]``, ``[ (node for "key2") ]``, ``[ (chars node for "my"), (group node
        for "{special,key}" ...) ]``, and ``[ (node for "keyN") ]``.

        If `sep_chars` is a Python callable object, then it is assumed to be a
        function that, when called with a string and a position, returns either
        a pair (index, len) the index of next separator start position and end
        position to use to split the string, or an object with `start()` and
        `end()` methods that returns those positions (e.g., a regex match
        object); return `None`, a strictly negative start index, an empty list
        to indicate splitting is done.  To split at a regex, for instance, you
        can use::

            # make sure there are no capturing parentheses, see re.split()
            rx_space = re.compile(r'\s+')

            # rx_object is also accepted
            split_node_lists = nodelist.split_at_chars(rx_space)

        If `sep_chars` is a Regular expression (or any object with a `search()`
        method returning match-like objects with `start()` and `end()`).
        """
        
        # untested code !

        split_node_lists = []
        
        def get_split_match_start_end(m, offset=0):
            if m is None:
                return (-1, None)
            if hasattr(m, 'start') and hasattr(m, 'end'):
                return (offset+m.start(), offset+m.end())
            if not m or not len(m):
                return (-1, None)
            start, end = m
            if start is None:
                start = -1
            else:
                start = offset + start
            end = offset + end
            return start, end

        def get_next_split(chars, pos):

            if max_split is not None and len(split_node_lists) >= max_split:
                return (-1, len(chars))

            if hasattr(sep_chars, 'search'):
                #__pragma__('skip')
                return get_split_match_start_end(sep_chars.search(chars, pos))
                #__pragma__('noskip')
                # Transcrypt's implementation of regexp.search(chars, pos) seems
                # buggy, so use the following code instead:
                m = sep_chars.search(chars[pos:])
                return get_split_match_start_end(m, pos)

            if callable(sep_chars):
                m = sep_chars(chars, pos)
                return get_split_match_start_end(m)

            idx = chars.find(sep_chars, pos)
            if idx is None or idx == -1:
                return (-1, None)
            return (idx, idx+len(sep_chars))


        lw = self.latex_walker
        if lw is not None:
            make_node = lw.make_node
            make_nodelist = lw.make_nodelist
        else:
            make_node = lambda cls, **kwargs: cls(**kwargs)
            make_nodelist = lambda nl, **kwargs: LatexNodeList(nl, **kwargs)

        def chars_to_node(chars, n, rel_pos, rel_pos_end):
            return make_node(LatexCharsNode,
                             parsing_state=self.parsing_state,
                             pos=n.pos + rel_pos,
                             pos_end=n.pos + rel_pos_end,
                             chars=chars)

        def flush_nodes(nodes, pos_end=None):
            newnodelist = make_nodelist(
                nodes,
                parsing_state=self.parsing_state,
                pos=None if len(nodes) else pos_end, # auto-detect from nodes if applicable
                pos_end=pos_end,
            )
            split_node_lists.append(newnodelist)

        pending_nodes = []

        for n in self.nodelist:

            if n is None:
                if not skip_none:
                    pending_nodes.append(n)
                continue

            if n.isNodeType(LatexCharsNode):

                next_sep_end = 0

                while True:
                    prev_sep_end = next_sep_end
                    next_sep_idx, next_sep_end = get_next_split(n.chars, prev_sep_end)

                    if next_sep_idx != -1:
                        p = n.chars[prev_sep_end:next_sep_idx]
                        if prev_sep_end == 0:
                            # This is the first match in the string. We might
                            # need to merge the first chunk with earlier pending
                            # nodes.
                            #
                            # There might already be nodes pending to be
                            # collected into a part; add the first chunk up to
                            # the first separator to those pending nodes (if
                            # applicable), and flush them into a section
                            if len(p):
                                pending_nodes.append(
                                    chars_to_node(p, n, prev_sep_end, next_sep_idx)
                                )
                            if len(pending_nodes) or keep_empty:
                                flush_nodes(pending_nodes, pos_end=n.pos+next_sep_idx)
                            pending_nodes = []
                            continue
                        else:
                            # separator encountered, add as a part to the split
                            # nodes list
                            thenodes = []
                            if len(p):
                                thenodes = [
                                    chars_to_node(p, n, prev_sep_end, next_sep_idx)
                                ]
                            if len(thenodes) or keep_empty:
                                flush_nodes(thenodes, pos_end=n.pos+next_sep_idx)
                            continue
                    else:
                        if prev_sep_end == 0:
                            # The string in this node did not contain any
                            # separator chars at all.  Simply add the entire
                            # node to the pending chars and stop here.
                            pending_nodes.append(n)
                            break
                        else:
                            # last bits of chars is part of a new part.  Add to
                            # pending_nodes and continue.
                            p = n.chars[prev_sep_end:]
                            if len(p):
                                pending_nodes.append(
                                    chars_to_node(p, n, prev_sep_end, len(n.chars))
                                )
                            break
                        # in all cases, we're done searching through this char
                        # node's string content
                        #break

                continue

            pending_nodes.append( n )

        if pending_nodes or keep_empty:
            flush_nodes(pending_nodes, pos_end=self.pos_end)

        return split_node_lists



    def get_content_as_chars(self):
        r"""
        Return the character string content associated with this node list, which is
        assumed to contain only characters, comments, or group nodes that
        contain such nodes.

        This method is useful to extract character arguments from macro calls
        with an argument that requires a single string, such as
        ``\label{my-label}`` or ``\href{https://example.com/}{..}``.  It also
        allows you to handle cases like ``\item[{*}]`` that result in nested
        group nodes.

        Group node delimiters (if applicable) are not included in the returned
        string.
        """
        return _get_content_as_chars(self.nodelist)



    def __eq__(self, other):
        if isinstance(other, list):
            return self.nodelist == other
        return (
            self.nodelist == other.nodelist
            # the "pos is None and other.pos is None" checks are there for transcrypt ...
            and ((self.pos is None and other.pos is None) or self.pos == other.pos)
            and ((self.pos_end is None and other.pos_end is None)
                 or self.pos_end == other.pos_end)
        )


    def to_json_object(self):
        return self.nodelist

    def __repr__(self):
        return 'LatexNodeList({nodelist!r}, pos={pos!r}, pos_end={pos_end!r})'.format(
            nodelist=self.nodelist,
            pos=self.pos,
            pos_end=self.pos_end
        )



def _get_content_as_chars(nodelist):

    # having a separate global method protects against group nodes that might
    # have a list instead of a LatexNodeList instance as their `nodelist`
    # attribute, by accident...

    if nodelist is None:
        return ''

    charslist = []

    for n in nodelist:

        if n is None:
            continue

        if n.isNodeType(LatexCommentNode):
            # skip comments
            continue

        if n.isNodeType(LatexGroupNode):
            # go recursively
            charslist.append( _get_content_as_chars(n.nodelist) )
            continue

        if n.isNodeType(LatexCharsNode):
            charslist.append(n.chars)
            continue

        raise LatexWalkerParseError(
            "Expected simple characters only, got ‘{}’".format(n.__class__.__name__),
            pos=n.pos
        )

    return "".join(charslist)



# ------------------------------------------------------------------------------


def _update_posposend_from_nodelist(pos, pos_end, nodelist):

    if pos is None:
        for n in nodelist:
            if n is not None:
                pos = n.pos
                break
        else:
            pos = None

    if pos_end is None:
        for n in reversed(nodelist):
            if n is not None:
                pos_end = n.pos_end
                break
        else:
            pos_end = None

    return pos, pos_end




# ------------------------------------------------------------------------------


class LatexNodesVisitor(object):
    r"""
    Implement a visitor pattern on a node structure.

    Doc ......................

    .. versionadded: 3.0

       The `LatexNodesVisitor` class was introduced in `pylatexenc 3.0`.
    """

    def visit(self, node):
        r"""
        Fallback for visiting any type of node.  This is called by the `visit_XXX()`
        methods below.  In your subclass, you can reimplement a subset of the
        `visit_XXXX()` methods, and whichever objects you didn't reimplement the
        `visit_XXX()` method for, you can catch with the `visit()` method.
        """
        pass

    def visit_chars_node(self, node):
        self.visit(node)

    def visit_group_node(self, node):
        self.visit(node)

    def visit_comment_node(self, node):
        self.visit(node)

    def visit_macro_node(self, node):
        self.visit(node)

    def visit_environment_node(self, node):
        self.visit(node)

    def visit_specials_node(self, node):
        self.visit(node)

    def visit_math_node(self, node):
        self.visit(node)

    def visit_node_list(self, nodes):
        self.visit(nodes)

    def visit_parsed_arguments(self, parsed_args):
        self.visit(parsed_args)


    def visit_unknown_node(self, node):
        self.visit(node)


    # --

    def start(self, node):
        r"""
        A shortcut for calling `node.accept_node_visitor()` with this visitor
        object.  It's a convenient starting point for your visiting pattern:

        .. code::

           visitor = MyNodeVisitor()
           visitor.start(node)

        You probably shouldn't override this method in your visitor subclass.
        """
        node.accept_node_visitor(self)



#
# ------------------------------------------------------------------------------
#

# we'll be using "from _types import *" for convenience, so to avoid polluting
# the other modules' namespaces, we define __all__ here.


# use tuple()  so that this can be used in " isinstance(x, latex_node_types) "
latex_node_types = (
    LatexNode,
    LatexCharsNode,
    LatexGroupNode,
    LatexCommentNode,
    LatexMacroNode,
    LatexEnvironmentNode,
    LatexSpecialsNode,
    LatexMathNode
)

__all__ = [ nc.__name__ for nc in latex_node_types ] + [
    'LatexNodeList',
    'LatexNodesVisitor',
]


