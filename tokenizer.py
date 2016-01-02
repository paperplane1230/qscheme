#!/usr/bin/env python3

class Tokenizer:
    """Tokenizer to read tokens."""
    import sys
    def __init__(self, file=sys.stdin):
        """Bind a file stream to read."""
        import re
        self._file = file
        self._line = ''
        self._regex = re.compile(self._generate_pattern())
    def _yield_patterns(self):
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
    def _generate_pattern(self):
        """Generate pattern for scheme."""
        result = []
        # space
        result.append(r"""\s*""")
        result.append('(')
        result.append('|'.join(self._yield_patterns()))
        result.append(')')
        # remaining
        result.append(r"""(.*)""")
        return ''.join(result)
    def next_token(self):
        """Get the next token."""
        while True:
            if self._line == '':
                self._line = self._file.readline()
            if self._line == '':
                return None
            token, self._line = self._regex.match(self._line).groups()
            if token != '':
                return token
    def empty(self):
        """Judge whether there are more than one expressions in a line."""
        return self._line == '' or self._line.isspace()

