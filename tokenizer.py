#!/usr/bin/env ipython3

class Tokenizer:
    """Tokenizer to read tokens."""
    import sys
    def __init__(self, file=sys.stdin):
        """Bind a file stream to read."""
        import re
        self.__file = file
        self.__line = ''
        self.__regex = re.compile(self.__generate_pattern())
    def __yield_patterns(self):
        """Yield patterns of regular expressions."""
        # comment
        yield r""";.*"""
        # string
        yield r'"(?:\\.|[^\\"])*"'
        # unquote splicing
        yield r""",@"""
        # special
        yield r"""[('`,)]"""
        # normal
        yield r"""[^\s('"`,;)]*"""
    def __generate_pattern(self):
        """Generate pattern for scheme."""
        result = []
        # space
        result.append(r"""\s*""")
        result.append('(')
        result.append('|'.join(self.__yield_patterns()))
        result.append(')')
        # remaining
        result.append(r"""(.*)""")
        return ''.join(result)
    def next_token(self):
        """Get the next token."""
        while True:
            if self.__line == '':
                self.__line = self.__file.readline()
            if self.__line == '':
                return None
            token, self.__line = self.__regex.match(self.__line).groups()
            if token != '':
                return token
    def empty(self):
        """Judge whether there are more than one expressions in a line."""
        return self.__line == ''
