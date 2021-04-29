import asyncio
import random

import discord
from boribay.core import Context


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
