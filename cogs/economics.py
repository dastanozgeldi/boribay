import math
from io import BytesIO
from typing import Optional
from utils.CustomEmbed import Embed
from utils.CustomCog import Cog

import discord
from discord.ext.commands import command, has_permissions
from dotenv import load_dotenv

load_dotenv()

"""1. rob command. randomly give robbed money. make random robbing events (its main name called 'attack' related with batyrs topic)."""


class Economics(Cog):
    '''Boribay's Economic Cog.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '💰 Economics'

    @command(
        aliases=['xp'],
        brief="see your experience",
        description="this is powerful command. by typing .rank you can also set a background for your rankcard."
    )
    async def rank(self, ctx, member: Optional[discord.Member], background: Optional[str]):
        member = member or ctx.author
        data = await self.bot.collection.find_one({'_id': member.id})
        username = member.display_name.replace(" ", "+")
        avatar = member.avatar_url_as(format='png')
        nextlevel = 500 + 100 * data['lvl']
        prevlevelxp = math.ceil(data['xp'] / nextlevel * 100)
        isboosting = bool(member.premium_since)
        cs = self.bot.session
        custombg = background or ''
        url = f'https://vacefron.nl/api/rankcard?username={username}&avatar={avatar}?size=1024&level={data["lvl"]}&rank=&currentxp={data["xp"]}&nextlevelxp={nextlevel}&previouslevelxp={prevlevelxp}&custombg={custombg}&isboosting={isboosting}'
        r = await cs.get(url)
        fp = BytesIO(await r.read())
        file = discord.File(fp=fp, filename="bgrankcard.png")
        await ctx.send(file=file)

    @command(
        brief="see leaderboard of the server",
        aliases=['lb']
    )
    async def leaderboard(self, ctx):
        leaderboard = []
        data = self.bot.collection.find().sort('lvl', -1)
        async for i in data:
            if ctx.guild.get_member(i['_id']) is None:
                pass
            else:
                leaderboard.append({"name": f"{ctx.guild.get_member(i['_id']).display_name}", "lvl": f"{i['lvl']}"})

        lb_embed = Embed()
        lb_embed.set_author(name=f"Rank Leaderboard of {ctx.guild.name}", icon_url=ctx.guild.icon_url)

        lb = [f"{e + 1}. {leaderboard[e]['name']} — {leaderboard[e]['lvl']} lvl" for e in range(0, 10)]
        lb_embed.description = '\n'.join(lb)
        await ctx.send(embed=lb_embed)

    @command(
        brief="learn about my currency!"
    )
    async def currency(self, ctx):
        me = await self.bot.collection.find_one({'_id': 735397931355471893})
        await ctx.send(embed=Embed(
            title="Batyrs💂‍♂️",
            description=f"My economy system uses Batyrs💂‍♂️. For example I have **{me['balance']}**💂‍♂️",
        ))

    @command(aliases=['cash'], brief="display user balance")
    async def balance(self, ctx, member: Optional[discord.Member]):
        member = member or ctx.author
        member_data = await self.bot.collection.find_one({'_id': member.id})
        await ctx.send(embed=Embed(
            description=f"User Balance __{member}__: **{member_data['balance']}**")
        )

    @command(
        aliases=['givecash'],
        brief='give some cash to user'
    )
    async def pay(self, ctx, member: discord.Member, amount: int):
        author_data = await self.bot.collection.find_one({'_id': ctx.author.id})
        member_data = await self.bot.collection.find_one({'_id': member.id})
        author_balance = author_data['balance']
        member_balance = member_data['balance']

        if amount <= 0:
            await ctx.send(embed=Embed(description=f"__{ctx.author}__, amount should be more than zero!"))
        else:
            await self.bot.collection.update_one({"_id": ctx.author.id}, {"$set": {"balance": author_balance - amount}})
            await self.bot.collection.update_one({"_id": member.id}, {"$set": {"balance": member_balance + amount}})
            await ctx.message.add_reaction("✅")

    @command(brief="reset user balance (admin)")
    @has_permissions(administrator=True)
    async def resetbalance(self, ctx, member: discord.Member):
        try:
            await self.bot.collection.update_one(
                {"_id": member.id},
                {"$set": {"balance": 0}}
            )
            await ctx.send(f"Successfully reset __{member.name}'s__ balance to **0** Batyrs💂‍♂️")
        except Exception as e:
            await ctx.send(f"Error: {e}")

    @command(brief="add balance to someone (admin)")
    @has_permissions(administrator=True)
    async def addbalance(self, ctx, member: discord.Member, cash: int):
        member_data = self.bot.collection.find_one({'_id': member.id})
        try:
            member_balance = member_data['balance']
            await self.bot.collection.update_one(
                {"_id": member.id},
                {"$set": {"balance": member_balance + cash}}
            )
            await ctx.send(f"Successfully added **{cash}** Batyrs💂‍♂️ to __{member.name}__")
        except Exception as e:
            await ctx.send(f"Error: {e}")


def setup(bot):
    bot.add_cog(Economics(bot))
