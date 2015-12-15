#!/usr/bin/env ipython3

import sys
import operator as op
import fractions

isa = isinstance

class Symbol(str):
    """Class for symbol."""
    pass

class Pair:
    """Class for pair in scheme(created by function cons)."""
    def __init__(self, first, second):
        """Construct a pair with given data."""
        self.__first = first
        self.__second = second
    def __rm_outer(self, symbol):
        """Remove outer boundary of second part when printing.
        :returns: Format with outer boundary removed.
        """
        if isa(symbol, Pair):
            return ' ' + str(symbol)[1:-1]
        return ' . ' + tostr(symbol)
    def __str__(self):
        """Format for printing.
        :returns: Format to be printed.
        """
        return ''.join(['(', tostr(self.__first), self.__rm_outer(self.__second), ')'])
    def car(self):
        return self.__first

def car(pair):
    """Return the first element of the pair.
    :returns: The first element of the pair.
    """
    require(pair, isa(pair, Pair), 'the parameter of car must be a pair')
    return pair.car()

def cons(first, second):
    """Construct a Pair.
    :returns: A pair constructed with specific parameters.
    """
    return Pair(first, second)

class Env(dict):
    """Context Environment."""
    def __init__(self, parms=(), args=(), outer=None):
        """Initialize the environment with specific parameters."""
        self.__outer = outer
        if isa(parms, Symbol):
            self.update({parms:list(args)})
        else:
            if len(parms) != len(args):
                raise TypeError('expected {0}, given {1}'
                        .format(tostr(parms), tostr(args)))
            self.update(list(zip(parms, args)))
    def find(self, op):
        """Find operator in the environment.
        :returns: Specific operator.
        """
        if op in self:
            return self[op]
        if self.__outer is None:
            raise LookupError('unbound '+op)
        return self.__outer.find(op)

class Procedure:
    """Class for procedure."""
    def __init__(self, parms, body, env):
        """Initialize a procedure with specific parameters, arguments and environment."""
        self.__parms = parms
        self.__body = body
        self.__env = env

def not_op(target):
    """Implementation of operator not.
    :returns: The situation.
    """
    if not isa(target, bool):
        return False
    return not target

def __init_global_env(env):
    """Initialize the global environment.
    :returns: A new environment filled with builtin operations.
    """
    env.update({
        '+':op.add, '-':op.sub, '*':op.mul, '/':op.truediv, 'not':not_op,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq,
        'length':len, 'cons':cons, 'car':car,
    })
    return env

global_env = __init_global_env(Env())

def tostr(token):
    """Convert a token into form in lisp.
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
        return '(' + ' '.join(map(tostr, token)) + ')'
    return str(token)

class Tokenizer:
    """Tokenizer to read tokens."""
    def __init__(self, file=sys.stdin):
        """Bind a file stream to read."""
        import re
        self.__file = file
        self.__line = ''
        self.__regex = re.compile(self.__generate_pattern())
    def __yield_patterns(self):
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
    def __generate_pattern(self):
        """Generate pattern for scheme.
        :returns: A pattern for regular expression to parse.
        """
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
        """Get the next token.
        :returns: The next token.
        """
        while True:
            if self.__line == '':
                self.__line = self.__file.readline()
            if self.__line == '':
                return None
            token, self.__line = self.__regex.match(self.__line).groups()
            if token != '':
                return token
    def empty(self):
        """Judge whether there are more than one expressions in a line.
        :returns: The situation.
        """
        return self.__line == ''

def _expand(parts):
    """Do expansion for list to be evaluated.
    :returns: List expanded.
    """
    if not isa(parts, list) or len(parts) == 0:
        return parts
    if parts[0] == 'quote':
        require(parts, len(parts)==2)
        return parts
    if parts[0] == 'define':
        if len(parts) == 2:
            parts.append(None)
        require(parts, len(parts)>=3)
        header = parts[1]
        if isa(header, list) and header:
            name = header[0]
            parms = header[1:]
            # (define (func parms...) body)
            #   => (define func (lambda (parms...) body))
            return _expand(['define', name, ['lambda', parms]+parts[2:]])
        require(parts, len(parts)==3)
        require(parts, isa(header, Symbol), "can only define a symbol")
        parts[2] = _expand(parts[2])
        return parts
    if parts[0] == 'lambda':
        require(parts, len(parts)>=3)
        parms = parts[1]
        # body is a list even there's only one expression to be evaluated
        body = parts[2:]
        require(parms, (isa(parms, list) and all(isa(i, Symbol) for i in parms)
            or isa(parms, Symbol), 'illegal lambda argument list'))
        body.insert(0, 'begin')
        return ['lambda', parms, _expand(body)]
    if parts[0] == 'set!':
        require(parts, len(parts)==3)
        symbol = parts[1]
        require(parts, isa(symbol, Symbol), "can set! only a symbol")
        parts[2] = _expand(parts[2])
        return parts
    # next branches share 'return' expression
    if parts[0] == 'if':
        if len(parts) == 3:
            parts.append(None)
        require(parts, len(parts)==4)
    elif parts[0] == 'begin':
        if len(parts) == 1:
            return parts + [None]
    # (proc args...)
    return [_expand(i) for i in parts]

quotes = {
        "'":Symbol('quote'), '`':Symbol('quasiquote'), ',':Symbol('unquote'),
        ',@':Symbol('unquote-splicing'),
}

def parse(tokenizer):
    """Parse scheme statements.
    :returns: List of members of an operation or None if encountering an EOF.
    """
    def _read_ahead(token):
        """Read ahead to construct an operation.
        :returns: Members of an operation.
        """
        if token in quotes:
            return [quotes[token], parse(tokenizer)]
        if token == '(':
            memebers = []
            while True:
                token = tokenizer.next_token()
                if token == ')':
                    return memebers
                memebers.append(_read_ahead(token))
        else:
            return _transform(token)
    # body of parse
    token = tokenizer.next_token()
    if token is None:
        return None
    if token.startswith(';'):
        return ';'
    return _expand(_read_ahead(token))

def _transform(token):
    """Transform token into proper form.
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
                    return fractions.Fraction(token)
                except ValueError:
                    return Symbol(token.lower())

def _mathop(func):
    """Judge whether operator is a math one.
    :returns: The situation.
    """
    return func in [op.add,op.sub,op.mul,op.truediv]

def _cmpop(func):
    """Judge whether operator is a comparison one.
    :returns: The situation.
    """
    return func in [op.eq,op.lt,op.le,op.gt,op.ge]

def _do_math_op(func, exprs):
    """Deal with basic math operator.
    :returns: Result of operation.
    """
    import functools
    if func is op.sub and len(exprs) == 1:
        exprs.insert(0, 0)
    if func is op.truediv and len(exprs) == 1:
        exprs.insert(0, 1)
    if func is op.truediv:
        molecular = exprs.pop(0)
        sum = functools.reduce(op.mul, exprs)
        return fractions.Fraction(molecular, sum)
    return functools.reduce(func, exprs)

def evaluate(parts, env=global_env):
    """Evaluate value of parts.
    :returns: Value of parts.
    """
    while True:
        if isa(parts, Symbol):
            return env.find(parts)
        if not isa(parts, list):
            return parts
        if len(parts) == 0:
            return ()
        if parts[0] == 'quote':
            return parts[1]
        if parts[0] == 'define':
            (_, symbol, val) = parts
            env[symbol] = evaluate(val, env)
            return symbol
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
            if _mathop(func):
                return _do_math_op(func, exprs)
            if _cmpop(func):
                for i in range(len(exprs)-1):
                    if not func(exprs[i], exprs[i+1]):
                        return False
                return True
            if isa(func, Procedure):
                parts = func.body
                env = Env(func.parms, exprs, func.env)
            else:
                return func(*exprs)

def require(var, condition, msg='wrong length'):
    """Assert if condition isn't satisfied."""
    if not condition:
        raise SyntaxError(tostr(var)+': '+msg)

def repl():
    """Read-evaluate-print-loop."""
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
            if parts == ';' or parts == ')':
                continue
            print(tostr(evaluate(parts)))
        except KeyboardInterrupt:
            sys.stderr.write('\n')
            sys.stderr.flush()
        except Exception as e:
            print("{0}: {1}".format(type(e).__name__, e))

if __name__ == '__main__':
    repl()
