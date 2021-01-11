from io import BytesIO

import discord
from discord.ext.commands import Cog
from PIL import Image, ImageDraw, ImageFont


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
    async def on_command_completion(self, ctx):
        self.bot.command_usage += 1

    @Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 765902232679481394:
            f = await self.welcome_card(member)
            await self.bot.get_channel(789161436499935242).send(file=discord.File(f))


def setup(bot):
    bot.add_cog(Events(bot))
