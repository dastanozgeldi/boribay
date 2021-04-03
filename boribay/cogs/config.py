from typing import Union

import discord
from discord.ext import commands
from boribay.utils import Cog, ColorConverter, SettingsConverter, is_mod


class Configuration(Cog):
    """The settings extension to work with guild config."""
    icon = '⚙'
    name = 'Configuration'

    def on_or_off(self, ctx, key):
        checks = ['.', None, 0x36393f, None, None, None]

        for check in checks:
            if ctx.bot.guild_cache[ctx.guild.id][key] == check:
                return '<:crossmark:814742130190712842>'

        return '<:tick:814838692459446293>'

    async def update(self, ctx, key, value):
        me = ctx.bot
        guild = ctx.guild.id
        query = f'UPDATE guild_config SET {key} = $1 WHERE guild_id = $2'

        await me.pool.execute(query, value, guild)
        me.guild_cache[guild][key] = value

    @commands.group(invoke_without_command=True, aliases=['gs'])
    async def settings(self, ctx):
        """The settings parent command.
        Shows the settings of the current server."""
        g = ctx.guild

        creds = await SettingsConverter().convert(g, ctx.bot.guild_cache)
        embed = ctx.bot.embed.default(
            ctx, description='\n'.join(f'**{self.on_or_off(ctx, k)} {k.replace("_", " ").title()}:** {v}' for k, v in creds.items())
        ).set_author(name=f'Settings of {g}', icon_url=g.icon_url)

        await ctx.send(embed=embed)

    @settings.command(name='help')
    async def settings_help(self, ctx):
        """Some kind of help information for users."""
        fields = [
            ('What does "None" mean?', 'This means this category is not set yet.'),
            ('What is written on "Embed Color" category?', 'This is the hex value of a color.\n'
                                                           'Check it with `{p}color` to be sure!'),
            ('What do tick and crossmark mean?', 'Tick represents whether the category is set,\n'
                                                 'Crossmark is shown when the set value is either default or None.')
        ]
        embed = ctx.bot.embed.default(ctx, title='Welcome to Settings!')

        for name, value in fields:
            embed.add_field(name=name, value=value.format(p=ctx.prefix), inline=False)

        await ctx.send(embed=embed)

    @settings.command(aliases=['wc'])
    @is_mod()
    async def welcomechannel(self, ctx, channel: Union[discord.TextChannel, str.lower]):
        """Set the welcome channel command.
        To disable this feature just put `disable` after the command."""
        if isinstance(channel, str) and channel == 'disable':
            await self.update(ctx, 'welcome_channel', None)
            return await ctx.send('✅ Disabled welcome-channel.')

        await self.update(ctx, 'welcome_channel', channel.id)
        await ctx.send(f'✅ Set {channel} as a welcoming channel.')

    @settings.command()
    @is_mod()
    async def prefix(self, ctx, new: str):
        """Set Prefix command.
        Args: prefix (str): a new prefix that you want to set."""
        await self.update(ctx, 'prefix', new)
        await ctx.send(f'Prefix has been changed to: `{new}`')

    @settings.command(aliases=['colour'])
    @is_mod()
    async def color(self, ctx, color: ColorConverter):
        """Sets the custom color for the bot. Then all embeds color will be one
        that you specified. To bring the default color back,
        use `settings color #36393e`"""
        color = int(str(color).replace('#', ''), 16)
        await self.update(ctx, 'embed_color', color)

        embed = ctx.bot.embed.default(ctx, title='As of now, the embed color will look like this.')
        await ctx.send(embed=embed)

    @settings.command()
    @is_mod()
    async def autorole(self, ctx, role: Union[discord.Role, str.lower]):
        """Sets the autorole for the current server.
        To disable this feature just put `disable` after the command."""
        if isinstance(role, str) and role == 'disable':
            await self.update(ctx, 'autorole', None)
            return await ctx.send('✅ Disabled autorole.')

        await self.update(ctx, 'autorole', role.id)
        await ctx.send(f'✅ Set `{role}` as an autorole.')

    @settings.command()
    @is_mod()
    async def automeme(self, ctx, channel: Union[discord.TextChannel, str.lower]):
        """Sets the automeme stuff for the current server."""
        if isinstance(channel, str) and channel == 'disable':
            await self.update(ctx, 'automeme', None)
            return await ctx.send('✅ Disabled automemes.')

        await self.update(ctx, 'automeme', channel.id)
        await ctx.send(f'✅ Set {channel} as automemes channel.')

    @settings.command()
    @is_mod()
    async def logging(self, ctx, channel: discord.TextChannel):
        """Sets the logging channel for the current server."""
        if isinstance(channel, str) and channel == 'disable':
            await self.update(ctx, 'logging_channel', None)
            return await ctx.send('✅ Disabled logging.')

        await self.update(ctx, 'logging_channel', channel.id)
        await ctx.send(f'✅ Set {channel} as the logging channel.')


def setup(bot):
    bot.add_cog(Configuration())
