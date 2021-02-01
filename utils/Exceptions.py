from discord.ext import commands


class NoReactionsPassed(commands.CommandInvokeError):
    """Specific exception for the trivia command."""
    pass


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


class AlreadyConnectedToChannel(commands.CommandError):
    """Raised when the bot is already connected to the channel."""
    pass


class NoVoiceChannel(commands.CommandError):
    """No mentioned voice channels found."""
    pass


class QueueIsEmpty(commands.CommandError):
    """Raised when someone called for either 'skip' or 'previous'
    or even for 'queue' command, but the current queue was empty."""
    pass


class NoTracksFound(commands.CommandError):
    """Raised when the search engine did not find the suitable results
    for the query."""
    pass


class PlayerIsAlreadyPaused(commands.CommandError):
    """Raised when someone called for a 'pause' command, but the player
    was already paused."""
    pass


class NoMoreTracks(commands.CommandError):
    """Raised on the skip command, means that there are no more tracks in queue."""
    pass


class NoPreviousTracks(commands.CommandError):
    """Raised on the previous command, means that there are no more tracks in queue."""
    pass


class TooManyOptions(commands.CommandError):
    """Raised when there were too many options on a poll."""
    pass


class NotEnoughOptions(commands.CommandError):
    """Raised when either there was only 1 options or no options."""
    pass
