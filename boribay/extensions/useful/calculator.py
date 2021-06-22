import decimal
import math
from functools import lru_cache

from boribay.core import exceptions
from sly import Lexer, Parser

__all__ = ('CalcLexer', 'CalcParser')


class CalcLexer(Lexer):
    tokens = {NUMBER, NEWLINE_CHAR, NAME}
    ignore = ' \t'
    literals = {'+', '-', '*', '/', '%', '!', '^', '(', ')', '='}
    NAME = '[a-zA-Z_][a-zA-Z0-9_]*'

    def error(self, t):
        raise exceptions.CalcError(t.value[0])

    @_(r'(\d+(?:\.\d+)?)')
    def NUMBER(self, t):
        t.value = decimal.Decimal(t.value)
        return t

    @_(r'\n+|;+')
    def NEWLINE_CHAR(self, t):
        self.lineno = t.value.count('\n') + t.value.count(';')
        return t


@lru_cache(5)
def fib(n):
    if n > 400:
        raise exceptions.Overflow()

    elif n <= 1:
        return n

    return fib(n - 1) + fib(n - 2)


class CalcParser(Parser):
    tokens = CalcLexer.tokens

    precedence = (
        ('left', '+', '-'),
        ('left', '*', '/', '%'),
        ('left', '^'),
        ('left', '!'),
        ('right', UMINUS)
    )
    funcs = {
        'round': round,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': lambda x: x.sqrt(),
        'abs': lambda x: x.copy_abs(),
        'fib': fib
    }
    constants = {
        'pi': decimal.Decimal(math.pi),
        'e': decimal.Decimal(math.e),
        'tau': decimal.Decimal(math.tau),
        'inf': decimal.Decimal(math.inf),
        'nan': decimal.Decimal(math.nan)
    }

    @_('statement')
    @_('statements NEWLINE_CHAR statement')
    def statements(self, p):
        self.result.append(p.statement)

    @_('NAME "=" expression')
    def statement(self, p):
        if p.NAME in self.funcs or p.NAME in self.constants:
            raise exceptions.KeywordAlreadyTaken

        self.variables[p.NAME] = p.expression
        return f'{p.NAME} = {p.expression}'

    @_('expression')
    def statement(self, p):
        return p.expression

    @_('expression "+" expression')
    def expression(self, p):
        return p.expression0 + p.expression1

    @_('expression "-" expression')
    def expression(self, p):
        return p.expression0 - p.expression1

    @_('expression "*" expression')
    def expression(self, p):
        return p.expression0 * p.expression1

    @_('expression "/" expression')
    def expression(self, p):
        return p.expression0 / p.expression1

    @_('expression "%" expression')
    def expression(self, p):
        return p.expression0 % p.expression1

    @_('expression "^" expression')
    def expression(self, p):
        if p.expression0 > 200 or p.expression1 > 200:
            raise exceptions.Overflow
        return p.expression0 ** p.expression1

    @_('expression "!"')
    def expression(self, p):
        if p.expression > 50:
            raise exceptions.Overflow
        return decimal.Decimal(math.gamma(p.expression + decimal.Decimal("1.0")))

    @_('"-" expression %prec UMINUS')
    def expression(self, p):
        return -p.expression

    @_('"(" expression ")"')
    def expression(self, p):
        return p.expression

    @_('NAME "(" expression ")"')
    def expression(self, p):
        try:
            return decimal.Decimal(self.funcs[p.NAME](p.expression))
        except KeyError:
            raise exceptions.UndefinedVariable(p.NAME)

    @_('NUMBER')
    def expression(self, p):
        return p.NUMBER

    @_('NAME')
    def expression(self, p):
        try:
            try:
                return self.constants[p.NAME]
            except KeyError:
                return self.variables[p.NAME]
        except KeyError:
            raise exceptions.UndefinedVariable(p.NAME)

    def error(self, p):
        raise exceptions.CalcError(getattr(p, 'value', 'EOF'))

    def __init__(self):
        self.variables = {}
        self.result = []
        super().__init__()

    @staticmethod
    def match(expression):
        o, c = tuple('({['), tuple(')}]')
        mapping = dict(zip(o, c))
        lis = []

        for letter in expression:
            if letter in o:
                lis.append(mapping[letter])
            elif letter in c and (not lis or letter != lis.pop()):
                return False

        return not lis

    def parse(self, expression):
        super().parse(expression)
        return self.result
