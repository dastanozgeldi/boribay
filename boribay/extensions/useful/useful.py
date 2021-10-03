import decimal
import random
import string
import zipfile
from datetime import datetime
from io import BytesIO

import nextcord
from boribay.core import exceptions, utils
from boribay.core.bot import Boribay
from nextcord.ext import commands
from humanize import time

from .calculator import CalcLexer, CalcParser
from .utils import Poll, TodoPageSource, UrbanDictionaryPageSource


class Useful(utils.Cog):
    """The useful commands extension.

    Made to help people in specific situations, such as solving math expressions.
    """

    def __init__(self, bot: Boribay):
        self.icon = '✨'
        self.bot = bot

    @utils.command()
    @commands.cooldown(1, 60.0, commands.BucketType.guild)
    async def zipemojis(self, ctx: utils.Context) -> None:
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
            file=nextcord.File(buffer, filename='emojis.zip')
        )

    @staticmethod
    def _generate_password(
        length: int, numbers: bool, uppercase: bool, special: bool
    ) -> str:
        """Generates a random password using given parameters.

        Parameters
        ----------
        length : int
            Length of the password.
        numbers : bool
            Include numbers.
        uppercase : bool
            Include uppercase characters.
        special : bool
            Include special characters.

        Returns
        -------
        str
            Randomly generated password.
        """
        RESULT = string.ascii_lowercase

        if numbers:
            RESULT += string.digits
        if uppercase:
            RESULT += string.ascii_uppercase
        if special:
            RESULT += string.punctuation

        result = random.choices(RESULT, k=length)
        return ''.join(result)

    @utils.command(aliases=('pw',))
    async def password(
        self,
        ctx: utils.Context,
        length: int = 25,
        numbers: bool = False,
        uppercase: bool = False,
        special: bool = False
    ) -> None:
        """The password creator. Get a safe password using this command.

        Examples
        --------
            **{p}password 40** - sends the generated password 40 characters long.
            **{p}password 25 y y y - 25 character-long password
            within numbers, uppercase and special characters included.

        Parameters
        ----------
        length : int, optional
            Length of the password, by default 25
        numbers : bool, optional
            Include numbers in the password, by default False
        uppercase : bool, optional
            Include uppercase characters, by default False
        special : bool, optional
            Include special characters, by default False

        Raises
        ------
        commands.BadArgument
            If too big password length was provided, like why would you need it?
        """
        if length > 50:
            raise commands.BadArgument(
                f'Too big length was given ({length}) while the limit is 50 characters.'
            )

        result = self._generate_password(length, numbers, uppercase, special)
        await ctx.reply('✅ Generated you the password.')
        # To make people sure this is working. ↑
        await ctx.author.send(f'Here is your password: ```{result}```')

    @utils.command()
    async def anime(self, ctx: utils.Context, *, anime: str) -> None:
        """Anime search command. Get the detailed information about an anime.

        Example:
            **{p}anime kimetsu no yaiba** - sends info about "Demon Slayer".

        Args:
            anime (str): An anime that you want to get info about.
        """
        anime = anime.replace(' ', '%20')
        r = await ctx.bot.session.get(f'https://kitsu.io/api/edge/anime?page[limit]=1&page[offset]=0&filter[text]={anime}&include=genres')
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

    @utils.command()
    async def manga(self, ctx: utils.Context, *, manga: str) -> None:
        """Manga search command. Get the detailed information about a manga.

        Example:
            **{p}manga kimetsu no yaiba** - sends info about "Demon Slayer".

        Args:
            manga (str): A manga that you want to get info about.
        """
        manga = manga.replace(' ', '%20')
        r = await ctx.bot.session.get(f'https://kitsu.io/api/edge/manga?page[limit]=1&page[offset]=0&filter[text]={manga}&include=genres')
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

    @utils.group()
    async def todo(self, ctx: utils.Context) -> None:
        """To-do commands parent. Sends help for its subcommands.
        Kind of pro-tip to use this instead of **{p}help todo**"""
        await ctx.send_help('todo')

    @todo.command(name='show', aliases=('list',))
    async def _todo_show(
        self,
        ctx: utils.Context,
        show_count: bool = False,
        dm: bool = False
    ) -> None:
        """To-do show command, a visual way to manipulate with your list.

        Parameters
        ----------
        show_count : bool, optional
            Whether to show to-do list items count, by default False
        dm : bool, optional
            Whether to DM your list, by default False
        """
        query = 'SELECT content, jump_url FROM todos WHERE user_id = $1 ORDER BY added_at'
        todos = [(todo['content'], todo['jump_url'])
                 for todo in await ctx.bot.pool.fetch(query, ctx.author.id)]
        dest = ctx.author if dm else ctx.channel

        if show_count:
            return await dest.send(len(todos))

        await utils.Paginate(
            TodoPageSource(ctx, todos),
            clear_reactions_after=True,
            timeout=60.0
        ).start(ctx, channel=dest)

    @todo.command(name='add')
    async def _todo_add(self, ctx: utils.Context, *, content: str) -> None:
        """Add anything you think you have to-do to your list.

        Example:
            **{p}todo add Start the project work from English.**

        Args:
            content (str): A to-do content which is going to be added.
        """
        query = '''
        INSERT INTO todos(user_id, content, added_at, jump_url)
        VALUES($1, $2, $3, $4)
        '''
        await ctx.bot.pool.execute(query, ctx.author.id, content, datetime.utcnow(), ctx.message.jump_url)
        await ctx.message.add_reaction('✅')

    @todo.command(name='remove', aliases=('rm', 'delete'))
    async def _todo_remove(
        self, ctx: utils.Context, numbers: commands.Greedy[int]
    ) -> None:
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
    async def _todo_info(self, ctx: utils.Context, number: int) -> None:
        """Shows some useful information about the specified to-do.
        Returns the jump-url, the time to-do was added.

        Example:
            **{p}todo info 13** - sends info about 13th to-do from your list.

        Args:
            number (int): The index of to-do you want to see info about.
        """
        query = '''
        WITH enumerated AS (SELECT todos.content, todos.added_at, todos.jump_url, row_number()
        OVER (ORDER BY added_at ASC) as count FROM todos WHERE user_id = $1)
        SELECT * FROM enumerated WHERE enumerated.count = $2
        '''
        row = await ctx.bot.pool.fetchrow(query, ctx.author.id, number)

        values = [
            ('Added', f'{time.naturaltime(row["added_at"])} by UTC'),
            ('Jump URL', f'[click here]({row["jump_url"]})')
        ]

        embed = ctx.embed(
            title=f'Todo #{number}', description=row['content']
        ).add_field(name='Additional Information', value='\n'.join(f'{n}: **{v}**' for n, v in values))

        await ctx.send(embed=embed)

    @todo.command(name='clear', aliases=('reset',))
    async def _todo_clear(self, ctx: utils.Context) -> None:
        """Clear your to-do list up using this command."""
        query = 'DELETE FROM todos WHERE user_id = $1'

        confirmation = await ctx.confirm('Are you sure? All to-do\'s will be dropped.')
        if confirmation:
            await ctx.bot.pool.execute(query, ctx.author.id)
            return await ctx.message.add_reaction('✅')

    @utils.command()
    async def poll(self, ctx: utils.Context, *, options: str) -> None:
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

        menu = Poll(ctx, options=options, description=description)
        await menu.start()

    @utils.command()
    async def reddit(self, ctx: utils.Context, subreddit: str) -> None:
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
            url = f'https://www.reddit.com/r/{subreddit}/hot.json'
            r = await ctx.bot.session.get(url)
            js = await r.json()
            data = js['data']['children'][random.randint(0, 10)]['data']
        except IndexError:
            raise commands.BadArgument(f'There is no subreddit called: {subreddit}.')

        if not ctx.channel.is_nsfw() and data['over_18']:  # no need in "is True"
            raise commands.NSFWChannelRequired(ctx.channel)

        embed = ctx.embed().set_image(url=data['url'])
        embed.set_author(name=data['title'], icon_url='https://tinyurl.com/yhkdozxx')
        embed.set_footer(text=f'from {data["subreddit_name_prefixed"]}')

        await ctx.send(embed=embed)

    @utils.command(aliases=('ud', 'urban'))
    async def urbandictionary(self, ctx: utils.Context, *, word: str) -> None:
        """Search for word definitions from urban dictionary.

        Example:
            **{p}urbandictionary ASAP** - sends the definition for this acronym.

        Args:
            word (str): Your word to search for.
        """
        r = await ctx.bot.session.get(
            'http://api.urbandictionary.com/v0/define?term=' + word
        )
        if (stat := r.status) != 200:
            return await ctx.send(f'Facing some issues: {stat} {r.reason}')

        js = await r.json()
        if not (source := js.get('list', [])):
            return await ctx.send(f'No definitions found for `{word}`.')

        # Everything is done, paginating...
        await utils.Paginate(
            UrbanDictionaryPageSource(ctx, source)
        ).start(ctx)

    @utils.command(aliases=('calc',))
    async def calculate(self, ctx: utils.Context, *, expression: str) -> None:
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
        lexer = CalcLexer()
        parser = CalcParser()
        reg = ''.join(i for i in expression if i in '()')

        try:
            if not parser.match(reg):
                raise exceptions.UnclosedBrackets

            for i in range(len(expression) - 1):
                if expression[i] == '(' and expression[i + 1] == ')':
                    raise exceptions.EmptyBrackets

            result = parser.parse(lexer.tokenize(expression))

        except exceptions.UndefinedVariable as e:
            return await ctx.send(e.exc)

        except (decimal.InvalidOperation, decimal.DivisionByZero):
            return await ctx.send('Invalid expression provided.')

        res = '\n'.join(str(i) for i in result)
        embed = ctx.embed()
        for n, v in (('Input', expression), ('Output', res)):
            embed.add_field(name=n, value=f'```\n{v}\n```', inline=False)

        await ctx.send(embed=embed)

    @utils.command(aliases=('colour',))
    async def color(
        self, ctx: utils.Context, *, color: utils.ColorConverter
    ) -> None:
        """Color visualizer command. Get HEX & RHB values of a color.

        Argument can be either RGB, HEX, or even a human-friendly word.

        Example:
            **{p}color orange** - sends the data for color 'orange'.

        Args:
            color (ColorConverter): Color that you have specified.
        """
        rgb = color.to_rgb()

        embed = ctx.embed(
            color=nextcord.Color.from_rgb(*rgb)
        ).set_thumbnail(url='https://kal-byte.co.uk/colour/' + '/'.join(str(i) for i in rgb))
        embed.add_field(name='Hex', value=str(color), inline=False)
        embed.add_field(name='RGB', value=str(rgb), inline=False)

        await ctx.send(embed=embed)

    @utils.command(aliases=('temp', 'temperature'))
    async def weather(self, ctx: utils.Context, *, city: str.capitalize) -> None:
        """Simply gets the weather statistics for a city | region.
        Returns: description, temperature, humidity%, atmospheric pressure.

        Example:
            **{p}weather Almaty** - sends weather stats of Almaty city.

        Args:
            city: The city you want to get weather data of.
        """
        key = ctx.config.api.weather
        r = await ctx.bot.session.get(f'http://api.openweathermap.org/data/2.5/weather?appid={key}&q={city}')
        x = await r.json()

        if x['cod'] != '404':
            embed = ctx.embed(title=f'Weather in {city}')
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
