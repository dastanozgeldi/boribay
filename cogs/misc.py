import platform
from collections import Counter
from datetime import datetime
from glob import glob
from time import perf_counter
from typing import Optional

import psutil
from discord import Forbidden, Member
from discord.ext import commands, flags
from humanize import naturaldate, naturaltime
from utils import Cog, has_voted


class Miscellaneous(Cog):
    """Misc commands extension. Here owner inserts commands that aren't
    related to other categories, such as ping etc."""
    icon = '💫'
    name = 'Miscellaneous'

    async def top_lb(self, ctx, limit: int):
        """The Global Leaderboard for TopGG."""
        upvotes = await ctx.bot.dblpy.get_bot_upvotes()
        medals = ['🥇', '🥈', '🥉'] + ['✨' for num in range(limit - 3)]
        d = Counter([voter['username'] for voter in upvotes]).most_common(limit)

        embed = ctx.bot.embed.default(
            ctx, title='Top voters of this month.',
            description='\n'.join(f'{k} **{i[0]}** → {i[1]} votes' for i, k in zip(d, medals)),
            url=ctx.bot.config['links']['topgg_url']
        )

        await ctx.send(embed=embed)

    async def eco_lb(self, ctx, limit: int):
        """The Global Leaderboard for Economics."""
        me = ctx.bot
        data = (await me.pool.fetch('SELECT * FROM users ORDER by wallet + bank DESC'))[:limit]
        description = '\n'.join(f'**{me.get_user(row["user_id"]) or row["user_id"]}** - {row["wallet"] + row["bank"]} 💂‍♂️' for row in data)
        embed = me.embed.default(ctx, title='The Global Leaderboard', description=description)
        await ctx.send(embed=embed)

    @commands.command()
    @has_voted()
    async def didivote(self, ctx):
        """Check did you vote last 12 hours."""
        await ctx.send('You\'ve already voted, thanks!')

    @commands.command()
    async def vote(self, ctx):
        """Vote for the bot on Top.GG!"""
        dbl_url = ctx.bot.config['links']['topgg_url']
        await ctx.send(f'Alright the link is right here, thanks for the vote! {dbl_url}')

    @flags.add_flag(
        '--limit', type=int, default=5,
        help='Set the limit of users you want to see.'
    )
    @flags.add_flag(
        '--of', choices=['dbl', 'eco'], default='dbl',
        help='A specific topic [dbl for TopGG, eco for economics].'
    )
    @flags.command(aliases=['lb'])
    async def leaderboard(self, ctx, **flags):
        """Leaderboard of top voters for Boribay. Defaults to 5 users,
        however you can specify the limitation of the leaderboard."""
        mode = flags.pop('of')
        if (limit := flags.pop('limit')) > 10:
            raise commands.BadArgument('I cannot get why do you need more than 10 people.')

        if mode == 'eco':
            return await self.eco_lb(ctx, limit)

        await self.top_lb(ctx, limit)

    @commands.command()
    async def github(self, ctx, login: str = 'Dositan'):
        """See some GitHub account information about user.
        Args: profile (optional): Account you want to get the data of."""
        cs = ctx.bot.session
        data = await (await cs.get(f'https://api.github.com/users/{login}')).json()
        repos = await (await cs.get(data['repos_url'])).json()

        fields = [
            ('Following', data['following']),
            ('Followers', data['followers']),
            ('Total Repos', data['public_repos']),
            ('Total Stars', sum(i['stargazers_count'] for i in repos)),
            ('One Repository', f'[here]({repos[0]["html_url"]})')
        ]

        embed = ctx.bot.embed.default(
            ctx, title=data['bio'],
            description='\n'.join(f'**{k}:** {v}' for k, v in fields)
        ).set_author(name=f'{data["login"]} ({data["name"]})', url=data['html_url'])
        embed.set_thumbnail(url=data['avatar_url'])

        await ctx.send(embed=embed)

    @commands.command(aliases=['cs'])
    async def codestats(self, ctx):
        """See the code statictics of the bot."""
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

        await ctx.send(embed=ctx.bot.embed.default(ctx, description='\n'.join([f'**{k.capitalize()}:** {v}' for k, v in ctr.items()])))

    @commands.command(aliases=['modules', 'exts'])
    async def extensions(self, ctx):
        """List of modules that work at a current time."""
        exts = []
        for ext in ctx.bot.cogs.values():
            name = ext.qualified_name

            if not await ctx.bot.is_owner(ctx.author) and name in ctx.bot.config['bot']['owner_exts']:
                continue

            exts.append(name)

        exts = [exts[i: i + 3] for i in range(0, len(exts), 3)]
        length = [len(element) for row in exts for element in row]
        rows = [''.join(e.ljust(max(length) + 2) for e in row) for row in exts]

        await ctx.send(embed=ctx.bot.embed.default(
            ctx, title='Currently working modules.',
            description='```%s```' % '\n'.join(rows)
        ))

    @commands.command()
    async def uptime(self, ctx):
        """Uptime command.
        Returns: uptime: How much time bot is online."""
        h, r = divmod((ctx.bot.uptime), 3600)
        (m, s), (d, h) = divmod(r, 60), divmod(h, 24)

        embed = ctx.bot.embed.default(ctx)
        embed.add_field(name='How long I am online?', value=f'{d}d {h}h {m}m {s}s')

        await ctx.send(embed=embed)

    @commands.command(aliases=['sys'])
    async def system(self, ctx):
        """Information of the system that is running the bot."""
        embed = ctx.bot.embed.default(ctx, title='System Information')
        memory = psutil.virtual_memory()
        info = {
            'System': {
                'Host OS': platform.platform(),
                'Last Boot': naturaltime(datetime.fromtimestamp(psutil.boot_time())),
            }, 'CPU': {
                'Frequency': f'{psutil.cpu_freq(percpu=True)[0][0]} MHz',
                'CPU Used': f'{psutil.cpu_percent(interval=1)}%'
            }, 'Memory': {
                'RAM Used': f'{memory.percent} GB',
                'RAM Available': f'{memory.available / (1024 ** 3):,.3f} GB'
            }
        }

        for key in info:
            embed.add_field(name=f'**{key}**', value='\n'.join([f'> **{k}:** {v}' for k, v in info[key].items()]), inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['about', 'bi', 'botinfo'])
    async def info(self, ctx):
        """See some kind of information about me (such as command usage, links etc.)"""
        me = ctx.bot
        embed = me.embed.default(ctx)
        embed.set_author(name=str(me.user), icon_url=me.user.avatar_url_as(size=64))

        fields = {
            'Development': {
                ('Developer', str(me.dosek)),
                ('Language', 'Python'),
                ('Library', 'Discord.py')
            }, 'General': {
                ('Currently in', f'{len(me.guilds)} servers'),
                ('Commands working', f'{len(me.all_commands)}'),
                ('Commands usage (last restart)', me.command_usage),
                ('Commands usage (last year)', await me.pool.fetchval('SELECT command_usage FROM bot_stats'))
            }
        }

        for key in fields:
            embed.add_field(name=key, value='\n'.join([f'> **{k}:** {v}' for k, v in fields[key]]), inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['memberinfo', 'ui', 'mi'])
    @commands.guild_only()
    async def userinfo(self, ctx, member: Optional[Member]):
        """See some general information about mentioned user."""
        member = member or ctx.author
        embed = ctx.bot.embed.default(ctx).set_thumbnail(url=member.avatar_url)
        embed.set_author(name=str(member), icon_url=ctx.guild.icon_url_as(size=64))

        fields = [
            ('Top role', member.top_role.mention),
            ('Boosted server', bool(member.premium_since)),
            ('Account created', naturaldate(member.created_at)),
            ('Here since', naturaldate(member.joined_at))
        ]

        embed.description = '\n'.join(f'**{name}:** {value}' for name, value in fields)
        await ctx.send(embed=embed)

    @commands.command(aliases=['guildinfo', 'si', 'gi'])
    @commands.guild_only()
    async def serverinfo(self, ctx):
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

        embed = ctx.bot.embed.default(
            ctx, description='\n'.join(f'**{n}:** {v}' for n, v in fields)
        ).set_author(name=g.name, icon_url=g.icon_url_as(size=64), url=g.icon_url)

        await ctx.send(embed=embed)

    @flags.add_flag('--tts', action='store_true', help='Whether to send a tts message.')
    @flags.command()
    async def say(self, ctx, message: str, **flags):
        """Make the bot say what you want.
        Args: message: A message that will be sent.
        Make sure to put your message in double quotes."""
        tts = flags.pop('tts', False)

        try:
            await ctx.message.delete()
        except Forbidden:
            pass

        await ctx.send(message, tts=tts)

    @commands.command()
    async def prefix(self, ctx):
        """See bot's prefix."""
        prefix = '.' if not ctx.guild else ctx.bot.cache[ctx.guild.id].get('prefix', '.')
        await ctx.send(embed=ctx.bot.embed.default(ctx, description=f'The prefix is: `{prefix}` or {ctx.bot.user.mention}'))

    @commands.command(aliases=['links'])
    async def invite(self, ctx):
        """Some useful invites (support server and the bot itself)"""
        embed = ctx.bot.embed.default(
            ctx, description=f'Invite me [here]({ctx.bot.config["links"]["invite_url"]})\n'
            f'Support server [here]({ctx.bot.config["links"]["support_url"]})'
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check latency of the bot and its system."""
        s = perf_counter()
        msg = await ctx.send('Pong!')
        e = perf_counter()

        elements = [
            ('<a:loading:787357834232332298> Websocket', f'{ctx.bot.latency * 1000:.2f}'),
            ('<a:typing:807306107508359228> Typing', f'{(e - s) * 1000:.2f}'),
            ('<:pg:795005204289421363> Database', f'{await ctx.bot.db_latency() * 1000:.2f}')
        ]

        embed = ctx.bot.embed.default(ctx, description='\n'.join([f'**{n}:** ```{v} ms```' for n, v in elements]))
        await msg.edit(embed=embed)

    @commands.command(aliases=['mrs'])
    async def messagereactionstats(self, ctx, message_link: str):
        """See what reactions are there in a message, shortly,
        message_reaction_stats."""
        ids = [int(i) for i in message_link.split('/')[5:]]
        msg = await ctx.guild.get_channel(ids[0]).fetch_message(ids[1])
        await ctx.send({f'{i}': i.count for i in msg.reactions})


def setup(bot):
    bot.add_cog(Miscellaneous())
