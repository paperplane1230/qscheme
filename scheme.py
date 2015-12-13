#!/usr/bin/env ipython3

import sys
import operator as op

isa = isinstance

class Symbol(str):
    """Class for symbol."""
    pass

class Env(dict):
    """Context Environment."""
    def __init__(self, parms=(), args=(), outer=None):
        """Initialize the environment with specific parameters.
        :outer: The outer environment.
        """
        self.outer = outer
        if isa(parms, Symbol):
            self.update({parms:list(args)})
        else:
            if len(parms) != len(args):
                raise TypeError('expected {0}, given {1}'
                        .format(tostr(parms), tostr(args)))
            self.update(list(zip(parms, args)))
    def find(self, op):
        """Find operator in the environment.
        :op: Operator to be found.
        :returns: Specific operator.
        """
        if op in self:
            return self[op]
        if self.outer == None:
            raise LookupError('unbound '+op)
        return self.outer.find(op)

class Procedure:
    """Class for procedure."""
    def __init__(self, parms, body, env):
        """Initialize a procedure with specific parameters, arguments and environment.
        :parms: Symbols of parameters.
        :body: Body of procedure.
        :env: Context environment to support closure.
        """
        self.parms = parms
        self.body = body
        self.env = env

def init_global_env(env):
    """Initialize the global environment.
    :env: The environment to be initialized.
    :returns: A new environment filled with builtin operations.
    """
    env.update({
        '+':op.add, '-':op.sub, '*':op.mul, '/':op.truediv, 'not':op.not_,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq,
    })
    return env

global_env = init_global_env(Env())

def tostr(token):
    """Convert a token into form in lisp.
    :token: Token to be converted.
    :returns: Token after converting.
    """
    if token is True:
        return '#t'
    if token is False:
        return '#f'
    if isa(token, Symbol):
        return token
    if isa(token, str):
        import json
        return json.dumps(token)
    if isa(token, complex):
        return str(token).replace('j', 'i')[1:-1]
    if isa(token, list):
        return '('+' '.join(map(tostr, token))+')'
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
        self.line = ''
        self.regex = re.compile(generate_pattern())
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
            if token != '':
                return token
    def empty(self):
        """Judge whether there are more than one expressions in a line.
        :returns: The situation.
        """
        return self.line == ''

def expand(parts):
    """Do expansion for list to be evaluated.
    :parts: List to be expanded.
    :returns: List expanded.
    """
    if not isa(parts, list) or len(parts) == 0:
        return parts
    if parts[0] == 'define':
        if len(parts) == 2:
            parts += [None]
        require(parts, len(parts)>=3)
        header = parts[1]
        if isa(header, list) and header:
            name = header[0]
            parms = header[1:]
            # (define (func parms...) body)
            #   => (define func (lambda (parms...) body))
            return expand(['define', name, ['lambda', parms]+parts[2:]])
        require(parts, len(parts)==3)
        require(parts, isa(header, Symbol), "can only define a symbol")
        parts[2] = expand(parts[2])
        return parts
    if parts[0] == 'lambda':
        require(parts, len(parts)>=3)
        parms = parts[1]
        # body is a list even there's only one expression to be evaluated
        body = parts[2:]
        require(parms, (isa(parms, list) and all(isa(i, Symbol) for i in parms)
            or isa(parms, Symbol), 'illegal lambda argument list'))
        body = ['begin'] + body
        return ['lambda', parms, expand(body)]
    if parts[0] == 'set!':
        require(parts, len(parts)==3)
        symbol = parts[1]
        require(parts, isa(symbol, Symbol), "can set! only a symbol")
        parts[2] = expand(parts[2])
        return parts
    # next branches share 'return' expression
    if parts[0] == 'if':
        if len(parts) == 3:
            parts += [None]
        require(parts, len(parts)==4)
    elif parts[0] == 'begin':
        if len(parts) == 1:
            return parts + [None]
    # (proc args...)
    return [expand(i) for i in parts]

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
    if token.startswith(';'):
        return ';'
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
                    return Symbol(token.lower())

def mathop(func):
    """Judge whether operator is a math one.
    :func: Operator to be judged.
    :returns: The situation.
    """
    return func in [op.add,op.sub,op.mul,op.truediv]

def cmpop(func):
    """Judge whether operator is a comparison one.
    :func: Operator to be judged.
    :returns: The situation.
    """
    return func in [op.eq,op.lt,op.le,op.gt,op.ge]

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
        if parts[0] == 'define':
            env[parts[1]] = evaluate(parts[2], env)
            return parts[1]
        if parts[0] == 'lambda':
            # get parameters and body of lambda
            return Procedure(parts[1], parts[2], env)
        if parts[0] == 'set!':
            (_, symbol, value) = parts
            try:
                oldVal = env.find(symbol)
            except KeyError as e:
                raise e
            env[symbol] = evaluate(value, env)
            return oldVal
        if parts[0] == 'if':
            (_, cond, branch1, branch2) = parts
            parts = branch1 if evaluate(cond, env) else branch2
        elif parts[0] == 'begin':
            for i in parts[1:-1]:
                evaluate(i, env)
            parts = parts[-1]
        else:
            # (proc args...)
            exprs = [evaluate(i, env) for i in parts]
            func = exprs.pop(0)
            if mathop(func):
                import functools
                return functools.reduce(func, exprs)
            if cmpop(func):
                for i in range(len(exprs)-1):
                    if not func(exprs[i], exprs[i+1]):
                        return False
                return True
            if isa(func, Procedure):
                parts = func.body
                env = Env(func.parms, exprs, func.env)
            else:
                raise SyntaxError("The first object not applicable.")

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
    tokenizer = Tokenizer()
    while True:
        try:
            if tokenizer.empty():
                sys.stderr.write(prompt)
            sys.stderr.flush()
            parts = parse(tokenizer)
            if parts is None:
                return
            if parts == ';':
                continue
            print(tostr(evaluate(parts)))
        except KeyboardInterrupt:
            sys.stderr.write('\n')
            sys.stderr.flush()
        except Exception as e:
            print("{0}: {1}".format(type(e).__name__, e))

if __name__ == '__main__':
    repl()
