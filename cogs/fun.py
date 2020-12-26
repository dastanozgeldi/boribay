from discord.ext import commands
import random
import asyncio
from utils.CustomEmbed import Embed


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['hi', 'hey'], brief="greeting, nothing else.")
    async def hello(self, ctx):
        await ctx.send(f'Hello there! I am {self.bot.user}, created by {self.bot.dosek}')

    @commands.command(name='rps', brief="the Rock | Paper | Scissors game.")
    async def rockpaperscissors(self, ctx):
        rps_dict = {
            "🪨": {"🪨": "draw", "📄": "lose", "✂": "win"},
            "📄": {"🪨": "win", "📄": "draw", "✂": "lose"},
            "✂": {"🪨": "lose", "📄": "win", "✂": "draw"}
        }
        choice = random.choice([*rps_dict.keys()])
        msg = await ctx.send(embed=Embed(description="**Choose one 👇**").set_footer(text="10 seconds left⏰"))
        for r in rps_dict.keys():
            await msg.add_reaction(r)
        try:
            r, u = await self.bot.wait_for('reaction_add', timeout=10, check=lambda re, us: us == ctx.author and str(re) in rps_dict.keys() and re.message.id == msg.id)
            play = rps_dict.get(str(r.emoji))
            await msg.edit(embed=Embed(description=f'''
                Result: **{play[choice].upper()}**
                My choice: **{choice}**
                Your choice: **{str(r.emoji)}**'''))
        except asyncio.TimeoutError:
            await msg.delete()

    @commands.command(brief="hack someone!")
    async def hack(self, ctx, *, user):
        # data
        logins = [
            'payton228',
            'anal_king',
            'urdream',
            'bedmonster',
            'gay_sensei',
            'AdskiiDrocher69',
            'pronmaster',
            'priemnyi'
        ]
        passwords = [
            '12345678',
            'Fx8Jdsl;a8JdaKlasNduiak4H',
            'iwannatan',
            'saskethebest',
            '1QAZ2WSX',
            'qwertyui',
            '87654321',
            'sakurawhore',
            'tanBirLitr',
            'tsoiNaSamomDeleNeZhiv',
            'vzlomshchikpidoras',
            'pornhubiswonder',
            'putintop',
            'nazarbayevlox',
            'watermelon4ever',
            'loverighthand'
        ]
        network = [
            'Instagram',
            'VK',
            'Steam',
            'Discord',
            'Epic Games',
            'Odnoklassniki.ru',
            'TikTok',
            'Tanki Online',
            'GTA Online Account'
        ]
        # random data
        randlog = random.choice(logins)
        randpas = random.choice(passwords)
        randnet = random.choice(network)
        # beginning
        message = await ctx.send('Process Started')
        await message.edit(content=f'Hacking {user}...')
        await asyncio.sleep(2)
        # getting login
        logins = ['Getting a login', 'Getting a login |', 'Getting a login /', 'Getting a login —', 'Getting a login \\ ', f'Done! Login is: {randlog}']
        for i in logins:
            await message.edit(content=i)
            await asyncio.sleep(1)
        # getting password
        passwords = ['Calculating a password', 'Calculating a password |', 'Calculating a password /', 'Calculating a password —', 'Calculating a password \\', f'Done! Password is {randpas}']
        for x in passwords:
            await asyncio.sleep(1)
            await message.edit(content=x)
        # the end
        await asyncio.sleep(1)
        await message.edit(content=f'The {randnet} data of user {user} are:\nLogin: {randlog}\nPassword: {randpas}')


def setup(bot):
    bot.add_cog(Fun(bot))
