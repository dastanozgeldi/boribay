import discord
from boribay.core import Boribay, Cog, Context
from boribay.utils import ColorConverter, is_mod
from discord.ext import commands


class Settings(Cog):
    """The commands extension to work with guild config."""
    icon = '⚙'

    def __init__(self, bot: Boribay):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        return await is_mod().predicate(ctx)

    async def update(self, ctx: Context, key: str, value: str, message: str) -> discord.Message:
        """A function to simply update changed values in the DB + cache.

        Args:
            ctx (Context): To get the bot, guild instances.
            key (str): A key going to be updated.
            value (str): The new value to replace the previous.
            message (str): Message of success.

        Returns:
            discord.Message: A message of the successfully-updated config.
        """
        me = self.bot
        guild = ctx.guild.id
        query = f'UPDATE guild_config SET {key} = $1 WHERE guild_id = $2'

        await me.pool.execute(query, value, guild)
        me.guild_cache[guild][key] = value

        embed = ctx.embed(description=message)
        return await ctx.send(embed=embed)

    async def shower(self, ctx: Context, *, value: str = None, attr: str = None, **kwargs) -> discord.Message:
        """A function to quickly show the current configuration for a given attribute.

        Args:
            ctx (Context): To get the bot, guild instances.
            value (str, optional): The default value to show. Defaults to None.
            attr (str, optional): Guild attribute to get. Defaults to None.

        Returns:
            discord.Message: The success message.
        """
        b = self.bot
        g = ctx.guild

        message = kwargs.pop('message')
        value = value or getattr(g, attr)(b.guild_cache[g.id].get(kwargs.pop('key')))

        embed = b.embed(ctx, description=message.format(value))
        return await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=['wc'])
    async def welcomechannel(self, ctx: Context):
        """The welcome channel setting parent command."""
        await self.shower(ctx, key='welcome_channel', attr='get_channel',
                          message='The welcoming channel is: {}')

    @welcomechannel.command(name='set')
    async def _set_welcome_channel(self, ctx: Context, channel: discord.TextChannel):
        """Set the welcome channel to your server.

        Example:
            **{p}welcomechannel set #welcomes** - sets channel 'welcomes'

        Args:
            channel (discord.TextChannel): A channel you would like to set.
        """
        await self.update(ctx, 'welcome_channel', channel.id,
                          f'✅ Set {channel} as a welcoming channel.')

    @welcomechannel.command(name='disable')
    async def _disable_welcome_channel(self, ctx: Context):
        """Disable the welcoming channel feature!"""
        await self.update(ctx, 'welcome_channel', None,
                          '✅ Disabled welcome-channel.')

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx: Context):
        """The prefix setting parent command. Simply shows the current prefix
        if nothing was specified. The default prefix is '.'"""
        b = self.bot
        g = ctx.guild
        prefix = '.' if not g else b.guild_cache[g.id].get('prefix', '.')
        await self.shower(ctx, value=prefix,
                          message='The prefix is: `{}` or %s' % b.user.mention)

    @prefix.command(name='set')
    async def _set_prefix(self, ctx: Context, new: str):
        """Set the custom prefix to your server.

        Example:
            **{p}prefix set b!** - sets "b!" as the main prefix.

        Args:
            new (str): A new prefix that you want to set.
        """
        await self.update(ctx, 'prefix', new,
                          f'✅ Prefix has been changed to: `{new}`')

    @prefix.command(name='default', aliases=['disable'])
    async def _default_prefix(self, ctx: Context):
        """Return back the default bot prefix!"""
        await self.update(ctx, 'prefix', '.',
                          '✅ Prefix has been set to the default one.')

    @commands.group(invoke_without_command=True, aliases=['embedcolour', 'ec'])
    async def embedcolor(self, ctx: Context):
        """The color setting parent command."""
        color = self.bot.guild_cache[ctx.guild.id].get('color', 3553599)
        await self.shower(ctx, value=hex(color), message='The custom color is: {}')

    @embedcolor.command(name='set')
    async def _set_color(self, ctx: Context, color: ColorConverter):
        """Sets the custom color for the bot.
        Then all embeds' color will be one that you specified."""
        color = int(str(color).replace('#', ''), 16)  # The hex value of a color.
        await self.update(ctx, 'embed_color', color,
                          '✅ As of now, the embed color will look like this.')

    @embedcolor.command(name='default', aliases=['disable'])
    async def _default_color(self, ctx: Context):
        """Return back the default color for your guild!"""
        await self.update(ctx, 'embed_color', 3553599,
                          '✅ Embed color has been set to the default one.')

    # Autorole Settings Part
    @commands.group(invoke_without_command=True)
    async def autorole(self, ctx: Context):
        """The autorole setting parent command."""
        await self.shower(ctx, attr='get_role', key='autorole',
                          message='The custom role is: {}')

    @autorole.command(name='set')
    async def _set_autorole(self, ctx: Context, role: discord.Role):
        """Set the autorole feature in your server.

        Example:
            **{p}autorole set @Members** - sets @Members role.

        Args:
            role (discord.Role): A role you would like to set.
        """
        await self.update(ctx, 'autorole', role.id,
                          f'✅ Set {role.mention} as an autorole.')

    @autorole.command(name='disable')
    async def _disable_autorole(self, ctx: Context):
        """Disable the autorole feature for your guild."""
        await self.update(ctx, 'autorole', None, '✅ Disabled autorole.')

    # Automeme Settings Part
    @commands.group(invoke_without_command=True)
    async def automeme(self, ctx: Context):
        """The automeme setting parent command."""
        await self.shower(ctx, attr='get_channel', key='automeme',
                          message='The automemes channel is: {}')

    @automeme.command(name='set')
    async def _set_automeme(self, ctx: Context, channel: discord.TextChannel):
        """Set the automeme channel to your server!
        Args: channel (discord.TextChannel): A channel you would like set."""
        await self.update(ctx, 'automeme', channel.id,
                          f'✅ Set `{channel}` as a channel to send memes.')

    @automeme.command(name='disable')
    async def _disable_automeme(self, ctx: Context):
        """Disable the automeme feature for your guild."""
        await self.update(ctx, 'automeme', None, '✅ Disabled automeme.')

    @commands.group(invoke_without_command=True)
    async def logging(self, ctx: Context):
        """The log-channel setting parent command."""
        await self.shower(ctx, attr='get_channel', key='logging_channel',
                          message='The logging channel is: {}')

    @logging.command(name='set')
    async def _set_logging(self, ctx: Context, channel: discord.TextChannel):
        """Set the logging channel to your server!
        Args: channel (discord.TextChannel): A channel you would like set."""
        await self.update(ctx, 'logging_channel', channel.id,
                          f'✅ Set `{channel}` as a logging channel.')

    @logging.command(name='disable')
    async def _disable_logging(self, ctx: Context):
        """Disable the logging feature for your guild."""
        await self.update(ctx, 'logging_channel', None, '✅ Disabled logging.')


def setup(bot: Boribay):
    bot.add_cog(Settings(bot))
