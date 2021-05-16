import platform
from collections import Counter
from datetime import datetime
from glob import glob
from time import perf_counter
from typing import Optional

import psutil
from boribay.core import BATYR, LOADING, PG, TYPING, Boribay, Cog, Context
from boribay.utils import Choices, SettingsConverter
from discord.ext import commands, flags
from humanize import naturaldate, naturaltime


class Miscellaneous(Cog):
    """Misc commands extension. Here owner inserts commands that aren't
    related to other categories, such as ping etc."""
    icon = '💫'

    def __init__(self, bot: Boribay):
        self.bot = bot

    @staticmethod
    async def top_lb(ctx: Context, limit: int):
        """The Global Leaderboard for TopGG.

        Args:
            limit (int): The user-limit on leaderboard.
        """
        upvotes = await ctx.bot.dblpy.get_bot_upvotes()
        medals = ['🥇', '🥈', '🥉'] + ['✨' for num in range(limit - 3)]
        d = Counter([voter['username'] for voter in upvotes]).most_common(limit)

        embed = ctx.embed(
            title='Top voters of this month.',
            description='\n'.join(f'{k} **{i[0]}** → {i[1]} votes' for i, k in zip(d, medals)),
            url=ctx.config.links.topgg_url
        )

        await ctx.send(embed=embed)

    @staticmethod
    async def eco_lb(ctx: Context, limit: int):
        """The Global Leaderboard for Economics.

        Args:
            limit (int): The user-limit on leaderboard.
        """
        me = ctx.bot
        data = (await me.pool.fetch('SELECT * FROM users ORDER by wallet + bank DESC'))[:limit]
        users = [f'**{me.get_user(row["user_id"]) or row["user_id"]}** - {row["wallet"] + row["bank"]} {BATYR}' for row in data]

        embed = ctx.embed(title='The Global Leaderboard', description='\n'.join(users))
        await ctx.send(embed=embed)

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
            if ctx.bot.guild_cache[ctx.guild.id][key] == check:
                return '<:crossmark:814742130190712842>'

        return '<:tick:814838692459446293>'

    @commands.command(aliases=('gs',))
    async def settings(self, ctx: Context):
        """The settings command. Shows the settings of the current server.

        What does "None" mean? → This means this category is not set yet.

        What is written on "Embed Color" category? → This is the hex value of a color.

        What do tick and crossmark mean? → Tick represents whether the category is set.
        """
        g = ctx.guild
        sc = SettingsConverter()

        creds = await sc.convert(g, self.bot.guild_cache)

        embed = ctx.embed(
            description='\n'.join(f'**{self.on_or_off(ctx, k)} {k.replace("_", " ").title()}:** {v}' for k, v in creds.items())
        ).set_author(name=f'Settings of {g}', icon_url=g.icon_url)

        await ctx.send(embed=embed)

    @commands.command(aliases=('suggestion',))
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

    @flags.add_flag('--limit', type=int, default=5,
                    help='Set the limit of users you want to see.')
    @flags.command(aliases=['lb'])
    async def leaderboard(self, ctx: Context, mode: str, **flags):
        """Leaderboard of top voters for Boribay. Defaults to 5 users,
        however you can specify the limitation of the leaderboard.

        Args:
            mode (str): The leaderboard mode, either "eco" or "dbl".

        Raises:
            commands.BadArgument: If the limit more than 10 users was specified.
        """
        if (limit := flags.pop('limit')) > 10:
            raise commands.BadArgument('I cannot get why do you need more than 10 people.')

        await Choices().convert(mode, {
            'eco': self.eco_lb(ctx, limit),
            'dbl': self.top_lb(ctx, limit)
        })

    @commands.command(aliases=('cs',))
    async def codestats(self, ctx: Context):
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

    @commands.command(aliases=('modules', 'exts'))
    async def extensions(self, ctx: Context):
        """List of modules that work at a current time."""
        exts = []
        for ext in self.bot.cogs.values():
            name = ext.qualified_name

            if not await self.bot.is_owner(ctx.author) and name in ctx.config.main.owner_exts:
                continue

            exts.append(name)

        exts = [exts[i: i + 3] for i in range(0, len(exts), 3)]
        length = [len(element) for row in exts for element in row]
        rows = [''.join(e.ljust(max(length) + 2) for e in row) for row in exts]

        embed = ctx.embed(title='Currently working modules.',
                          description='```%s```' % '\n'.join(rows))

        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx: Context):
        """Returns uptime: How long the bot is online."""
        h, r = divmod((self.bot.uptime), 3600)
        (m, s), (d, h) = divmod(r, 60), divmod(h, 24)

        embed = ctx.embed().add_field(name='How long I am online?',
                                      value=f'{d}d {h}h {m}m {s}s')

        await ctx.send(embed=embed)

    @commands.command(aliases=('sys',))
    async def system(self, ctx: Context):
        """Information of the system that is running the bot."""
        embed = ctx.embed(title='System Information')
        memory = psutil.virtual_memory()
        info = {
            'System': {
                'Host OS': platform.platform(),
                'Last Boot': naturaltime(datetime.fromtimestamp(psutil.boot_time())),
            }, 'CPU': {
                'Frequency': f'{psutil.cpu_freq(percpu=True)[0][0]} MHz',
                'CPU Used': f'{psutil.cpu_percent(interval=1)}%'
            }, 'Memory': {
                'RAM Used': f'{memory.percent}%',
                'RAM Available': f'{memory.available / (1024 ** 3):,.3f} GB'
            }
        }

        for key in info:
            embed.add_field(name=f'**{key}**', value='\n'.join([f'> **{k}:** {v}' for k, v in info[key].items()]), inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=('about',))
    async def info(self, ctx: Context):
        """See some kind of information about me (such as command usage, links etc.)"""
        me = self.bot
        version = me.config.main.version
        embed = ctx.embed().set_author(
            name=f'{me.user} - v{version}', icon_url=me.user.avatar_url
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

    @commands.command(aliases=('memberinfo', 'ui', 'mi'))
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

    @commands.command(aliases=('guildinfo', 'si', 'gi'))
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

    @commands.command(aliases=('mrs',))
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
