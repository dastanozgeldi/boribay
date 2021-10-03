from collections import Counter
from glob import glob
from typing import Optional

import boribay
from boribay.core import utils
from nextcord.ext import commands
from humanize import naturaldate, naturaltime

LOADING = '<a:loading:837049644462374935>'
POSTGRES = '<:pg:795005204289421363>'


class Miscellaneous(utils.Cog):
    """The miscellaneous extension.

    Commands that do not match other categories will be inserted here.
    """

    icon = '💫'

    @utils.command(aliases=('suggestion',))
    async def suggest(self, ctx: utils.Context, *, content: str) -> None:
        """Suggest an idea to the bot owner.

        Example:
            **{p}suggest More casino commands in economics e.g blackjack.**

        Args:
            content (str): Accordingly, the content of your suggestion.
        """
        query = 'INSERT INTO ideas(content, author_id) VALUES($1, $2);'

        await ctx.bot.pool.execute(query, content, ctx.author.id)
        await ctx.send('✅ Added your suggestion, you will be notified when it will be approved/rejected.')

    @utils.command(aliases=('codestats', 'cs'))
    async def codestatistics(self, ctx: utils.Context) -> None:
        """See the code statistics of the bot."""
        ctr = Counter()

        for ctr['files'], f in enumerate(glob('./**/*.py', recursive=True)):
            with open(f, encoding='UTF-8') as fp:
                for ctr['lines'], line in enumerate(fp, ctr['lines']):
                    line = line.lstrip()
                    ctr['classes'] += line.startswith('class')
                    ctr['comments'] += '#' in line
                    ctr['functions'] += line.startswith('def')
                    ctr['coroutines'] += line.startswith('async def')
                    ctr['docstrings'] += line.startswith('"""')

        embed = ctx.embed(description='\n'.join(f'**{k.capitalize()}:** {v}' for k, v in ctr.items()))
        await ctx.send(embed=embed)

    @utils.command()
    async def uptime(self, ctx: utils.Context) -> None:
        """Returns uptime: How long the bot is online."""
        h, r = divmod((ctx.bot.uptime), 3600)
        (m, s), (d, h) = divmod(r, 60), divmod(h, 24)

        embed = ctx.embed()
        embed.add_field(name='How long I am online?', value=f'{d}d {h}h {m}m {s}s')

        await ctx.send(embed=embed)

    @utils.command(aliases=('about',))
    async def info(self, ctx: utils.Context) -> None:
        """See some kind of information about Boribay (such as command usage)."""
        bot = ctx.bot
        embed = ctx.embed().set_author(
            name=f'{bot.user} - v{boribay.__version__}',
            icon_url=bot.user.avatar_url
        )
        fields = {
            'Development': {
                ('Developer', str(bot.owner)),
                ('Language', 'Python'),
                ('Library', 'nextcord.py')
            },
            'General': {
                ('Currently in', f'{len(bot.guilds)} servers'),
                ('Commands working', f'{len(bot.commands)}'),
                ('Commands usage (last restart)', bot.counter['command_usage'])
            }
        }
        for key in fields:
            embed.add_field(
                name=key,
                value='\n'.join(f'> **{k}:** {v}' for k, v in fields[key]),
                inline=False
            )

        await ctx.send(embed=embed)

    @utils.command(aliases=('memberinfo', 'ui', 'mi'))
    @commands.guild_only()
    async def userinfo(
        self,
        ctx,
        member: Optional[commands.MemberConverter]
    ) -> None:
        """See some general information about the mentioned user.

        Example:
            **{p}userinfo @Dosek**

        Args:
            member (Optional[commands.MemberConverter]): A user to get info about.
        """
        member = member or ctx.author
        fields = [
            ('Top role', member.top_role.mention),
            ('Boosted server', bool(member.premium_since)),
            ('Account created', naturaldate(member.created_at)),
            ('Here since', naturaldate(member.joined_at))
        ]

        embed = ctx.embed(
            description='\n'.join(f'**{name}:** {value}' for name, value in fields)
        ).set_thumbnail(url=member.avatar_url)
        embed.set_author(name=str(member), icon_url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

    @utils.command(aliases=('guildinfo', 'si', 'gi'))
    @commands.guild_only()
    async def serverinfo(self, ctx: utils.Context) -> None:
        """See some general information about current guild."""
        g = ctx.guild

        fields = [
            ('Region', str(g.region).title()),
            ('Created', naturaltime(g.created_at)),
            ('Members', g.member_count),
            ('Boosts', g.premium_subscription_count),
            ('Roles', len(g.roles)),
            ('Text channels', len(g.text_channels)),
            ('Voice channels', len(g.voice_channels)),
            ('Categories', len(g.categories)),
        ]

        embed = ctx.embed(
            description='\n'.join(f'**{n}:** {v}' for n, v in fields)
        ).set_author(name=str(g), icon_url=g.icon_url)

        await ctx.send(embed=embed)

    @utils.command()
    async def say(self, ctx: utils.Context, message: str, tts: bool = False) -> None:
        """Make the bot say what you want.

        Parameters
        ----------
        message : str
            A message that is going to be sent, make sure to put in "double quotes".
        tts : bool, optional
            Whether to enable TTS, by default False
        """
        await ctx.try_delete(ctx.message)
        await ctx.send(message, tts=tts)

    @utils.command()
    async def links(self, ctx: utils.Context):
        """Some useful invites (support server, bot invite and voting URL)."""
        links = ctx.config.links
        embed = ctx.embed(description=f'Invite me [here]({links.invite})\n'
                          f'Support server [here]({links.support})'
                          f'Vote on TopGG [here]({links.top_gg})')

        await ctx.send(embed=embed)

    @utils.command()
    async def ping(self, ctx: utils.Context) -> None:
        """Check latency of the bot and its system."""
        fields = (
            (f'{LOADING} Websocket', ctx.bot.latency),
            (f'{POSTGRES} Database', await ctx.db_latency)
        )

        embed = ctx.embed()
        for name, value in fields:
            embed.add_field(
                name=name,
                value=f'```{value * 1000:.2f} ms```',
                inline=False
            )
        await ctx.send(embed=embed)

    @utils.command(aliases=('exts', 'extensions'))
    async def cogs(self, ctx: utils.Context) -> None:
        """Get the list of modules that are available to use."""
        exts = [str(ext) for ext in ctx.bot.cogs.values()]
        embed = ctx.embed(
            title='Currently working modules.',
            description=f'Currently loaded: {len(ctx.bot.cogs)}\n'
            f'Available to you: {1}\n'
            '\n'.join(exts)
        )
        await ctx.send(embed=embed)

    @utils.command(aliases=('mrs',))
    async def messagereactionstats(self, ctx: utils.Context, *, link: str) -> None:
        """See what reactions are there in a message, i.e reaction statistics.

        Example:
            **{p}mrs https://nextcord.com/channels/12345/54321/32451**

        Args:
            link (str): An URL of a message.
        """
        ids = [int(i) for i in link.split('/')[5:]]
        msg = await ctx.guild.get_channel(ids[0]).fetch_message(ids[1])

        await ctx.send({f'{i}': i.count for i in msg.reactions})
