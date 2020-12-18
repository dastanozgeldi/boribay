import discord
from discord.ext.commands import command, Cog, is_nsfw
import aiohttp


class Anime(Cog):
    def __init__(self, bot):
        self.bot = bot

    async def command_creator(self, topic: str, description: str):
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f'https://nekos.life/api/v2/img/{topic}') as r:
                json = await r.json()
        await cs.close()
        url = str(json['url'])
        embed = discord.Embed(
            description=f'**[{description}]({url})**',
            color=discord.Color.dark_theme()
        ).set_image(url=url)
        return embed

    @command(brief="random waifu image")
    @is_nsfw()
    async def waifu(self, ctx):
        async with ctx.channel.typing():
            embed = await self.command_creator('waifu', 'See in browser')
            await ctx.send(embed=embed)

    @command(brief="pat")
    async def pat(self, ctx):
        async with ctx.channel.typing():
            embed = await self.command_creator('pat', 'Good gui')
            await ctx.send(embed=embed)

    @command(brief="baka")
    async def baka(self, ctx):
        async with ctx.channel.typing():
            embed = await self.command_creator('baka', 'Baka')
            await ctx.send(embed=embed)

    @command(brief="random neko image")
    @is_nsfw()
    async def neko(self, ctx):
        async with ctx.channel.typing():
            embed = await self.command_creator('neko', 'See in browser')
            await ctx.send(embed=embed)

    @command(brief="random anime wallpaper")
    @is_nsfw()
    async def wallpaper(self, ctx):
        async with ctx.channel.typing():
            embed = await self.command_creator('wallpaper', 'See in browser')
            await ctx.send(embed=embed)

    @command(brief="slap-slap")
    async def slap(self, ctx, member: str):
        async with ctx.channel.typing():
            embed = await self.command_creator('slap', f'Slapping {member}')
            await ctx.send(embed=embed)

    @command(
        name='anime',
        brief='search for some info of anime that you want.'
    )
    async def anime_command(self, ctx, *, anime: str):
        anime = anime.replace(' ', '+')
        async with ctx.channel.typing():
            # Data from API
            async with aiohttp.ClientSession() as cs:
                async with cs.get(f'https://kitsu.io/api/edge/anime?filter[text]={anime}') as r:
                    js = await r.json()
                _id = js['data'][0]['id']
                async with cs.get(f'https://kitsu.io/api/edge/anime/{_id}/genres') as g:
                    gs = await g.json()
            await cs.close()
            attributes = js['data'][0]['attributes']
            # Collecting Genres List
            genres_list = []
            for i in range(0, len(gs['data'])):
                genres_list.append(gs['data'][i]['attributes']['name'])
            fields = [
                ('Type', f"{js['data'][0]['type']} | {attributes['status']}", True),
                ('Rating', f"{attributes['averageRating']}/100⭐", True),
                ('Aired', f"from **{attributes['startDate']}** to **{attributes['endDate']}**", True),
                ('NSFW', attributes['nsfw'], True),
                ('Episodes', attributes['episodeCount'], True),
                ('Duration', attributes['episodeLength'], True),
                ('Rank', attributes['ratingRank'], True),
                ('Age Rating', attributes['ageRatingGuide'], True),
                ('Genres', 'Not specified.' if not genres_list else ' • '.join(genres_list), True)
            ]
            embed = discord.Embed(
                title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
                # title=anime.replace('+', ' ').title(),
                description=attributes['description'],
                color=discord.Color.dark_theme(),
                url=f'https://kitsu.io/anime/{_id}'
            ).set_thumbnail(url=attributes['posterImage']['small'])
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await ctx.send(embed=embed)

    '''
    @command(brief="manga find command", description="get information about manga that you want!")
    async def manga(self, ctx, *, manga: str):
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as cs:
                async with cs.get(f'https://kitsu.io/api/edge/manga?filter[text]={manga}') as r:
                    try:
                        manga = manga.replace(" ", "+")
                        # creating json file and getting data
                        js = await r.json()
                        # the data of anime
                        attributes = js['data'][0]['attributes']
                        title = attributes['titles']
                        en_title = title['en_jp']
                        ja_title = title['ja_jp']
                        thumbnail = attributes['posterImage']['small']
                        description = attributes['description']
                        # rating
                        avg_rating = attributes['averageRating']
                        # start — end field
                        from_date = attributes['startDate']
                        end_date = attributes['endDate']
                        # type field
                        manga_type = js['data'][0]['type']
                        status = attributes['status']
                        chapters = attributes['chapterCount']
                        volume = attributes['volumeCount']
                        rank = attributes['ratingRank']
                        # fields
                        fields = [("Rating📊", avg_rating, True),
                                  ("Chapters🎫", chapters, True),
                                  ("Volume⏲", f"{volume}📖", True),
                                  ("Rank🎊", rank, True)]

                        manga_link = f"https://kitsu.io/manga/{manga}"

                        # embed including data
                        manga_embed = discord.Embed(title=f"{en_title} ({ja_title})", description=description[0:1500], color=0x68BAF1, url=manga_link)
                        manga_embed.add_field(name="Type | Status📺", value=f"{manga_type} | {status}")
                        manga_embed.add_field(name="Start | End🐧", value=f"{from_date}\n{end_date}")
                        for name, value, inline in fields:
                            manga_embed.add_field(name=name, value=value if value is not None else '\u200b', inline=inline)

                        manga_embed.set_thumbnail(url=thumbnail)
                        manga_embed.set_footer(text=f"Requested by: {ctx.author.name}", icon_url=ctx.author.avatar_url)
                        await ctx.send(embed=manga_embed)

                    except Exception as e:
                        await ctx.send(f"Error: {e}")
    '''


def setup(bot):
    bot.add_cog(Anime(bot))
