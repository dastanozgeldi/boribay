from discord.ext import commands


class TooManyOptions(commands.CommandError):
    """Raised when there were more than 10 options on a poll."""
    pass


class NotEnoughOptions(commands.CommandError):
    """Raised when the options count is < 2."""
    pass


class CustomException(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f'❌ {self.message}'


class NotAnInteger(CustomException):
    def __init__(self):
        super().__init__('The number must be positive.')


class NotEnough(CustomException):
    def __init__(self):
        super().__init__('You have not enough batyrs.')


class PastMinimum(CustomException):
    def __init__(self, minimum: int):
        super().__init__(f'The minimum bet for this command: {minimum} batyrs.')


class CalcError(CustomException):
    """Raised when parsing the task was unsuccessful."""

    def __init__(self, char):
        super().__init__(f'Inadmissable character in the task: `{char}`')


class UndefinedVariable(CustomException):
    """Raised when the called variable does not exist."""

    def __init__(self, variable):
        super().__init__(f'Wrong variable name given: `{variable}`.')


class KeywordAlreadyTaken(Exception):
    """Raised when the keyword that is created by user is already taken."""
    pass


class Overflow(Exception):
    """Raised when the given expression output was too big."""
    pass


class UnclosedBrackets(Exception):
    """Raised when the given expression has unclosed brackets."""
    pass


class EmptyBrackets(Exception):
    """Raised when the given expression has empty or unused brackets."""
    pass
