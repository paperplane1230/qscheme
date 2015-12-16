#!/usr/bin/env ipython3

import fractions

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
        """Remove outer boundary of second part when printing."""
        if isa(symbol, Pair):
            return ' ' + str(symbol)[1:-1]
        # deal with situation where cdr is '()
        if self.__second == []:
            return ''
        return ' . ' + tostr(symbol)
    def __str__(self):
        """Format for printing."""
        return ''.join(['(', tostr(self.__first), self.__rm_outer(self.__second), ')'])
    def __eq__(self, pair):
        """Compare two pairs."""
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
    @cdr.setter
    def cdr(self, value):
        """Set the second element."""
        self.__second = value

# class List(Pair):
#     """Class for list."""
#     def __init__(self, members):
#         """Construct a list in scheme with members in a list."""
#         self.__members = members
#         self.__cons = self.__list(self.__members)
#     def __list(self, exprs):
#         """Construct a list with method cons."""
#         result = Pair(exprs[-1], [])
#         for i in reversed(range(len(exprs)-1)):
#             result = Pair(exprs[i], result)
#         return result
#     def __str__(self):
#         """Format for printing."""
#         return str(self.__cons)
#     def __len__(self):
#         """Length of list."""
#         return len(self.__members)
#     def __getitem__(self, i):
#         """Get member by index."""
#         return self.__members[i]
#     def __setitem__(self, key, val):
#         """Set member by index."""
#         self.__members[key] = val
#         pair = self.__cons
#         for i in range(key):
#             pair = cdr(pair)
#         set_car(pair, val)
#     @property
#     def car(self):
#         """Return the first part."""
#         return self.__cons.car
#     @property
#     def cdr(self):
#         """Return the second part."""
#         return self.__cons.cdr
#     @car.setter
#     def car(self, value):
#         """Set the first element."""
#         self.__cons.car = value
#     @cdr.setter
#     def cdr(self, value):
#         """Set the second element."""
#         self.__cons.cdr = value

# def list_ref(s_list, i):
#     """Return the ith element of the list."""
#     require(s_list, isa(s_list, List), 'parameter of list-ref must be a list')
#     return s_list[i]

def car(pair):
    """Return the first element of the pair."""
    return pair.car

def cdr(pair):
    """Return the second element of the pair."""
    return pair.cdr

def set_car(pair, val):
    """Set car of the pair."""
    pair.car = val
    return None

def set_cdr(pair, val):
    """Set cdr of the pair."""
    pair.cdr = val
    return None

isa = isinstance

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

def is_bool(symbol):
    """Judge whether the symbol is boolean."""
    return isa(symbol, bool)

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

def is_null(symbol):
    """Judge whether the symbol is null."""
    return symbol == []

def ref_eq(op_left, op_right):
    """Judge whether the two object are the same."""
    return op_left is op_right

