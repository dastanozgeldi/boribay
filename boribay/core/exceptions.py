
class BoribayError(Exception):
    """The base exception class of the bot."""


class UserError(BoribayError):
    """The base for exceptions, caused by user."""

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f'❌ {self.message}'


class EconomyError(BoribayError):
    """The base for the economics-related exceptions."""


class NotAnInteger(EconomyError):
    """Raised when the given int is negative."""

    def __init__(self, argument: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argument = argument

    def __str__(self):
        return f'Argument "{self.argument}" does not look like a number at all.'


class NotEnough(EconomyError):
    """Raised when a user has not enough money to do a transaction."""

    def __init__(self, argument: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argument = argument

    def __str__(self):
        return f'You have not enough batyrs ({self.argument} given).'


class PastMinimum(EconomyError):
    """Raised when a user bets fewer money than the required minimum."""

    def __init__(self, minimum: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minimum = minimum

    def __str__(self):
        return f'The minimum bet for this command: {self.minimum} batyrs.'


class CalcError(UserError):
    """The base for the calculator-related exceptions."""


class InadmissableChar(CalcError):
    """Raised when parsing the task was unsuccessful."""

    def __init__(self, char):
        super().__init__(f'Inadmissable character in the task: `{char}`')


class UndefinedVariable(CalcError):
    """Raised when the called variable does not exist."""

    def __init__(self, variable):
        super().__init__(f'Wrong variable name given: `{variable}`.')


class KeywordAlreadyTaken(CalcError):
    """Raised when the keyword that is created by user is already taken."""

    def __str__(self):
        return 'The given variable name is shadowing a reserved keyword argument.'


class Overflow(CalcError):
    """Raised when the given expression output was too big."""

    def __str__(self):
        return 'Too big number was given.'


class UnclosedBrackets(CalcError):
    """Raised when the given expression has unclosed brackets."""

    def __str__(self):
        return 'Given expression has unclosed brackets.'


class EmptyBrackets(CalcError):
    """Raised when the given expression has empty or unused brackets."""

    def __str__(self):
        return 'Given expression has empty brackets.'
