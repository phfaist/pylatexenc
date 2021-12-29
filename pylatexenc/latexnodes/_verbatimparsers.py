
from ._exctypes import *
from ._nodetypes import *


class LatexVerbatimBaseParser(object):
    r"""
    Note: this parser requires the token reader to provide character-level
    access to the input string.
    """
    
    def __init__(self, **kwargs):
        super(LatexVerbatimParser, self).__init__(**kwargs)

    def new_char_check_stop_condition(self, char, verbatim_string):
        r"""
        The default implementation in this base class is to read a single verbatim
        char.  Reimplement this method in a subclass for more advanced behavior.
        """
        if verbatim_string:
            return True
        return False

    def error_end_of_stream(self, pos, recovery_nodes, latex_walker):
        raise LatexWalkerParseError(
            msg="End of stream reached while reading verbatim content",
            pos=pos,
            recovery_nodes=recovery_nodes
        )
        

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        return self.read_verbatim_content(latex_walker, token_reader, parsing_state, **kwargs)


    def read_verbatim_content(self, latex_walker, token_reader, parsing_state, **kwargs):
        r"""
        ....
        
        The `token_reader` is left *after* the character that caused the
        processing to stop.
        """

        verbatim_string = ''
        stop_condition_met = False

        orig_pos = token_reader.cur_pos_chars()

        ended_with_eos = False

        try:
            while not stop_condition_met:
                char = token_readers.next_chars(1, parsing_state=parsing_state)

                if self.new_char_check_stop_condition(char, verbatim_string):
                    # stop condition met
                    stop_condition_met = True
                else:
                    verbatim_string += char

        except LatexWalkerEndOfStream:
            ended_with_eos = True

        pos_end = token_reader.cur_pos_chars()
        nodes = latex_walker.make_node(
            LatexCharsNode,
            chars=verbatim_string,
            pos=orig_pos,
            len=pos_end - orig_pos,
            parsing_state=parsing_state,
        )

        if ended_with_eos:
            return self.error_end_of_stream( pos=pos_end,
                                             recovery_nodes=nodes,
                                             latex_walker=latex_walker )
        
        return nodes, None



class LatexVerbatimDelimParser(LatexVerbatimBaseParser):
    def __init__(self,
                 delimiter_chars=None,
                 **kwargs):
        super(LatexVerbatimDelimParser, self).__init__(**kwargs)

        self.delimiter_chars = delimiter_chars

        self.depth_counter = 1


    def new_char_check_stop_condition(self, char, verbatim_string):
        r"""
        The default implementation in this base class is to read a single verbatim
        char.  Reimplement this method in a subclass for more advanced behavior.
        """
        if char == self.delimiter_chars[1]:
            # closing delimiter
            self.depth_counter -= 1
            if self.depth_counter <= 0:
                # final closing delimiter
                return True
        elif char == self.delimiter_chars[0]:
            # opening delimiter, if not the same as the closing delimiter
            self.depth_counter += 1

        return False


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):
        
        token_reader.skip_space_chars()

        orig_pos = token_reader.cur_pos_chars()

        if self.delimiter_chars is None:
            # read the delimiter character

            open_delim_char = token_reader.next_chars(1, parsing_state=parsing_state)
            
            close_delim_char = {
                '{': '}',
                '[': ']',
                '<': '>',
                '(': ')',
            }.get(open_delim_char, open_delim_char)

            self.delimiter_chars = (open_delim_char, close_delim_char)

        else:

            first_char = token_reader.next_chars(1, parsing_state=parsing_state)
            if first_char != self.delimiter_chars[0]:
                raise LatexWalkerParseError(
                    msg="Expected opening delimiter ‘{}’ for verbatim content".format(
                        self.delimiter_chars[0]
                    ),
                    pos=pos,
                )
            
        verbatim_node, _ = \
            self.read_verbatim_content(latex_walker, token_reader, parsing_state, **kwargs)

        nodes = latex_walker.make_node(
            LatexGroupNode,
            delimiters=self.delimiter_chars,
            nodelist=LatexNodeList(verbatim_node),
            pos=orig_pos,
            len=verbatim_node.pos + verbatim_node.len + 1 - orig_pos,
            parsing_state=parsing_state
        )

        return nodes, None



# class LatexVerbatimEnvironmentParser(LatexVerbatimBaseParser):
#     def __init__(self,
#                  environment_name=None,
#                  **kwargs):
#         super(LatexVerbatimDelimParser, self).__init__(**kwargs)

#     ........................

#     # TODO
