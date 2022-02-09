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

from ._parsedargs import ParsedMacroArgs


# for Py3
_unicode_from_str = lambda x: x

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _unicode_from_str = lambda x: x.decode('utf-8')
## End Py2 support code



# we'll be using "from _types import *" for convenience, so to avoid polluting
# the other modules' namespaces, we define __all__ here.

__all__ = [
    'LatexNode',
    'LatexCharsNode',
    'LatexGroupNode',
    'LatexCommentNode',
    'LatexMacroNode',
    'LatexEnvironmentNode',
    'LatexSpecialsNode',
    'LatexMathNode',
    'LatexNodeList',
]



# ------------------------------------------------------------------------------



class LatexNode(object):
    """
    Represents an abstract 'node' of the latex document.

    Use :py:meth:`nodeType()` to figure out what type of node this is, and
    :py:meth:`isNodeType()` to test whether it is of a given type.

    You should use :py:meth:`LatexWalker.make_node()` to create nodes, so that
    the latex walker has the opportunity to do some additional setting up.

    All nodes have the following attributes:

    .. py:attribute:: parsing_state

       The parsing state at the time this node was created.  This object stores
       additional context information for this node, such as whether or not this
       node was parsed in a math mode block of LaTeX code.

       See also the :py:meth:`LatexWalker.make_parsing_state()` and the
       `parsing_state` argument of :py:meth:`LatexWalker.get_latex_nodes()`.

    .. py:attribute:: pos

       The position in the parsed string that this node represents.  The parsed
       string can be recovered as `parsing_state.s`, see
       :py:attr:`ParsingState.s`.

    .. py:attribute:: pos_end

       The position in the parsed string that is immediately after the present
       node.  The parsed string can be recovered as `parsing_state.s`, see
       :py:attr:`ParsingState.s`.

    .. py:attribute:: len

       (Read-only attribute.)  How many characters in the parsed string this
       node represents, starting at position `pos`.  The parsed string can be
       recovered as `parsing_state.s`, see :py:attr:`ParsingState.s`.

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

        This is a shorthand for ``node.parsing_state.s[node.pos:node.pos_end]``.
        """
        if self.parsing_state is None:
            raise TypeError("Can't use latex_verbatim() on node because we don't "
                            "have any parsing_state set")
        return self.parsing_state.s[self.pos : self.pos_end]

    def __eq__(self, other):
        return other is not None  and  \
            self.nodeType() == other.nodeType()  and  \
            other.parsing_state is self.parsing_state and \
            other.latex_walker is self.latex_walker and \
            other.pos == self.pos and \
            other.pos_end == self.pos_end and \
            all(
                ( getattr(self, f) == getattr(other, f)  for f in self._fields )
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
            ", ".join([ "%s=%r"%(k,getattr(self,k))  for k in self._fields ]) +
            ")"
            )


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
            else:
                d[fld] = self.__dict__[fld]
        d.update(latexwalker.pos_to_lineno_colno(self.pos, as_dict=True))
        return d



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

       The :py:class:`pylatexenc.macrospec.ParsedMacroArgs` object that
       represents the macro arguments.

       For macros that do not accept any argument, this is an empty
       :py:class:`~pylatexenc.macrospec.ParsedMacroArgs` instance.  The
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
        nodeargd = kwargs.pop('nodeargd', ParsedMacroArgs())
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

    #

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

       The :py:class:`pylatexenc.macrospec.ParsedMacroArgs` object that
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
        nodeargd = kwargs.pop('nodeargd', ParsedMacroArgs())
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

    @property
    def envname(self):
        # Obsolete, don't use.
        return self.environmentname

    # @property
    # def optargs(self):
    #     return None
    # @property
    # def args(self):
    #     return self.nodeargd.argnlist

    def nodeType(self):
        return LatexEnvironmentNode


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
       is a :py:class:`pylatexenc.macrospec.ParsedMacroArgs` instance that 
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


    .. py:attribute:: len

       (Read-only attribute.)  The total length spanned by this node list,
       assuming that the `nodelist` represents a single continuous sequence of
       nodes in the latex string.
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

        self.parsing_state = kwargs.pop('parsing_state', None)
        self.latex_walker = kwargs.pop('latex_walker', None)
        self.pos = kwargs.pop('pos', None)
        self.pos_end = kwargs.pop('pos_end', None)

        if kwargs:
            raise ValueError("Unexpected keyword arguments to LatexNodeList: "
                             + repr(kwargs))

        self.pos, self.pos_end = \
            _update_posposend_from_nodelist(self.pos, self.pos_end, self.nodelist)


    @property
    def len(self):
        if self.pos is None or self.pos_end is None:
            return None
        return self.pos_end - self.pos

    def __getitem__(self, index):
        # supports slicing, too, and returns a simple list in such cases
        if isinstance(index, int) and index < 0:
            # do this manually here for potential future use with transcrypt,
            # where negative indexing is not supported.
            index = len(self.nodelist) + index
        return self.nodelist[index]

    def __len__(self):
        return len(self.nodelist)
    
    
    def split_at_chars(self, sep_chars):
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
        function that, when called with a string, returns a list of strings
        corresponding to the string split at the desired locations.  To split at
        a regex, for instance, you can use::

            # make sure there are no capturing parentheses, see re.split()
            rx_space = re.compile(r'\s+')

            split_node_lists = nodelist.split_at_chars(rx_space.split)
        """
        

        # untested code !

        split_node_lists = []
        
        if callable(sep_chars):
            sep_chars_fn = sep_chars
        else:
            sep_chars_fn = lambda chars, sep_chars=sep_chars: chars.split(sep_chars)

        lw = self.latex_walker
        if lw is not None:
            make_node = lw.make_node
        else:
            make_node = lambda cls, **kwargs: cls(**kwargs)

        def chars_to_node(chars, orig_node, rel_pos):
            pos = orig_node.pos + rel_pos
            return make_node(LatexCharsNode,
                             parsing_state=self.parsing_state,
                             pos=pos,
                             pos_end=pos + len(chars),
                             chars=chars)

        pending_nodes = []

        for n in self.nodelist:
            if n.isNodeType(latexwalker.LatexCharsNode):
                parts = sep_chars_fn(n.chars)
                rel_pos = 0
                if parts[0]:
                    pending_nodes.append( chars_to_node(parts[0], n, 0) )
                    rel_pos = len(parts[0])
                    parts = parts[1:]
                if not parts:
                    # string didn't contain any separator
                    continue
                if pending_nodes:
                    split_node_lists.append(pending_nodes)
                    pending_nodes = []
                for p in parts:
                    split_node_lists.append( [ chars_to_node(p, n, rel_pos) ] )
                    rel_pos += len(p)

                continue

            pending_nodes.append( n )

        if pending_nodes:
            split_node_lists.append(pending_nodes)

        return split_node_lists
        

    def __eq__(self, other):
        return (
            self.nodelist == other.nodelist
            and self.pos == other.pos
            and self.pos_end == other.pos_end
        )


    def to_json_object(self):
        return self.nodelist

    def __repr__(self):
        import pprint
        return 'LatexNodeList({nodelist}, pos={pos!r}, pos_end={pos_end!r})'.format(
            nodelist=pprint.pformat(self.nodelist),
            pos=self.pos,
            pos_end=self.pos_end
        )




# ------------------------------------------------------------------------------


def _update_posposend_from_nodelist(pos, pos_end, nodelist):

    if pos is None:
        pos = next( (n.pos for n in nodelist if n is not None),
                    None )

    if pos_end is None:
        pos_end = next( (n.pos_end for n in reversed(nodelist) if n is not None),
                        None )

    return pos, pos_end
