import decimal
import random
import re
import zipfile
from contextlib import suppress
from datetime import datetime
from io import BytesIO
from textwrap import wrap
from typing import Optional

import aiowiki
import discord
from async_cse import NoResults
from discord.ext import commands, flags
from humanize import time
from utils import (CalcLexer, CalcParser, Cog, ColorConverter, EmbedPageSource,
                   Manip, MyPages, TodoPageSource, exceptions, has_voted)


class Useful(Cog, command_attrs={'cooldown': commands.Cooldown(1, 5, commands.BucketType.user)}):
    """Useful commands extension. Simply made to help people in some kind of
    specific situations, such as solving math expression, finding lyrics
    of the song and so on."""
    icon = '<:pickaxe:807534625785380904>'
    name = 'Useful'

    @commands.command()
    @has_voted()
    @commands.cooldown(1, 60.0, commands.BucketType.guild)
    async def zipemojis(self, ctx, guild: Optional[discord.Guild]):
        """Zip All Emojis.
        Args: guild: The guild you want to grab emojis from."""
        guild = guild or ctx.guild
        buffer = BytesIO()

        async with ctx.typing():
            with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                for emoji in guild.emojis:
                    bts = await emoji.url.read()
                    f.writestr(f'{emoji.name}.{"gif" if emoji.animated else "png"}', bts)
            buffer.seek(0)

        await ctx.reply('Sorry for being slow as hell but anyways:', file=discord.File(buffer, filename='emojis.zip'))

    @commands.command()
    async def password(self, ctx, length: int = 25):
        """A Password creator command.
        Args: length (optional): Length of characters. Defaults to 25.
        Raises: BadArgument: Too big length of the password was given."""
        if length > 50:
            raise commands.BadArgument(f'Too big length was given ({length}) while the limit is 50 characters.')

        else:
            asset = random.choices(open('data/chars.txt', 'r').read(), k=length)
            await ctx.author.send(''.join(char for char in asset))
            await ctx.message.add_reaction('✅')

    @commands.command(aliases=['wiki'])
    async def wikipedia(self, ctx, language: str, *, topic: str):
        """Wikipedia Search Command.
        Args: topic: The Wikipedia topic you want to search for."""
        self.wikipedia = aiowiki.Wiki.wikipedia(language, session=ctx.bot.session)

        try:
            page = (await self.wikipedia.opensearch(topic))[0]
            text = await page.summary()

        except (aiowiki.exceptions.PageNotFound, IndexError):
            return await ctx.send('No wikipedia article found, sorry.')

        if not text:
            return await ctx.send('Article summary gave no results on call.')

        wrapped = wrap(text, 1000, drop_whitespace=False, replace_whitespace=False)
        embed_list = []

        for description in wrapped:
            embed = ctx.bot.embed.default(ctx, title=page.title, description=description).set_thumbnail(url=(await page.media())[0])
            embed_list.append(embed)

        await MyPages(EmbedPageSource(embed_list)).start(ctx)

    @commands.command()
    async def anime(self, ctx, *, anime: str):
        """Anime search command. See some information like rating, episodes
        count etc. of your given anime.
        Args: anime (str): Anime that you specify."""
        anime = anime.replace(' ', '%20')
        r = await ctx.bot.session.get(f'{ctx.bot.config["API"]["anime_api"]}/anime?page[limit]=1&page[offset]=0&filter[text]={anime}&include=genres')
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
        title = attributes['titles']['en_jp']
        embed = ctx.bot.embed.default(
            ctx,
            title=f"{title} ({attributes['titles']['ja_jp']})",
            description='[**Watch now!**](https://4anime.to/{})'.format('-'.join(w.lower() for w in title.split())),
            url=f"https://kitsu.io/anime/{js['data'][0]['id']}"
        ).set_thumbnail(url=attributes['posterImage']['small'])

        embed.add_field(name='Statistics', value='\n'.join(f'**{name}:** {value}' for name, value in fields))
        embed.add_field(name='Description', value=attributes['description'][:300] + '...')

        await ctx.send(embed=embed)

    @commands.command()
    async def manga(self, ctx, *, manga: str):
        """Manga search command. See information like ranking, volume etc.
        of manga that you passed.
        Args: manga (str): A manga that you want to get info of."""
        manga = manga.replace(' ', '%20')
        r = await ctx.bot.session.get(f'{ctx.bot.config["API"]["anime_api"]}/manga?page[limit]=1&page[offset]=0&filter[text]={manga}&include=genres')
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

        embed = ctx.bot.embed.default(
            ctx,
            title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
            url=f'https://kitsu.io/manga/{manga}'
        ).set_thumbnail(url=attributes['posterImage']['small'])
        embed.add_field(name='Statistics', value='\n'.join([f'**{name}:** {value}' for name, value in fields]))
        embed.add_field(name='Description', value=attributes['description'][:300] + '...')
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=['to-do'])
    async def todo(self, ctx):
        """Todo commands parent.
        It just sends the help for its subcommands.
        Call for this command to learn how to use to-do commands."""
        await ctx.send_help('todo')

    @flags.add_flag('--count', action='store_true', help='Sends the count of todos.')
    @flags.add_flag('--dm', action='store_true', help='Figures out whether to DM todo list or send in a current channel.')
    @todo.command(cls=flags.FlagCommand, aliases=['list'])
    async def show(self, ctx, **flags):
        """To-Do show command, a visual way to manipulate with your list.
        Args: number (Optional): Index of to-do you want to see."""
        query = 'SELECT content, jump_url FROM todos WHERE user_id = $1 ORDER BY added_at'
        todos = [(todo['content'], todo['jump_url']) for todo in await ctx.bot.pool.fetch(query, ctx.author.id)]
        dest = ctx.author if flags.pop('dm', False) else ctx

        if flags.pop('count', False):
            return await dest.send(len(todos))

        await MyPages(
            TodoPageSource(ctx, todos), clear_reactions_after=True, timeout=60.0,
        ).start(ctx, channel=dest)

    @todo.command(aliases=['append'])
    async def add(self, ctx, *, content: str):
        """Add anything you think you have to-do to your list.
        Args: content: Basically a message which will be added to the list."""
        query = 'INSERT INTO todos(user_id, content, added_at, jump_url) VALUES($1, $2, $3, $4)'
        await ctx.bot.pool.execute(query, ctx.author.id, content, datetime.utcnow(), ctx.message.jump_url)
        await ctx.message.add_reaction('✅')

    @todo.command(aliases=['rm', 'delete'])
    async def remove(self, ctx, numbers: commands.Greedy[int]):
        """Remove done to-do's from your list. Multiple numbers may be specified.
        Args: numbers: Number or range of numbers of to-do's you want to delete."""
        query = '''WITH enumerated AS (SELECT todos.content, row_number() OVER (ORDER BY added_at ASC) AS count FROM todos WHERE user_id = $1)
        DELETE FROM todos WHERE user_id = $1 AND content IN (SELECT enumerated.content FROM enumerated WHERE enumerated.count=ANY($2::bigint[]))
        RETURNING content'''
        await ctx.bot.pool.fetch(query, ctx.author.id, numbers)
        await ctx.message.add_reaction('✅')

    @todo.command(aliases=['stats'])
    async def info(self, ctx, number: int):
        """Shows information about specific to-do.
        Args: number (int): Index of todo you are looking for info about."""
        query = '''WITH enumerated AS (SELECT todos.content, todos.added_at, todos.jump_url, row_number()
        OVER (ORDER BY added_at ASC) as count FROM todos WHERE user_id = $1)
        SELECT * FROM enumerated WHERE enumerated.count = $2'''
        row = await ctx.bot.pool.fetchrow(query, ctx.author.id, number)

        values = [
            ('Added', f'{time.naturaltime(row["added_at"])} by UTC'),
            ('Jump URL', f'[click here]({row["jump_url"]})')
        ]

        embed = ctx.bot.embed.default(
            ctx, title=f'Todo #{number}', description=row['content']
        ).add_field(name='Additional Information', value='\n'.join(f'{n}: **{v}**' for n, v in values))

        await ctx.send(embed=embed)

    @todo.command(aliases=['reset'])
    async def clear(self, ctx):
        """Clear your to-do list up."""
        query = 'DELETE FROM todos WHERE user_id = $1'
        confirmation = await ctx.confirm('Are you sure? All to-do\'s will be dropped.')

        if confirmation:
            await ctx.bot.pool.execute(query, ctx.author.id)
            return await ctx.message.add_reaction('✅')

        await ctx.send('The `todo clear` session was closed.')

    @commands.command(aliases=['g'])
    async def google(self, ctx, *, query: str):
        """Paginated Google-Search command.
        Args: query (str): Your search request. Results will be displayed,
        otherwise returns an error which means no results found."""
        safesearch = False if ctx.channel.is_nsfw() else True

        try:
            results = await ctx.bot.cse.search(query, safesearch=safesearch)

        except NoResults:
            raise commands.BadArgument(f'Your query `{query}` returned no results.')

        embed_list = []
        for i in range(0, 10 if len(results) >= 10 else len(results)):
            embed = ctx.bot.embed.default(
                ctx, title=results[i].title,
                description=results[i].description,
                url=results[i].url
            ).set_thumbnail(url=results[i].image_url)
            embed.set_author(
                name=f'Page {i + 1} / {10 if len(results) >= 10 else len(results)}',
                icon_url=ctx.author.avatar_url
            )
            embed_list.append(embed)

        await MyPages(EmbedPageSource(embed_list), delete_message_after=True).start(ctx)

    @commands.command()
    async def poll(self, ctx, question, *options):
        """Make a simple poll using this command. You can also add an image.
        Args: question (str): Title of the poll.
        options (str): Maximum is 10. separate each option by quotation marks."""
        if len(options) > 10:
            raise exceptions.TooManyOptions('There were too many options to create a poll.')

        elif len(options) < 2:
            raise exceptions.NotEnoughOptions('There were not enough options to create a poll.')

        elif len(options) == 2 and options[0].lower() == 'yes' and options[1].lower() == 'no':
            reactions = ['<:thumbs_up:746352051717406740>', '<:thumbs_down:746352095510265881>']

        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        description = '\n'.join(f'{reactions[x]} {option}' for x, option in enumerate(options))
        embed = ctx.bot.embed.default(ctx, title=question.replace('\n', ''), description=description)

        if ctx.message.attachments:
            embed.set_image(url=ctx.message.attachments[0].url)

        message = await ctx.send(embed=embed)

        for emoji in reactions[:len(options)]:
            await message.add_reaction(emoji)

        with suppress(discord.Forbidden):
            await ctx.message.delete()

    @commands.command(aliases=['r'])
    @has_voted()
    async def reddit(self, ctx, subreddit: str):
        """Find a randomized post from subreddit that you want to."""
        try:
            r = await ctx.bot.session.get(f'https://www.reddit.com/r/{subreddit}/hot.json')
            r = await r.json()
            data = r['data']['children'][random.randint(0, 10)]['data']

        except IndexError:
            raise commands.BadArgument(f'There is no subreddit called **{subreddit}**.')

        if not ctx.channel.is_nsfw() and data['over_18'] is True:
            raise commands.NSFWChannelRequired(ctx.channel)

        embed = ctx.bot.embed.default(ctx).set_image(url=data['url'])

        embed.set_author(name=data['title'], icon_url='https://icons.iconarchive.com/icons/papirus-team/papirus-apps/96/reddit-icon.png')
        embed.set_footer(text=f'from {data["subreddit_name_prefixed"]}')

        await ctx.send(embed=embed)

    @commands.command(aliases=['yt'])
    async def youtube(self, ctx, *, search: str):
        """Youtube-Search command. Lets you to search YouTube videos through Discord.
        Args: search (str): Search topic. The bot will send the first faced result."""
        r = await ctx.bot.session.get(
            'https://youtube.com/results',
            params={'search_query': search},
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        found = re.findall(r'watch\?v=(\S{11})', await r.text())

        try:
            await ctx.send(f'https://youtu.be/{found[0]}')

        except IndexError:
            raise commands.BadArgument(f'No videos found for query: {search}')

    @commands.command(aliases=['ud', 'urban'])
    async def urbandictionary(self, ctx, *, word: str):
        """Urban Dictionary words' definition wrapper.
        Args: word (str): A word you want to know the definition of."""
        try:
            r = await ctx.bot.session.get(f'{ctx.bot.config["API"]["ud_api"]}?term={word}')
            js = await r.json()
            source = js['list'][0]

        except IndexError:
            raise commands.BadArgument(f'No definition found for **{word}**')

        embed = ctx.bot.embed.default(ctx, description=f"**{source['definition'].replace('[', '').replace(']', '')}**")
        embed.set_author(
            name=word,
            url=source['permalink'],
            icon_url='https://is4-ssl.mzstatic.com/image/thumb/Purple111/v4/7e/49/85/7e498571-a905-d7dc-26c5-33dcc0dc04a8/source/64x64bb.jpg'
        ).add_field(name='Example:', value=js['list'][0]['example'].replace('[', '').replace(']', '')[:1024])
        embed.set_footer(text=f'{source["thumbs_up"]}👍 | {source["thumbs_down"]}👎 | {source["written_on"][0:10]}')

        await ctx.send(embed=embed)

    @commands.command(aliases=['calculate', 'calculator'])
    async def calc(self, ctx, *, expression: str):
        """A simple calculator that supports useful features.
        Args: expression (str): Maths expression to solve."""
        lexer = CalcLexer()
        parser = CalcParser()
        reg = ''.join(i for i in expression if i in '()')

        try:
            if not parser.match(reg):
                raise exceptions.UnclosedBrackets()
            for i in range(len(expression) - 1):
                if expression[i] == '(' and expression[i + 1] == ')':
                    raise exceptions.EmptyBrackets()
            result = parser.parse(lexer.tokenize(expression))

        except Exception as e:
            if isinstance(e, exceptions.Overflow):
                return await ctx.send('Too big number was given.')

            if isinstance(e, exceptions.UndefinedVariable):
                return await ctx.send(e.exc)

            if isinstance(e, exceptions.KeywordAlreadyTaken):
                return await ctx.send('The given variable name is shadowing a reserved keyword argument.')

            if isinstance(e, exceptions.UnclosedBrackets):
                return await ctx.send('Given expression has unclosed brackets.')

            if isinstance(e, exceptions.EmptyBrackets):
                return await ctx.send('Given expression has empty brackets.')

            if isinstance(e, decimal.InvalidOperation):
                return await ctx.send('Invalid expression given.')

        res = '\n'.join(str(i) for i in result)

        embed = ctx.bot.embed.default(ctx)
        embed.add_field(name='Input', value=f'```\n{expression}\n```', inline=False)
        embed.add_field(name='Output', value=f'```\n{res}\n```', inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['colour'])
    async def color(self, ctx, *, color: ColorConverter):
        """Color command. Get color in HEX & RGB.
        Args: color (ColorConverter): Color that you specify.
        It can be either RGB, HEX, or even a human-friendly word."""
        rgb = color.to_rgb()

        embed = ctx.bot.embed(
            color=discord.Color.from_rgb(*rgb)
        ).set_thumbnail(url=f'https://kal-byte.co.uk/colour/{"/".join(str(i) for i in rgb)}')
        embed.add_field(name='Hex', value=str(color), inline=False)
        embed.add_field(name='RGB', value=str(rgb), inline=False)

        await ctx.send(embed=embed)

    @flags.add_flag('--continent', type=str, help='Search through continents.')
    @flags.add_flag('--country', type=str, help='Search through countries.')
    @flags.command(aliases=['ncov', 'coronavirus'])
    async def covid(self, ctx, **flags):
        """Coronavirus command.
        Returns world statistics if no country is mentioned.
        Cases, deaths, recovered cases, active cases, and critical cases"""
        cs = ctx.bot.session

        if bool(flags):
            r = await cs.get(f'{ctx.bot.config["API"]["covid_api"]}all')
            js = await r.json()
            title = 'Covid-19 World Statistics'
            field = ('Affected Countries', str(js['affectedCountries']))
            url = 'https://www.freepngimg.com/thumb/globe/40561-7-earth-globe-png-download-free.png'

        if continent := flags.pop('continent', False):
            r = await cs.get(f'{ctx.bot.config["API"]["covid_api"]}continents/{continent}?strict=true')
            js = await r.json()
            title = f'Covid-19 Statistics for {continent.title()}'
            field = ('Tests', str(js['tests']))
            url = ctx.guild.icon_url

        if country := flags.pop('country', False):
            r = await cs.get(f'{ctx.bot.config["API"]["covid_api"]}countries/{country}?strict=true')
            js = await r.json()
            title = f'Covid-19 Statistics for {country.title()}'
            field = ('Continent', str(js['continent']))
            url = str(js['countryInfo']['flag'])

        embed = ctx.bot.embed.default(ctx, title=title).set_thumbnail(url=url)
        fields = [
            ('Total Cases', str(js['cases'])),
            ('Today Cases', str(js['todayCases'])),
            ('Deaths', str(js['deaths'])),
            ('Today Deaths', str(js['todayDeaths'])),
            ('Recovered', str(js['recovered'])),
            ('Today Recov', str(js['todayRecovered'])),
            ('Active Cases', str(js['active'])),
            ('Critical', str(js['critical'])),
            field
        ]

        for name, value in fields:
            embed.add_field(name=name, value=value)

        await ctx.send(embed=embed)

    @commands.command(aliases=['temp', 'temperature'])
    async def weather(self, ctx, *, city: str.capitalize):
        """Simply gets weather statistics of a given city.
        Gives: Description, temperature, humidity%, atmospheric pressure (hPa)"""
        r = await ctx.bot.session.get(f'{ctx.bot.config["API"]["weather_api"]}appid={ctx.bot.config["API"]["weather_id"]}&q={city}')
        x = await r.json()

        if x['cod'] != '404':
            embed = ctx.bot.embed.default(ctx, title=f'Weather in {city}')
            embed.set_thumbnail(url='https://i.ibb.co/CMrsxdX/weather.png')

            fields = [
                ('Description', f'**{x["weather"][0]["description"]}**', False),
                ('Temperature', f'**{x["main"]["temp"] - 273.15:.0f}°C**', False),
                ('Humidity', f'**{x["main"]["humidity"]}%**', False),
                ('Atmospheric Pressure', f'**{x["main"]["pressure"]}hPa**', False)
            ]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            return await ctx.send(embed=embed)

        await ctx.send(f'City `{city}` not found.')

    @commands.command()
    async def translate(self, ctx, language, *, sentence, **flags):
        """Translates a given text to language you want.
        Shows the translation and pronunciation of a text."""
        translation = await Manip.translate(language, sentence=sentence)
        embed = ctx.bot.embed.default(
            ctx, title=f'Translating from {translation.src} to {translation.dest}:'
        ).add_field(name='Translation:', value=f'```{translation.text}```', inline=False)
        embed.add_field(name='Pronunciation:', value=f'```{translation.pronunciation}```')

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Useful())
