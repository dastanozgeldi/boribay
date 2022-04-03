import asyncio
import copy
import random
from typing import Optional

import discord
from discord.ext import commands

from boribay.core import exceptions, utils
from boribay.core.database import Cache

from .games import Trivia, Work
from .utils import CasinoConverter

BATYR = "<:batyr:822488889020121118>"


class Economics(utils.Cog):
    """The Economics extension."""

    icon = "💵"

    def __init__(self, bot):
        self.bot = bot
        self.economy_cache = Cache("SELECT * FROM economy", "user_id", self.bot.pool)

    async def cog_check(self, ctx: utils.Context):
        return await commands.guild_only().predicate(ctx)

    @utils.command()
    async def register(self, ctx: utils.Context) -> None:
        """Register into Boribay economics system."""
        if self.economy_cache[ctx.author.id]:
            return await ctx.send("You are already registered in the economics system.")

        await self.bot.pool.execute(
            "INSERT INTO users(user_id) VALUES($1)", ctx.author.id
        )
        await self.economy_cache.refresh()
        await ctx.send(
            "Welcome to the economics system! (test has successfully been passed.)"
        )

    @utils.command()
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def trivia(
        self, ctx: utils.Context, difficulty: str.lower = "medium"
    ) -> None:
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
        if difficulty not in ("easy", "medium", "hard"):
            raise exceptions.DefaultError("Invalid difficulty provided.")

        await Trivia(ctx).run(difficulty)

    @utils.command(aliases=("lb",))
    async def leaderboard(self, ctx: utils.Context, limit: int = 5) -> None:
        """Boribay economics leaderboard. Defaults to 5 users,
        however you can specify the limitation of the leaderboard.

        Parameters
        ----------
        limit : int, optional
            Set the limit of users you want to see, by default 5

        Raises
        ------
        commands.BadArgument
            If more than 10 users were specified in the limit.
        """
        if limit > 10:
            raise commands.BadArgument(
                "I cannot get why do you need more than 10 people."
            )

        data = await ctx.bot.pool.fetch(
            "SELECT * FROM users ORDER by wallet + bank DESC"
        )
        users = [
            f'**{ctx.bot.get_user(row["user_id"]) or row["user_id"]}** - {row["wallet"] + row["bank"]} {BATYR}'
            for row in data[:limit]
        ]

        embed = ctx.embed(title="The Global Leaderboard", description="\n".join(users))
        await ctx.send(embed=embed)

    @utils.group()
    async def balance(self, ctx: utils.Context) -> None:
        """The moderator-only user balance management command."""
        await ctx.send_help("balance")

    @balance.command(name="add")
    @utils.is_mod()
    async def _add_balance(
        self, ctx: utils.Context, member: discord.Member, amount: int
    ) -> None:
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
            raise exceptions.DefaultError(
                "Balance adding limit has reached. " "Specify between 100 and 100 000."
            )

        member = member or ctx.author
        query = "UPDATE users SET bank = bank + $1 WHERE user_id = $2;"
        await ctx.db.push(query, amount, member.id)
        await ctx.send(f"✅ Successfully added **{amount} {BATYR}** to **{member}**.")

    @balance.command(name="remove")
    @utils.is_mod()
    async def _remove_balance(
        self, ctx: utils.Context, member: discord.Member, amount: int
    ) -> None:
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
        if not 100 <= amount <= 100_000:
            raise exceptions.DefaultError(
                "Balance adding limit has reached. " "Specify between 100 and 100 000."
            )

        query = "UPDATE users SET bank = bank - $1 WHERE user_id = $2;"
        await ctx.db.push(query, amount, member.id)
        await ctx.send(
            f"✅ Successfully removed **{amount} {BATYR}** from **{member}**."
        )

    @utils.command(aliases=("card",))
    async def profile(
        self, ctx: utils.Context, member: Optional[discord.Member]
    ) -> None:
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
            raise exceptions.DefaultError(f"{member} has no profile card.")

        data = copy.copy(data)

        embed = ctx.embed(
            title=f"{member}'s profile card",
            description=data.pop("bio") or "No bio has been set.",
        ).set_thumbnail(url=member.avatar_url)

        embed.add_field(
            name="📊 Statistics",
            value="\n".join(f"• **{k.title()}:** {v}" for k, v in data.items()),
        )

        await ctx.send(embed=embed)

    @utils.command(aliases=("dep",))
    async def deposit(self, ctx: utils.Context, amount: int = None) -> None:
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
        wallet = data.get("wallet")
        amount = amount or wallet

        if amount > wallet or wallet == 0:
            raise exceptions.DefaultError(
                "Transfering amount cannot be higher than your wallet balance"
            )

        query = (
            "UPDATE users SET bank = bank + $1, wallet = wallet - $1 WHERE user_id = $2"
        )

        await ctx.db.push(query, amount, ctx.author.id)
        await ctx.send(f"Successfully transfered **{amount}** {BATYR} into your bank!")

    @utils.command(aliases=("wd",))
    async def withdraw(self, ctx: utils.Context, amount: int = None) -> None:
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
        bank = data.get("bank")
        amount = amount or bank

        if amount > bank or bank == 0:
            raise exceptions.DefaultError(
                "Withdrawing amount cannot be higher than your bank balance."
            )

        query = """
        UPDATE users
        SET bank = bank - $1, wallet = wallet + $1
        WHERE user_id = $2
        """

        await ctx.db.push(query, amount, ctx.author.id)
        await ctx.send(f"Successfully withdrew **{amount}** {BATYR} to your wallet!")

    @utils.command()
    async def transfer(
        self, ctx: utils.Context, member: utils.AuthorCheckConverter, amount: int
    ) -> None:
        """Transfer someone Batyrs whoever they would be.

        Example:
            **{p}transfer @Dosek 1000** - gives Dosek 1000 Batyrs.

        Args:
            member (utils.AuthorCheckConverter): Member you'd like to transfer money to.
            amount (int): Amount of Batyrs to transfer.

        Raises:
            DefaultError: If you have less than 100 batyrs on your balance.
        """
        if (wallet := ctx.user_cache[ctx.author.id]["wallet"]) < 100:
            raise exceptions.DefaultError(
                f"You have nothing to pay (less than 100 {BATYR})"
            )

        if amount > wallet:
            raise exceptions.DefaultError(
                "Unfortunately, you cannot remain in debt. "
                f"(You only have {wallet} {BATYR})."
            )

        if not 10 < amount < 10_000:
            raise exceptions.DefaultError(
                "Too big/small amount was specified. "
                f"It should be between 10 and 10 000 {BATYR}."
            )

        await ctx.db.double("wallet", amount, ctx.author, member)
        await ctx.send(f"Transfered **{amount}** {BATYR} to **{member}**")

    @utils.group()
    async def bio(self, ctx: utils.Context) -> None:
        """
        Set your bio that will be displayed on your profile.
        """
        await ctx.send_help("bio")

    @bio.command(name="set")
    async def _set_bio(self, ctx: utils.Context, *, information: str) -> None:
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

        if (bank := ctx.user_cache[author]["bank"]) < 1000:
            raise exceptions.DefaultError(
                f"Setting bio requires at least 1000 {BATYR} (You have {bank})."
            )

        query = "UPDATE users SET bio = $1, bank = bank - 1000 WHERE user_id = $2;"
        await ctx.db.push(query, information, author)
        await ctx.send("✅ Set your bio successfully.")

    @bio.command(name="disable")
    async def _disable_bio(self, ctx: utils.Context) -> None:
        """Disable bio feature in your profile.

        This is useful when you want just to remove your bio without paying.
        """
        # Avoiding useless database call.
        if not ctx.user_cache[ctx.author.id]["bio"]:
            raise exceptions.DefaultError(
                "You do not currently have bio set, "
                "so there is no point on trying to disable it."
            )

        confirmation = await ctx.confirm(
            "Are you sure? You will not be able to bring back batyrs paid to set your bio."
        )
        if confirmation:
            await ctx.db.push(
                "UPDATE users SET bio = null WHERE user_id = $1;", ctx.author.id
            )
            await ctx.send("✅ Disabled your bio successfully.")

    @utils.command(aliases=("rob",))
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def attack(
        self, ctx: utils.Context, member: utils.AuthorCheckConverter
    ) -> None:
        """Rob someone whoever they would be.

        Remember that this only works when the victim has more than 100 batyrs
        in their wallet. Rob anyone's bank isn't possible.

        There also is a chance that you can **get caught** by the **police**.

        Example:
            **{p}attack @Dosek** - tries to rob Dosek's batyrs.

        Args:
            member (utils.AuthorCheckConverter): The victim you want to rob.

        Raises:
            DefaultError: When a user tries to be funny (rob themself).
            DefaultError: When a victim has not enough batyrs to get robbed.
        """
        if (member_wallet := ctx.user_cache[member.id]["wallet"]) < 100:
            raise exceptions.DefaultError(
                f"{member} had nothing to steal (less than 100 {BATYR})"
            )

        choice = random.choices(
            population=["success", "caught"], weights=(0.5, 0.5), k=1
        )[0]
        if choice == "caught":
            author_bank = ctx.user_cache[ctx.author.id]["bank"]
            fine = author_bank * 0.1
            await ctx.db.double("bank", fine, ctx.author, member)
            return await ctx.reply(
                f"You were caught by police and **{fine}** from your bank "
                f"will be transfered to **{member}** as a fine."
            )

        amount = random.randint(100, member_wallet)
        await ctx.db.double("bank", fine, member, ctx.author)
        await ctx.send(f"✅ Stole **{amount}** {BATYR} from **{member}**")

    @utils.command(aliases=("slots",))
    async def slot(self, ctx: utils.Context, bet: CasinoConverter(50)) -> None:
        """Play the game on a slot machine!

        Example:
            **{p}slot 69** - bets 69 batyrs to play slots.

        Args:
            bet (CasinoConverter(50)): Your bet amount. Minimum is 50 batyrs.

        Raises:
            DefaultError: If bet' amount reaches limits.
        """
        a, b, c = random.choices("🍎🍊🍐🍋🍉🍇🍓🍒", k=3)
        text = f"{a} | {b} | {c}\n{ctx.author.display_name}, "
        query = "UPDATE users SET wallet = wallet + $1 WHERE user_id = $2;"

        if a == b == c:
            result = bet * 20
            await ctx.send(
                f"{text}All match, we have a big winner! 🎉 {result} {BATYR}!"
            )

        elif (a == b) or (a == c) or (b == c):
            result = bet * 2
            await ctx.send(f"{text}2 match, you won! 🎉 {result} {BATYR}!")

        else:
            query = "UPDATE users SET wallet = wallet - $1 WHERE user_id = $2;"
            result = bet
            await ctx.send(f"{text}No matches, I wish you win next time. No batyrs.")

        await ctx.db.push(query, result, ctx.author.id)

    @utils.command()
    async def work(self, ctx: utils.Context) -> None:
        """Working is the most legal way to get batyrs.

        Reverse numbers, guess their lengths, more later.
        """
        await Work(ctx).start()

    @utils.command(aliases=("hnt",))
    @commands.cooldown(1, 60.0, commands.BucketType.user)
    async def headsandtails(self, ctx: utils.Context) -> None:
        """Try your luck playing heads and tails!

        If your choice equals the random one, this means you won.

        Example:
            **{p}headsandtails heads** - I hope it's clear enough.

        Args:
            choice (str): Your choice [heads | tails]
        """
        await ctx.send("Share your choice, you have 10 seconds.")

        def check(msg: discord.Message):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            choice = (
                await ctx.bot.wait_for("message", timeout=10.0, check=check)
            ).content

        except asyncio.TimeoutError:
            return await ctx.send("❌ You took too long.")

        choices = ("heads", "tails")

        if choice not in choices:
            raise exceptions.DefaultError(
                f"Choice {choice} does not exist. " "Choose from: " + ", ".join(choices)
            )

        embed = ctx.embed(title="Flipping the coin...")
        embed.set_image(url="http://www.mathwire.com/images/animatedcoinflip2.gif")

        message = await ctx.send(embed=embed)
        await asyncio.sleep(5.0)

        if choice == (answer := random.choice(choices)):
            query = "UPDATE users SET wallet = wallet + 50 WHERE user_id = $1"
            embed.title = f"You guessed right! ({answer}) → +50 {BATYR}."

            await ctx.db.push(query, ctx.author.id)

        else:
            embed.title = f"Unfortunately, you guessed wrong ({answer})."

        await message.edit(embed=embed)
