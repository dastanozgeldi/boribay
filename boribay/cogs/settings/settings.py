import discord
from boribay.core import Boribay, Cog, Context
from boribay.utils import ColorConverter, SettingsConverter, is_mod
from discord.ext import commands


class Settings(Cog):
    """The settings extension.

    Created to make users able to manage the guild configuration.
    """

    def __init__(self, bot: Boribay):
        self.icon = '⚙'
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

    @staticmethod
    def on_or_off(ctx: Context, key: str) -> str:
        """A function to check whether the setting is set or not.

        Args:
            ctx (Context): To get the bot instance.
            key (str): A key from cache to check.

        Returns:
            str: Either crossmark or a tick.
        """
        checks = ('.', None, 0x36393f, None, None, None)
        # Someone help how to not hardcode this ;-;

        for check in checks:
            if ctx.guild_cache[ctx.guild.id][key] == check:
                return '<:crossmark:814742130190712842>'

        return '<:tick:814838692459446293>'

    @commands.command(aliases=('gs', 'settings'))
    async def guildsettings(self, ctx: Context):
        """The settings command. Shows the settings of the current server.

        FAQ
        ---
        1. What does "None" mean?
            This means this category is not set yet.

        2. What is written on "Embed Color" category?
            This is the hex value of a color.

        3. What do tick and crossmark mean?
            Tick represents whether the category is set.
        """
        g = ctx.guild
        sc = SettingsConverter()

        creds = await sc.convert(g, ctx.guild_cache)
        embed = ctx.embed(
            description='\n'.join(f'**{self.on_or_off(ctx, k)} {k.replace("_", " ").title()}:** {v}' for k, v in creds.items())
        ).set_author(name=f'Settings of {g}', icon_url=g.icon_url)

        await ctx.send(embed=embed)

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
        await self.update(ctx, 'welcome_channel', None, '✅ Disabled welcome-channel.')

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx: Context):
        """The prefix setting parent command.

        Simply shows the current prefix if nothing was specified.

        The default prefix is '.'
        """

        b = self.bot
        g = ctx.guild
        prefix = '.' if not g else b.guild_cache[g.id].get('prefix', '.')
        await self.shower(ctx, value=prefix, message='The prefix is: `{}` or %s' % b.user.mention)

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
        color = ctx.guild_cache[ctx.guild.id].get('color', 3553599)
        await self.shower(ctx, value=hex(color), message='The custom color is: {}')

    @embedcolor.command(name='set')
    async def _set_color(self, ctx: Context, color: ColorConverter):
        """Set the custom color to your server.

        Example:
            **{p}color set 0xff0000** - sets this color (red in hex).

        Args:
            color (ColorConverter): The color you would like to set.
            It can be hex, a word (e.g blurple) or an integer.
        """
        color = int(str(color).replace('#', ''), 16)  # The hex value of a color.
        await self.update(ctx, 'embed_color', color,
                          '✅ As of now, the embed color will look like this.')

    @embedcolor.command(name='default', aliases=['disable'])
    async def _default_color(self, ctx: Context):
        """Return back the default color for your guild!"""
        await self.update(ctx, 'embed_color', 3553599, '✅ Embed color has been set to the default one.')

    # Autorole Settings Part
    @commands.group(invoke_without_command=True)
    async def autorole(self, ctx: Context):
        """The autorole setting parent command."""
        await self.shower(ctx, attr='get_role', key='autorole', message='The custom role is: {}')

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

    @commands.group(invoke_without_command=True)
    async def logging(self, ctx: Context):
        """The log-channel setting parent command."""
        await self.shower(
            ctx, attr='get_channel', key='logging_channel', message='The logging channel is: {}'
        )

    @logging.command(name='set')
    async def _set_logging(self, ctx: Context, channel: discord.TextChannel):
        """Set the logging channel to your server!
        Args: channel (discord.TextChannel): A channel you would like set."""
        await self.update(
            ctx, 'logging_channel', channel.id, f'✅ Set `{channel}` as a logging channel.'
        )

    @logging.command(name='disable')
    async def _disable_logging(self, ctx: Context):
        """Disable the logging feature for your guild."""
        await self.update(ctx, 'logging_channel', None, '✅ Disabled logging.')
