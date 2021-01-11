import re
import random
from discord.ext import commands, menus
import async_cse
from utils.CustomCog import Cog
from utils.Paginators import EmbedPageSource


class Networks(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🕸 Networks'

    @commands.command(aliases=['g'])
    async def google(self, ctx, *, query: str):
        '''Paginated embed-google-search command.'''
        cse = async_cse.Search(self.bot.config['API']['google_key'])
        safesearch = False if ctx.channel.is_nsfw() else True
        results = await cse.search(query, safesearch=safesearch)
        embed_list = []
        for i in range(0, 10 if len(results) >= 10 else len(results)):
            embed = self.bot.embed(
                title=results[i].title,
                description=results[i].description,
                url=results[i].url
            ).set_thumbnail(url=results[i].image_url).set_author(
                name=f'Page {i + 1} of {10 if len(results) >= 10 else len(results)}',
                icon_url=ctx.author.avatar_url
            )
            embed_list.append(embed)
        await cse.close()
        menu = menus.MenuPages(EmbedPageSource(embed_list), delete_message_after=True)
        await menu.start(ctx)

    @commands.command()
    async def reddit(self, ctx, subreddit: str):
        """Find a randomized post from subreddit that you want to."""
        cs = self.bot.session
        r = await cs.get(f'https://www.reddit.com/r/{subreddit}/hot.json')
        r = await r.json()
        data = r['data']['children'][random.randint(0, 10)]['data']
        if not ctx.channel.is_nsfw() and data['over_18'] is True:
            raise commands.NSFWChannelRequired(ctx.channel)
        embed = self.bot.embed().set_image(url=data['url'])
        embed.set_author(name=data['title'], icon_url='https://icons.iconarchive.com/icons/papirus-team/papirus-apps/96/reddit-icon.png')
        embed.set_footer(text=f'from {data["subreddit_name_prefixed"]}')
        await ctx.send(embed=embed)

    @commands.command(aliases=['yt'])
    async def youtube(self, ctx, *, search):
        """Search from YouTube through Discord."""
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
            r = await cs.get(f'{self.bot.config["API"]["ud_api"]}?term={word}')
            js = await r.json()
            source = js['list'][0]
            description = source['definition'].replace('[', '').replace(']', '')
            example = js['list'][0]['example'].replace('[', '').replace(']', '')
            embed = self.bot.embed(
                description=f'**{description}**'
            ).set_author(
                name=word,
                url=source['permalink'],
                icon_url='https://is4-ssl.mzstatic.com/image/thumb/Purple111/v4/7e/49/85/7e498571-a905-d7dc-26c5-33dcc0dc04a8/source/64x64bb.jpg'
            )
            embed.add_field(name='Example:', value=f"{example}", inline=False)
            embed.add_field(name='Stats:', value=f"**{source['thumbs_up']}👍 | {source['thumbs_down']}👎**", inline=False)
            embed.set_footer(text=f"Written by {js['list'][0]['author']} | {source['written_on'][0:10]}")
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Networks(bot))
