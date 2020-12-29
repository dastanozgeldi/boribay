from utils.CustomCog import Cog
from utils.CustomEmbed import Embed
from discord.ext.commands import command


class Anime(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = '✨ Anime'

    async def command_creator(self, ctx, topic: str, description: str):
        cs = self.bot.session
        r = await cs.get(f'https://nekos.life/api/v2/img/{topic}')
        json = await r.json()
        url = str(json['url'])
        embed = Embed.default(ctx=ctx, description=f'**[{description}]({url})**').set_image(url=url)
        return embed

    @command(brief="pat")
    async def pat(self, ctx):
        embed = await self.command_creator(ctx, 'pat', 'See in browser')
        await ctx.send(embed=embed)

    @command(brief="baka")
    async def baka(self, ctx):
        embed = await self.command_creator(ctx, 'baka', 'Baka')
        await ctx.send(embed=embed)

    @command(brief="slap-slap")
    async def slap(self, ctx, member: str):
        embed = await self.command_creator(ctx, 'slap', f'Slapping {member}')
        await ctx.send(embed=embed)

    @command(brief='search for some info of anime that you want.')
    async def anime(self, ctx, *, anime: str):
        anime = anime.replace(' ', '%20')
        async with ctx.channel.typing():
            # Data from API
            cs = self.bot.session
            r = await cs.get(f'https://kitsu.io/api/edge/anime?page[limit]=1&page[offset]=0&filter[text]={anime}&include=genres')
            js = await r.json()
            _id = js['data'][0]['id']
            attributes = js['data'][0]['attributes']
            genres_list = []
            try:
                for i in range(len(js['included'])):
                    genres_list.append(js['included'][i]['attributes']['name'])
                genres = ' • '.join(genres_list)
            except KeyError:
                genres = 'Not specified.'
            fields = [
                ('Status', attributes['status'], True),
                ('Rating', f"{attributes['averageRating']}/100⭐", True),
                ('Aired', f"from **{attributes['startDate']}** to **{attributes['endDate']}**", True),
                ('NSFW', str(attributes['nsfw']), True),
                ('Episodes', attributes['episodeCount'], True),
                ('Duration', attributes['episodeLength'], True),
                ('Rank', attributes['ratingRank'], True),
                ('Age Rating', attributes['ageRatingGuide'], True),
                ('Genres', genres, True)
            ]
            embed = Embed(
                title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
                description=attributes['description'],
                url=f'https://kitsu.io/anime/{_id}'
            ).set_thumbnail(url=attributes['posterImage']['small'])
            for name, value, inline in fields:
                embed.add_field(name=name, value=value or 'Not specified.', inline=inline)
            await ctx.send(embed=embed)

    @command(brief="manga find command")
    async def manga(self, ctx, *, manga: str):
        async with ctx.channel.typing():
            cs = self.bot.session
            r = await cs.get(f'https://kitsu.io/api/edge/manga?page[limit]=1&page[offset]=0&filter[text]={manga}&include=genres')
            try:
                manga = manga.replace(" ", "%20")
                js = await r.json()
                attributes = js['data'][0]['attributes']
                description = attributes['description']
                genres_list = []
                try:
                    for i in range(len(js['included'])):
                        genres_list.append(js['included'][i]['attributes']['name'])
                    genres = ' • '.join(genres_list)
                except KeyError:
                    genres = 'Not specified.'
                fields = [
                    ("Status", attributes['status'], True),
                    ("Rating", attributes['averageRating'], True),
                    ("Aired", f"from **{attributes['startDate']}** to **{attributes['endDate']}**", True),
                    ("Chapters", attributes['chapterCount'], True),
                    ("Volume", attributes['volumeCount'], True),
                    ("Rank", attributes['ratingRank'], True),
                    ("Age Rating", attributes['ageRatingGuide'], True),
                    ("Genres", genres, True)
                ]
                embed = Embed(
                    title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
                    description=description[0:1500],
                    url=f"https://kitsu.io/manga/{manga}"
                ).set_thumbnail(url=attributes['posterImage']['small'])
                for name, value, inline in fields:
                    embed.add_field(name=name, value=value or 'Not specified.', inline=inline)
                await ctx.send(embed=embed)

            except Exception as e:
                await ctx.send(f"Error: {e}")


def setup(bot):
    bot.add_cog(Anime(bot))
