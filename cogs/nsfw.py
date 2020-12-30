import os
import praw
import random
from dotenv import load_dotenv
from discord.ext.commands import command
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed
load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('client_id'),
    client_secret=os.getenv('client_secret'),
    username=os.getenv('username'),
    user_agent=os.getenv('user_agent')
)


class NSFW(Cog, name='Maybe NSFW'):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🔞 Maybe NSFW'

    async def cog_check(self, ctx):
        return ctx.channel.is_nsfw()

    async def command_creator(self, ctx, topic: str):
        cs = self.bot.session
        r = await cs.get(f'https://nekos.life/api/v2/img/{topic}')
        json = await r.json()
        url = str(json['url'])
        embed = Embed.default(ctx=ctx, description=f'**[See in browser]({url})**').set_image(url=url)
        return embed

    @command(brief='find post from subreddit you want to.')
    async def reddit(self, ctx, subreddit: str):
        async with ctx.typing():
            subreddit = reddit.subreddit(subreddit)
            all_subs = []
            hot = subreddit.hot(limit=50)
            for submission in hot:
                all_subs.append(submission)
            random_sub = random.choice(all_subs)
            embed = Embed(
                title=random_sub.title,
                url=random_sub.url
            ).set_author(
                name=f'{ctx.author.display_name} | From r/{subreddit}', icon_url=ctx.author.avatar_url_as(size=128)
            ).set_image(url=random_sub.url)
            await ctx.send(embed=embed)

    @command(brief="random waifu image")
    async def waifu(self, ctx):
        embed = await self.command_creator(ctx, 'waifu')
        await ctx.send(embed=embed)

    @command(brief="random neko image")
    async def neko(self, ctx):
        embed = await self.command_creator(ctx, 'neko')
        await ctx.send(embed=embed)

    @command(brief="random anime wallpaper")
    async def wallpaper(self, ctx):
        embed = await self.command_creator(ctx, 'wallpaper')
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(NSFW(bot))
