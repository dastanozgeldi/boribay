from typing import Dict, Tuple

from nextcord.ext import commands

__all__ = (
    'Cog',
    'Group',
    'Command',
    'group',
    'command'
)


class Command(commands.Command):
    """The customized command instance for Boribay.

    This class inherits from `nextcord.ext.commands.Command`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.translator = kwargs.pop('i18n', None)

        if len(self.qualified_name) > 50:
            raise RuntimeError(
                f'"{self.qualified_name}" cannot be set as a command name, the name '
                'length is too big. That may cause issues with some other utilities.'
            )

    @property
    def oneline_help(self):
        return self.help.split('\n')[0]


class Cog(commands.Cog, metaclass=commands.CogMeta):
    """The customized cog instance for Boribay.

    All cogs of this bot will be of this type.

    This class inherits from `nextcord.ext.commands.Cog`.
    """

    __cog_commands__: Tuple[Command]

    def __str__(self):
        if hasattr(self, 'icon'):
            return f'{self.icon} {self.qualified_name}'

        return self.qualified_name

    @property
    def all_commands(self) -> Dict[str, Command]:
        return {cmd.name: cmd for cmd in self.__cog_commands__}


class GroupMixin(commands.GroupMixin):
    """Mixin class for the class `Group`.

    This class inherits from `commands.GroupMixin`.
    """

    def command(self, *args, **kwargs):
        def deco(func):
            kwargs.setdefault('parent', self)
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return deco

    def group(self, *args, **kwargs):
        def deco(func):
            kwargs.setdefault('parent', self)
            result = group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return deco


class Group(GroupMixin, commands.Group):
    """Boribay's custom Group command class.

    This class inherits from `commands.Command` and `commands.Group`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoke_without_command = True


def command(name=None, cls=Command, **attrs):
    return commands.command(name, cls, **attrs)


def group(name=None, cls=Group, **attrs):
    return commands.command(name, cls, **attrs)
