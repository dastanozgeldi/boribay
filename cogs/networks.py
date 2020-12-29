import os
import re
from discord.ext import commands, menus
import async_cse
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed
from utils.Paginators import EmbedPageSource
from dotenv import load_dotenv
load_dotenv()

client = async_cse.Search(os.getenv('GOOGLE_KEY'))


class Networks(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🕸 Networks'

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
            embed = Embed(description=f'**{description}**').set_author(name=word, url=source['permalink'], icon_url='https://is4-ssl.mzstatic.com/image/thumb/Purple111/v4/7e/49/85/7e498571-a905-d7dc-26c5-33dcc0dc04a8/source/64x64bb.jpg')
            embed.add_field(name='Example:', value=f"{example}", inline=False)
            embed.add_field(name='Stats:', value=f"**{source['thumbs_up']}👍 | {source['thumbs_down']}👎**", inline=False)
            embed.set_footer(text=f"Written by {js['list'][0]['author']} | {source['written_on'][0:10]}")
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Networks(bot))
