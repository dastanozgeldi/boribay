import asyncio
import copy
import random
from typing import Optional

import discord
from boribay.core import Boribay, Context
from boribay.utils import Cog, is_mod
from discord.ext import commands


class Work:
    def __init__(self, ctx: Context):
        self.ctx = ctx

    def __dir__(self):
        return ['digit_length', 'reverse_number']

    async def template(self, start_message: str, number: str):
        ctx = self.ctx

        await ctx.send(start_message + '\nYou have 10 seconds.')

        def check(msg: discord.Message):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            message = await ctx.bot.wait_for('message', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send('❌ You took too long.')

        try:
            guessed = int(message.content)
        except ValueError:
            return await ctx.send('❌ Seems you did not provide the number.')

        if guessed == number:
            query = 'UPDATE users SET wallet = wallet + 100 WHERE user_id = $1;'
            await ctx.bot.pool.execute(query, ctx.author.id)
            await ctx.bot.user_cache.refresh()
            return await ctx.send(f'✅ You are right! The number was: {number} → +100 batyrs.')

        await ctx.send(f'❌ Looks you guessed a wrong number (the actual one is {number}). I wish you win next time.')

    async def digit_length(self):
        number = str(random.getrandbits(random.randint(32, 64)))
        await self.template(f'Guess the length of this number: {number}', len(number))

    async def reverse_number(self):
        number = str(random.getrandbits(random.randint(32, 64)))
        await self.template(f'Send the reversed version of this number: {number}', number[::-1])


class Economics(Cog):
    """The Economics extension which is currently in beta-testing."""
    icon = '💵'
    name = 'Economics'

    def __init__(self, bot: Boribay):
        self.bot = bot
        self.bad_words = open('./boribay/data/textfiles/badwords.txt', 'r').read()

    async def cog_check(self, ctx):
        return await commands.guild_only().predicate(ctx)

    async def double(self, choice: str, amount: int, reducer, adder):
        reducer_query = f'UPDATE users SET {choice} = {choice} - $1 WHERE user_id = $2'
        adder_query = f'UPDATE users SET {choice} = {choice} + $1 WHERE user_id = $2'
        await self.bot.pool.execute(reducer_query, amount, reducer.id)
        await self.bot.pool.execute(adder_query, amount, adder.id)

    @commands.group(invoke_without_command=True)
    async def balance(self, ctx):
        """The admin-only user balance management command."""
        await ctx.send_help('balance')

    @balance.command(name='add')
    @is_mod()
    async def _add_balance(self, ctx: Context, amount: int, member: Optional[discord.Member]):
        """Increase someone's balance for being well behaved."""
        if not 10 <= amount <= 100_000:
            raise commands.BadArgument('❌ Balance adding limit has reached. '
                                       'Specify between 10 and 100 000.')

        member = member or ctx.author
        query = 'UPDATE users SET bank = bank + $1 WHERE user_id = $2;'
        await ctx.send(f'✅ Successfully added **{amount} batyrs** to **{member}**.')

        await self.bot.pool.execute(query, amount, member.id)
        await self.bot.user_cache.refresh()

    @balance.command(name='remove')
    @is_mod()
    async def _remove_balance(self, ctx: Context, amount: int, member: Optional[discord.Member]):
        """Decrease someone's balance for being bad behaved."""
        if not 10 <= amount <= 100_000:
            raise commands.BadArgument('❌ Balance adding limit has reached. '
                                       'Specify between 10 and 100 000.')

        member = member or ctx.author
        query = 'UPDATE users SET bank = bank - $1 WHERE user_id = $2;'
        await ctx.send(f'✅ Successfully removed **{amount} batyrs** from **{member}**.')

        await self.bot.pool.execute(query, amount, member.id)
        await self.bot.user_cache.refresh()

    @commands.command(aliases=['card'])
    async def profile(self, ctx: Context, member: Optional[discord.Member]):
        """Check your profile. Specify a member to see their profile card.
        You can set your bio to be shown here by doing {p}bio <whatever you want>"""
        member = member or ctx.author

        if not (data := self.bot.user_cache[member.id]):
            raise commands.BadArgument(f'{member} has no profile card.')

        data = copy.copy(data)

        embed = self.bot.embed.default(
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
        await ctx.send(f'Gave you {amount} <:batyr:822488889020121118> for good behavior!')

        await self.bot.pool.execute(query, amount, ctx.author.id)
        await self.bot.user_cache.refresh()

    @commands.command(aliases=['dep'])
    async def deposit(self, ctx: Context, amount: int = None):
        """Deposit your money into BoriBank!
        By not specifying the amount of money you deposit them all."""
        data = self.bot.user_cache[ctx.author.id]
        wallet = data.get('wallet')
        amount = amount or wallet

        if amount > wallet or wallet == 0:
            raise commands.BadArgument('Transfering amount cannot be higher than your wallet balance')

        query = 'UPDATE users SET bank = bank + $1, wallet = wallet - $1 WHERE user_id = $2'

        await self.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully transfered **{amount}** <:batyr:822488889020121118> into your bank!')
        await self.bot.user_cache.refresh()

    @commands.command(aliases=['wd'])
    async def withdraw(self, ctx: Context, amount: int = None):
        """Withdraw your money from BoriBank!
        By not specifying the amount of money you withdraw them all."""
        data = self.bot.user_cache[ctx.author.id]
        bank = data.get('bank')
        amount = amount or bank

        if amount > bank or bank == 0:
            raise commands.BadArgument('Withdrawing amount cannot be higher than your bank balance')

        query = 'UPDATE users SET bank = bank - $1, wallet = wallet + $1 WHERE user_id = $2'

        await self.bot.pool.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully withdrew **{amount} <:batyr:822488889020121118>** to your wallet!')
        await self.bot.user_cache.refresh()

    @commands.command()
    async def transfer(self, ctx: Context, amount: int, member: discord.Member):
        """Transfer someone batyrs whoever they would be."""
        if self.bot.user_cache[ctx.author.id]['wallet'] < 100:
            raise commands.BadArgument('❌ You have nothing to pay (less than 100 <:batyr:822488889020121118>)')

        await self.double('wallet', amount, ctx.author, member)
        await self.bot.user_cache.refresh()
        await ctx.send(f'Paid **{amount}** <:batyr:822488889020121118> to **{member}**')

    @commands.group(invoke_without_command=True)
    async def bio(self, ctx: Context, *, information: str):
        """Set your bio that will be displayed on your profile! Requires to pay 1000 <:batyr:822488889020121118>"""
        await ctx.send_help('bio')

    @bio.command(name='set')
    async def _set_bio(self, ctx: Context, *, information: str):
        """Set your bio that will be shown on your profile card.
        Requires to pay 1000 <:batyr:822488889020121118>.

        Example:
            **{p}bio set Hi, my name is Dastan and I love coding!**

        Args:
            information (str): Your bio you want to set.

        Raises:
            BadArgument: If there were either not enough batyrs or swearing words.
        """
        author = ctx.author.id

        if (bank := self.bot.user_cache[author]['bank']) < 1000:
            raise commands.BadArgument(f'❌ Setting bio requires at least 1000 batyrs (You have {bank}).')

        for bad_word in self.bad_words:
            if bad_word in information:
                raise commands.BadArgument('❌ Swearing words are not allowed to be set.')

        query = '''
        UPDATE users
        SET bio = $1, bank = bank - 1000
        WHERE user_id = $2;
        '''

        await self.bot.pool.execute(query, information, author)
        await self.bot.user_cache.refresh()
        await ctx.send('✅ Set your bio successfully.')

    @bio.command(name='disable')
    async def _disable_bio(self, ctx):
        """Disable bio feature in your profile.

        This is useful when you want to remove the info about you
        without having to pay batyrs.
        """
        query = 'UPDATE users SET bio = null WHERE user_id = $1;'
        await self.bot.pool.execute(query, ctx.author.id)
        await self.bot.user_cache.refresh()
        await ctx.send('✅ Disabled your bio successfully.')

    @commands.command(aliases=['rob'])
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def attack(self, ctx: Context, member: discord.Member):
        """Rob someone whoever they would be.

        Remember that this only works when the victim has more than 100 batyrs
        in their wallet. Rob anyone's bank isn't possible.

        There also is a chance that you can **get caught** by the **police**.

        Args:
            member (discord.Member): The victim you want to rob.

        Raises:
            BadArgument: When a user tries to be funny (rob themself).
            BadArgument: When a victim has not enough batyrs to get robbed.
        """
        if ctx.author == member:
            raise commands.BadArgument('A suicide attempt found!')

        if (member_wallet := self.bot.user_cache[member.id]['wallet']) < 100:
            raise commands.BadArgument(f'{member} had nothing to steal (less than 100 <:batyr:822488889020121118>)')

        choice = random.choices(population=['success', 'caught'], weights=[.5, .5], k=1)[0]

        if choice == 'caught':
            author_bank = self.bot.user_cache[ctx.author.id]['bank']
            await self.double('bank', author_bank * .1, ctx.author, member)
            return await ctx.reply(f'You were caught by police and 10% of your bank will be transfered to {member}!')

        amount = random.randint(100, member_wallet)
        await self.double('wallet', amount, member, ctx.author)
        await self.bot.user_cache.refresh()
        await ctx.send(f'✅ Stole **{amount}** <:batyr:822488889020121118> from **{member}**')

    @commands.command(aliases=['slots'])
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def slot(self, ctx: Context, bet: int):
        """Play the game on a slot machine!

        Args:
            bet (int): Your bet amount.

        Raises:
            BadArgument: If bets' amount reaches limits.
        """
        wallet = self.bot.user_cache[ctx.author.id]['wallet']
        if bet > wallet:
            raise commands.BadArgument('❌ Bet amount cannot be higher than your wallet balance.')

        if bet < 50:
            raise commands.BadArgument('❌ Bet amount is too small, bets start from 50 batyrs.')

        a, b, c = random.choices('🍎🍊🍐🍋🍉🍇🍓🍒', k=3)
        text = f'{a} | {b} | {c}\n{ctx.author.display_name}, '

        query = 'UPDATE users SET wallet = wallet + $1 WHERE user_id = $2;'

        if a == b == c:
            result = bet * 20
            await ctx.send(f'{text}All match, we have a big winner! 🎉 {result} <:batyr:822488889020121118>!')

        elif (a == b) or (a == c) or (b == c):
            result = bet * 2
            await ctx.send(f'{text}2 match, you won! 🎉 {result} <:batyr:822488889020121118>!')

        else:
            query = 'UPDATE users SET wallet = wallet - $1 WHERE user_id = $2;'
            result = bet
            await ctx.send(f'{text}No matches, I wish you win next time. No batyrs.')

        await self.bot.pool.execute(query, result, ctx.author.id)
        await self.bot.user_cache.refresh()

    @commands.command()
    async def work(self, ctx):
        """Working is the most legal way to get batyrs.

        Remember that there is a chance you can get scammed by your boss.
        """
        game = Work(ctx)
        job = random.choice(dir(game))
        await getattr(game, job)()

    @commands.command(aliases=['hnt'])
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def headsandtails(self, ctx: Context):
        """Try your luck playing heads and tails!

        If your choice equals the random one, this means you won.

        Example:
            **{p}headsandtails heads** - I hope it's clear enough.

        Args:
            choice (str): Your choice [heads | tails]
        """
        await ctx.send('Share your choice, you have 10 seconds.')

        def check(msg: discord.Message):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            choice = (await self.bot.wait_for('message', timeout=10.0, check=check)).content

        except asyncio.TimeoutError:
            return await ctx.send('❌ You took too long.')

        choices = ('heads', 'tails')

        if choice not in choices:
            raise commands.BadArgument(f'❌ Choice {choice} does not exist.\n'
                                       f'Choose from **{", ".join(choices)}**')

        embed = self.bot.embed.default(ctx, title='Flipping the coin...')
        embed.set_image(url='http://www.mathwire.com/images/animatedcoinflip2.gif')

        message = await ctx.send(embed=embed)
        await asyncio.sleep(5.0)

        if choice == (answer := random.choice(choices)):
            query = 'UPDATE users SET wallet = wallet + 50 WHERE user_id = $1'
            embed.title = f'You guessed right! ({answer}) → +50 batyrs.'

            await self.bot.pool.execute(query, ctx.author.id)
            await self.bot.user_cache.refresh()

        else:
            embed.title = f'Unfortunately, you guessed wrong ({answer}).'

        await message.edit(embed=embed)


def setup(bot: Boribay):
    bot.add_cog(Economics(bot))
