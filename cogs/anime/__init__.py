from utils.Cog import Cog
from discord.ext.commands import command


class Anime(Cog):
    '''Anime extension. Not anime at all, just had no idea
    how to name it otherways. Slap, anime search, manga and so on.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '✨ Anime'

    async def command_creator(self, ctx, topic: str, description: str):
        async with self.bot.session.get(f'https://nekos.life/api/v2/img/{topic}') as r:
            json = await r.json()
        url = str(json['url'])
        embed = self.bot.embed.default(ctx=ctx, description=f'**[{description}]({url})**')
        embed.set_image(url=url)
        return embed

    @command()
    async def pat(self, ctx):
        """Sends 'pat' image."""
        embed = await self.command_creator(ctx, 'pat', 'See in browser')
        await ctx.send(embed=embed)

    @command()
    async def baka(self, ctx):
        """This baka needs to be punished"""
        embed = await self.command_creator(ctx, 'baka', 'Baka')
        await ctx.send(embed=embed)

    @command()
    async def slap(self, ctx, member: str):
        """**Magikarp slap sounds**"""
        embed = await self.command_creator(ctx, 'slap', f'Slapping {member}')
        await ctx.send(embed=embed)

    @command()
    async def anime(self, ctx, *, anime: str):
        """Anime search command. See some information like rating, episodes
        count etc. of your given anime.
        Args: anime (str): Anime that you specify."""
        anime = anime.replace(' ', '%20')
        async with ctx.typing():
            cs = self.bot.session
            r = await cs.get(f'https://kitsu.io/api/edge/anime?page[limit]=1&page[offset]=0&filter[text]={anime}&include=genres')
            try:
                js = await r.json()
                _id = js['data'][0]['id']
                attributes = js['data'][0]['attributes']
            except (IndexError, KeyError):
                return await ctx.send('Could not find anime that matches your request.')
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
                ('Episodes', f"{attributes['episodeCount']} min", True),
                ('Duration', attributes['episodeLength'], True),
                ('Rank', attributes['ratingRank'], True),
                ('Age Rating', attributes['ageRatingGuide'], True),
                ('Genres', genres, True)
            ]
            embed = self.bot.embed.default(
                ctx,
                title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
                description=attributes['description'],
                url=f'https://kitsu.io/anime/{_id}'
            )
            embed.set_thumbnail(url=attributes['posterImage']['small'])
            for name, value, inline in fields:
                embed.add_field(name=name, value=value or 'Not specified.', inline=inline)
            await ctx.send(embed=embed)

    @command()
    async def manga(self, ctx, *, manga: str):
        """Manga search command. See information like ranking, volume etc.
        of manga that you passed.
        Args: manga (str): A manga that you want to get info of."""
        manga = manga.replace(' ', '%20')
        async with ctx.typing():
            cs = self.bot.session
            r = await cs.get(f'https://kitsu.io/api/edge/manga?page[limit]=1&page[offset]=0&filter[text]={manga}&include=genres')
            try:
                js = await r.json()
                attributes = js['data'][0]['attributes']
                genres_list = []
            except (IndexError, KeyError):
                return await ctx.send('Could not find manga that matches your request.')
            try:
                for i in range(len(js['included'])):
                    genres_list.append(js['included'][i]['attributes']['name'])
                genres = ' • '.join(genres_list)
            except KeyError:
                genres = 'Not specified.'
            fields = [
                ('Status', attributes['status'], True),
                ('Rating', attributes['averageRating'], True),
                ('Aired', f"from **{attributes['startDate']}** to **{attributes['endDate']}**", True),
                ('Chapters', attributes['chapterCount'], True),
                ('Volume', attributes['volumeCount'], True),
                ('Rank', attributes['ratingRank'], True),
                ('Age Rating', attributes['ageRatingGuide'], True),
                ('Genres', genres, True)
            ]
            embed = self.bot.embed.default(
                ctx,
                title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
                description=attributes['description'],
                url=f"https://kitsu.io/manga/{manga}"
            )
            embed.set_thumbnail(url=attributes['posterImage']['small'])
            for name, value, inline in fields:
                embed.add_field(name=name, value=value or 'Not specified.', inline=inline)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Anime(bot))
