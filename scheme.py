#!/usr/bin/env ipython3

import sys
import operator as op

from scheme_types import *

def _init_global_env(env):
    """Initialize the global environment."""
    import math
    env.update({
        '+':op.add, '-':op.sub, '*':op.mul, '/':op.truediv, 'not':not_op,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.is_, 'length':len,
        'cons':cons, 'set-car!':set_car, 'set-cdr!':set_cdr, 'gcd':fractions.gcd,
        'car':lambda x: x.car, 'cdr':lambda x: x.cdr, 'rational?':is_rational,
        'boolean?':lambda x: isa(x,bool), 'integer?':is_int, 'lcm':lcm,
        'real?':is_rational,    # it seems in scheme rational? equals real?
        'number?':is_number, 'null?':lambda x: x==[], 'equal?':op.eq,
        'string?':lambda x: isa(x,str), 'expt':math.pow, 'list-set!':list_set,
        'max': max, 'min':min, 'abs':abs, 'list':List, 'list-ref':list_ref,
        'number->string':num2str,'string->number':str2num, 'make-list':make_list,
        'pair?':is_pair, 'list?':is_list, 'append':append, 'display':display,
        'quotient':quotient, 'remainder':remainder, 'modulo':op.mod,
        'sqrt':lambda x: x ** 0.5, 'numerator':numerator, 'denominator':denominator,
    })
    return env

global_env = _init_global_env(Env())

def _expand(parts, can_define=False):
    """Do expansion for list to be evaluated."""
    if not isa(parts, list) or not parts:
        return parts
    if parts[0] == 'quote':
        require(parts, len(parts)==2)
        return parts
    if parts[0] == 'define':
        if not can_define:
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
            return _expand(['define',name,['lambda', parms]+parts[2:]], can_define)
        require(parts, len(parts)==3)
        require(parts, isa(header, Symbol), "can only define a symbol")
        parts[2] = _expand(parts[2])
        return parts
    if parts[0] == 'lambda':
        require(parts, len(parts)>=3)
        parms = parts[1]
        require(parms, (isa(parms, list) and all(isa(i, Symbol) for i in parms)
            or isa(parms, Symbol), 'illegal lambda argument list'))
        # body is a list even there's only one expression to be evaluated
        body = parts[2:]
        body.insert(0, 'begin')
        return ['lambda', parms, _expand(body,can_define)]
    if parts[0] == 'set!':
        require(parts, len(parts)==3)
        symbol = parts[1]
        require(parts, isa(symbol, Symbol), "can set! only a symbol")
        parts[2] = _expand(parts[2])
        return parts
    if parts[0] == 'quasiquote':
        require(parts, len(parts)==2)
        return _expand_quasiquote(parts[1])
    if parts[0] == 'let':
        require(parts, len(parts)>2)
        binds = parts[1]
        require(parts, all(isa(i, list) and len(i)==2 and isa(i[0], Symbol)
                    for i in binds), 'illegal binding list')
        # _expand in lambda will expand bodies
        bodies = parts[2:]
        parms, values = zip(*binds)
        args = list(map(_expand,values))
        return _expand([['lambda',list(parms)]+bodies]+args, can_define)
    if parts[0] == 'do':
        require(parts, len(parts)>2)
        binds = parts[1]
        require(parts, all(isa(i, list) and len(i)==3 and isa(i[0], Symbol)
                    for i in binds), 'illegal binding list')
        condition_val = parts[2]
        require(parts, isa(condition_val,list) and condition_val,
                'do must have a condition to stop')
        if len(condition_val) == 1:
            condition_val.append(None)
        bodies = parts[3:]
        parms, inits, steps = zip(*binds)
        inits = list(map(_expand,inits))
        steps = list(map(_expand,steps))
        cond, return_val = list(map(_expand,condition_val))
        bodies = list(map(_expand,bodies))
        return ['do', parms, inits, steps, cond, return_val, bodies]
    # next branches share 'return' expression
    if parts[0] == 'if':
        if len(parts) == 3:
            parts.append(None)
        require(parts, len(parts)==4)
        can_define = False
    elif parts[0] == 'begin':
        if len(parts) == 1:
            return parts + [None]
    # (proc args...)
    return [_expand(i, can_define) for i in parts]

def _list_cat(part1, part2):
    """Catenate two parts into a list."""
    if isa(part2, List):
        part2 = part2.members
    return [part1] + part2

def _need_expand_quotes(parts):
    """Judge whether the parts need to be expanded when dealing with quotes."""
    return parts != [] and isa(parts, list)

def _break_list(s_list):
    """Break the outer list to construct a scheme list."""
    if not isa(s_list, list):
        raise TypeError('the parameter must a list')
    return List(s_list)

def _add_slist(left_list, right_list):
    """Add two lists, may be a scheme list."""
    if isa(left_list, List):
        left_list = left_list.members
    if isa(right_list, List):
        right_list = right_list.members
    return left_list + right_list

def _expand_quasiquote(parts):
    """Expand parts related to quasiquote."""
    if not _need_expand_quotes(parts) or parts[0] == 'quasiquote':
        return [quotes["'"], parts]
    require(parts, parts[0]!='unquote-splicing', "can't splice here")
    if parts[0] == 'unquote':
        require(parts, len(parts)==2)
        return parts[1]
    if _need_expand_quotes(parts[0]) and parts[0][0] == 'unquote-splicing':
        require(parts[0], len(parts[0])==2)
        return [_add_slist, parts[0][1], _expand_quasiquote(parts[1:])]
    result = [_list_cat, _expand_quasiquote(parts[0]), _expand_quasiquote(parts[1:])]
    result = [_break_list, result]
    return result

quotes = {
        "'":Symbol('quote'), '`':Symbol('quasiquote'), ',':Symbol('unquote'),
        ',@':Symbol('unquote-splicing'),
}

def parse(tokenizer):
    """Parse scheme statements."""
    return _expand(_read(tokenizer), True)

def _read(tokenizer):
    """Read symbol to parse."""
    def _read_ahead(token):
        """Read ahead to construct an operation."""
        if token in quotes:
            return [quotes[token], _read(tokenizer)]
        if token == '(':
            members = []
            while True:
                token = tokenizer.next_token()
                if token == ')':
                    return members
                members.append(_read_ahead(token))
        else:
            return transform(token)
    # body of parse
    token = tokenizer.next_token()
    if token is None:
        return None
    if token.startswith(';'):
        return ';'
    return _read_ahead(token)

def _findop(func, op_list):
    """Judge whether the operator is in the list."""
    try:
        return func in op_list
    except Exception:
        return False

def _mathop(func):
    """Judge whether operator is a math one."""
    return _findop(func, [lcm,fractions.gcd,op.add,op.sub,op.mul,op.truediv])

def _cmpop(func):
    """Judge whether operator is a comparison one."""
    return _findop(func, [op.is_,op.lt,op.le,op.gt,op.ge])

def _modop(func):
    """Judge whether the operator is related to mod."""
    return _findop(func, [remainder,op.mod,quotient])

def _do_math_op(func, exprs):
    """Deal with basic math operator."""
    import functools
    if func is fractions.gcd:
        if not all(isa(i,int) for i in exprs):
            raise TypeError('parameters of gcd must be  integers')
        exprs.insert(0, 0)
    if func is lcm:
        if not all(isa(i,int) for i in exprs):
            raise TypeError('parameters of lcm must be  integers')
        exprs.insert(0, 1)
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

def _do_mod_op(func, exprs):
    """Do operations related to mod."""
    require(exprs, len(exprs)==2)
    if not isa(exprs[0],int) or not isa(exprs[1],int):
        raise TypeError('parameters of mod operation must be integers')
    return func(*exprs)

_special_forms = {
        _mathop: _do_math_op, _cmpop: _do_cmp_op, _modop: _do_mod_op,
}

def _do_quote(parts):
    """Return pair or list if possible when returning from quote."""
    if not _need_expand_quotes(parts):
        return parts
    if parts.count('.')>1 or parts.count('.')==1 and parts.index('.')<len(parts)-2:
        require(parts, False, 'ill-formed dotted list')
    if len(parts) >= 3 and parts[-2] == '.':
        return Pair(_do_quote(parts[0]), _do_quote(parts[1:]))
    return List(parts)

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
            return _do_quote(parts[1])
        if parts[0] == 'define':
            _, symbol, val = parts
            env[symbol] = evaluate(val, env)
            return symbol
        if parts[0] == 'lambda':
            # get parameters and body of lambda
            return Procedure(parts[1], parts[2], env)
        if parts[0] == 'set!':
            _, symbol, value = parts
            try:
                oldVal = env.find(symbol)
            except KeyError as e:
                raise e
            env[symbol] = evaluate(value, env)
            return oldVal
        if parts[0] == 'do':
            _, parms, inits, steps, cond, ret_val, bodies = parts
            env = Env(outer=env)
            init_vals = [evaluate(i, env) for i in inits]
            env.update(zip(parms,init_vals))
            while not evaluate(cond, env):
                for i in bodies[0:]:
                    evaluate(i, env)
                new_vals = [evaluate(i, env) for i in steps]
                env.update(zip(parms,new_vals))
            parts = ret_val
        elif parts[0] == 'if':
            _, cond, branch1, branch2 = parts
            parts = branch1 if evaluate(cond, env) else branch2
        elif parts[0] == 'begin':
            for i in parts[1:-1]:
                evaluate(i, env)
            parts = parts[-1]
        else:
            # (proc args...)
            exprs = [evaluate(i, env) for i in parts]
            func = exprs.pop(0)
            for is_op in _special_forms:
                if is_op(func):
                    return _special_forms[is_op](func, exprs)
            if func is List:
                return List(exprs)
            if isa(func, Procedure):
                parts = func.body
                env = Env(func.parms, exprs, func.env)
            else:
                result = func(*exprs)
                # set-car and set-cdr may change pair into list or conversely
                if isa(parts[0], str) and parts[0].startswith('set-'):
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
