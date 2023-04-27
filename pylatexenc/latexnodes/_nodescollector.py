# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2022 Philippe Faist
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

import logging
logger = logging.getLogger(__name__)

from ._exctypes import *
from .nodes import *


from ._parsingstatedelta import (
    ParsingStateDeltaReplaceParsingState,
    ParsingStateDeltaEnterMathMode,
    get_updated_parsing_state_from_delta,
)


class LatexNodesCollector(object):
    r"""
    Process a stream of LaTeX tokens and convert them into a list of nodes.

    The `LatexNodesCollector` class functions hand-in-hand with parsers to
    transform tokens into nodes.  A parser such as
    :py:class:`~pylatexenc.latexnodes.parsers.LatexGeneralNodesParser` might set
    up the parsing state correctly and then defer to a `LatexNodesCollector`
    instance to actually parse a bulk of contents.  The `LatexNodesCollector`
    instance, on the other hand, recurses down to calling parsers when we
    encounter new macros, environments, specials, etc. in the bulk that is being
    parsed.  The result is a node list containing a full tree of child nodes
    that represents the logical structure of the tokens that were encountered.
    
    The public API of this class resides essentially in the
    :py:meth:`process_tokens()`, as well as the :py:meth:`get_final_nodelist()`
    (and some other friends, see docs below).


    .. versionadded:: 3.0
    
       The :py:class:`LatexNodesCollector` class was added in `pylatexenc 3.0`.
    """

    class ReachedEndOfStream(Exception):
        r"""
        Raised by the :py:meth:`process_one_token()` method if we reached the end of
        stream.
        
        You should not have to worry about this exception unless you call
        :py:meth:`process_one_token()` yourself.  But most of the time you'll be
        calling :py:meth:`process_tokens()` instead, which does not raise this
        exception; it directly raises :py:exc:`LatexWalkerEndOfStream` as the
        higher-level parsers do.
        """
        pass

    class ReachedStoppingCondition(Exception):
        r"""
        Raised by the :py:meth:`process_one_token()` method to indicate that a
        stopping condition was met.
        
        You should not have to worry about this exception unless you call
        :py:meth:`process_one_token()` yourself.  But most of the time you'll be
        calling :py:meth:`process_tokens()` instead, which simply stops
        processing tokens if a stopping condition is met.
        """
        def __init__(self, stop_data, **kwargs):
            super(LatexNodesCollector.ReachedStoppingCondition, self).__init__(**kwargs)
            self.stop_data = stop_data


    def __init__(self,
                 latex_walker,
                 token_reader,
                 parsing_state,
                 stop_token_condition=None,
                 stop_nodelist_condition=None,
                 make_child_parsing_state=None,
                 include_stop_token_pre_space_chars=True,
                 ):

        super(LatexNodesCollector, self).__init__()

        self.latex_walker = latex_walker
        self.token_reader = token_reader

        self.stop_token_condition = stop_token_condition
        self.stop_nodelist_condition = stop_nodelist_condition

        self.include_stop_token_pre_space_chars = include_stop_token_pre_space_chars

        self._stop_token_condition_met = False
        # the token that caused the condition to be met:
        self._stop_token_condition_met_token = None
        self._stop_nodelist_condition_met = False
        self._stop_condition_stop_data = None
        self._reached_end_of_stream = False

        # current parsing state. This attribute might change as we parse tokens
        # and nodes.
        self.parsing_state = parsing_state

        self.start_parsing_state = parsing_state

        # a node list that we are building
        self._nodelist = []

        # characters that we are accumulating
        self._pending_chars_pos = None
        self._pending_chars = ''

        # whether finalize() was called or not
        self._finalized = False

        # override custom function to make the child parsing state
        self._make_child_parsing_state_fn = make_child_parsing_state



    def get_final_nodelist(self):
        r"""
        Returns the final nodelist collected from the processed tokens.

        The return value is a
        :py:class:`~pylatexenc.latexnodes.nodes.LatexNodeList` instance.
        """
        if not self._finalized:
            raise RuntimeError("Call to get_final_nodelist() before finalize()")

        return self.latex_walker.make_nodelist(
            nodelist=self._nodelist,
            parsing_state=self.start_parsing_state,
        )


    def get_parser_parsing_state_delta(self):
        r"""
        Doc. ............
        """
        if not self._finalized:
            raise RuntimeError("Call to get_parser_parsing_state_delta() before finalize()")

        if self.start_parsing_state is self.parsing_state:
            # we ended with the same object as the initial parsing state
            return None

        # report our updated parsing state
        return ParsingStateDeltaReplaceParsingState(set_parsing_state=self.parsing_state)


    def pos_start(self):
        r"""
        Returns the first position of nodes in the collected node list (collected up
        to this point).
        """
        try:
            # transcrypt doesn't seem to support default value in next(iter, default)
            p = next( ( n.pos for n in self._nodelist if n is not None ) )
        except StopIteration:
            p = None
        if p is not None:
            return p
        return self._pending_chars_pos

    def pos_end(self):
        r"""
        Returns the position immediately after the last node in the collected node
        list (collected up to this point).
        """
        try:
            # transcrypt doesn't seem to support default value in next(iter, default)
            lastnode = next( ( n for n in reversed(self._nodelist) if n is not None ) )
        except StopIteration:
            lastnode = None
        if lastnode is None:
            return None
        return lastnode.pos_end


    def stop_token_condition_met(self):
        r"""
        Returns `True` if the condition set as `stop_token_condition` was met while
        processing tokens.
        """
        return self._stop_token_condition_met

    def stop_token_condition_met_token(self):
        r"""
        Returns the token that caused the stop condition to be met.
        """
        return self._stop_token_condition_met_token

    def stop_nodelist_condition_met(self):
        r"""
        Returns `True` if the condition set as `stop_nodelist_condition` was met
        while processing tokens.
        """
        return self._stop_nodelist_condition_met

    def stop_condition_stop_data(self):
        r"""
        If a stopping condition was met, returns whatever the stopping condition
        callback returned that was non-`None` and caused the processing to stop.
        """
        return self._stop_condition_stop_data

    def reached_end_of_stream(self):
        r"""
        Returns `True` if we reached the end of the stream.
        """
        return self._reached_end_of_stream


    def is_finalized(self):
        r"""
        Whether this object's node list has been finalized.

        Once the object is finalized, you cannot parse any more tokens.  See
        :py:meth:`finalize()`.
        """
        return self._finalized

    def finalize(self):
        r"""
        Finalize this object's node list.  This ensures that any pending characters
        that were read are collected into a final chars node.  (In the future,
        there might be other tasks to perform to finalize the node list.)

        Normally you don't have to worry about calling `finalize()` yourself,
        because it is automatically called by :py:meth:`process_tokens()`.  You
        should only worry about calling `finalize()` if you are calling
        `process_one_token()` manually.

        Once you call `finalize()`, you can no longer make any further calls to
        :py:meth:`process_tokens()` or :py:meth:`process_one_token()`.
        """
        if self._finalized:
            return

        exc = self.flush_pending_chars()

        self._finalized = True

        if exc is not None:
            logger.debug('finalize(): raising exc=%r', exc)
            raise exc


    # -----

    #
    # "Protected methods" -- should only be called by subclasses' dervied
    # methods.
    #

    def push_pending_chars(self, chars, pos):
        r"""
        This method should only be called internally or by subclass derived methods.
    
        Adds `chars` to the pending chars string, i.e., the latest chars that we
        have seen that will have to be collected into a chars node once we
        encounter anything other than a regular char.
        """
        self._pending_chars += chars
        if self._pending_chars_pos is None:
            self._pending_chars_pos = pos

    def flush_pending_chars(self):
        r"""
        This method should only be called internally or by subclass derived methods.
    
        Create a chars node out of all the pending chars that were added with
        calls to `push_pending_chars()`.  Adds the chars node to the node list,
        and clears the pending chars string.
        """
        if not self._pending_chars:
            # no pending chars to flush
            return None

        charspos, chars = self._pending_chars_pos, self._pending_chars
        self._pending_chars = ''
        self._pending_chars_pos = None

        strnode = self.latex_walker.make_node(
            LatexCharsNode,
            parsing_state=self.parsing_state,
            chars=chars,
            pos=charspos,
            pos_end=charspos+len(chars),
        )
        return self.push_to_nodelist(strnode)

    def push_to_nodelist(self, node):
        r"""
        This method should only be called internally or by subclass derived methods.

        Add the given node to the final node list that we are building.
        """

        if self._finalized:
            raise RuntimeError("You already called finalize()")

        self._nodelist.append(node)

        exc = self._check_nodelist_stop_condition()
        if exc is not None:
            return exc
        return None


    def update_state_from_parsing_state_delta(self, parsing_state_delta):
        r"""
        This method should only be called internally or by subclass derived methods.

        Update our `parsing_state` attribute to account for any parsing state
        changes information that might have been provided by some parsed
        construct (say, a macro call).
        """

        if parsing_state_delta is not None:
            ps = self.parsing_state

            self.parsing_state = parsing_state_delta.get_updated_parsing_state(
                self.parsing_state,
                self.latex_walker
            )

            logger.debug("Updated parsing state using parsing_state_delta %r: %r →→→ %r",
                         parsing_state_delta, ps, self.parsing_state)



    # ------------------


    def _check_nodelist_stop_condition(self):
        stop_nodelist_condition = self.stop_nodelist_condition
        if stop_nodelist_condition is not None:
            stop_data = stop_nodelist_condition(self._nodelist)
            if stop_data:
                self._stop_nodelist_condition_met = True
                logger.debug("nodes collector reached nodelist stop condition; nodelist = %r",
                             self._nodelist)
                return LatexNodesCollector.ReachedStoppingCondition(stop_data=stop_data)
        return None

    def _check_token_stop_condition(self, tok):
        stop_token_condition = self.stop_token_condition
        if stop_token_condition is not None:
            stop_data = stop_token_condition(tok)
            if stop_data:
                self._stop_token_condition_met = True
                self._stop_token_condition_met_token = tok
                logger.debug("nodes collector reached token stop condition; tok = %r, "
                             "current node list = %r",
                             tok, self._nodelist)
                return LatexNodesCollector.ReachedStoppingCondition(stop_data=stop_data)
        return None


    def process_tokens(self):
        r"""
        Read tokens from `token_reader` until either we reach the end of the stream,
        or a stopping condition is met.

        This function never returns anything interesting.

        In all cases, the object is finalized (see :py:meth:`finalize()`) before
        this method finishes its execution, regardless of whether the function
        finishes by normal return or by raising an exception.

        You can inspect the reason that caused the end of the processing using
        the methods :py:meth:`stop_token_condition_met()`,
        :py:meth:`stop_nodelist_condition_met()` and
        :py:meth:`reached_end_of_stream()`.
        
        You can then call :py:meth:`get_final_nodelist()` to get the nodelist,
        :py:meth:`get_parser_parsing_state_delta()` to get any carry-over information
        for the parser for future parsing, etc.
        """

        try:
            while True:
                self.process_one_token()

        except LatexNodesCollector.ReachedStoppingCondition as e:
            # all good! We finished collecting our node list.
            self._stop_condition_stop_data = e.stop_data
            logger.debug("nodes collector process_tokens() reached stop condition")
            return

        except LatexNodesCollector.ReachedEndOfStream as e:
            # all good!  We reached the end of the input.  Note that any final
            # space has already been included into a chars node in the nodelist.
            self._reached_end_of_stream = True
            logger.debug("nodes collector process_tokens() reached end of stream")
            return

        except LatexWalkerError as e:
            # we got an error! We'll let whoever called us process this
            logger.debug("process_tokens() - relaying error -- %r", e)
            raise

        finally:
            self.finalize()




    def process_one_token(self):
        r"""
        Read a single token and process it, recursing into brace blocks and
        environments etc if needed, and appending stuff to nodelist.

        Whereas :py:meth:`process_tokens()` gathers tokens into nodes until a
        stopping condition is met or until the end of the stream is reached, the
        `process_one_token()` provides finer control on the execution of the
        process of collecting tokens and gathering them into nodes.

        .. warning::

           Normally, it is better to use `process_tokens()` directly.  If you
           want to read a single node, simply set a stopping condition that
           stops for instance once the node list has length at least one.

           The `process_one_token()` method requires you to take care of some
           tasks yourself, which are normally automatically taken care of by
           :py:meth:`process_tokens()`.  Read on below for more information.

        A number of tasks that are taken care of by :py:meth:`process_tokens()`
        are NOT taken care of here:

        - If an end of stream is reached, we raise the exception
          `LatexNodesCollector.ReachedEndOfStream`.  It's up to you to catch it
          and do something relevant.

        - If a stopping condition is met, we raise the exception
          `LatexNodesCollector.ReachedStoppingCondition`.  It's up to you to
          catch it and do something relevant.

        - The function returns normally (without any return value) if neither a
          stopping condition is met nor the end of stream is met.  Normally,
          this means we should continue processing tokens.

        - You have to take care that you call :py:meth:`finalize()` on the nodes
          collector instance once you're done processing tokens.
        """

        if self._finalized:
            raise RuntimeError("You already called finalize()")

        latex_walker = self.latex_walker
        token_reader = self.token_reader

        try:

            tok = token_reader.next_token(parsing_state=self.parsing_state)
            logger.debug("nodes collector read token %r", tok)

        except LatexWalkerEndOfStream as e:
            final_space = getattr(e, 'final_space', None)
            if final_space:
                # process the final space as an extra char token
                final_space_pos = token_reader.cur_pos()+len(final_space)
                tok = token_reader.make_token(
                    tok='char',
                    arg='',
                    pre_space=final_space,
                    pos=final_space_pos,
                    pos_end=final_space_pos,
                )
                token_reader.move_past_token(tok)
            else:
                #print("*** reached end of stream!")
                exc = LatexNodesCollector.ReachedEndOfStream()
                exc.pos_end = token_reader.cur_pos()
                logger.debug('process_one_token(): reached end of stream, exc=%r', exc)
                raise exc


        # first, let's check if a token-based stopping condition is met.
        
        stop_exc = self._check_token_stop_condition(tok)
        if stop_exc is not None:
            if self.include_stop_token_pre_space_chars:
                # quickly push the pre_space whitespace into the pending chars
                # so they get included into the content, as well
                self.push_pending_chars(
                    chars=tok.pre_space,
                    pos=tok.pos - len(tok.pre_space),
                )
                rewind_pre_space=False
            else:
                rewind_pre_space=True
            # leave the token in the input stream if it generated a stopping
            # condition.
            token_reader.move_to_token(tok, rewind_pre_space=rewind_pre_space)
            stop_exc.pos_end = tok.pos_end
            logger.debug('process_one_token(): stop token condition reached, exc=%r', stop_exc)
            raise stop_exc

        # if it's a char, just append it to the stream of last "pending"
        # characters.
        if tok.tok == 'char':
            self.push_pending_chars(
                chars=(tok.pre_space + tok.arg),
                pos=(tok.pos - len(tok.pre_space)),
            )
            return

        # if it's not a char, push the last pending chars into the node list
        # before we do anything else (include the present token's pre_space)
        if self._pending_chars:
            self._pending_chars += tok.pre_space
            tok.pre_space = ''
            stop_exc = self.flush_pending_chars()
            if stop_exc is not None:
                # rewind to position immediately after the new token's
                # pre_space, because we didn't parse that new token yet but we
                # absorbed its pre_space
                token_reader.move_to_token(tok, rewind_pre_space=False)
                stop_exc.pos_end = tok.pos
                logger.debug('process_one_token(): stop condition reached (a), exc=%r',
                             stop_exc)
                raise stop_exc

        # If we have pre_space, add a separate chars node that contains the
        # spaces.  We do this seperately, so that latex2text can ignore these
        # groups by default to avoid too much space on the output.  This allows
        # latex2text to implement the `strict_latex_spaces=...` flag correctly.

        elif tok.pre_space:
            spacestrnode = latex_walker.make_node(LatexCharsNode,
                                                  parsing_state=self.parsing_state,
                                                  chars=tok.pre_space,
                                                  pos=tok.pos-len(tok.pre_space),
                                                  pos_end=tok.pos)
            tok.pre_space = ''
            stop_exc = self.push_to_nodelist(spacestrnode)
            if stop_exc is not None:
                # rewind to position immediately after the new token's
                # pre_space, because we didn't parse that new token yet but we
                # absorbed its pre_space
                token_reader.move_to_token(tok, rewind_pre_space=False)
                stop_exc.pos_end = tok.pos
                logger.debug('process_one_token(): stop condition reached (b), exc=%r',
                             stop_exc)
                raise stop_exc

        # now, process the encountered token `tok`, keeping in mind that the
        # pre_space has already been dealt with.

        # check for tokens that are illegal in this context

        if tok.tok == 'brace_close':
            raise LatexWalkerNodesParseError(
                msg=("Unexpected mismatching closing delimiter ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_past_token=tok,
                error_type_info={
                    'what': 'nodes_unexpected_closing_group_delimiter',
                    'delimiter': tok.arg,
                },
            )

        if tok.tok == 'end_environment':
            raise LatexWalkerNodesParseError(
                msg=("Unexpected closing environment: ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_past_token=tok,
                error_type_info={
                    'what': 'nodes_unexpected_end_environment',
                    'environmentname': tok.arg,
                },
            )

        if tok.tok in ('mathmode_inline', 'mathmode_display') \
           and tok.arg not in self.parsing_state._math_delims_info_by_open:
            # an unexpected closing math mode delimiter
            raise LatexWalkerNodesParseError(
                msg="Unexpected closing math mode token ‘{}’".format(
                    tok.arg,
                ),
                pos=tok.pos,
                recovery_past_token=tok,
                error_type_info={
                    'what': 'nodes_unexpected_closing_math_delimiter',
                    'mathmode_type': tok.tok,
                    'delimiter': tok.arg,
                },
            )

        # now we can start parsing the token and taking the appropriate action.

        if tok.tok == 'comment':
            self.parse_comment_node(tok)
            return

        elif tok.tok == 'brace_open':
            # a braced group.
            self.parse_latex_group(tok)
            return

        elif tok.tok == 'macro':

            self.parse_macro(tok)
            return

        elif tok.tok == 'begin_environment':
            
            self.parse_environment(tok)
            return

        elif tok.tok == 'specials':

            self.parse_specials(tok)
            return

        elif tok.tok in ('mathmode_inline', 'mathmode_display'):

            self.parse_math(tok)
            return

        else:
            
            raise LatexWalkerParseError(
                "Unknown token type: {}".format(tok.tok),
                pos=tok.pos
            )



    # ------------------

    #
    # Methods that can be reimplemented:
    #

    def make_child_parsing_state(self, parsing_state, node_class):
        r"""
        Create a parsing state a child node of the given type `node_class`.

        You can reimplement this method to customize the parsing state of child
        nodes.
        """
        if self._make_child_parsing_state_fn is not None:
            return self._make_child_parsing_state_fn(parsing_state=parsing_state,
                                                     node_class=node_class)
        return self.parsing_state


    def parse_comment_node(self, tok):
        r"""
        Process a token that introduces a comment. The token `tok` is of type
        ``tok.tok == 'comment'``.

        The default implementation creates a :py:class:`LatexCommentNode` and
        pushes it onto the node list.

        This method can be reimplemented to customize its behavior.
        Implementations should create the relevant node(s) and push them onto
        the node list with a call to :py:meth:`push_to_nodelist()` (refer to
        that method's doc).
        """

        commentnode = self.latex_walker.make_node(
                LatexCommentNode,
                parsing_state=self.parsing_state,
                comment=tok.arg,
                comment_post_space=tok.post_space,
                pos=tok.pos,
                pos_end=tok.pos_end
        )

        stop_exc = self.push_to_nodelist( commentnode )
        if stop_exc is not None:
            stop_exc.pos_end = tok.pos_end
            logger.debug('parse_comment_node(): stop_exc=%r', stop_exc)
            raise stop_exc


    def parse_latex_group(self, tok):
        r"""
        Process a token that introduces a LaTeX group (e.g. ``{a group}``). The
        token `tok` is of type ``tok.tok == 'brace_open'`` according to the
        current parsing state.

        The default implementation uses the `make_latex_group_parser` provided
        by the LatexWalker instance to parse the group node, and pushes the
        resulting node onto the node list.

        This method can be reimplemented to customize its behavior.
        Implementations should create the relevant node(s) and push them onto
        the node list with a call to :py:meth:`push_to_nodelist()` (refer to
        that method's doc).
        """

        logger.debug("nodes collector is now parsing a latex group, %r", tok)

        self.token_reader.move_to_token(tok, rewind_pre_space=False)

        group_parser = self.latex_walker.make_latex_group_parser(
            delimiters=tok.arg,
        )

        groupnode, parsing_state_delta = \
            self.latex_walker.parse_content(
                group_parser,
                token_reader=self.token_reader,
                parsing_state=self.make_child_parsing_state(self.parsing_state,
                                                            LatexGroupNode),
        )

        if parsing_state_delta is not None:
            logger.warning("parsing_state_delta is ignored after parsing a LaTeX group: %r",
                           parsing_state_delta)

        stop_exc = self.push_to_nodelist(groupnode)
        if stop_exc is not None:
            stop_exc.pos_end = groupnode.pos_end
            logger.debug('parse_latex_group(): stop_exc=%r', stop_exc)
            raise stop_exc

        logger.debug("nodes collector finished parsing group → %r", groupnode)


    def parse_macro(self, tok):
        r"""
        Process a token representing a macro (e.g. ``\macro``). The token `tok` is
        of type ``tok.tok == 'macro'``.

        The default implementation looks up the corresponding macro
        specification object via the parsing state's latex context database, and
        defers to :py:meth:`parse_invocable_token_type()`.

        This method can be reimplemented to customize its behavior.
        Implementations should create the relevant node(s) and push them onto
        the node list with a call to :py:meth:`push_to_nodelist()` (refer to
        that method's doc).
        """

        macroname = tok.arg

        mspec = None
        if self.parsing_state.latex_context is not None:
            mspec = self.parsing_state.latex_context.get_macro_spec(macroname)

        if mspec is None:
            exc = self.latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    msg=r"Encountered unknown macro ‘\{}’".format(macroname),
                    pos=tok.pos,
                    error_type_info={
                        'what': 'nodes_unknown_macro_name',
                        'macroname': macroname,
                    },
                )
            )
            if exc is not None:
                raise exc
            mspec = None

        node_class = LatexMacroNode
        what = 'macro ‘\\{}’'.format(macroname)

        return self.parse_invocable_token_type(tok, mspec, node_class, what)

    def parse_environment(self, tok):
        r"""
        Process a token representing an environment
        (e.g. ``\begin{environment}``). The token `tok` is of type ``tok.tok ==
        'begin_environment'``.

        The default implementation looks up the corresponding environment
        specification object via the parsing state's latex context database, and
        defers to :py:meth:`parse_invocable_token_type()`.

        This method can be reimplemented to customize its behavior.
        Implementations should create the relevant node(s) and push them onto
        the node list with a call to :py:meth:`push_to_nodelist()` (refer to
        that method's doc).
        """

        latex_walker = self.latex_walker
        #token_reader = self.token_reader

        environmentname = tok.arg
        # envspec = tok.spec
        # if envspec is None:
        envspec = \
            self.parsing_state.latex_context.get_environment_spec(environmentname)

        if envspec is None:
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    msg=r"Encountered unknown environment ‘{}{}{}’"
                    .format('{', environmentname, '}'),
                    pos=tok.pos,
                    error_type_info={
                        'what': 'nodes_unknown_environment_name',
                        'environmentname': environmentname,
                    },
                )
            )
            if exc is not None:
                raise exc
            envspec = None

        node_class = LatexEnvironmentNode
        what = 'environment ‘{}{}{}’'.format('{', environmentname, '}')

        return self.parse_invocable_token_type(tok, envspec, node_class, what)

    def parse_specials(self, tok):
        r"""
        Process a token representing LaTeX specials (e.g. ``~``). The token `tok` is
        of type ``tok.tok == 'specials'``.

        The default implementation defers to
        :py:meth:`parse_invocable_token_type()`.

        This method can be reimplemented to customize its behavior.
        Implementations should create the relevant node(s) and push them onto
        the node list with a call to :py:meth:`push_to_nodelist()` (refer to
        that method's doc).
        """

        specials_spec = tok.arg

        node_class = LatexSpecialsNode
        what = 'specials ‘{}’'.format(getattr(specials_spec, 'specials_chars', '<unkonwn>'))

        return self.parse_invocable_token_type(tok, specials_spec, node_class, what)

    def parse_invocable_token_type(self, tok, spec, node_class, what):
        r"""
        Process a token representing either a macro call, a begin environment call,
        or specials chars.

        This method is a convenience method that collects the similar processing
        for these three node types.  The specification class is queried for the
        relevant parser object (``spec.get_node_parser()``), to which we defer
        for parsing the macro call / the environment / the specials.

        Additionally, the current parsing state is updated using the carry-over
        information reported by the call parser.


        This method can be reimplemented to customize its behavior.
        Implementations should create the relevant node(s) and push them onto
        the node list with a call to :py:meth:`push_to_nodelist()` (refer to
        that method's doc).
        """

        latex_walker = self.latex_walker
        token_reader = self.token_reader

        if spec is not None:
            node_parser = spec.get_node_parser(tok)
        else:
            node_parser = None

        if node_parser is None:

            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    msg="No parser found for callable token {!r}".format(tok),
                    pos=tok.pos,
                )
            )
            if exc is not None:
                logger.debug('parse_invocable_token_type(): no-parser error, exc=%r', exc)
                raise exc
            result_node = None
            parsing_state_delta = None

        else:

            result_node, parsing_state_delta = latex_walker.parse_content(
                node_parser,
                token_reader,
                self.make_child_parsing_state(self.parsing_state, node_class),
                open_context=(what, tok),
            )

        self.update_state_from_parsing_state_delta(parsing_state_delta)

        if result_node is None:
            logger.warning("Parser %r produced no node (None) for token %r", node_parser, tok)
            return

        exc = self.push_to_nodelist(result_node)
        if exc is not None:
            exc.pos_end = result_node.pos_end
            logger.debug('parse_invocable_token_type(): exc=%r', exc)
            raise exc


    def parse_math(self, tok):
        r"""
        Process a token that introduces LaTeX math mode (e.g. ``$ ... $`` or ``\[
        ... \]``). The token `tok` is of type ``tok.tok in ('mathmode_inline',
        'mathmode_display')`` according to the current parsing state.

        The default implementation uses the `make_latex_math_parser()` provided
        by the latex walker to parse the group node, and pushes the resulting
        node onto the node list.

        This method can be reimplemented to customize its behavior.
        Implementations should create the relevant node(s) and push them onto
        the node list with a call to :py:meth:`push_to_nodelist()` (refer to
        that method's doc).
        """
        logger.debug("parse_math, tok=%r", tok)

        self.token_reader.move_to_token(tok, rewind_pre_space=False)

        # The math parser instance is responsible for setting the parsing state.

        child_math_parsing_state = self.make_child_parsing_state(
            self.parsing_state,
            LatexMathNode
        )
        logger.debug("child_math_parsing_state = %r", child_math_parsing_state)

        math_parser = self.latex_walker.make_latex_math_parser(
            math_mode_delimiters=tok.arg,
        )

        # a math inline or display environment
        mathnode, parsing_state_delta = \
            self.latex_walker.parse_content(
                math_parser,
                token_reader=self.token_reader,
                parsing_state=child_math_parsing_state,
            )

        self.update_state_from_parsing_state_delta(parsing_state_delta)

        if mathnode is None:
            logger.warning("Math parser produced no node (None) for token %r", tok)
            return

        stop_exc = self.push_to_nodelist(mathnode)
        if stop_exc is not None:
            stop_exc.pos_end = mathnode.pos_end
            logger.debug('parse_math_node(): stop_exc=%r', stop_exc)
            raise stop_exc
