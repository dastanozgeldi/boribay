# TODO implement shopping stuff: buy, exchange etc.
# TODO some fascinating features, challenges and assignments on work command.
import copy
import random
from html import unescape
from typing import Optional

import discord
from discord.ext import commands
from utils import Cog, Trivia


class Economics(Cog):
    """The Economics extension which is currently in beta-testing."""
    icon = '💵'
    name = 'Economics'
    bad_words = open('./data/badwords.txt', 'r').readlines()[1:]

    async def cog_check(self, ctx):
        return await commands.guild_only().predicate(ctx)

    async def double(self, ctx, choice: str, amount: int, reducer: discord.Member, adder: discord.Member):
        reducer_query = f'UPDATE users SET {choice} = {choice} - $1 WHERE user_id = $2'
        adder_query = f'UPDATE users SET {choice} = {choice} + $1 WHERE user_id = $2'

        await ctx.bot.pool.execute(reducer_query, amount, reducer.id)
        await ctx.bot.pool.execute(adder_query, amount, adder.id)

    async def question(self, ctx, difficulty: str):
        """Getting and sorting questions taken from API."""
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
    async def currency(self, ctx):
        """A brief information about my currency."""
        await ctx.send('My economics system uses **batyrs** <:batyr:822488889020121118>')

    @commands.command(aliases=['card'])
    async def profile(self, ctx, member: Optional[discord.Member]):
        """Check your profile. Specify a member to see their profile card.
        You can set your bio to be shown here by doing {p}bio <whatever you want>"""
        member = member or ctx.author

        if not (data := ctx.bot.user_cache[member.id]):
            raise commands.BadArgument(f'{member} has no profile card.')

        data = copy.copy(data)

        embed = ctx.bot.embed.default(
            ctx, title=f'{member}\'s profile card',
            description=data.pop('bio', None)
        ).set_thumbnail(url=member.avatar_url)

        embed.add_field(
            name='📊 Statistics',
            value='\n'.join(f'• **{k.title()}:** {v}' for k, v in data.items())
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 86400.0, commands.BucketType.user)
    async def daily(self, ctx):
        """Get your daily award!"""
        amount = random.randint(50, 200)
        query = 'UPDATE users SET wallet = wallet + $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Gave you {amount} <:batyr:822488889020121118> for good behavior!')
        await ctx.bot.user_cache.refresh()

    @commands.command(aliases=['dep'])
    async def deposit(self, ctx, amount: int = None):
        """Deposit your money into BoriBank!
        By not specifying the amount of money you deposit them all."""
        data = ctx.bot.user_cache[ctx.author.id]
        wallet = data.get('wallet')
        amount = amount or wallet

        if amount > wallet or wallet == 0:
            raise commands.BadArgument('Transfering amount cannot be higher than your wallet balance')

        query = 'UPDATE users SET bank = bank + $1, wallet = wallet - $1 WHERE user_id = $2'

        await ctx.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully transfered **{amount}** <:batyr:822488889020121118> into your bank!')
        await ctx.bot.user_cache.refresh()

    @commands.command(aliases=['wd'])
    async def withdraw(self, ctx, amount: int = None):
        """Withdraw your money from BoriBank!
        By not specifying the amount of money you withdraw them all."""
        data = ctx.bot.user_cache[ctx.author.id]
        bank = data.get('bank')
        amount = amount or bank

        if amount > bank or bank == 0:
            raise commands.BadArgument('Withdrawing amount cannot be higher than your bank balance')

        query = 'UPDATE users SET bank = bank - $1, wallet = wallet + $1 WHERE user_id = $2'

        await ctx.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully withdrew **{amount} <:batyr:822488889020121118>** to your wallet!')
        await ctx.bot.user_cache.refresh()

    @commands.command()
    async def pay(self, ctx, amount: int, member: discord.Member):
        """Pay someone whoever they would be."""
        wallet = ctx.bot.user_cache[ctx.author.id]['wallet']
        if wallet < 100:
            raise commands.BadArgument('You have nothing to pay (less than 100 <:batyr:822488889020121118>)')

        await self.double(ctx, 'wallet', amount, ctx.author, member)
        await ctx.send(f'Paid **{amount}** <:batyr:822488889020121118> to **{member}**')
        await ctx.bot.user_cache.refresh()

    @commands.command(name='bio')
    async def user_bio(self, ctx, *, information: str):
        """Set your bio that will be displayed on your profile! Requires to pay 1000 <:batyr:822488889020121118>"""
        author = ctx.author.id
        bank = ctx.bot.user_cache[author]['bank']

        if bank < 1000:
            raise commands.BadArgument('Setting/Changing bio requires at least 1000 <:batyr:822488889020121118>')

        for bad_word in self.bad_words:
            if bad_word in information:
                raise commands.BadArgument('Swearing words are not allowed to be set.')

        method = ctx.bot.pool.execute
        await method('UPDATE users SET bio = $1 WHERE user_id = $2', information, author)
        await method('UPDATE users SET bank = bank - 1000 WHERE user_id = $1', author)

        await ctx.send('✅ Set your bio successfully!')
        await ctx.bot.user_cache.refresh()

    @commands.command(aliases=['rob'])
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def attack(self, ctx, member: discord.Member):
        """Rob someone whoever they would be.
        The chance you can get caught is equal to 50%, be careful!"""
        if ctx.author == member:
            raise commands.BadArgument('A suicide attempt found!')

        member_wallet = ctx.bot.user_cache[member.id]['wallet']

        if member_wallet < 100:
            raise commands.BadArgument(f'{member} had nothing to steal (less than 100 <:batyr:822488889020121118>)')

        choice = random.choices(population=['success', 'caught'], weights=[.5, .5], k=1)[0]

        if choice == 'caught':
            author_bank = ctx.bot.user_cache[ctx.author.id]['bank']
            await self.double(ctx, 'bank', author_bank * .1, ctx.author, member)
            return await ctx.reply(f'You were caught by police and 10% of your bank will be transfered to {member}!')

        amount = random.randint(100, member_wallet)
        await self.double(ctx, 'wallet', amount, member, ctx.author)
        await ctx.send(f'Stole **{amount}** <:batyr:822488889020121118> from **{member}**')
        await ctx.bot.user_cache.refresh()

    @commands.command(aliases=['slots'])
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def slot(self, ctx, bet: int):
        """Play the game on a slot machine!"""
        wallet = ctx.bot.user_cache[ctx.author.id]['wallet']
        if bet > wallet:
            raise commands.BadArgument('Bet amount cannot be higher than your wallet balance.')

        if bet < 50:
            raise commands.BadArgument('Bet amount is too small, bets start from 50 <:batyr:822488889020121118>')

        await ctx.bot.pool.execute('UPDATE users SET wallet = wallet - $1 WHERE user_id = $2', bet, ctx.author.id)

        a, b, c = random.choices('🍎🍊🍐🍋🍉🍇🍓🍒', k=3)
        distinction = bet / 50
        text = f'{a} | {b} | {c}\n{ctx.author.display_name}, '

        if a == b == c:
            won = 1000 * distinction
            await ctx.send(f'{text}All match, we have a big winner! 🎉 {won} <:batyr:822488889020121118>!')

        elif (a == b) or (a == c) or (b == c):
            won = 100 * distinction
            await ctx.send(f'{text}2 match, you won! 🎉 {won} <:batyr:822488889020121118>!')

        else:
            await ctx.bot.user_cache.refresh()
            return await ctx.send(f'{text}No matches, I wish you win next time. No batyrs.')

        await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + $1 WHERE user_id = $2', won, ctx.author.id)
        await ctx.bot.user_cache.refresh()

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def work(self, ctx):
        """Work to get clean money without robbing or whatever else."""
        amount = random.randint(0, 100)  # getting random money amount.

        await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + $1 WHERE user_id = $2', amount, ctx.author.id)
        await ctx.send(f'You were working a lot and got **{"scammed" if amount == 0 else amount}** <:batyr:822488889020121118>')
        await ctx.bot.user_cache.refresh()

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def trivia(self, ctx, difficulty: str.lower = 'medium'):
        """Trivia game! Has 3 difficulties: `easy`, `medium` and `hard`.
        Args: difficulty (optional): Questions difficulty in the game.
        Defaults to "easy". Returns: A correct answer."""
        try:
            question = await self.question(ctx, difficulty)

        except ValueError:
            raise commands.BadArgument('Invalid difficulty specified.')

        if await self.answer(ctx, question):
            msg = f'**{ctx.author}** answered correct and received **50** <:batyr:822488889020121118> as a reward.'
            await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + 50 WHERE user_id = $1', ctx.author.id)

        else:
            msg = f'**{ctx.author}** was a bit wrong'

        await ctx.send(msg + f'\nThe answer was: `{question["correct_answer"]}`.')
        await ctx.bot.user_cache.refresh()

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def coinflip(self, ctx):
        """A very simple coinflip game! Chances are:
        **head → 49.5%**, **tail → 49.5%** and **side → 1%**"""
        if (choice := random.choices(population=['head', 'tail', 'side'], weights=[0.495, 0.495, 0.01], k=1)[0]) == 'side':
            await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + 10000 WHERE user_id = $1', ctx.author.id)
            return await ctx.send('Coin was flipped **to the side**! +10000')

        await ctx.send(f'Coin flipped to the `{choice}`, no reward.')
        await ctx.bot.user_cache.refresh()


def setup(bot):
    bot.add_cog(Economics())
