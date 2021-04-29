from discord.ext import commands


class CalcError(Exception):
    """Raised when parsing the task was unsuccessful."""

    def __init__(self, char):
        self.exc = f'Inadmissable character in the task: `{char}`'


class KeywordAlreadyTaken(Exception):
    """Raised when the keyword that is created by user is already taken."""
    pass


class UndefinedVariable(Exception):
    """Raised when the called variable does not exist."""

    def __init__(self, variable):
        self.exc = f'Wrong variable name given: `{variable}`.'


class Overflow(Exception):
    """Raised when the given expression output was too big."""
    pass


class UnclosedBrackets(Exception):
    """Raised when the given expression has unclosed brackets."""
    pass


class EmptyBrackets(Exception):
    """Raised when the given expression has empty or unused brackets."""
    pass


class TooManyOptions(commands.CommandError):
    """Raised when there were more than 10 options on a poll."""
    pass


class NotEnoughOptions(commands.CommandError):
    """Raised when the options count is < 2."""
    pass


class NotAnInteger(Exception):
    def __init__(self, message: str = 'The number must be positive.'):
        self.message = message

    def __str__(self):
        return self.message


class NotEnough(Exception):
    def __init__(self, message: str = 'You have not enough batyrs.'):
        self.message = message

    def __str__(self):
        return self.message


class PastMinimum(Exception):
    def __init__(self, minimum: int, message: str = 'The minimum bet for this command: {} batyrs.'):
        super().__init__(message)
        self.message = message.format(minimum)

    def __str__(self):
        return self.message
