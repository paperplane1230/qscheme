#!/usr/bin/env ipython3

import sys
import operator as op

from scheme_types import *

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
        """Find operator in the environment."""
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
    @property
    def env(self):
        """Get context environment."""
        return self.__env
    @property
    def body(self):
        """Get body."""
        return self.__body
    @property
    def parms(self):
        """Get parameters."""
        return self.__parms

def _init_global_env(env):
    """Initialize the global environment."""
    import math
    env.update({
        '+':op.add, '-':op.sub, '*':op.mul, '/':op.truediv, 'not':not_op,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.is_, 'length':len,
        'cons':cons, 'set-car!':set_car, 'set-cdr!':set_cdr,
        'car':lambda x: x.car, 'cdr':lambda x: x.cdr, 'rational?':is_rational,
        'boolean?':lambda x: isa(x,bool), 'integer?':is_int,
        'real?':is_rational,    # it seems in scheme rational? equals real?
        'number?':is_number, 'null?':lambda x: x==[], 'equal?':op.eq,
        'string?':lambda x: isa(x,str), 'expt':math.pow, 'list-set!':list_set,
        'max': max, 'min':min, 'abs':abs, 'list':List, 'list-ref':list_ref,
        'number->string':num2str,'string->number':str2num, 'make-list':make_list,
        'pair?':lambda x: isa(x,Pair), 'list?':lambda x: isa(x,List),
    })
    return env

global_env = _init_global_env(Env())

def _expand(parts, top_env=False):
    """Do expansion for list to be evaluated."""
    if not isa(parts, list) or len(parts) == 0:
        return parts
    if parts[0] == 'quote':
        require(parts, len(parts)==2)
        return parts
    if parts[0] == 'define':
        if not top_env:
            raise SyntaxError("can't bind name in null syntactic environment")
        if len(parts) == 2 and not isa(parts[1], list):
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
    """Parse scheme statements."""
    def _read_ahead(token):
        """Read ahead to construct an operation."""
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
            return transform(token)
    # body of parse
    token = tokenizer.next_token()
    if token is None:
        return None
    if token.startswith(';'):
        return ';'
    return _expand(_read_ahead(token), True)

def _mathop(func):
    """Judge whether operator is a math one."""
    return func in [op.add,op.sub,op.mul,op.truediv]

def _cmpop(func):
    """Judge whether operator is a comparison one."""
    return func in [op.is_,op.lt,op.le,op.gt,op.ge]

def _do_math_op(func, exprs):
    """Deal with basic math operator."""
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

def _do_cmp_op(func, exprs):
    """Do comparable operation."""
    for i in range(len(exprs)-1):
        if not func(exprs[i], exprs[i+1]):
            return False
    return True

def evaluate(parts, env=global_env):
    """Evaluate value of parts."""
    while True:
        if isa(parts, Symbol):
            return env.find(parts)
        if not isa(parts, list):
            return parts
        if not parts:
            return []
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
                return _do_cmp_op(func, exprs)
            if func is List:
                return List(exprs)
            if isa(func, Procedure):
                parts = func.body
                env = Env(func.parms, exprs, func.env)
            else:
                result = func(*exprs)
                # set-car and set-cdr may change pair into list or conversely
                if parts[0].startswith('set-'):
                    try:
                        env.update({parts[1]:result})
                    except TypeError:
                        # the changed object may temporary
                        return result
                    except Exception as e:
                        raise e
                return result

def repl():
    """Read-evaluate-print-loop."""
    prompt = '> '
    from tokenizer import Tokenizer
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
