
# runtime soft bindings

ABI = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']


class KIND:
    UNDEFINED = 0
    INT    = 1
    STRING = 2
    ARRAY  = 3
    DICT   = 4
    FRAC   = 5


class OP:
    PLUS  = 1
    MINUS = 2
    TIMES = 3

    DIVIDE = 4
    POWER  = 5

    EQUAL   = 6
    INEQUAL = 7

    NEGATE = 8

    SMALLER = 9
    GREATER = 10





