import asyncio
import copy
import html
import random
from typing import Optional

import discord
from boribay.core import Boribay, Cog, Context
from boribay.utils import (AuthorCheckConverter, CasinoConverter, DefaultError,
                           is_mod)
from discord.ext import commands

from .games import Trivia, Work


class Economics(Cog):
    """The Economics extension which is currently in beta-testing."""
    icon = '💵'

    def __init__(self, bot: Boribay):
        self.bot = bot

    async def cog_check(self, ctx: Context):
        return await commands.guild_only().predicate(ctx)

    async def _get_question(self, difficulty: str):
        url = f'https://opentdb.com/api.php?amount=1&difficulty={difficulty}'
        r = await self.bot.session.get(url)
        res = await r.json()

        res = res['results'][0]
        res['question'] = html.unescape(res['question'])
        res['correct_answer'] = html.unescape(res['correct_answer'])
        res['incorrect_answers'] = [html.unescape(x) for x in res['incorrect_answers']]

        return res

    async def _get_answer(self, ctx: Context, question: list):
        entries = [question['correct_answer']] + question['incorrect_answers']
        entries = random.sample(entries, len(entries))
        answer = await Trivia(ctx, entries, question['question']).start()
        return answer == question['correct_answer']

    @commands.command()
    async def trivia(self, ctx: Context, difficulty: str.lower = 'medium'):
        """Play the trivia game to make some money.

        Example:
            **{p}trivia** - starts the trivia game with medium difficulty.
            **{p}trivia hard** - sets the hard difficulty to play.

        Args:
            difficulty (optional): The difficulty of a question. Defaults to 'medium'.

        Raises:
            Default: If the invalid difficulty was provided.
            Available ones are: **easy | medium | hard**
        """
        if difficulty not in ('easy', 'medium', 'hard'):
            raise DefaultError('Invalid difficulty provided.')

        question = await self._get_question(difficulty)

        if await self._get_answer(ctx, question):
            await ctx.reply(f'**Correct! (+50 batyrs)** The answer was: **{question["correct_answer"]}**')
            return await self.bot.db.add('wallet', ctx.author, 50)

        return await ctx.reply(f'**Wrong!** The answer was: **{question["correct_answer"]}**.')

    @commands.group(invoke_without_command=True)
    async def balance(self, ctx: Context):
        """The moderator-only user balance management command."""
        await ctx.send_help('balance')

    @balance.command(name='add')
    @is_mod()
    async def _add_balance(self, ctx: Context, member: discord.Member, amount: int):
        """Increase someone's balance for being well behaved.

        However, balance adding has limits: the transaction money
        must be 100 <= x <= 100 000 batyrs.

        Example:
            **{p}balance add @Dosek 1000** - gives Dosek 1000 batyrs.

        Args:
            member (discord.Member): A member you'd like to add some money to.
            amount (int): Amount of money to add.

        Raises:
            DefaultError: If you have specified too small or too big amount to pay.
        """
        if not 100 <= amount <= 100_000:
            raise DefaultError('Balance adding limit has reached. '
                               'Specify between 10 and 100 000.')

        member = member or ctx.author
        query = 'UPDATE users SET bank = bank + $1 WHERE user_id = $2;'
        await ctx.send(f'✅ Successfully added **{amount} batyrs** to **{member}**.')

        await ctx.db.execute(query, amount, member.id)
        await ctx.user_cache.refresh()

    @balance.command(name='remove')
    @is_mod()
    async def _remove_balance(self, ctx: Context, member: discord.Member, amount: int):
        """Decrease someone's balance for being bad behaved.

        However, balance removing has limits: the transaction money
        must be 100 <= x <= 100 000 batyrs.

        Example:
            **{p}balance remove @Dosek 1000** - takes 1000 batyrs from Dosek.

        Args:
            member (discord.Member): A member you'd like to remove some money from.
            amount (int): Amount of money to remove.

        Raises:
            DefaultError: If you have specified too small or too big amount to take.
        """
        if not 10 <= amount <= 100_000:
            raise DefaultError('Balance adding limit has reached. '
                               'Specify between 10 and 100 000.')

        query = 'UPDATE users SET bank = bank - $1 WHERE user_id = $2;'
        await ctx.send(f'✅ Successfully removed **{amount} batyrs** from **{member}**.')

        await ctx.db.execute(query, amount, member.id)
        await ctx.user_cache.refresh()

    @commands.command(aliases=['card'])
    async def profile(self, ctx: Context, member: Optional[discord.Member]):
        """Check the profile card of a user in Economics system.
        If you don't specify anyone you get your own card information.

        Example:
            **{p}profile** - get your own profile card.
            **{p}profile @Dosek** - get Dosek's profile.

        Args:
            member (Optional[discord.Member]): A member whose card you'd like to see.

        Raises:
            DefaultError: If the member has no profile card set yet.
        """
        member = member or ctx.author

        if not (data := ctx.user_cache[member.id]):
            raise DefaultError(f'{member} has no profile card.')

        data = copy.copy(data)

        embed = ctx.embed(
            title=f'{member}\'s profile card',
            description=data.pop('bio') or 'No bio has been set.'
        ).set_thumbnail(url=member.avatar_url)

        embed.add_field(
            name='📊 Statistics',
            value='\n'.join(f'• **{k.title()}:** {v}' for k, v in data.items())
        )

        await ctx.send(embed=embed)

    @commands.command(aliases=['dep'])
    async def deposit(self, ctx: Context, amount: int = None):
        """Deposit given amount of money into your bank.
        By not specifying the amount of money you deposit them all.

        Example:
            **{p}deposit** - deposit all your money to the bank.
            **{p}deposit 100** - deposit 100 batyrs to the bank.

        Args:
            amount (int, optional): Amount of batyrs to deposit. Defaults to all.

        Raises:
            DefaultError: If you ask to {p}dep more money than you do have.
        """
        data = ctx.user_cache[ctx.author.id]
        wallet = data.get('wallet')
        amount = amount or wallet

        if amount > wallet or wallet == 0:
            raise DefaultError('Transfering amount cannot be higher than your wallet balance')

        query = 'UPDATE users SET bank = bank + $1, wallet = wallet - $1 WHERE user_id = $2'

        await ctx.db.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully transfered **{amount}** batyrs into your bank!')
        await ctx.user_cache.refresh()

    @commands.command(aliases=['wd'])
    async def withdraw(self, ctx: Context, amount: int = None):
        """Withdraw given amount of money from your bank.
        By not specifying the amount of money you withdraw them all.

        Example:
            **{p}withdraw** - transfers all bank money to your wallet.
            **{p}withdraw 100** - transfers 100 batyrs bank → wallet.

        Args:
            amount (int, optional): Amount of batyrs to withdraw. Defaults to all.

        Raises:
            DefaultError: If you ask to {p}wd more money than you do have.
        """
        data = ctx.user_cache[ctx.author.id]
        bank = data.get('bank')
        amount = amount or bank

        if amount > bank or bank == 0:
            raise DefaultError('Withdrawing amount cannot be higher than your bank balance.')

        query = '''
        UPDATE users
        SET bank = bank - $1, wallet = wallet + $1
        WHERE user_id = $2
        '''

        await ctx.db.execute(query, amount, ctx.author.id)
        await ctx.send(f'Successfully withdrew **{amount} batyrs** to your wallet!')
        await ctx.user_cache.refresh()

    @commands.command()
    async def transfer(self, ctx: Context, member: AuthorCheckConverter, amount: int):
        """Transfer someone Batyrs whoever they would be.

        Example:
            **{p}transfer @Dosek 1000** - gives Dosek 1000 Batyrs.

        Args:
            member (discord.Member): Member you'd like to transfer money to.
            amount (int): Amount of Batyrs to transfer.

        Raises:
            DefaultError: If you have less than 100 batyrs on your balance.
        """
        if (wallet := ctx.user_cache[ctx.author.id]['wallet']) < 100:
            raise DefaultError('You have nothing to pay (less than 100 batyrs)')

        if amount > wallet:
            raise DefaultError('Unfortunately, you cannot remain in debt. '
                               f'(You only have {wallet} batyrs).')

        if not 10 < amount < 10_000:
            raise DefaultError('Too big/small amount was specified. '
                               'It should be between 10 and 10 000 batyrs.')

        await self.bot.db.double('wallet', amount, ctx.author, member)
        await ctx.send(f'Transfered **{amount}** batyrs to **{member}**')

    @commands.group(invoke_without_command=True)
    async def bio(self, ctx: Context):
        """Set your bio that will be displayed on your profile!"""
        await ctx.send_help('bio')

    @bio.command(name='set')
    async def _set_bio(self, ctx: Context, *, information: str):
        """Set your bio that will be shown on your profile card.
        Requires to pay 1000 batyrs from your bank.

        Example:
            **{p}bio set Hi, my name is Dastan and I love coding!**

        Args:
            information (str): Your bio you want to set.

        Raises:
            DefaultError: If there were either not enough batyrs or swearing words.
        """
        author = ctx.author.id

        if (bank := ctx.user_cache[author]['bank']) < 1000:
            raise DefaultError(f'Setting bio requires at least 1000 batyrs (You have {bank}).')

        query = 'UPDATE users SET bio = $1, bank = bank - 1000 WHERE user_id = $2;'
        await ctx.db.execute(query, information, author)
        await ctx.user_cache.refresh()
        await ctx.send('✅ Set your bio successfully.')

    @bio.command(name='disable')
    async def _disable_bio(self, ctx: Context):
        """Disable bio feature in your profile.

        This is useful when you want to remove the info about you
        without having to pay batyrs.
        """
        # Avoiding useless database call.
        if not ctx.user_cache[ctx.author.id]['bio']:
            raise commands.CheckFailure('❌ You do not currently have bio set, '
                                        'so there is no point on trying to disable it.')

        confirmation = await ctx.confirm('Are you sure? You will not be able to bring back the money paid to set your bio.')
        if confirmation:
            await ctx.db.execute('UPDATE users SET bio = null WHERE user_id = $1;', ctx.author.id)
            await ctx.user_cache.refresh()
            return await ctx.send('✅ Disabled your bio successfully.')

    @commands.command(aliases=['rob'])
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def attack(self, ctx: Context, member: AuthorCheckConverter):
        """Rob someone whoever they would be.

        Remember that this only works when the victim has more than 100 batyrs
        in their wallet. Rob anyone's bank isn't possible.

        There also is a chance that you can **get caught** by the **police**.

        Example:
            **{p}attack @Dosek** - tries to rob Dosek's batyrs.

        Args:
            member (discord.Member): The victim you want to rob.

        Raises:
            DefaultError: When a user tries to be funny (rob themself).
            DefaultError: When a victim has not enough batyrs to get robbed.
        """
        if (member_wallet := ctx.user_cache[member.id]['wallet']) < 100:
            raise DefaultError(f'{member} had nothing to steal (less than 100 batyrs)')

        choice = random.choices(population=['success', 'caught'], weights=[.5, .5], k=1)[0]
        if choice == 'caught':
            author_bank = ctx.user_cache[ctx.author.id]['bank']
            fine = author_bank * .1
            await self.bot.db.double('bank', fine, ctx.author, member)
            return await ctx.reply(f'You were caught by police and **{fine}** from your bank will be transfered to **{member}** as a fine.')

        amount = random.randint(100, member_wallet)
        await self.bot.db.double('bank', fine, member, ctx.author)
        await ctx.send(f'✅ Stole **{amount}** batyrs from **{member}**')

    @commands.command(aliases=['slots'])
    async def slot(self, ctx: Context, bet: CasinoConverter(50)):
        """Play the game on a slot machine!

        Example:
            **{p}slot 69** - bets 69 batyrs to play slots.

        Args:
            bet (CasinoConverter(50)): Your bet amount. Minimum is 50 batyrs.

        Raises:
            DefaultError: If bet' amount reaches limits.
        """
        a, b, c = random.choices('🍎🍊🍐🍋🍉🍇🍓🍒', k=3)
        text = f'{a} | {b} | {c}\n{ctx.author.display_name}, '
        query = 'UPDATE users SET wallet = wallet + $1 WHERE user_id = $2;'

        if a == b == c:
            result = bet * 20
            await ctx.send(f'{text}All match, we have a big winner! 🎉 {result} batyrs!')

        elif (a == b) or (a == c) or (b == c):
            result = bet * 2
            await ctx.send(f'{text}2 match, you won! 🎉 {result} batyrs!')

        else:
            query = 'UPDATE users SET wallet = wallet - $1 WHERE user_id = $2;'
            result = bet
            await ctx.send(f'{text}No matches, I wish you win next time. No batyrs.')

        await ctx.db.execute(query, result, ctx.author.id)
        await ctx.user_cache.refresh()

    @commands.command()
    async def diceroll(self, ctx: Context, bet: CasinoConverter()):
        rolls = random.choices(times := range(1, 7), k=2)
        my_rolls = random.choices(times, k=2)

        winner = sum(rolls) > sum(my_rolls)
        draw = sum(rolls) == sum(my_rolls)

        def _visualize(r: list):
            return f'{r[0]} {r[1]}'

        embed = ctx.embed()
        query = '''
        UPDATE users
        SET wallet = wallet + $1
        WHERE user_id = $2;
        '''

        if winner:
            _multiplier = random.randint(.5, .95)
            profit = round(bet * _multiplier)

            await ctx.db.execute(query, profit, ctx.author.id)
            await ctx.user_cache.refresh()
            wallet = ctx.user_cache[ctx.author.id]['wallet']

            embed.add_field(name='Winner!', value=(
                f'You won **{profit} batyrs**. ({round(_multiplier * 100)}%)\n'
                f'You now have **{wallet} batyrs**.'
            ), inline=False)

        elif draw:
            embed.add_field(name='Draw!', value=(
                'Our sums are the same. Try again later..?'
            ), inline=False)

        else:
            await ctx.db.execute(query, -bet, ctx.author.id)
            await ctx.user_cache.refresh()
            wallet = ctx.user_cache[ctx.author.id]['wallet']

            embed.add_field(name='Loser!', value=(
                f'You lost **{bet} batyrs.**\n'
                f'You now have **{wallet} batyrs**.'
            ), inline=False)

        embed.add_field(name=f'{ctx.author} ({sum(rolls)})', value=_visualize(rolls))
        embed.add_field(name=f'{ctx.bot.user} ({sum(my_rolls)})', value=_visualize(my_rolls))

        message = await ctx.send(f'Rolling your dice... (Bet: {bet})')
        await asyncio.sleep(3)

        await message.edit(content=None, embed=embed)

    @commands.command()
    async def work(self, ctx: Context):
        """Working is the most legal way to get batyrs.

        Reverse numbers, guess their lengths, more later."""
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
            raise DefaultError(f'Choice {choice} does not exist.\n'
                               f'Choose from **{", ".join(choices)}**')

        embed = ctx.embed(title='Flipping the coin...')
        embed.set_image(url='http://www.mathwire.com/images/animatedcoinflip2.gif')

        message = await ctx.send(embed=embed)
        await asyncio.sleep(5.0)

        if choice == (answer := random.choice(choices)):
            query = 'UPDATE users SET wallet = wallet + 50 WHERE user_id = $1'
            embed.title = f'You guessed right! ({answer}) → +50 batyrs.'

            await ctx.db.execute(query, ctx.author.id)
            await ctx.user_cache.refresh()

        else:
            embed.title = f'Unfortunately, you guessed wrong ({answer}).'

        await message.edit(embed=embed)
