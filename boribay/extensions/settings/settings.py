import discord
from boribay.core import utils


class Settings(utils.Cog):
    """The settings extension.

    type `[p]guildsettings` to see current guild settings.
    """

    def __init__(self):
        self.icon = '⚙'
        self.default_settings = {
            'prefix': '.',
            'welcome_channel': None,
            'embed_color': 3553598,
            'autorole': None
        }

    async def cog_check(self, ctx) -> bool:
        """
        Making sure that only Mods are trying to run those commands.
        """
        return await utils.is_mod().predicate(ctx)

    async def _update(self, ctx: utils.Context, key: str, value: str) -> None:
        """A function to simply update changed values in the DB + cache.

        Args:
            ctx (utils.Context): To get the bot, guild instances.
            key (str): A key going to be updated.
            value (str): The new value to replace the previous.
        """
        # Initializing variables.
        guild = ctx.guild.id
        query = f'UPDATE guild_config SET {key} = $1 WHERE guild_id = $2'

        # Doing the stuff.
        await ctx.bot.pool.execute(query, value, guild)
        ctx.bot.guild_cache[guild][key] = value

    async def _disable(self, ctx: utils.Context, key: str) -> None:
        # Here by passing `None` we kind of disable the feature.
        await self._update(ctx, key, None)

    def on_or_off(self, ctx: utils.Context, key: str) -> str:
        """A function to check whether the setting is set or not.

        Args:
            ctx (utils.Context): To get the bot instance.
            key (str): A key from cache to check.

        Returns:
            str: Either crossmark or a tick.
        """
        for check in self.default_settings.values():
            if ctx.guild_cache[ctx.guild.id][key] == check:
                return '<:crossmark:814742130190712842>'

        return '<:tick:814838692459446293>'

    @utils.command(aliases=('gs', 'settings'))
    async def guildsettings(self, ctx: utils.Context):
        """The settings command. Shows the settings of the current server.

        FAQ
        ---
        What does "None" mean?
            This means this category is not set yet.

        What is written on "Embed Color" category?
            This is the hex value of a color.

        What do tick and crossmark mean?
            Tick represents whether the category is set.
        """
        g = ctx.guild
        sc = utils.SettingsConverter()

        creds = await sc.convert(g, ctx.guild_cache)
        embed = ctx.embed(
            description='\n'.join(
                f'**{self.on_or_off(ctx, k)} {k.replace("_", " ").title()}:** {v}'
                for k, v in creds.items()
            )
        ).set_author(name=f'Settings for {g}', icon_url=g.icon_url)

        await ctx.send(embed=embed)

    @utils.group(aliases=('wc',))
    async def welcomechannel(self, ctx: utils.Context) -> None:
        """
        The welcome channel setting parent command.
        """
        await ctx.send_help('welcomechannel')

    @welcomechannel.command(name='set')
    async def _set_welcome_channel(
        self, ctx: utils.Context, channel: discord.TextChannel
    ) -> None:
        """Set the welcome channel to your server.

        Example:
            **{p}welcomechannel set #welcomes** - sets channel 'welcomes'

        Args:
            channel (discord.TextChannel): A channel you would like to set.
        """
        await self._update(ctx, 'welcome_channel', channel.id)
        await ctx.send(f'✅ Set {channel} as a welcoming channel.')

    @welcomechannel.command(name='disable')
    async def _disable_welcome_channel(self, ctx: utils.Context) -> None:
        """
        Disable the welcoming channel with this command.
        """
        await self._disable(ctx, 'welcome_channel')
        await ctx.send('✅ Disabled the welcoming channel.')

    @utils.group()
    async def prefix(self, ctx: utils.Context):
        """The prefix setting parent command.

        Simply shows the current prefix if nothing was specified.

        The default prefix is '.'
        """
        await ctx.send_help('prefix')

    @prefix.command(name='set')
    async def _set_prefix(self, ctx: utils.Context, new_prefix: str) -> None:
        """Set the custom prefix to your server.

        Example:
            **{p}prefix set b!** - sets "b!" as the main prefix.

        Args:
            new_prefix (str): A new prefix that you want to set.
        """
        await self._update(ctx, 'prefix', new_prefix)
        await ctx.send(f'✅ Prefix has been changed to: `{new_prefix}`')

    @prefix.command(name='default', aliases=('disable',))
    async def _default_prefix(self, ctx: utils.Context) -> None:
        """
        Bring back the default bot prefix with this command.
        """
        await self._update(ctx, 'prefix', '.')
        await ctx.send('✅ Prefix has been set to the default one.')

    @utils.group(aliases=('embedcolour', 'ec'))
    async def embedcolor(self, ctx: utils.Context) -> None:
        """
        The color setting parent command.
        """
        await ctx.send_help('embedcolor')

    @embedcolor.command(name='set')
    async def _set_color(
        self, ctx: utils.Context, color: utils.ColorConverter
    ) -> None:
        """Set the custom color to your server.

        Example:
            **{p}color set 0xff0000** - sets this color (red in hex).

        Args:
            color (ColorConverter): The color you would like to set.
            It can be hex, a word (e.g blurple) or an integer.
        """
        color = int(str(color).replace('#', ''), 16)  # The hex value of a color.
        await self._update(ctx, 'embed_color', color)

        # Making an embed since the user has to see color changes.
        embed = ctx.embed(description='✅ As of now, the embed color will look like this.')
        await ctx.send(embed=embed)

    @embedcolor.command(name='default', aliases=('disable',))
    async def _default_color(self, ctx: utils.Context) -> None:
        """
        Bring back the default color for your guild with this command.
        """
        await self._update(ctx, 'embed_color', 3553599)

        # Making an embed since the user has to see color changes.
        embed = ctx.embed(description='✅ Embed color has been set to the default one.')
        await ctx.send(embed=embed)

    # Autorole Settings Part
    @utils.group()
    async def autorole(self, ctx: utils.Context):
        """
        The autorole setting parent command.
        """
        await ctx.send_help('autorole')

    @autorole.command(name='set')
    async def _set_autorole(self, ctx: utils.Context, role: discord.Role) -> None:
        """Set the autorole feature in your server.

        Example:
            **{p}autorole set @Members** - sets @Members role.

        Args:
            role (discord.Role): A role you would like to set.
        """
        await self._update(ctx, 'autorole', role.id)
        await ctx.send(f'✅ Set {role.mention} as an autorole.')

    @autorole.command(name='disable')
    async def _disable_autorole(self, ctx: utils.Context) -> None:
        """
        Disable the autorole feature for your guild.
        """
        await self._disable(ctx, 'autorole')
        await ctx.send('✅ Disabled autorole.')
