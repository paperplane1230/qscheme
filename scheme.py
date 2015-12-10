#!/usr/bin/env ipython3

import sys

class Symbol(str):
    pass

class Env(dict):
    """Context Environment."""
    def __init__(self, outer=None):
        """Initialize the environment with specific parameters.
        :outer: The outer environment.
        """
        self.outer = outer
    def find(self, op):
        """Find operator in the environment.
        :op: Operator to be found.
        :returns: Specific operator.
        """
        if op in self:
            return self[op]
        if self.outer == None:
            raise LookupError(op)
        return self.outer.find(op)

def init_global_env(env):
    """Initialize the global environment.
    :env: The environment to be initialized.
    :returns: A new environment filled with builtin operations.
    """
    import operator as op
    env.update({
        '+':op.add, '-':op.sub, '*':op.mul, '/':op.truediv, 'not':op.not_,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq,
    })
    return env

global_env = init_global_env(Env())

isa = isinstance

def tostr(token):
    """Convert a token into form in lisp.
    :token: Token to be converted.
    :returns: Token after converting.
    """
    if token is True:
        return '#t'
    if token is False:
        return '#f'
    if isa(token, str):
        import json
        return json.dumps(token)
    if isa(token, complex):
        return str(token).replace('j', 'i')[1:-1]
    return str(token)

def yield_patterns():
    """Yield patterns of regular expressions.
    :returns: Strings corresponds to each conditions.
    """
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

def generate_pattern():
    """Generate pattern for scheme.
    :returns: A pattern for regular expression to parse.
    """
    result = []
    # space
    result.append(r"""\s*""")
    result.append('(')
    result.append('|'.join(yield_patterns()))
    result.append(')')
    # remaining
    result.append(r"""(.*)""")
    return ''.join(result)

class Tokenizer:
    """Tokenizer to read tokens."""
    def __init__(self, file=sys.stdin):
        """Bind a file stream to read.
        :file: File to be bound for reading tokens.
        """
        import re
        self.file = file
        self.pattern = generate_pattern()
        self.line = ''
        self.regex = re.compile(self.pattern)
    def next_token(self):
        """Get the next token.
        :returns: The next token.
        """
        while True:
            if self.line == '':
                self.line = self.file.readline()
            if self.line == '':
                return None
            token, self.line = self.regex.match(self.line).groups()
            if token != '' and not token.startswith(';'):
                return token

def expand(parts):
    """Do expansion for list to be evaluated.
    :parts: List to be expanded.
    :returns: List expanded.
    """
    if not isa(parts, list):
        return parts
    if parts[0] == 'if':
        length = len(parts)
        if length == 3:
            return parts + [None]
        require(parts, length == 4)
        return [i for i in map(expand, parts)]
    if parts[0] == 'begin':
        if len(parts) == 1:
            return parts + [None]
        return [expand(i) for i in parts]
    return parts

def parse(tokenizer):
    """Parse scheme statements.
    :tokenizer: Tokenizer for parser to parse.
    :returns: List of members of an operation or None if encountering an EOF.
    """
    def read_ahead(token):
        """Read ahead to construct an operation.
        :token: The current token in stream.
        :returns: Members of an operation.
        """
        if token == '(':
            memebers = []
            while True:
                token = tokenizer.next_token()
                if token == ')':
                    return memebers
                memebers.append(read_ahead(token))
        elif token == ')':
            raise SyntaxError('unexpected )')
        else:
            return transform(token)
    # body of parse
    token = tokenizer.next_token()
    if token == None:
        return None
    return expand(read_ahead(token))

def transform(token):
    """Transform token into proper form.
    :token: To be transformed.
    :returns: Token after transformation.
    """
    if token == '#t':
        return True
    if token == '#f':
        return False
    if token[0] == '"':
        return bytes(token[1:-1], "utf-8").decode('unicode-escape')
    if token.startswith('#b'):
        return int(token[2:], 2)
    if token.startswith('#o'):
        return int(token[2:], 8)
    if token.startswith('#d'):
        return int(token[2:])
    if token.startswith('#x'):
        return int(token[2:], 16)
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            try:
                return complex(token.replace('i', 'j'))
            except ValueError:
                try:
                    import fractions
                    return fractions.Fraction(token)
                except ValueError:
                    return Symbol(token)

def evaluate(parts, env=global_env):
    """Evaluate value of parts.
    :parts: Parts to be evaluated.
    :returns: Value of parts.
    """
    while True:
        if isa(parts, Symbol):
            return env.find(parts)
        if not isa(parts, list):
            return parts
        if len(parts) == 0:
            return ()
        if parts[0] == 'if':
            (_, cond, branch1, branch2) = parts
            parts = branch1 if evaluate(cond, env) else branch2
        elif parts[0] == 'begin':
            for i in parts[1:-1]:
                evaluate(i, env)
            parts = parts[-1]
        else:
            func = env.find(parts.pop(0))
            try:
                exprs = [evaluate(i, env) for i in parts]
                import functools
                return functools.reduce(func, exprs)
            except ValueError:
                return func(*exprs)

def require(var, condition, msg='wrong length'):
    """Assert if condition isn't satisfied.
    :var: Variable related.
    :condition: Condition to be satisfied.
    :msg: The message to be shown.
    """
    if not condition:
        raise SyntaxError(tostr(var)+': '+msg)

def repl():
    """Read-evaluate-print-loop.
    """
    prompt = '> '
    while True:
        try:
            sys.stderr.write(prompt)
            sys.stderr.flush()
            parts = parse(Tokenizer())
            if parts is None:
                return
            print(tostr(evaluate(parts)))
        except KeyboardInterrupt:
            sys.stderr.write('\n')
            sys.stderr.flush()
        except Exception as e:
            print("{0}: {1}".format(type(e).__name__, e))

if __name__ == '__main__':
    repl()
