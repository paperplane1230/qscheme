#!/usr/bin/env ipython3

import fractions
import sys

class Env(dict):
    """Context Environment."""
    def __init__(self, parms=(), args=(), outer=None):
        """Initialize the environment with specific parameters."""
        self._outer = outer
        if isa(parms, Symbol):
        # (lambda x (...))
            self.update({parms:list(args)})
        else:
            if len(parms) != len(args):
                raise TypeError('expected {0}, given {1}'
                        .format(tostr(parms), tostr(args)))
            self.update(zip(parms, args))
    def find(self, op):
        """Find operator in the environment."""
        # return the environment itself so that invoker can update information
        # in specific environment
        if op in self:
            return self
        if self._outer is None:
            raise LookupError('unbound '+op)
        return self._outer.find(op)

class Procedure:
    """Class for procedure."""
    def __init__(self, parms, body, env):
        """Initialize a procedure with specific parameters, arguments and environment."""
        self.parms = parms
        self.body = body
        self.env = env

class Symbol(str):
    """Class for symbol."""
    pass

def _property(attr):
    """Get attribute of a class. It's a closure."""
    name = '_' + attr
    @property
    def prop(self):
        """Get the specific attribute."""
        return getattr(self, name)
    @prop.setter
    def prop(self, value):
        """Set the attribute."""
        setattr(self, name, value)
        if isa(self, Pair):
            self.update_str()
    return prop

class Pair:
    """Class for pair in scheme(created by function cons)."""
    car = _property('car')
    cdr = _property('cdr')
    def __init__(self, car, cdr):
        """Construct a pair with given data."""
        # be the cache for string form of this pair
        self._str = ''
        # here can't use prop to update _str
        # because _car and _cdr aren't constructed
        self._car = car
        self._cdr = cdr
        # invoke update_str() manually only here
        self.update_str()
    def _rm_outer(self, symbol):
        """Remove outer boundary of second part when printing."""
        if isa(symbol, Pair) or isa(symbol, List):
            return ' ' + str(symbol)[1:-1]
        # deal with situation where cdr is '()
        if self.cdr == []:
            return ''
        return ' . ' + tostr(symbol)
    def update_str(self):
        """Format for printing."""
        self._str = ''.join(['(',tostr(self.car),self._rm_outer(self.cdr),')'])
    def __str__(self):
        """Return string form."""
        return self._str
    def __eq__(self, pair):
        """Compare two pairs."""
        require_type(isa(pair, Pair), "the two type can't be compared")
        return self.car == pair.car and self.cdr == pair.cdr

class List:
    """Class for list."""
    def __init__(self, members):
        """Construct a list in scheme with members in a list."""
        require_type(isa(members, list),
                'the parameter of list must be a list of objects')
        self.members = members
        self.pair = self._list(members)
    def _list(self, exprs):
        """Construct a list with method cons."""
        require(exprs, len(exprs)!=0)
        result = Pair(exprs[-1], [])
        for i in reversed(exprs[:-1]):
            result = Pair(i, result)
        return result
    def __str__(self):
        """Format for printing."""
        return str(self.pair)
    def __len__(self):
        """Length of list."""
        return len(self.members)
    def __eq__(self, s_list):
        """Compare two lists."""
        require_type(isa(s_list, List), "the two type can't be compared")
        return self.pair == s_list.pair
    def __getitem__(self, i):
        """Get member by index."""
        return self.members[i]
    def __setitem__(self, key, val):
        """Set member by index."""
        self.members[key] = val
        pair = self.pair
        for i in range(key):
            pair = pair.cdr
        pair.car = val
    def __add__(self, right):
        """Add scheme list with another thing."""
        try:
            if right == []:
                return self
        except TypeError:
            None
        raise TypeError("+ can't be applied between list and "+str(type(right)))
    @property
    def car(self):
        """Return the first part."""
        return self.pair.car
    @property
    def cdr(self):
        """Return the second part."""
        return self.pair.cdr
    @car.setter
    def car(self, value):
        """Set the first element."""
        self.pair.car = value
    @cdr.setter
    def cdr(self, value):
        """Set the second element."""
        self.pair.cdr = value

class Promise:
    """Class for lazy binding."""
    def __init__(self, exprs):
        """Construct a promise with its content."""
        self.exprs = exprs

def _pair2list(pair):
    """Convert a pair to list."""
    members = []
    while pair:
        members.append(pair.car)
        pair = pair.cdr
    return List(members)

def _list2pair(s_list):
    """Convert a list into pair."""
    return s_list.pair

def append(*values):
    """Append val to a list, not modifying the list."""
    require(values, len(values)>=2)
    values = list(values)
    s_list = values[0]
    appended = values[1:]
    require_type(isa(s_list,List), 'the first parameter of append must be a list')
    last = appended.pop()
    members = s_list.members + appended
    result = Pair(members[-1], last)
    for i in reversed(members[:-1]):
        result = Pair(i, result)
    return result

def is_list(s_list):
    """Judge whether it's a list."""
    return isa(s_list, List)

def is_pair(pair):
    """Judge whether it's a pair."""
    return isa(pair, Pair) or is_list(pair)

def cons(first, second):
    """Construct a pair or a list if possible.
    """
    pair = Pair(first, second)
    if str(pair).find(' . ') < 0:
        pair = _pair2list(pair)
    return pair

def list_ref(s_list, i):
    """Return the ith element of the list."""
    require_type(isa(s_list,List), 'parameters of list-ref must be a list')
    return s_list[i]

def list_set(s_list, i, val):
    """Set value in list by index."""
    require_type(isa(s_list,List), 'parameters of list-set! must be a list')
    s_list[i] = val
    return None

def make_list(num, val):
    """Construct a list filled with num numbers of value val."""
    return List([val for i in range(num)])

def set_car(pair, val):
    """Set car of the pair."""
    pair.car = val
    return pair

def set_cdr(pair, val):
    """Set cdr of the pair."""
    pair.cdr = val
    if isa(pair, Pair) and str(pair).find(' . ') < 0:
        return _pair2list(pair)
    if isa(pair, List) and str(pair).find(' . ') > 0:
        return _list2pair(pair)
    return pair

isa = isinstance

def transform(token):
    """Transform token into proper form."""
    if token == '#t':
        return True
    if token == '#f':
        return False
    if token[0] == '"':
        return bytes(token[1:-1], "utf-8").decode('unicode-escape')
    if token.startswith(';'):
        return ';'
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
                result = complex(token.replace('i', 'j'))
                # user can't write a+bj and form like i, 2i, 3i where no '+' appers
                if token.find('j') >= 0 or token.find('+') < 0:
                    return Symbol(token.lower())
                return result
            except ValueError:
                try:
                    return fractions.Fraction(token)
                except ValueError:
                    return Symbol(token.lower())

def tostr(token):
    """Convert a token into form in lisp."""
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
        result = str(token).replace('j', 'i')
        if result.find('(') < 0:
            return result
        return result[1:-1]
    if isa(token, list):
        return '(' + ' '.join(map(tostr, token)) + ')'
    return str(token)

def require(var, condition, msg='wrong length'):
    """Assert if condition isn't satisfied."""
    if not condition:
        raise SyntaxError(tostr(var)+': '+msg)

def require_type(cond, msg):
    """Assert for TypeError."""
    if not cond:
        raise TypeError(msg)

def not_op(target):
    """Implementation of operator not."""
    if not isa(target, bool):
        return False
    return not target

def is_int(symbol):
    """Judge whether the symbol is an integer."""
    return isa(symbol, int)

def _is_real(symbol):
    """Judge whether the symbol is a real number."""
    return isa(symbol, float) or is_int(symbol)

def is_rational(symbol):
    """Judge whether the symbol is rational."""
    return isa(symbol, fractions.Fraction) or _is_real(symbol)

def is_number(symbol):
    """Judge whether the symbol is a number."""
    return isa(symbol, complex) or is_rational(symbol)

def num2str(num):
    """Convert number to string."""
    require_type(is_number(num), 'parameter of number->string must be a number')
    return tostr(num)

def str2num(numstr):
    """Convert string to number."""
    require_type(isa(numstr,str), 'parameter of string->number must be a string')
    return transform(numstr)

def quotient(left_object, right_object):
    """Return quotient of the two and round towards 0."""
    return int(float(left_object)/right_object)

def remainder(left_object, right_object):
    """Return left % right whose sign is the same with the left one."""
    result = left_object % right_object
    if left_object < 0 and result > 0 or left_object > 0 and result < 0:
        result = result - right_object
    return result

def display(content):
    """Print content."""
    print(content if isa(content, str) else tostr(content))

def lcm(num1, num2):
    """Compute the least common multiple for two numbers."""
    return num1 * num2 // fractions.gcd(num1,num2)

def numerator(num):
    """Return numerator of a fraction."""
    require_type(isa(num,fractions.Fraction) or isa(num,int),
            'parameter of numerator must be a fraction or integer')
    return num.numerator

def denominator(num):
    """Return denominator of a fraction."""
    require_type(isa(num,fractions.Fraction) or isa(num,int),
            'parameter of denominator must be a fraction or integer')
    return num.denominator

def make_rectangular(num1, num2):
    """Construct complex with two numbers."""
    require_type((isa(num1,int) or isa(num1,float)) and (isa(num2,int) or isa(num2,float)),
            'parameters of make_rectangular must be integers or float numbers')
    return complex(num1, num2)

def is_complex(num):
    """Judge whether the number is a complex."""
    try:
        complex(num)
    except Exception:
        return False
    return True

def str2symbol(string):
    """Convert a string to symbol."""
    require_type(isa(string, str), 'parameter of string->symbol must be a string')
    if string.find('"') >= 0:
        string = ''.join(['|', string, '|'])
    return Symbol(string)

def substr(string, beg, end):
    """Return substring from beg to end."""
    require_type(isa(string, str), 'the first parameter of substring must be a string')
    if beg < 0 or end >= len(string) or beg > end:
        raise IndexError('the index of substring is invalid')
    return string[beg:end]

def append_str(*strs):
    """Append strings."""
    return ''.join(list(strs))

def reverse_list(s_list):
    """Reverse a scheme list."""
    require_type(isa(s_list, List), 'parameter of reverse must be a list')
    new_list = s_list.members.copy()
    new_list.reverse()
    return List(new_list)

def is_procedure(procedure):
    """Judge whether it's a procedure."""
    return isa(procedure,Procedure) or isa(procedure,type(max)) or isa(procedure,type(tostr))

def is_input(port):
    """Judge whether the port is an input port."""
    try:
        return port.mode == 'r'
    except Exception:
        return False

def is_output(port):
    """Judge whether the port is an output port."""
    try:
        return port.mode == 'w'
    except Exception:
        return False

def read(in_file):
    """Read a line from the file."""
    require_type(is_input(in_file), 'the parameter of read must be an input file')
    txt = in_file.readline().lower()
    while txt == '\n':
        txt = in_file.readline().lower()
    return txt.strip() if txt else Symbol('#!eof')

def is_eof(eof):
    """Judge whether it's an eof."""
    return eof == Symbol('#!eof')

def close_input(in_file):
    """Close input file."""
    require_type(is_input(in_file), 'the parameter must be an input file')
    in_file.close()

def write(content, port=sys.stdout):
    """Write content to the port."""
    require_type(is_output(port), 'the parameter of write must be an output file')
    if port is sys.stdout:
        display(content)
        return
    port.write(tostr(content))

def close_output(out_file):
    """Close the output file."""
    require_type(is_output(out_file), 'the parameter must be an output file')
    out_file.close()

def s_or(*args):
    """Logical or."""
    result = False
    for i in args:
        result = result or i
        if result:
            break
    return result

def s_and(*args):
    """Logical and."""
    result = True
    for i in args:
        result = result and i
        if not result:
            break
    return result

def promise_forced(promise):
    """Judge whether the promise has been forced."""
    require_type(isa(promise,Promise),
            'the parameter of promise_forced must be a Promise')
    return promise.exprs.env.find(Symbol('already-run?'))['already-run?']

def promise_value(promise):
    """Return forced value in promise else raise exception."""
    require_type(isa(promise,Promise),
            'the parameter of promise_forced must be a Promise')
    if promise_forced(promise):
        return promise.exprs.env.find(Symbol('result'))['result']
    raise RuntimeError('the promise has not been forced')
