from io import BytesIO
import discord
from discord.ext.commands import Cog, command
from PIL import Image, ImageDraw, ImageFont


class Events(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def welcome_card(self, member):
        font = ImageFont.truetype('./data/fonts/arial_bold.ttf', size=20)
        join_text, member_text = (f'{member} just spawned in the server.', f'Member #{member.guild.member_count}')
        (join_w, _), (member_w, _) = font.getsize(join_text), font.getsize(member_text)
        buffer = BytesIO()
        data = BytesIO(await member.avatar_url.read())
        pfp = Image.open(data).resize((263, 263))
        with Image.new('RGB', (600, 400)) as card:
            card.paste(pfp, (170, 32))
            draw = ImageDraw.Draw(card)
            draw.text(((600 - join_w) / 2, 309), join_text, (255, 255, 255), font=font)
            draw.text(((600 - member_w) / 2, 1), member_text, (169, 169, 169), font=font)
            card.save(buffer, 'png', optimize=True)
        buffer.seek(0)
        file = discord.File(buffer, 'welcomer.png')
        return file

    @command()
    async def whalecum(self, ctx):
        f = await self.welcome_card(ctx.author)
        await ctx.send(file=f)

    @Cog.listener()
    async def on_command_completion(self, ctx):
        self.bot.command_usage += 1
        await self.bot.pool.execute('UPDATE bot_stats SET command_usage = command_usage + 1')

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id == 765902232679481394:
            f = await self.welcome_card(member)
            await self.bot.get_channel(789161436499935242).send(file=f)

    @Cog.listener()
    async def on_guild_unavailable(self, guild: discord.Guild):
        await self.bot.get_guild(guild.id).leave()


def setup(bot):
    bot.add_cog(Events(bot))
