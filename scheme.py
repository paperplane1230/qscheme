#!/usr/bin/env ipython3

import operator as op

from tokenizer import Tokenizer
from scheme_types import *

def s_eval(content, env):
    """Procedure eval of scheme."""
    if isa(content, List):
        content = content.members
    return evaluate(_expand(content,True), env)

def s_map(*args):
    """Map in scheme."""
    args = list(args)
    env = args.pop()
    require(args, len(args)>1)
    require_type(is_procedure(args[0]),
            'the first parameter of map must be a procedure')
    min_len = sys.maxsize
    proc = args.pop(0)
    for s_list in args:
        require_type(isa(s_list, List), 'parameters of map must be lists')
        if len(s_list) < min_len:
            min_len = len(s_list)
    result = []
    for i in range(min_len):
        subexpr = [proc]
        for arg in args:
            subexpr.append(arg[i])
        result.append(evaluate(subexpr,env))
    return List(result)

def s_apply(*args):
    """Apply in scheme."""
    args = list(args)
    env = args.pop()
    require(args, len(args)>1)
    require_type(isa(args[-1], List), 'the last parameter of apply must be a list')
    require_type(is_procedure(args[0]),
            'the first parameter of apply must be a procedure')
    end_list = args.pop()
    args += end_list.members
    return evaluate(args, env)

def load_file(filename):
    """Load file to evaluate."""
    repl(open(filename))

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
        'string?':lambda x: isa(x,str) and not is_eof(x), 'expt':math.pow,
        'max': max, 'min':min, 'abs':abs, 'list':List, 'list-ref':list_ref,
        'number->string':num2str,'string->number':str2num, 'make-list':make_list,
        'pair?':is_pair, 'list?':is_list, 'append':append, 'display':display,
        'quotient':quotient, 'remainder':remainder, 'modulo':op.mod,
        'sqrt':math.sqrt, 'numerator':numerator, 'denominator':denominator,
        'floor':math.floor, 'ceiling':math.ceil, 'truncate':math.trunc,
        'round':round, 'zero?':lambda x: x==0, 'negative?':lambda x: x<0,
        'positive?':lambda x: x>0, 'even?':lambda x: x%2==0, 'or':s_or,
        'sin':math.sin, 'cos':math.cos, 'tan':math.tan, 'asin':math.asin,
        'acos':math.acos, 'atan':math.atan, 'make-rectangular':make_rectangular,
        'real-part':lambda x: x.real, 'imag-part':lambda x: x.imag,
        'magnitude':lambda x: math.sqrt(x.real*x.real+x.imag*x.imag),
        'complex?':is_complex, 'string->symbol':str2symbol, 'substring':substr,
        'string-append':append_str, 'symbol?':lambda x:isa(x,Symbol),
        'reverse':reverse_list, 'procedure?':is_procedure, 'load':load_file,
        'eval':s_eval, 'odd?':lambda x: x%2!=0, 'apply':s_apply, 'map':s_map,
        'open-input-file':open, 'port?':lambda x: isa(x,type(sys.stdout)),
        'input-port?':is_input, 'read':read, 'list-set!':list_set, 'true': True,
        'eof-object?':is_eof, 'close-input-port':close_input, 'and':s_and,
        'open-output-file':lambda x: open(x,'w'), 'output-port?':is_output,
        'write':write, 'close-output-port':close_output, 'false':False,
        'promise?':lambda x: isa(x,Promise), 'promise-forced?':promise_forced,
        'promise-value':promise_value,
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
        require(can_define, "can't bind name in null syntactic environment")
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
        require_type(isa(header, Symbol), "can only define a symbol")
        if not (isa(parts[2], list) and parts[2] and parts[2][0] == 'lambda'):
            can_define = False
        parts[2] = _expand(parts[2], can_define)
        return parts
    if parts[0] == 'lambda':
        require(parts, len(parts)>=3)
        parms = parts[1]
        require_type((isa(parms, list) and all(isa(i, Symbol) for i in parms))
            or isa(parms, Symbol), 'illegal lambda argument list')
        # body is a list even there's only one expression to be evaluated
        body = ['begin'] + parts[2:]
        return ['lambda', parms, _expand(body,can_define)]
    if parts[0] == 'set!':
        require(parts, len(parts)==3)
        symbol = parts[1]
        require_type(isa(symbol, Symbol), "can set! only a symbol")
        parts[2] = _expand(parts[2])
        return parts
    if parts[0] == 'quasiquote':
        require(parts, len(parts)==2)
        return _expand_quasiquote(parts[1])
    # named let
    if parts[0] == 'nlet':
        require(parts, len(parts)>3)
        name = parts[1]
        require_type(isa(name,Symbol), 'the first parameter of nlet must be a symbol')
        binds = parts[2]
        require_type(all(isa(i, list) and len(i)==2 and isa(i[0], Symbol)
                    for i in binds), 'illegal binding list')
        bodies = parts[3:]
        parms, values = zip(*binds) if binds else ([], [])
        letrec = ['letrec', name]
        new_binds = [name,['lambda',list(parms)]+bodies]
        letrec.insert(1, [new_binds])
        values = list(values)
        values.insert(0, letrec)
        return _expand(values, can_define)
    if parts[0] == 'let' or parts[0] == 'let*' or parts[0] == 'letrec':
        require(parts, len(parts)>2)
        binds = parts[1]
        require_type(all(isa(i, list) and len(i)==2 and isa(i[0], Symbol)
                    for i in binds), 'illegal binding list')
        # _expand in lambda will expand bodies
        bodies = parts[2:]
        # convert let* and letrec into equal let form
        if parts[0] == 'let*':
            new_form = ['let', [binds[-1]]] + bodies
            for i in reversed(binds[:-1]):
                new_form = ['let', [i], new_form]
            return _expand(new_form, can_define)
        if parts[0] == 'letrec':
            outer, inner = [['let'] for i in range(2)]
            outer_bind, inner_bind = [[] for i in range(2)]
            for name, val in binds:
                outer_bind.append([name,None])
                inner_bind.append([Symbol(name+'.1'),val])
                inner.append(['set!',name,Symbol(name+'.1')])
            inner += bodies
            inner.insert(1, inner_bind)
            outer.append(outer_bind)
            outer.append(inner)
            return _expand(outer, can_define)
        parms, values = zip(*binds) if binds else ([], [])
        return _expand([['lambda',list(parms)]+bodies]+list(values), can_define)
    if parts[0] == 'do':
        require(parts, len(parts)>2)
        binds = parts[1]
        require_type(all(isa(i, list) and len(i)==3 and isa(i[0], Symbol)
                    for i in binds), 'illegal binding list')
        condition_val = parts[2]
        require_type(isa(condition_val,list) and condition_val,
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
    if parts[0] == 'cond':
        require(parts, len(parts)>1)
        if parts[1:-1]:
            require_type(all(isa(i,list) and i and i[0]!='else' for i in parts[1:-1]),
                    'ill-formed clause in cond')
        require_type(isa(parts[-1],list) and parts[-1], 'ill-formed clause in cond')
        if parts[-1][0] != 'else':
            parts.append(['else',None])
        else:
            require(parts, len(parts[-1])>1)
        for cond in parts[1:]:
            cond = list(map(_expand,cond))
        return parts
    if parts[0] == 'delay' or parts[0] == 'force':
        require(parts, len(parts)==2)
        if parts[0] == 'delay':
            # (delay expr) => (delay (memo-proc (lambda () expr)))
            parts[1] = [Symbol('memo-proc'),['lambda',[],parts[1]]]
        parts[1] = _expand(parts[1])
        return parts
    if parts[0] == 'case':
        require(parts, len(parts)>2)
        if parts[2:-1]:
            if not all(isa(i,list) and len(i)>1 and isa(i[0],list) for i in parts[2:-1]):
                require_type(False, 'ill-formed clause in case')
        require_type(isa(parts[-1],list) and len(parts[-1])>1
                    and (isa(parts[-1][0],list) or parts[-1][0]=='else'),
                'ill-formed clause in case')
        if parts[-1][0] != 'else':
            parts.append(['else',None])
        parts[1] = _expand(parts[1])
        for case in parts[2:]:
            case[0] = [quotes["'"], case[0]]
            case[1:] = list(map(_expand,case[1:]))
        return parts
    if parts[0] == 'if':
        if len(parts) == 3:
            parts.append(None)
        require(parts, len(parts)==4)
        bodies = list(map(_expand, parts[1:]))
        return ['cond', [bodies[0],bodies[1]], ['else',bodies[2]]]
    # next branches share 'return' expression
    if parts[0] == 'begin':
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
    require_type(isa(s_list, list), 'the parameter must be a list')
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

_quotes = {
        "'":'quote', '`':'quasiquote', ',':'unquote', ',@':'unquote-splicing',
}

quotes = {s:Symbol(_quotes[s]) for s in _quotes}

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
                new_token = _read_ahead(token)
                if new_token != ';':
                    members.append(new_token)
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
        require_type(all(isa(i,int) for i in exprs),
                'parameters of gcd must be integers')
        exprs.insert(0, 0)
    if func is lcm:
        require_type(all(isa(i,int) for i in exprs),
                'parameters of lcm must be integers')
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
    require_type(isa(exprs[0],int) and isa(exprs[1],int),
            'parameters of mod operation must be integers')
    return func(*exprs)

_special_forms = {
        _mathop: _do_math_op, _cmpop: _do_cmp_op, _modop: _do_mod_op,
}

_need_env = [s_eval, s_apply, s_map]

def _do_quote(parts):
    """Return pair or list if possible when returning from quote."""
    if not _need_expand_quotes(parts):
        return parts
    if parts.count('.')>1 or parts.count('.')==1 and parts.index('.')<len(parts)-2:
        require(parts, False, 'ill-formed dotted list')
    if len(parts) >= 3 and parts[-2] == '.':
        return Pair(_do_quote(parts[0]), _do_quote(parts[1:]))
    return List(parts)

def _deal_special(func, exprs):
    """Deal with special functions."""
    for is_op in _special_forms:
        if is_op(func):
            return _special_forms[is_op](func, exprs)

def evaluate(parts, env=global_env):
    """Evaluate value of parts."""
    while True:
        if isa(parts, Symbol):
            return env.find(parts)[parts]
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
            oldVal = env.find(symbol)[symbol]
            env.find(symbol)[symbol] = evaluate(value, env)
            return oldVal
        if parts[0] == 'delay':
            return Promise(evaluate(parts[1],env))
        if parts[0] == 'force':
            parts[1] = evaluate(parts[1], env)
            require_type(isa(parts[1],Promise), 'parameter of force must be a promise')
            parts = [parts[1].exprs]
        elif parts[0] == 'case':
            expr = evaluate(parts[1], env)
            for case in parts[2:-1]:
                if expr in evaluate(case[0],env):
                    parts = ['begin'] + case[1:]
                    return evaluate(parts, env)
            parts = ['begin'] + parts[-1][1:]
        elif parts[0] == 'cond':
            for cond in parts[1:-1]:
                do_branch = evaluate(cond[0], env)
                # (cond ('() 3)) is valid
                if do_branch or isa(do_branch, list):
                    parts = cond[1:]
                    if not parts:
                        return do_branch
                    parts.insert(0, 'begin')
                    return evaluate(parts, env)
            parts = ['begin'] + parts[-1][1:]
        elif parts[0] == 'do':
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
                if func in _need_env:
                    exprs.append(env)
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

def repl(in_from=sys.stdin):
    """Read-evaluate-print-loop."""
    prompt = '> '
    tokenizer = Tokenizer(in_from)
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

# use this to implement delay
_pre_procedure = """
    (define (memo-proc proc)
        (let ((already-run? #f) (result #f))
            (lambda ()
                (if (not already-run?)
                (begin (set! result (proc))
                        (set! already-run? #t)
                        result)
                result))))
"""

try:
    from io import StringIO
    evaluate(parse(Tokenizer(StringIO(_pre_procedure))))
except TypeError:
    # make it compatible with python2 when debugging with winpdb
    from StringIO import StringIO
    evaluate(parse(Tokenizer(StringIO(_pre_procedure))))

if __name__ == '__main__':
    repl()

