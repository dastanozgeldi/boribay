import decimal
import random
import re
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Optional

import discord
from boribay.core import Boribay, Cog, Context, constants
from boribay.utils import (calculator, converters, exceptions, make_image_url,
                           paginators)
from discord.ext import commands, flags
from humanize import time


class Poll:
    def __init__(self, ctx: Context, options: list, **kwargs):
        self.ctx = ctx
        self.options = options
        self.embed = ctx.embed(**kwargs)

    def get_reactions(self) -> tuple:
        if len(self.options) == 2 and ('y', 'n') == tuple(map(str.lower, self.options)):
            return (
                '<:thumbs_up:746352051717406740>',
                '<:thumbs_down:746352095510265881>'
            )

        return (
            '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'
        )

    async def start(self) -> None:
        ctx = self.ctx
        opt = len(self.options)
        reactions = self.get_reactions()

        if not 2 <= opt <= 10:
            raise exceptions.OptionsNotInRange(
                'Please keep poll options range (min 2 : max 10).'
            )

        # Adding reactions on an embed field.
        self.embed.add_field(
            name='📊 Options',
            value='\n'.join(
                f'{reactions[x]} {option}' for x, option in enumerate(self.options)
            )
        )

        # Attempting to delete a message sent by user.
        await ctx.try_delete(ctx.message)
        message = await ctx.send(embed=self.embed)

        # Adding some real reactions.
        for emoji in reactions[:opt]:
            await message.add_reaction(emoji)


class Useful(Cog):
    """The useful commands extension.

    Made to help people in specific situations, such as solving math expressions.
    """

    def __init__(self, bot: Boribay):
        self.icon = '<:pickaxe:807534625785380904>'
        self.bot = bot

    async def _youtube_search(self, query: str) -> list:
        r = await self.bot.session.get(
            'https://www.youtube.com/results',
            params={'search_query': query},
            headers={'user-agent': 'Mozilla/3.0'}
        )

        result = await r.text()

        found = re.findall(r'{"videoId":"(.{11})', result)
        return [f'https://youtube.com/watch?v={res}' for res in found[:11]]

    @commands.command(aliases=['yt'])
    async def youtube(self, ctx: Context, *, query: str):
        if not (results := await self._youtube_search(query)):
            return await ctx.send(f'❌ Could not find videos for query: **{query}**')

        await ctx.send(results[0])

    @commands.command()
    @commands.cooldown(1, 60.0, commands.BucketType.guild)
    async def zipemojis(self, ctx: Context):
        """Zip all emojis of the current guild.

        Returns a .zip file with all emojis compressed.
        """
        buffer = BytesIO()

        async with ctx.typing():
            with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                for emoji in ctx.guild.emojis:
                    bts = await emoji.url.read()
                    f.writestr(f'{emoji.name}.{"gif" if emoji.animated else "png"}', bts)
            buffer.seek(0)

        await ctx.reply(
            'Sorry for being slow as hell but anyways:',
            file=discord.File(buffer, filename='emojis.zip')
        )

    def _generate_password(self, length: int, **flags) -> str:
        """The core of this module, generates a random password for you.

        Args:
            length (int, optional): Length of the password. Defaults to 25.

        Returns:
            str: Randomly generated password due to your parameters."""
        BASE = 'qwertyuiopasdfghjklzxcvbnm'
        NUMBERS = '1234567890'
        UPPERCASE = 'QWERTYUIOPASDFGHJKLZXCVBNM'
        SPECIAL = '!@#$%^&*()'

        if flags.pop('numbers'):
            BASE += NUMBERS

        if flags.pop('uppercase'):
            BASE += UPPERCASE

        if flags.pop('special_characters'):
            BASE += SPECIAL

        result = random.choices(BASE, k=length)
        return ''.join(result)

    @flags.add_flag(
        '--numbers',
        '-n',
        action='store_true',
        help='Whether to add numbers.'
    )
    @flags.add_flag(
        '--uppercase', '-u',
        action='store_true',
        help='Whether to add Uppercased Characters.'
    )
    @flags.add_flag(
        '--special-characters',
        '-sc',
        action='store_true',
        help='Whether to add special characters, like: $%^&'
    )
    @flags.command(aliases=['pw'])
    async def password(self, ctx: Context, length: int = 25, **flags):
        """A password creator command. Get a safe password using this command.

        Example:
            **{p}password 40** - sends the generated password 40 characters long.

        Args:
            length (int): Length of the password. Defaults to 25.

        Raises:
            commands.BadArgument: If too big length of the password was given.
        """
        if length > 50:
            raise commands.BadArgument(f'Too big length was given ({length}) while the limit is 50 characters.')

        result = self._generate_password(length, flags)
        await ctx.reply('✅ Generated you the password.')
        # To make people sure this is working. ↑
        await ctx.author.send(f'Here is your password: ```{result}```')

    @commands.command()
    async def anime(self, ctx: Context, *, anime: str):
        """Anime search command. Get the detailed information about an anime.

        Example:
            **{p}anime kimetsu no yaiba** - sends info about "Demon Slayer".

        Args:
            anime (str): An anime that you want to get info about.
        """
        anime = anime.replace(' ', '%20')
        r = await ctx.bot.session.get(f'{ctx.config.api.anime}/anime?page[limit]=1&page[offset]=0&filter[text]={anime}&include=genres')
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
            ('Episodes', attributes['episodeCount']),
            ('Duration', f"{attributes['episodeLength']} min"),
            ('Age Rate', attributes['ageRatingGuide']),
            ('Genres', rl)
        ]
        title = attributes['titles']['en_jp']
        embed = ctx.embed(
            title=f"{title} ({attributes['titles']['ja_jp']})",
            url=f"https://kitsu.io/anime/{js['data'][0]['id']}"
        ).set_thumbnail(url=attributes['posterImage']['small'])

        embed.add_field(name='Statistics', value='\n'.join(f'**{name}:** {value}' for name, value in fields))
        embed.add_field(name='Description', value=attributes['description'][:300] + '...')

        await ctx.send(embed=embed)

    @commands.command()
    async def manga(self, ctx: Context, *, manga: str):
        """Manga search command. Get the detailed information about a manga.

        Example:
            **{p}manga kimetsu no yaiba** - sends info about "Demon Slayer".

        Args:
            manga (str): A manga that you want to get info about.
        """
        manga = manga.replace(' ', '%20')
        r = await ctx.bot.session.get(f'{ctx.config.api.anime}/manga?page[limit]=1&page[offset]=0&filter[text]={manga}&include=genres')
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

        embed = ctx.embed(
            title=f"{attributes['titles']['en_jp']} ({attributes['titles']['ja_jp']})",
            url=f'https://kitsu.io/manga/{manga}'
        ).set_thumbnail(url=attributes['posterImage']['small'])
        embed.add_field(name='Statistics', value='\n'.join([f'**{name}:** {value}' for name, value in fields]))
        embed.add_field(name='Description', value=attributes['description'][:300] + '...')

        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=['to-do'])
    async def todo(self, ctx: Context):
        """To-do commands parent. Sends help for its subcommands.
        Kind of pro-tip to use this instead of **{p}help todo**"""
        await ctx.send_help('todo')

    @flags.add_flag('--count', action='store_true', help='Sends the count of todos.')
    @flags.add_flag('--dm', action='store_true', help='Whether to DM you the todo list.')
    @todo.command(cls=flags.FlagCommand, name='show', aliases=['list'])
    async def _todo_show(self, ctx: Context, **flags):
        """To-do show command, a visual way to manipulate with your list.

        Example:
            **{p}todo show --dm** - DM's you the to-do list.
            **{p}todo show --count** - sends the current count of to-do's.
            Use them together to get both features.
        """
        query = 'SELECT content, jump_url FROM todos WHERE user_id = $1 ORDER BY added_at'
        todos = [(todo['content'], todo['jump_url']) for todo in await ctx.bot.pool.fetch(query, ctx.author.id)]
        dest = ctx.author if flags.pop('dm', False) else ctx.channel

        if flags.pop('count', False):
            return await dest.send(len(todos))

        await paginators.Paginate(
            paginators.TodoPageSource(ctx, todos),
            clear_reactions_after=True,
            timeout=60.0
        ).start(ctx, channel=dest)

    @todo.command(name='add', aliases=['append'])
    async def _todo_add(self, ctx: Context, *, content: str):
        """Add anything you think you have to-do to your list.

        Example:
            **{p}todo add Start the project work from English.**

        Args:
            content (str): A to-do content which is going to be added.
        """
        query = 'INSERT INTO todos(user_id, content, added_at, jump_url) VALUES($1, $2, $3, $4)'
        await ctx.bot.pool.execute(query, ctx.author.id, content, datetime.utcnow(), ctx.message.jump_url)
        await ctx.message.add_reaction('✅')

    @todo.command(name='remove', aliases=['rm', 'delete'])
    async def _todo_remove(self, ctx: Context, numbers: commands.Greedy[int]):
        """Remove to-do's that you don't need from your list.

        Multiple numbers may be specified. Order does not matter.

        Example:
            **{p}todo remove 7 3 10** - removes to-do's by the given indexes.

        Args:
            numbers: Range of to-do indexes you want to remove.
        """
        query = '''
        WITH enumerated AS (SELECT todos.content, row_number()
        OVER (ORDER BY added_at ASC) AS count FROM todos WHERE user_id = $1)
        DELETE FROM todos WHERE user_id = $1 AND content IN (
            SELECT enumerated.content FROM enumerated
            WHERE enumerated.count=ANY($2::bigint[])
        ) RETURNING content
        '''
        await ctx.bot.pool.execute(query, ctx.author.id, numbers)
        await ctx.message.add_reaction('✅')

    @todo.command(name='info')
    async def _todo_info(self, ctx: Context, number: int):
        """Shows some useful information about the specified to-do.
        Returns the jump-url, the time to-do was added.

        Example:
            **{p}todo info 13** - sends info about 13th to-do from your list.

        Args:
            number (int): The index of to-do you want to see info about.
        """
        query = '''WITH enumerated AS (SELECT todos.content, todos.added_at, todos.jump_url, row_number()
        OVER (ORDER BY added_at ASC) as count FROM todos WHERE user_id = $1)
        SELECT * FROM enumerated WHERE enumerated.count = $2'''
        row = await ctx.bot.pool.fetchrow(query, ctx.author.id, number)

        values = [
            ('Added', f'{time.naturaltime(row["added_at"])} by UTC'),
            ('Jump URL', f'[click here]({row["jump_url"]})')
        ]

        embed = ctx.embed(
            title=f'Todo #{number}', description=row['content']
        ).add_field(name='Additional Information', value='\n'.join(f'{n}: **{v}**' for n, v in values))

        await ctx.send(embed=embed)

    @todo.command(name='clear')
    async def _todo_clear(self, ctx: Context):
        """Clear your to-do list up using this command."""
        query = 'DELETE FROM todos WHERE user_id = $1'
        confirmation = await ctx.confirm('Are you sure? All to-do\'s will be dropped.')
        if confirmation:
            await ctx.bot.pool.execute(query, ctx.author.id)
            return await ctx.message.add_reaction('✅')

    @commands.command(name='poll')
    async def command_poll(self, ctx: Context, *, options: str) -> None:
        """Make a simple poll in your server using this command.
        You can add an image so it will be added as the main image.

        Don't forget to separate options using quotation marks ("")

        Example:
            **{p}poll What to do with @Dosek ? | kick him | give him the last chance**

        Args:
            options: Title + Options for your poll. Separate by `|`.
        """
        # Variable assignment.
        options = list(map(str.strip, options.split('|')))
        description = options.pop(0)  # Getting the first one as the poll title.

        await Poll(ctx, options, description=description).start()

    @commands.command()
    async def reddit(self, ctx: Context, subreddit: str):
        """Get fresh posts from your favorite subreddit.

        Example:
            **{p}reddit dankmemes** - sends a random post taken from dankmemes.

        Args:
            subreddit (str): A subreddit you want to search posts from.

        Raises:
            BadArgument: If no subreddit was found (does not exist).
            NSFWChannelRequired: If the post is NSFW and the channel isn't.
        """
        try:
            r = await ctx.bot.session.get(f'https://www.reddit.com/r/{subreddit}/hot.json')
            r = await r.json()
            data = r['data']['children'][random.randint(0, 10)]['data']

        except IndexError:
            raise commands.BadArgument(f'There is no subreddit called **{subreddit}**.')

        if not ctx.channel.is_nsfw() and data['over_18']:  # no need in "is True"
            raise commands.NSFWChannelRequired(ctx.channel)

        embed = ctx.embed().set_image(url=data['url'])

        embed.set_author(name=data['title'], icon_url=constants.REDDIT_ICON_URL)
        embed.set_footer(text=f'from {data["subreddit_name_prefixed"]}')

        await ctx.send(embed=embed)

    @commands.command(aliases=['ud', 'urban'])
    async def urbandictionary(self, ctx: Context, *, word: str):
        """Search for word definitions from urban dictionary.

        Example:
            **{p}urbandictionary ASAP** - sends the definition for this acronym.

        Args:
            word (str): Your word to search for.
        """
        r = await ctx.bot.session.get(f'{ctx.config.api.ud}?term={word}')

        if (stat := r.status) != 200:
            return await ctx.send(f'Facing some issues: {stat} {r.reason}')

        js = await r.json()
        if not (source := js.get('list', [])):
            return await ctx.send(f'No definitions found for `{word}`.')

        # Everything is done, paginating...
        await paginators.Paginate(
            paginators.UrbanDictionaryPageSource(ctx, source)
        ).start(ctx)

    @commands.command(aliases=['calc'])
    async def calculate(self, ctx: Context, *, expression: str):
        """A simple calculator command that supports useful features.

        Features:
            round, sin, cos, tan, sqrt, abs, fib.

        Constants:
            pi, e, tau, inf, NaN.

        Example:
            **{p}calculator fib(50)** - sends the Fibonacci value of number 50.

        Args:
            expression (str): Your expression to solve.

        Raises:
            UnclosedBrackets: If an expression has unclosed brackets.
            EmptyBrackets: If an expression has empty-useless brackets.
        """
        lexer = calculator.CalcLexer()
        parser = calculator.CalcParser()
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

        embed = ctx.embed()
        embed.add_field(name='Input', value=f'```\n{expression}\n```', inline=False)
        embed.add_field(name='Output', value=f'```\n{res}\n```', inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['colour'])
    async def color(self, ctx: Context, *, color: converters.ColorConverter):
        """Color visualizer command. Get HEX & RHB values of a color.

        Argument can be either RGB, HEX, or even a human-friendly word.

        Example:
            **{p}color orange** - sends the data for color 'orange'.

        Args:
            color (ColorConverter): Color that you have specified.
        """
        rgb = color.to_rgb()

        embed = ctx.embed(
            color=discord.Color.from_rgb(*rgb)
        ).set_thumbnail(url='https://kal-byte.co.uk/colour/' + '/'.join(str(i) for i in rgb))
        embed.add_field(name='Hex', value=str(color), inline=False)
        embed.add_field(name='RGB', value=str(rgb), inline=False)

        await ctx.send(embed=embed)

    @flags.add_flag('--continent', type=str, help='Search through continents.')
    @flags.add_flag('--country', type=str, help='Search through countries.')
    @flags.command(aliases=['ncov', 'coronavirus'])
    async def covid(self, ctx: Context, **flags):
        """Get coronavirus statistics with this command.
        Returns current world statistics if no country was specified.

        Cases, deaths, recovers, active and critical cases will be sent.

        Example:
            **{p}covid** - sends world statistics.
            **{p}covid --continent Europe** - sends Europe statistics.
            **{p}covid --country Kazakhstan** - sends Kazakhstan statistics.
        """
        cs = ctx.bot.session
        api = ctx.config.api.covid

        if bool(flags):
            r = await cs.get(f'{api}all')
            js = await r.json()
            title = 'Covid-19 World Statistics'
            field = ('Affected Countries', js['affectedCountries'])
            url = 'https://www.freepngimg.com/thumb/globe/40561-7-earth-globe-png-download-free.png'

        if continent := flags.pop('continent', False):
            r = await cs.get(f'{api}continents/{continent}?strict=true')
            js = await r.json()
            title = f'Covid-19 Statistics for {continent.title()}'
            field = ('Tests', js['tests'])
            url = ctx.guild.icon_url

        if country := flags.pop('country', False):
            r = await cs.get(f'{api}countries/{country}?strict=true')
            js = await r.json()
            title = f'Covid-19 Statistics for {country.title()}'
            field = ('Continent', js['continent'])
            url = js['countryInfo']['flag']

        embed = ctx.embed(title=title).set_thumbnail(url=url)
        fields = [
            ('Total Cases', js['cases']),
            ('Today Cases', js['todayCases']),
            ('Deaths', js['deaths']),
            ('Today Deaths', js['todayDeaths']),
            ('Recovered', js['recovered']),
            ('Today Recov', js['todayRecovered']),
            ('Active Cases', js['active']),
            ('Critical', js['critical']),
            field
        ]

        for name, value in fields:
            embed.add_field(name=name, value=str(value))

        await ctx.send(embed=embed)

    @commands.command(aliases=['temp', 'temperature'])
    async def weather(self, ctx: Context, *, city: str.capitalize):
        """Simply gets the weather statistics for a city | region.
        Returns: description, temperature, humidity%, atmospheric pressure.

        Example:
            **{p}weather Almaty** - sends weather stats of Almaty city.

        Args:
            city: The city you want to get weather data of.
        """
        conf = ctx.config.api.weather
        r = await ctx.bot.session.get(f'{conf[0]}appid={conf[1]}&q={city}')
        x = await r.json()

        if x['cod'] != '404':
            embed = ctx.embed(title=f'Weather in {city}')
            embed.set_thumbnail(url=constants.WEATHER_ICON_URL)

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
    async def qr(self, ctx: Context, url: Optional[str]):
        """Make QR-code from a given URL.
        URL can be atttachment or a user avatar.

        Args:
            url (Optional[str]): URL to make the QR-code from.

        Example:
            **{p}qr @Dosek** - sends the QR code using Dosek's avatar.
        """
        url = await make_image_url(ctx, url)
        r = await ctx.bot.session.get(ctx.config.api.qr + url)
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(io, 'qr.png'))
