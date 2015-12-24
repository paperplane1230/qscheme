#!/usr/bin/env ipython3

import fractions

class Env(dict):
    """Context Environment."""
    def __init__(self, parms=(), args=(), outer=None):
        """Initialize the environment with specific parameters."""
        self.__outer = outer
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

class Symbol(str):
    """Class for symbol."""
    pass

class Pair:
    """Class for pair in scheme(created by function cons)."""
    def __init__(self, first, second):
        """Construct a pair with given data."""
        self.__first = first
        self.__second = second
        # be the cache for string form of this pair
        self.__str = ''
        self.__update_str()
    def __rm_outer(self, symbol):
        """Remove outer boundary of second part when printing."""
        if isa(symbol, Pair) or isa(symbol, List):
            return ' ' + str(symbol)[1:-1]
        # deal with situation where cdr is '()
        if self.__second == []:
            return ''
        return ' . ' + tostr(symbol)
    def __update_str(self):
        """Format for printing."""
        self.__str = ''.join(['(', tostr(self.__first),
                self.__rm_outer(self.__second), ')'])
    def __str__(self):
        """Return string form."""
        return self.__str
    def __eq__(self, pair):
        """Compare two pairs."""
        if not isa(pair, Pair):
            raise TypeError("the two type can't be compared")
        return self.__first == pair.car and self.__second == pair.cdr
    @property
    def car(self):
        """Return the first part."""
        return self.__first
    @property
    def cdr(self):
        """Return the second part."""
        return self.__second
    @car.setter
    def car(self, value):
        """Set the first element."""
        self.__first = value
        self.__update_str()
    @cdr.setter
    def cdr(self, value):
        """Set the second element."""
        self.__second = value
        self.__update_str()

class List:
    """Class for list."""
    def __init__(self, members):
        """Construct a list in scheme with members in a list."""
        if not isa(members, list):
            raise TypeError('the parameter of list must be a list of objects')
        self.__members = members
        self.__cons = self.__list(self.__members)
    def __list(self, exprs):
        """Construct a list with method cons."""
        require(exprs, len(exprs)!=0)
        result = Pair(exprs[-1], [])
        for i in reversed(range(len(exprs)-1)):
            result = Pair(exprs[i], result)
        return result
    def __str__(self):
        """Format for printing."""
        return str(self.__cons)
    def __len__(self):
        """Length of list."""
        return len(self.__members)
    def __eq__(self, s_list):
        """Compare two lists."""
        if not isa(s_list, List):
            raise TypeError("the two type can't be compared")
        return self.__cons == s_list.pair
    def __getitem__(self, i):
        """Get member by index."""
        return self.__members[i]
    def __setitem__(self, key, val):
        """Set member by index."""
        self.__members[key] = val
        pair = self.__cons
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
    def members(self):
        """Get the list inside."""
        return self.__members
    @property
    def pair(self):
        """Return the pair inside it."""
        return self.__cons
    @property
    def car(self):
        """Return the first part."""
        return self.__cons.car
    @property
    def cdr(self):
        """Return the second part."""
        return self.__cons.cdr
    @car.setter
    def car(self, value):
        """Set the first element."""
        self.__cons.car = value
    @cdr.setter
    def cdr(self, value):
        """Set the second element."""
        self.__cons.cdr = value

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
    if not isa(s_list, List):
        raise TypeError("the first parameter of append must be a list")
    last = appended.pop()
    members = s_list.members + appended
    result = Pair(members[-1], last)
    for i in reversed(range(len(members)-1)):
        result = Pair(members[i], result)
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
    if not isa(s_list, List):
        raise TypeError("parameter of list-ref must be a list")
    return s_list[i]

def list_set(s_list, i, val):
    """Set value in list by index."""
    if not isa(s_list, List):
        raise TypeError("parameter of list-set! must be a list")
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
                # user can't write a+bj
                if token.find('j') >= 0:
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
        return str(token).replace('j', 'i')[1:-1]
    if isa(token, list):
        return '(' + ' '.join(map(tostr, token)) + ')'
    return str(token)

def require(var, condition, msg='wrong length'):
    """Assert if condition isn't satisfied."""
    if not condition:
        raise SyntaxError(tostr(var)+': '+msg)

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
    if not is_number(num):
        raise TypeError("parameter of number->string must be a number")
    return tostr(num)

def str2num(numstr):
    """Convert string to number."""
    if not isa(numstr, str):
        raise TypeError("parameter of string->number must be a string")
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

