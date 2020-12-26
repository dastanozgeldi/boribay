import os
import re
import praw
import random
from discord.ext import commands, menus
import async_cse
from utils.CustomEmbed import Embed
from utils.EmbedPagination import EmbedPageSource
from dotenv import load_dotenv
load_dotenv()

client = async_cse.Search(os.getenv('GOOGLE_KEY'))

reddit = praw.Reddit(
    client_id=os.getenv('client_id'),
    client_secret=os.getenv('client_secret'),
    username=os.getenv('username'),
    user_agent=os.getenv('user_agent')
)


class Networks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['g'], brief="google outside google.")
    async def google(self, ctx, *, query: str):
        '''Paginated embed-google-search command.'''
        if ctx.channel.is_nsfw():
            safesearch = False
        else:
            safesearch = True
        query = query.replace(" ", "+")
        results = await client.search(query, safesearch=safesearch)
        embed_list = []
        for i in range(0, 10 if len(results) >= 10 else len(results)):
            embed = Embed(
                title=results[i].title,
                description=results[i].description,
                url=results[i].url
            ).set_thumbnail(url=results[i].image_url).set_author(name=f'Page {i + 1} of {10 if len(results) >= 10 else len(results)}', icon_url=ctx.author.avatar_url)
            embed_list.append(embed)
        menu = menus.MenuPages(EmbedPageSource(embed_list), delete_message_after=True)
        await menu.start(ctx)

    @commands.command(aliases=['yt'], brief="search from youtube, but in discord")
    async def youtube(self, ctx, *, search):
        BASE = "https://youtube.com/results"
        p = {"search_query": search}
        h = {"User-Agent": "Mozilla/5.0"}
        cs = self.bot.session
        r = await cs.get(BASE, params=p, headers=h)
        dom = await r.text()
        found = re.findall(r"watch\?v=(\S{11})", dom)
        return await ctx.send(f"https://youtu.be/{found[0]}")

    @commands.command(aliases=['ud'], brief="abbreviature definition", description="with this command you can learn the definitions of words like: ASAP")
    async def urban(self, ctx, *, word):
        async with ctx.channel.typing():
            cs = self.bot.session
            r = await cs.get(f'http://api.urbandictionary.com/v0/define?term={word}')
            js = await r.json()
            source = js['list'][0]
            description = source['definition'].replace('[', '').replace(']', '')
            example = js['list'][0]['example'].replace('[', '').replace(']', '')
            embed = Embed(
                title=f'Explanation for {word}',
                url=source['permalink'],
                description=f'**{description}**'
            ).set_thumbnail(url='https://slack-files2.s3-us-west-2.amazonaws.com/avatars/2018-01-11/297387706245_85899a44216ce1604c93_512.jpg')
            embed.add_field(name='Example🤓', value=f"{example}", inline=False)
            embed.add_field(name='Stats📈', value=f"**{source['thumbs_up']}👍 | {source['thumbs_down']}👎**", inline=False)
            embed.set_footer(text=f"Written by {js['list'][0]['author']} | {source['written_on'][0:10]}", icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(brief='find post from subreddit you want to.')
    @commands.is_nsfw()
    async def reddit(self, ctx, subreddit: str):
        try:
            async with ctx.channel.typing():
                subreddit = reddit.subreddit(subreddit)
                all_subs = []
                hot = subreddit.hot(limit=50)
                for submission in hot:
                    all_subs.append(submission)
                random_sub = random.choice(all_subs)
                embed = Embed(
                    title=random_sub.title,
                    url=random_sub.url
                ).set_footer(
                    text=f'{ctx.author.display_name} | From r/{subreddit}', icon_url=ctx.author.avatar_url
                ).set_image(url=random_sub.url)
                await ctx.send(embed=embed)
        except:
            await ctx.send(f'Could not find subreddit **{subreddit}**')


def setup(bot):
    bot.add_cog(Networks(bot))
