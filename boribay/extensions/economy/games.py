import asyncio
import random
from html import unescape

import discord
from discord.ext import commands


class Work:
    def __init__(self, ctx):
        self.ctx = ctx

    async def start(self):
        # Uncomment the stuff below when one more type of job appears :)
        # available = () - include jobs there consequently.
        # job = random.choice(available)
        return await self.digit_length()

    async def _template(self, start_message: str, number: str):
        ctx = self.ctx

        await ctx.send(start_message + "\nYou have 10 seconds.")

        def check(msg: discord.Message):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            message = await ctx.bot.wait_for("message", timeout=10.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("❌ You took too long.")

        try:
            guessed = int(message.content)
        except ValueError:
            return await ctx.send("❌ Seems you did not provide the number.")

        if guessed == number:
            query = "UPDATE users SET wallet = wallet + 100 WHERE user_id = $1;"
            await ctx.bot.pool.execute(query, ctx.author.id)
            await ctx.bot.user_cache.refresh()
            return await ctx.send(
                f"✅ You are right! The number was: {number} → +100 batyrs."
            )

        await ctx.send(
            f"❌ Looks you guessed a wrong number (the actual one is {number}). I wish you win next time."
        )

    async def digit_length(self):
        number = str(random.getrandbits(random.randint(32, 64)))
        await self._template(f"Guess the length of this number: {number}", len(number))


class Trivia:
    def __init__(self, ctx, entries: list = None, title: str = None):
        self.ctx = ctx
        self.entries = entries
        self.title = title

    async def _get_question(self, difficulty: str):
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}"
        r = await self.ctx.bot.session.get(url)
        res = await r.json()

        res = res["results"][0]
        res["question"] = unescape(res["question"])
        res["correct_answer"] = unescape(res["correct_answer"])
        res["incorrect_answers"] = [unescape(x) for x in res["incorrect_answers"]]

        return res

    async def run(self, difficulty: str):
        ctx = self.ctx
        question = await self._get_question(difficulty)
        correct = question["correct_answer"]

        entries = [correct] + question["incorrect_answers"]
        entries = random.sample(entries, len(entries))
        answer = await Trivia(ctx, entries, question["question"]).start()

        if answer == question["correct_answer"]:
            await ctx.reply(f"**Correct! (+50)** The answer was: **{correct}**")
            return await self.ctx.bot.db.add("wallet", ctx.author, 50)

        return await ctx.reply(f"**Wrong!** The answer was: **{correct}**.")

    async def start(self, user: discord.Member = None):
        embed = self.ctx.embed(title=self.title, description="")
        self.emojis = []

        for index, chunk in enumerate(self.entries):
            self.emojis.append(f"{index+1}\u20e3")
            embed.description = f"{embed.description}{self.emojis[index]} {chunk}\n"

        self.embed = embed
        return await self._controller(user)

    async def _controller(self, user: discord.Member):
        base = await self.ctx.send(embed=self.embed)

        for emoji in self.emojis:
            await base.add_reaction(emoji)

        def check(r, u):
            if (
                str(r) not in self.emojis
                or u.id == self.ctx.bot.user.id
                or r.message.id != base.id
            ):
                return False

            if not user:
                if u.id != self.ctx.author.id:
                    return False

            else:
                if u.id != user.id:
                    return False

            return True

        try:
            r, u = await self.ctx.bot.wait_for(
                "reaction_add", check=check, timeout=15.0
            )

        except asyncio.TimeoutError:
            await self.ctx.try_delete(base)
            raise commands.BadArgument("You didn't choose anything.")

        control = self.entries[self.emojis.index(str(r))]

        await self.ctx.try_delete(base)
        return control
