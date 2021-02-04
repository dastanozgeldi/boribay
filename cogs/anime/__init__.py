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
        cs = self.bot.session
        r = await cs.get(f'{ctx.bot.config["API"]["anime_api"]}/anime?page[limit]=1&page[offset]=0&filter[text]={anime}&include=genres')
        js = await r.json()
        attributes = js['data'][0]['attributes']
        try:
            rl = js['included']
            rl = ' • '.join([rl[i]['attributes']['name'] for i in range(len(rl))])
        except KeyError:
            rl = 'No genres specified.'
        fields = [
            ('Rank', attributes['ratingRank']),
            ('Rating', f"{attributes['averageRating']}/100⭐"),
            ('Status', attributes['status']),
            ('Started', attributes['startDate']),
            ('Ended', attributes['endDate']),
            ('Episodes', str(attributes['episodeCount'])),
            ('Duration', f"{attributes['episodeLength']} min"),
            ('Age Rate', attributes['ageRatingGuide']),
            ('Genres', rl)
        ]
        embed = self.bot.embed.default(
            ctx,
            title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
            url=f"https://kitsu.io/anime/{js['data'][0]['id']}"
        ).set_thumbnail(url=attributes['posterImage']['small'])
        embed.add_field(name='Statistics', value='\n'.join([f'**{name}:** {value}' for name, value in fields]))
        embed.add_field(name='Description', value=attributes['description'][:300] + '...')
        await ctx.send(embed=embed)

    @command()
    async def manga(self, ctx, *, manga: str):
        """Manga search command. See information like ranking, volume etc.
        of manga that you passed.
        Args: manga (str): A manga that you want to get info of."""
        manga = manga.replace(' ', '%20')
        cs = self.bot.session
        r = await cs.get(f'{ctx.bot.config["API"]["anime_api"]}/manga?page[limit]=1&page[offset]=0&filter[text]={manga}&include=genres')
        js = await r.json()
        attributes = js['data'][0]['attributes']
        try:
            rl = js['included']
            rl = ' • '.join([rl[i]['attributes']['name'] for i in range(len(rl))])
        except KeyError:
            rl = 'No genres specified.'
        fields = [
            ('Rank', attributes['ratingRank']),
            ('Rating', f"{attributes['averageRating']}/100⭐"),
            ('Status', attributes['status']),
            ('Started', attributes['startDate']),
            ('Ended', attributes['endDate']),
            ('Chapters', attributes['chapterCount']),
            ('Volume', attributes['volumeCount']),
            ('Age Rate', attributes['ageRatingGuide']),
            ('Genres', rl)
        ]
        embed = self.bot.embed.default(
            ctx,
            title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
            url=f'https://kitsu.io/manga/{manga}'
        ).set_thumbnail(url=attributes['posterImage']['small'])
        embed.add_field(name='Statistics', value='\n'.join([f'**{name}:** {value}' for name, value in fields]))
        embed.add_field(name='Description', value=attributes['description'][:300] + '...')
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Anime(bot))
