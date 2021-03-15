# TODO implement shopping stuff: buy, exchange etc.
# TODO some fascinating features, challenges and assignments on work command.

import random
from html import unescape
from typing import Optional

import discord
from discord.ext import commands
from utils import Cog, Trivia, is_logged


class Economics(Cog):
    """The Economics extension which is currently in beta-testing.
    Type **login** to log into economic system."""
    icon = '💵'
    name = 'Economics'

    async def cog_check(self, ctx):
        return await is_logged().predicate(ctx)

    async def double(self, ctx, amount: int, reducer: discord.Member, adder: discord.Member):
        reducer_query = 'UPDATE users SET wallet = wallet - $1 WHERE user_id = $2'
        adder_query = 'UPDATE users SET wallet = wallet + $1 WHERE user_id = $2'

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
    async def login(self, ctx):
        """Log into the database."""
        query = 'INSERT INTO users(user_id) VALUES($1)'
        await ctx.bot.pool.execute(query, ctx.author.id)
        await ctx.send('Successfully logged you into Economics!')

    @commands.command()
    async def currency(self, ctx):
        """A brief information about my currency."""
        await ctx.send('My economics system uses **batyrs**💂‍♂️. 1 batyr, 5 batyrs...')

    @commands.command(aliases=['bal'])
    async def balance(self, ctx, member: Optional[discord.Member]):
        """Check your balance. Specify a member to see their balance card."""
        member = member or ctx.author
        query = 'SELECT wallet, bank FROM users WHERE user_id = $1'
        data = await ctx.bot.pool.fetchrow(query, member.id)

        try:
            embed = ctx.bot.embed.default(
                ctx, title=f'{member}\'s balance card',
                description='\n'.join(f'• **{k.title()}:** {v} 💂‍♂️' for k, v in data.items())
            )
            embed.set_thumbnail(url=member.avatar_url)

        except AttributeError:
            raise commands.BadArgument(f'{member} has not logged in yet.')

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addbalance(self, ctx, amount: int, member: Optional[discord.Member]):
        """Increase someone's balance for being well behaved."""
        if not 10 <= amount <= 100_000:
            raise commands.BadArgument('Balance adding limit has reached. Specify between 10 and 100 000')

        member = member or ctx.author
        query = 'UPDATE users SET bank = bank + $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, member.id)
        await ctx.send(f'Successfully added **{amount} batyrs** to **{member}**!')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removebalance(self, ctx, amount: int, member: Optional[discord.Member]):
        """Decrease someone's balance for being bad behaved."""
        if not 10 <= amount <= 100_000:
            raise commands.BadArgument('Balance removing limit has reached. Specify between 10 and 100 000')

        member = member or ctx.author
        query = 'UPDATE users SET bank = bank - $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, member.id)
        await ctx.send(f'Successfully removed **{amount} batyrs** from **{member}**!')

    @commands.command()
    @commands.cooldown(1, 86400.0, commands.BucketType.user)
    async def daily(self, ctx):
        """Get your daily award!"""
        amount = random.randint(50, 200)
        query = 'UPDATE users SET wallet = wallet + $1 WHERE user_id = $2'
        await ctx.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Gave you {amount} for good behavior!')

    @commands.command(aliases=['dep'])
    async def deposit(self, ctx, amount: int = None):
        """Deposit your money into BoriBank!
        By not specifying the amount of money you deposit them all."""
        data = await ctx.bot.pool.fetchrow('SELECT * FROM users WHERE user_id = $1', ctx.author.id)
        wallet = data.get('wallet')
        amount = amount or wallet

        if amount > wallet or amount == 0:
            raise commands.BadArgument('Transfering amount cannot be higher than your wallet balance')

        query = 'UPDATE users SET bank = bank + $1, wallet = wallet - $1 WHERE user_id = $2'

        await ctx.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully transfered **{amount} batyrs** into your bank!')

    @commands.command(aliases=['wd'])
    async def withdraw(self, ctx, amount: int = None):
        """Deposit your money into BoriBank!"""
        data = await ctx.bot.pool.fetchrow('SELECT * FROM users WHERE user_id = $1', ctx.author.id)
        bank = data.get('bank')
        amount = amount or bank

        if amount > bank:
            raise commands.BadArgument('Withdrawing amount cannot be higher than your bank balance')

        query = 'UPDATE users SET bank = bank - $1, wallet = wallet + $1 WHERE user_id = $2'

        await ctx.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully withdrew **{amount} batyrs** to your wallet!')

    @commands.command()
    async def pay(self, ctx, amount: int, member: discord.Member):
        """Pay someone whoever they would be."""
        wallet = await ctx.bot.pool.fetchval('SELECT wallet FROM users WHERE user_id = $1', ctx.author.id)
        if wallet < 100:
            raise commands.BadArgument('You have nothing to pay (less than 100 batyrs)')

        await self.double(ctx, amount, ctx.author, member)
        await ctx.send(f'Paid **{amount}** 💂‍♂️ to **{member}**')

    @commands.command(aliases=['rob'])
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def attack(self, ctx, member: discord.Member):
        """Rob someone whoever they would be.
        The chance you can get caught is equal to 50%, be careful!"""
        query = 'SELECT wallet FROM users WHERE user_id = $1'
        author_wallet = await ctx.bot.pool.fetchval(query, ctx.author.id)
        member_wallet = await ctx.bot.pool.fetchval(query, member.id)

        if member_wallet < 100:
            raise commands.BadArgument(f'{member} had nothing to steal (less than 100 batyrs)')

        choice = random.choices(population=['success', 'caught'], weights=[.5, .5], k=1)[0]

        if choice == 'caught':
            await self.double(ctx, author_wallet, ctx.author, member)
            return await ctx.reply(f'You were caught by police and all your money will go to **{member}**!')

        amount = random.randint(100, member_wallet)
        await self.double(ctx, amount, member, ctx.author)
        await ctx.send(f'Stole **{amount}** 💂‍♂️ from **{member}**')

    @commands.command(aliases=['slots'])
    async def slot(self, ctx, bet: int):
        """Play the game on a slot machine!"""
        wallet = await ctx.bot.pool.fetchval('SELECT wallet FROM users WHERE user_id = $1', ctx.author.id)
        if bet > wallet:
            raise commands.BadArgument('Bet amount cannot be higher than your wallet balance.')

        if not 50 <= bet <= 250:
            raise commands.BadArgument('Bet limit has reached (should be between 50 and 250)')

        await ctx.bot.pool.execute('UPDATE users SET wallet = wallet - $1 WHERE user_id = $2', bet, ctx.author.id)

        a, b, c = random.choices('🍎🍊🍐🍋🍉🍇🍓🍒', k=3)
        distinction = bet / 50
        text = f'{a} | {b} | {c}\n{ctx.author.display_name}, '

        if a == b == c:
            won = 1000 * distinction
            await ctx.send(f'{text}All match, we have a big winner! 🎉 {won} batyrs!')

        elif (a == b) or (a == c) or (b == c):
            won = 100 * distinction
            await ctx.send(f'{text}2 match, you won! 🎉 {won} batyrs!')

        else:
            return await ctx.send(f'{text}No matches, I wish you win next time. No batyrs.')

        await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + $1 WHERE user_id = $2', won, ctx.author.id)

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def work(self, ctx):
        """Work to get clean money without robbing or whatever else."""
        amount = random.randint(0, 100)
        await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + $1 WHERE user_id = $2', amount, ctx.author.id)
        await ctx.send(f'You were working a lot and got **{"scammed" if amount == 0 else amount}** 💂‍♂️')

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def trivia(self, ctx, difficulty: str.lower = 'medium'):
        """Trivia game! Has 3 difficulties: `easy`, `medium` and `hard`.
        Args: difficulty (optional): Questions difficulty in the game.
        Defaults to "easy". Returns: A correct answer."""
        try:
            q = await self.question(ctx, difficulty)
        except ValueError:
            raise commands.BadArgument('Invalid difficulty specified.')

        if await self.answer(ctx, q):
            msg = f'**{ctx.author}** answered correct and received **50** 💂‍♂️ as a reward.'
            await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + 50 WHERE user_id = $1', ctx.author.id)

        else:
            msg = f'**{ctx.author}** was a bit wrong'

        await ctx.send(msg + f'\nThe answer was: `{q["correct_answer"]}`.')

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def coinflip(self, ctx):
        """A very simple coinflip game! Chances are:
        **head → 49.5%**, **tail → 49.5%** and **side → 1%**"""
        if (choice := random.choices(population=['head', 'tail', 'side'], weights=[0.495, 0.495, 0.01], k=1)[0]) == 'side':
            await ctx.bot.pool.execute('UPDATE users SET wallet = wallet + 10000 WHERE user_id = $1', ctx.author.id)
            return await ctx.send('You\'ve got an amazing luck since the coin was flipped to the side!')

        await ctx.send(f'Coin flipped to the `{choice}`, no reward.')


def setup(bot):
    bot.add_cog(Economics())
