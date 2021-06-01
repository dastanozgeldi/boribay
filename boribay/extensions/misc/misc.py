from collections import Counter
from glob import glob
from time import perf_counter
from typing import Optional

from boribay import __version__
from boribay.core import LOADING, PG, TYPING, Boribay, Cog, Context
from discord.ext import commands, flags
from humanize import naturaldate, naturaltime


class Miscellaneous(Cog):
    """The miscellaneous extension.

    Commands that do not match other categories will be inserted here.
    """

    def __init__(self, bot: Boribay):
        self.icon = '💫'
        self.bot = bot

    @commands.command(aliases=['suggestion'])
    async def suggest(self, ctx: Context, *, content: str):
        """Suggest an idea to the bot owner.

        Example:
            **{p}suggest More casino commands in economics e.g blackjack.**

        Args:
            content (str): Accordingly, the content of your suggestion.
        """
        query = 'INSERT INTO ideas(content, author_id) VALUES($1, $2);'

        await self.bot.pool.execute(query, content, ctx.author.id)
        await ctx.send('✅ Added your suggestion, you will be notified when it will be approved/rejected.')

    @commands.command(aliases=['codestats', 'cs'])
    async def codestatistics(self, ctx: Context):
        """See the code statistics of the bot."""
        ctr = Counter()

        for ctr['files'], f in enumerate(glob('./**/*.py', recursive=True)):
            with open(f, encoding='UTF-8') as fp:
                for ctr['lines'], line in enumerate(fp, ctr['lines']):
                    line = line.lstrip()
                    ctr['imports'] += line.startswith('import') + line.startswith('from')
                    ctr['classes'] += line.startswith('class')
                    ctr['comments'] += '#' in line
                    ctr['functions'] += line.startswith('def')
                    ctr['coroutines'] += line.startswith('async def')
                    ctr['docstrings'] += line.startswith('"""') + line.startswith("'''")

        embed = ctx.embed(description='\n'.join(f'**{k.capitalize()}:** {v}' for k, v in ctr.items()))
        await ctx.send(embed=embed)

    @commands.command(aliases=['modules'])
    async def extensions(self, ctx: Context):
        """Get the list of modules that are currently loaded."""
        exts = [str(ext) for ext in self.bot.cogs.values()]
        exts = [exts[i: i + 3] for i in range(0, len(exts), 3)]
        length = [len(element) for row in exts for element in row]
        rows = [''.join(e.ljust(max(length) + 2) for e in row) for row in exts]

        embed = ctx.embed(
            title='Currently working modules.',
            description='```%s```' % '\n'.join(rows)
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx: Context):
        """Returns uptime: How long the bot is online."""
        h, r = divmod((self.bot.uptime), 3600)
        (m, s), (d, h) = divmod(r, 60), divmod(h, 24)

        embed = ctx.embed().add_field(name='How long I am online?',
                                      value=f'{d}d {h}h {m}m {s}s')

        await ctx.send(embed=embed)

    @commands.command(aliases=['about'])
    async def info(self, ctx: Context):
        """See some kind of information about me (such as command usage, links etc.)"""
        me = self.bot
        embed = ctx.embed().set_author(
            name=f'{me.user} - v{__version__}', icon_url=me.user.avatar_url
        )

        fields = {
            'Development': {
                ('Developer', str(me.dosek)),
                ('Language', 'Python'),
                ('Library', 'Discord.py')
            },
            'General': {
                ('Currently in', f'{len(me.guilds)} servers'),
                ('Commands working', f'{len(me.commands)}'),
                ('Commands usage (last restart)', me.command_usage),
                ('Commands usage (last year)', ctx.config['command_usage'])
            }
        }

        for key in fields:
            embed.add_field(
                name=key,
                value='\n'.join(f'> **{k}:** {v}' for k, v in fields[key]),
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(aliases=['memberinfo', 'ui', 'mi'])
    @commands.guild_only()
    async def userinfo(self, ctx: Context, member: Optional[commands.MemberConverter]):
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

    @commands.command(aliases=['guildinfo', 'si', 'gi'])
    @commands.guild_only()
    async def serverinfo(self, ctx: Context):
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

    @flags.add_flag('--tts', action='store_true', help='Whether to send a tts message.')
    @flags.command()
    async def say(self, ctx: Context, message: str, **flags):
        """Make the bot say what you want

        Example:
            **{p}say "Achievement Completed" --tts**

        Args:
            message (str): A message that is going to be sent.
            Make sure to put your message in "double quotes".
        """
        tts = flags.pop('tts', False)

        await ctx.try_delete(ctx.message)
        await ctx.send(message, tts=tts)

    @commands.command()
    async def links(self, ctx: Context):
        """Some useful invites (support server, bot invite and voting URL)."""
        links = ctx.config.links
        embed = ctx.embed(description=f'Invite me [here]({links.invite_url})\n'
                          f'Support server [here]({links.support_url})'
                          f'Vote on TopGG [here]({links.topgg_url})')

        await ctx.send(embed=embed)

    async def _db_latency(self):
        start = perf_counter()
        await self.bot.pool.fetchval('SELECT 1;')
        end = perf_counter()

        return end - start

    @commands.command()
    async def ping(self, ctx: Context):
        """Check latency of the bot and its system."""
        s = perf_counter()
        msg = await ctx.send('Pong!')
        e = perf_counter()

        elements = {
            f'{LOADING} Websocket': self.bot.latency,
            f'{TYPING} Typing': e - s,
            f'{PG} Database': await self._db_latency()
        }

        embed = ctx.embed(description='\n'.join(f'**{n}:** ```{v * 1000:.2f} ms```' for n, v in elements.items()))
        await msg.edit(embed=embed)

    @commands.command(aliases=['mrs'])
    async def messagereactionstats(self, ctx: Context, *, message_link: str):
        """See what reactions are there in a message, i.e reaction statistics.

        Example:
            **{p}mrs https://discord.com/channels/12345/54321/32451**

        Args:
            message_link (str): An URL of a message.
        """
        ids = [int(i) for i in message_link.split('/')[5:]]
        msg = await ctx.guild.get_channel(ids[0]).fetch_message(ids[1])

        await ctx.send({f'{i}': i.count for i in msg.reactions})
