import decimal

from sly import Lexer

from .exceptions import CalcError


class CalcLexer(Lexer):
    tokens = {NUMBER, NEWLINE_CHAR, NAME}
    ignore = ' \t'
    literals = {
        '+', '-', '*', '/', '%', '!', '^', '(', ')', '='
    }
    NAME = '[a-zA-Z_][a-zA-Z0-9_]*'

    def error(self, t):
        raise CalcError(t.value[0])

    @_(r'(\d+(?:\.\d+)?)')
    def NUMBER(self, t):
        t.value = decimal.Decimal(t.value)
        return t

    @_(r'\n+|;+')
    def NEWLINE_CHAR(self, t):
        self.lineno = t.value.count('\n') + t.value.count(';')
        return t
