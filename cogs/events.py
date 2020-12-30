import random
from io import BytesIO

import discord
from discord.ext.commands import Cog
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()


class Events(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def welcome_card(self, member):
        arial_font = ImageFont.truetype('./data/fonts/arial_bold.ttf', size=20)
        monoid_font = ImageFont.truetype('./data/fonts/monoid.ttf', size=20)
        join_text = f'{member} just joined the server.'
        member_text = f'Member #{len(member.guild.members)}'
        join_w, join_h = arial_font.getsize(join_text)
        member_w, member_h = monoid_font.getsize(member_text)

        author_data = BytesIO(await member.avatar_url.read())
        author_pfp = Image.open(author_data)
        author_pfp = author_pfp.resize((263, 263))
        card = Image.open('./data/assets/welcomer.jpg')
        card.paste(author_pfp, (170, 32))
        draw = ImageDraw.Draw(card)
        draw.text(((600 - join_w) / 2, 309), join_text, (255, 255, 255), font=arial_font)
        draw.text(((600 - member_w) / 2, 1), member_text, (169, 169, 169), font=monoid_font)
        card.save('./data/images/welcomer.png')
        file = './data/images/welcomer.png'
        return file

    @Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            pass
        if message.guild:
            if message.guild.id == 735186558830772286:
                user = message.author
                data = await self.bot.collection.find_one({"_id": user.id})

                if data["xp"] >= 500 + 100 * data["lvl"]:
                    await self.bot.collection.update_one(
                        {"_id": user.id},
                        {"$set": {"lvl": data["lvl"] + 1}}
                    )
                    await self.bot.collection.update_one(
                        {"_id": user.id},
                        {"$set": {"xp": 0}}
                    )
                    random_cash = random.randint(50, 200)

                    author = await self.bot.collection.find_one({'_id': message.author.id})
                    author_balance = author['balance']
                    await self.bot.collection.update_one(
                        {"_id": message.author.id},
                        {"$set": {"balance": author_balance + random_cash}}
                    )
                    await message.channel.send(f'''{user.mention} level up! Check your rank by typing `.rank @mention`\nAlso I give you {random_cash} Batyrs💂‍♂️. Have a good day!''')

                else:
                    await self.bot.collection.update_one(
                        {"_id": user.id},
                        {"$set": {"xp": data["xp"] + random.randint(1, 10)}}
                    )

    @Cog.listener()
    async def on_command(self, ctx):
        todo_post = {
            "_id": ctx.author.id,
            "todo": ["nothing yet."]
        }
        if await self.bot.todos.count_documents({"_id": ctx.author.id}) == 0:
            await self.bot.todos.insert_one(todo_post)

        if str(ctx.command).startswith('rank'):
            post = {
                "_id": ctx.author.id,
                "guild_id": ctx.guild.id,
                "balance": 300,
                "xp": 0,
                "lvl": 1
            }
            if await self.bot.collection.count_documents({"_id": ctx.author.id}) == 0:
                await self.bot.collection.insert_one(post)

    @Cog.listener()
    async def on_guild_join(self, guild):
        post = {"_id": guild.id, "prefix": "."}
        if await self.bot.prefixes.count_documents({"_id": guild.id}) == 0:
            await self.bot.prefixes.insert_one(post)

    @Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.prefixes.delete_one({'_id': guild.id})

    @Cog.listener()
    async def on_member_join(self, member):
        post = {
            '_id': member.id,
            'balance': 300,
            'xp': 0,
            'lvl': 1
        }
        if await self.bot.collection.count_documents({'_id': member.id}) == 0:
            await self.bot.collection.insert_one(post)

        if member.guild.id == 765902232679481394:
            f = await self.welcome_card(member)
            await self.bot.get_channel(789161436499935242).send(file=discord.File(f))

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.collection.delete_one({'_id': member.id})


def setup(bot):
    bot.add_cog(Events(bot))
