import asyncio
import random
import textwrap
from contextlib import suppress
from io import BytesIO
from time import time
from typing import Optional

import discord
from discord.ext import commands, flags
from utils import Cog, Manip


class Fun(Cog):
    """Fun extension. Hope the name makes sense and commands correspond their parent."""
    icon = '🎉'
    name = 'Fun'

    @flags.add_flag(
        '--timeout', type=float, default=60.0,
        help='Set your own timeout! Defaults to 60 seconds.'
    )
    @flags.command(aliases=['tr', 'typerace'])
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    async def typeracer(self, ctx, **flags):
        """Typeracer Command. Compete with others!
        If you don't like the given quote, react with a wastebasket to close the game.
        Returns: Average WPM of the winner, time spent and the original text."""
        timeout = flags.pop('timeout')
        if not 10.0 < timeout < 120.0:
            raise commands.BadArgument('Timeout limit has been reached. Specify between 10 and 120.')

        r = await (await ctx.bot.session.get(ctx.bot.config['API']['quote_api'])).json()
        content = r['content']
        buffer = await Manip.typeracer('\n'.join(textwrap.wrap(content, 30)))

        embed = ctx.bot.embed.default(
            ctx, title='Typeracer', description='see who is fastest at typing.'
        ).set_image(url='attachment://typeracer.png')
        embed.set_footer(text=f'© {r["author"]}')

        race = await ctx.send(file=discord.File(buffer, 'typeracer.png'), embed=embed)
        await race.add_reaction('🗑')
        start = time()

        try:
            done, pending = await asyncio.wait([
                ctx.bot.wait_for(
                    'raw_reaction_add',
                    check=lambda p: str(p.emoji) == '🗑' and p.user_id == ctx.author.id and p.message_id == race.id
                ),
                ctx.bot.wait_for(
                    'message',
                    check=lambda m: m.content == content,
                    timeout=timeout
                )
            ], return_when=asyncio.FIRST_COMPLETED)

            stuff = done.pop().result()

            if isinstance(stuff, discord.RawReactionActionEvent):
                return await race.delete()

            final = round(time() - start, 2)
            await ctx.send(embed=ctx.bot.embed.default(
                ctx, title=f'{stuff.author} won!',
                description=f'**Done in**: {final}s\n'
                f'**Average WPM**: {r["length"] / 5 / (final / 60):.0f} words\n'
                f'**Original text:**```diff\n+ {content}```',
            ))

        except asyncio.TimeoutError:
            with suppress(discord.NotFound):
                await race.delete()

    @commands.command(aliases=['rps'])
    async def rockpaperscissors(self, ctx):
        """The Rock | Paper | Scissors game.
        There are three different reactions, depending on your choice
        random will find did you win, lose or made draw."""
        rps_dict = {
            '🪨': {'🪨': 'draw', '📄': 'lose', '✂': 'win'},
            '📄': {'🪨': 'win', '📄': 'draw', '✂': 'lose'},
            '✂': {'🪨': 'lose', '📄': 'win', '✂': 'draw'}
        }
        choice = random.choice([*rps_dict.keys()])
        embed = ctx.bot.embed.default(ctx, description='**Choose one 👇**')
        msg = await ctx.send(embed=embed.set_footer(text='10 seconds left⏰'))

        for r in rps_dict.keys():
            await msg.add_reaction(r)

        try:
            r, u = await ctx.bot.wait_for(
                'reaction_add', timeout=10,
                check=lambda re, us: us == ctx.author and str(re) in rps_dict.keys() and re.message.id == msg.id
            )
            game = rps_dict.get(str(r.emoji))
            embed = ctx.bot.embed.default(
                ctx, description=f'Result: **{game[choice].upper()}**\n'
                f'My choice: **{choice}**\n'
                f'Your choice: **{r.emoji}**'
            )
            await msg.edit(embed=embed)

        except asyncio.TimeoutError:
            await msg.delete()

    @commands.command()
    async def eject(self, ctx, color: str.lower, is_impostor: bool, *, name: Optional[str]):
        """Among Us ejected meme maker.
        Colors: black • blue • brown • cyan • darkgreen • lime • orange • pink • purple • red • white • yellow.
        Ex: {p}eject blue True Dosek."""
        name = name or ctx.author.display_name
        r = await ctx.bot.session.get(f'https://vacefron.nl/api/ejected?name={name}&impostor={is_impostor}&crewmate={color}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='ejected.png'))

    @commands.command(aliases=['pp', 'penis'])
    async def peepee(self, ctx, member: Optional[discord.Member]):
        """Basically, returns your PP size."""
        member = member or ctx.author
        sz = 100 if member.id in ctx.bot.owner_ids else random.randint(1, 10)
        await ctx.send(f'{member}\'s pp size is:\n3{"=" * sz}D')

    @commands.command()
    async def uselessfact(self, ctx):
        """Returns an useless fact."""
        r = await ctx.bot.session.get('https://uselessfacts.jsph.pl/random.json?language=en')
        js = await r.json()
        await ctx.send(embed=ctx.bot.embed.default(ctx, description=js['text']))


def setup(bot):
    bot.add_cog(Fun())
