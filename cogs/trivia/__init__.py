import html
import random
from discord.ext import commands
from utils import Paginators


class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def question(self, difficulty: str):
        if difficulty not in ("easy", "medium", "hard"):
            raise ValueError("Invalid difficulty specified.")
        async with self.bot.session.get(f"{self.bot.config['API']['trivia_api']}&difficulty={difficulty}") as r:
            js = await r.json()
        js = js['results'][0]
        js["incorrect_answers"] = [html.unescape(x) for x in js["incorrect_answers"]]
        js["question"] = html.unescape(js["question"])
        js["correct_answer"] = html.unescape(js["correct_answer"])
        return js

    async def answer(self, ctx, q):
        """Takes a question parameter."""
        entr = q["incorrect_answers"] + [q["correct_answer"]]
        entr = random.sample(entr, len(entr))
        ans = await Paginators.Poll(title=q["question"], entries=entr).pagination(ctx)
        return ans == q["correct_answer"]

    @commands.command()
    async def trivia(self, ctx, difficulty: str = "medium"):
        """Trivia game! Has 3 difficulties: `easy`, `medium` and `hard`.
        Args: difficulty (optional): Questions difficulty in the game. Defaults to "easy".
        Returns: A correct answer."""
        try:
            q = await self.question(difficulty.lower())
        except ValueError:
            return await ctx.send("Invalid difficulty specified.")
        # except Exception:
        #    return await ctx.send("Error occurred with getting a question.")
        if await self.answer(ctx, q):
            await ctx.send(f"**{ctx.author}** answered correct.")
        else:
            await ctx.send(f'**{ctx.author}** was a bit wrong\nThe answer is: `{q["correct_answer"]}`.')


def setup(bot):
    bot.add_cog(Trivia(bot))
