from discord.ext.commands import command, guild_only
from utils.CustomCog import Cog


class NSFW(Cog, name='Maybe NSFW'):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🔞 Maybe NSFW'

    async def cog_check(self, ctx):
        if ctx.guild:
            return ctx.channel.is_nsfw()

    async def command_creator(self, ctx, topic: str):
        cs = self.bot.session
        r = await cs.get(f'https://nekos.life/api/v2/img/{topic}')
        json = await r.json()
        url = str(json['url'])
        embed = self.bot.embed.default(ctx=ctx, description=f'**[See in browser]({url})**').set_image(url=url)
        return embed

    @command(brief="random waifu image")
    @guild_only()
    async def waifu(self, ctx):
        embed = await self.command_creator(ctx, 'waifu')
        await ctx.send(embed=embed)

    @command(brief="random neko image")
    @guild_only()
    async def neko(self, ctx):
        embed = await self.command_creator(ctx, 'neko')
        await ctx.send(embed=embed)

    @command(brief="random anime wallpaper")
    @guild_only()
    async def wallpaper(self, ctx):
        embed = await self.command_creator(ctx, 'wallpaper')
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(NSFW(bot))
