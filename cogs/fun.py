import asyncio
import random
import textwrap
from html import unescape
from io import BytesIO
from time import time
from typing import Optional

import discord
from discord.ext import commands, flags
from utils import Cog, Manip, Trivia


class Fun(Cog):
    """Fun extension. Hope the name makes sense and commands correspond their parent."""
    icon = '🎉'
    name = 'Fun'

    async def question(self, ctx, difficulty: str):
        if difficulty not in ('easy', 'medium', 'hard'):
            raise ValueError('Invalid difficulty specified.')

        r = await ctx.bot.session.get(f'{ctx.bot.config["API"]["trivia_api"]}&difficulty={difficulty}')
        js = await r.json()
        js = js['results'][0]

        js['incorrect_answers'] = [unescape(x) for x in js['incorrect_answers']]
        js['question'] = unescape(js['question'])
        js['correct_answer'] = unescape(js['correct_answer'])

        return js

    async def answer(self, ctx, q):
        """Takes a question parameter."""
        entr = q['incorrect_answers'] + [q['correct_answer']]
        ans = await Trivia(title=q['question'], entries=random.sample(entr, len(entr))).pagination(ctx)
        return ans == q['correct_answer']

    @commands.command()
    async def coinflip(self, ctx):
        """A very simple coinflip game! Chances are:
        **head → 47.5%**, **tail → 47.5%** and **side → 5%**"""
        if (choice := random.choices(population=['head', 'tail', 'side'], weights=[0.475, 0.475, 0.05], k=1)[0]) == 'side':
            return await ctx.send('You\'ve got an amazing luck since the coin was flipped to the side!')

        await ctx.send(f'Coin flipped to the `{choice}`')

    @commands.command()
    async def trivia(self, ctx, difficulty: str.lower = 'medium'):
        """Trivia game! Has 3 difficulties: `easy`, `medium` and `hard`.
        Args: difficulty (optional): Questions difficulty in the game.
        Defaults to "easy". Returns: A correct answer."""
        try:
            q = await self.question(ctx, difficulty)

        except ValueError:
            raise commands.BadArgument('Invalid difficulty specified.')

        if await self.answer(ctx, q):
            msg = f'**{ctx.author}** answered correct.'

        else:
            msg = f'**{ctx.author}** was a bit wrong'

        await ctx.send(msg + f'\nThe answer was: `{q["correct_answer"]}`.')

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
            try:
                await race.delete()
            except discord.errors.NotFound:
                pass

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

    @commands.command(aliases=['slots'])
    async def slot(self, ctx):
        """Play the game on a slot machine!"""
        a, b, c = random.choices('🍎🍊🍐🍋🍉🍇🍓🍒', k=3)
        text = f'{a} | {b} | {c}\n{ctx.author.display_name}, '

        if a == b == c:
            await ctx.send(f'{text}All match, we have a big winner! 🎉')

        elif (a == b) or (a == c) or (b == c):
            await ctx.send(f'{text}2 match, you won! 🎉')

        else:
            await ctx.send(f'{text}No matches, I wish you win next time.')

    @commands.command(name='random')
    async def _random(self, ctx):
        """Executes a random command that the bot has.
        Perfect feature when you want to use Boribay but don't even know
        what to call."""
        denied = ['random', 'jishaku', 'su']
        command = random.choice([cmd.name for cmd in ctx.bot.commands if len(cmd.signature.split()) == 0 and cmd.name not in denied])
        await ctx.send(f'Invoking command {command}...')
        await ctx.bot.get_command(command)(ctx)

    @commands.command()
    async def eject(self, ctx, color: str.lower, is_impostor: bool, *, name: Optional[str]):
        """Among Us ejected meme maker.
        Colors: black • blue • brown • cyan • darkgreen • lime • orange • pink • purple • red • white • yellow.
        Ex: eject blue True Dosek."""
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
