import asyncio

import discord
from boribay.core import Boribay, Context
from boribay.utils import (Cog, ColorConverter, SettingsConverter,
                           ValueConverter, is_mod)
from discord.ext import commands


class Settings(Cog):
    """The commands extension to work with guild config."""
    icon = '⚙'
    name = 'Settings'

    def __init__(self, bot: Boribay):
        self.bot = bot

    def on_or_off(self, ctx: Context, key: str) -> str:
        """A function to check whether the setting is set or not.

        Args:
            ctx (Context): To get the bot instance.
            key (str): A key from cache to check.

        Returns:
            str: Either crossmark or a tick.
        """
        checks = ('.', None, 0x36393f, None, None, None)

        for check in checks:
            if self.bot.guild_cache[ctx.guild.id][key] == check:
                return '<:crossmark:814742130190712842>'

        return '<:tick:814838692459446293>'

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

        embed = self.bot.embed.default(ctx, description=message)
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

        embed = b.embed.default(ctx, description=message.format(value))
        return await ctx.send(embed=embed)

    @commands.command(name='setup', aliases=['setupwizard'])
    @is_mod()
    async def _run_setup_wizard(self, ctx: Context):
        """The interactive setup wizard to set guild-settings.

        This walks you through the process of setting the configuration of
        your guild. Work similar to all other commands.

        Raises:
            commands.BadArgument: On wrong given setting/subcommand.
        """
        cmds = ctx.cog.get_commands()
        available = '\n'.join(str(x) for x in cmds if isinstance(x, commands.Group))
        await ctx.reply(f'What setting you would like to setup? The available ones are:\n{available}')

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        timeout = 20.0
        try:
            setting = await self.bot.wait_for('message', timeout=timeout, check=check)

        except asyncio.TimeoutError:
            return await ctx.send('You took long.')

        import itertools  # If you feel lazy to import from the top, this is for you.

        flat = itertools.chain.from_iterable([cmd.aliases for cmd in cmds])
        cmds = [str(cmd) for cmd in cmds] + list(flat)

        if (setting := setting.content) not in cmds:
            raise commands.BadArgument('There is no setting like this.')

        await ctx.send(f'Neat. So the setting is {setting}. What about its mode? **(set/disable)**\n'
                       f'You can type **abort** to abort the setup process.')

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=timeout)

        except asyncio.TimeoutError:
            return await ctx.send('You took long.')

        if (mode := msg.content) == f'{ctx.prefix}abort':
            return await ctx.send('✅ Aborting...')

        if mode == 'disable':
            return await self.bot.get_command(f'{setting} {mode}')(ctx)

        elif mode not in ('set', 'disable'):
            raise commands.BadArgument('Invalid subcommand given. Choose from set | disable.')

        await ctx.send('The last step left. Specify the argument you want to set.\n'
                       'This is either **channel/role/color** or a **prefix**. Depends on the context.')

        try:
            argument = (await self.bot.wait_for('message', check=check, timeout=timeout)).content

        except asyncio.TimeoutError:
            return await ctx.send('You took long.')

        # Finishing.
        value = await ValueConverter().convert(ctx, str(self.bot.get_command(setting)), argument)
        await self.bot.get_command(f'{setting} {mode}')(ctx, value)

    @commands.group(invoke_without_command=True, aliases=['gs'])
    async def settings(self, ctx: Context):
        """The settings command. Shows the settings of the current server.

        What does "None" mean? → This means this category is not set yet.

        What is written on "Embed Color" category? → This is the hex value of a color.

        What do tick and crossmark mean? → Tick represents whether the category is set."""
        g = ctx.guild

        creds = await SettingsConverter().convert(g, self.bot.guild_cache)

        embed = self.bot.embed.default(
            ctx, description='\n'.join(f'**{self.on_or_off(ctx, k)} {k.replace("_", " ").title()}:** {v}' for k, v in creds.items())
        ).set_author(name=f'Settings of {g}', icon_url=g.icon_url)

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=['wc'])
    @is_mod()
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
    @is_mod()
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
    @is_mod()
    async def _default_prefix(self, ctx: Context):
        """Return back the default bot prefix!"""
        await self.update(ctx, 'prefix', '.',
                          '✅ Prefix has been set to the default one.')

    @commands.group(invoke_without_command=True, aliases=['embedcolour', 'ec'])
    @is_mod()
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
    @is_mod()
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
    @is_mod()
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
    @is_mod()
    async def logging(self, ctx: Context):
        """The log-channel setting parent command."""
        await self.shower(ctx, attr='get_channel', key='audit_logger',
                          message='The logging channel is: {}')

    @logging.command(name='set')
    async def _set_logging(self, ctx: Context, channel: discord.TextChannel):
        """Set the logging channel to your server!
        Args: channel (discord.TextChannel): A channel you would like set."""
        await self.update(ctx, 'audit_logger', channel.id,
                          f'✅ Set `{channel}` as a logging channel.')

    @logging.command(name='disable')
    async def _disable_logging(self, ctx: Context):
        """Disable the logging feature for your guild."""
        await self.update(ctx, 'audit_logger', None, '✅ Disabled logging.')


def setup(bot: Boribay):
    bot.add_cog(Settings(bot))
