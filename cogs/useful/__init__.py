import decimal
import random
import re
import zlib
import zipfile
from io import BytesIO
from textwrap import wrap
from typing import Optional

import aiowiki
import discord
from async_cse import Search
from discord.ext.commands import (
    group,
    command,
    cooldown,
    Cooldown,
    BucketType,
    BadArgument,
    NSFWChannelRequired
)
from googletrans import Translator
from utils.Converters import ColorConverter
from utils.Cog import Cog
from utils.Exceptions import (
    EmptyBrackets,
    KeywordAlreadyTaken,
    NotEnoughOptions,
    Overflow,
    TooManyOptions,
    UnclosedBrackets,
    UndefinedVariable
)
from utils.Checks import has_voted
from utils.Paginators import EmbedPageSource, MyPages, TodoPageSource

from . import calclex, calcparse


class Useful(Cog, command_attrs={'cooldown': Cooldown(1, 5, BucketType.user)}):
    '''Useful commands extension. Simply made to help people in some kind of
    specific situations, such as solving math expression, finding lyrics
    of the song and so on.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '<:pickaxe:807534625785380904> Useful'
        self.todos = self.bot.db.Boribay.todos

    @command()
    @has_voted()
    @cooldown(1, 60.0, BucketType.guild)
    async def zipemojis(self, ctx, guild: Optional[discord.Guild]):
        """Zip All Emojis.
        Args: guild (Guild): The guild you wanna grab emojis from."""
        guild = guild or ctx.guild
        buffer = BytesIO()
        async with ctx.typing():
            with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as f:
                for emoji in guild.emojis:
                    bts = await emoji.url.read()
                    f.writestr(f'{emoji.name}.{"gif" if emoji.animated else "png"}', bts)
            buffer.seek(0)
        await ctx.reply('Sorry for being slow as hell but anyways:', file=discord.File(buffer, filename='emojis.zip'))

    @command(aliases=['ss'])
    @has_voted()
    async def screenshot(self, ctx, url: str):
        """Screenshot command.
        Args: url (str): a web-site that you want to get a screenshot from."""
        if not re.search(self.bot.regex['URL_REGEX'], url):
            return await ctx.send('Please leave a valid url!')
        cs = self.bot.session
        r = await cs.get(f'{self.bot.config["API"]["screenshot_api"]}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='screenshot.png'))

    @command()
    async def password(self, ctx, length: int=25):
        """A Password creator command.
        Args: length (optional): Length of characters. Defaults to 25.
        Raises: BadArgument: Too big length of the password was given."""        
        if length > 50:
            raise BadArgument(f'Too big length was given ({length}).')
        else:
            asset = random.choices(open('cogs/useful/chars.txt', 'r').read(), k=length)
            await ctx.author.send(''.join(char for char in asset))

    @command(aliases=['wiki'])
    async def wikipedia(self, ctx, language: str, *, topic: str):
        """Wikipedia Search Command.
        Args: topic (str): The Wikipedia topic you wanna search for."""
        self.bot.wikipedia = aiowiki.Wiki.wikipedia(language, session=self.bot.session)
        try:
            page = (await self.bot.wikipedia.opensearch(topic))[0]
            text = await page.summary()
        except (aiowiki.exceptions.PageNotFound, IndexError):
            return await ctx.send('No wikipedia article found, sorry.')
        if not text:
            return await ctx.send('Article summary gave no results on call.')
        text = wrap(text, 1000, drop_whitespace=False, replace_whitespace=False)
        embed_list = []
        for description in text:
            embed = self.bot.embed.default(ctx, title=page.title, description=description).set_thumbnail(url=(await page.media())[0])
            embed_list.append(embed)
        await MyPages(EmbedPageSource(embed_list)).start(ctx)

    @group(invoke_without_command=True, aliases=['to-do'])
    async def todo(self, ctx):
        """Todo commands parent.
        It just basically sends the help for its category.
        Call for this command to learn how to use to-do commands."""
        await ctx.send_help('todo')

    @todo.command()
    async def show(self, ctx, number: int = None):
        '''Basically, shows author's todo list.
        Have nothing to explain, so try it and see.'''
        todos = await self.todos.find_one({'_id': ctx.author.id})
        if number:
            return await ctx.send(embed=self.bot.embed.default(ctx, description=f'{number}: {todos["todo"][number]}'))
        else:
            return await MyPages(
                TodoPageSource(ctx, todos['todo'][1:]),
                clear_reactions_after=True,
                timeout=60.0
            ).start(ctx)

    @todo.command()
    async def add(self, ctx, *, message: str):
        '''To-do add command. The message you send will be added to your to-do list.
        Ex: **todo add art project.**'''
        await self.todos.update_one(
            {'_id': ctx.author.id},
            {'$addToSet': {'todo': message}}
        )
        await ctx.message.add_reaction('✅')

    @todo.command()
    async def edit(self, ctx, number: int, *, new_todo: str):
        '''Lets you edit todo with a given number, for example, if you messed up some details.
        Ex: **todo edit 5 play rocket league with teammate at 5 pm**'''
        await self.todos.update_one(
            {'_id': ctx.author.id},
            {'$set': {f'todo.{number}': new_todo}}
        )
        await ctx.message.add_reaction('✅')

    @todo.command()
    async def switch(self, ctx, task_1: int, task_2: int):
        '''Lets user switch their tasks. It is useful when you got more important task.
        Ex: **todo switch 1 12** — switches places of 1st and 12th tasks.'''
        todo_list = (await self.todos.find_one({'_id': ctx.author.id}))['todo']
        await self.todos.update_one(
            {'_id': ctx.author.id},
            {'$set': {
                f'todo.{task_1}': todo_list[task_2],
                f'todo.{task_2}': todo_list[task_1]}
            }
        )
        await ctx.message.add_reaction('✅')

    @todo.command(aliases=['delete', 'rm'])
    async def remove(self, ctx, *numbers: int):
        '''Removes specific to-do from the list
        Ex: **todo remove 7**'''
        todo_list = (await self.todos.find_one({'_id': ctx.author.id}))['todo']
        if len(todo_list) <= 1:
            await ctx.send(f'You have no tasks to delete. To add a task type `{ctx.prefix}todo add <your task here>`')
        for number in numbers:
            if number >= len(todo_list):
                return await ctx.send(f'Could not find todo #{number}')
            await self.todos.update_one({'_id': ctx.author.id}, {'$unset': {f'todo.{number}': 1}})
            await self.todos.update_one({'_id': ctx.author.id}, {'$pull': {'todo': None}})
        await ctx.message.add_reaction('✅')

    @todo.command(aliases=['clear'])
    async def reset(self, ctx):
        '''Resets all elements from user's to-do list.'''
        await self.todos.update_one(
            {'_id': ctx.author.id},
            {'$set': {'todo': ['nothing yet.']}}
        )
        await ctx.message.add_reaction('✅')

    @command(aliases=['g'])
    async def google(self, ctx, *, query: str):
        """Paginated Google-Search command.
        Args: query (str): Your search request. Results will be displayed,
        otherwise returns an error which means no results found."""
        cse = Search(self.bot.config['API']['google_key'])
        safesearch = False if ctx.channel.is_nsfw() else True
        results = await cse.search(query, safesearch=safesearch)
        embed_list = []
        for i in range(0, 10 if len(results) >= 10 else len(results)):
            embed = self.bot.embed.default(
                ctx,
                title=results[i].title,
                description=results[i].description,
                url=results[i].url
            ).set_thumbnail(url=results[i].image_url)
            embed.set_author(
                name=f'Page {i + 1} / {10 if len(results) >= 10 else len(results)}',
                icon_url=ctx.author.avatar_url
            )
            embed_list.append(embed)
        await cse.close()
        await MyPages(
            EmbedPageSource(embed_list),
            delete_message_after=True
        ).start(ctx)

    @command()
    async def poll(self, ctx, question, *options):
        """Make a simple poll using this command. You can also add an image.
        Args: question (str): Title of the poll.
        options (str): Maximum is 10. separate each option by quotation marks."""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        if len(options) > 10:
            raise TooManyOptions('There were too many options to create a poll.')
        elif len(options) < 2:
            raise NotEnoughOptions('There were not enough options to create a poll.')
        elif len(options) == 2 and options[0].lower() == 'yes' and options[1].lower() == 'no':
            reactions = ['<:thumbs_up:746352051717406740>', '<:thumbs_down:746352095510265881>']
        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        embed = self.bot.embed.default(ctx, title=question.replace('\n', ''), description='\n'.join([f'{reactions[x]} {option}' for x, option in enumerate(options)]))
        if ctx.message.attachments:
            embed.set_image(url=ctx.message.attachments[0].url)
        message = await ctx.send(embed=embed)
        for emoji in reactions[:len(options)]:
            await message.add_reaction(emoji)

    @command(aliases=['r'])
    @has_voted()
    async def reddit(self, ctx, subreddit: str):
        """Find a randomized post from subreddit that you want to."""
        cs = self.bot.session
        r = await cs.get(f'https://www.reddit.com/r/{subreddit}/hot.json')
        r = await r.json()
        data = r['data']['children'][random.randint(0, 10)]['data']
        if not ctx.channel.is_nsfw() and data['over_18'] is True:
            raise NSFWChannelRequired(ctx.channel)
        embed = self.bot.embed.default(ctx).set_image(url=data['url'])
        embed.set_author(name=data['title'], icon_url='https://icons.iconarchive.com/icons/papirus-team/papirus-apps/96/reddit-icon.png')
        embed.set_footer(text=f'from {data["subreddit_name_prefixed"]}')
        await ctx.send(embed=embed)

    @command(aliases=['yt'])
    async def youtube(self, ctx, *, search: str):
        """Youtube-Search command. Lets you to search YouTube videos through Discord.
        Args: search (str): Search topic. The bot will send the first faced result."""
        cs = self.bot.session
        r = await cs.get('https://youtube.com/results', params={'search_query': search}, headers={'User-Agent': 'Mozilla/5.0'})
        found = re.findall(r'watch\?v=(\S{11})', await r.text())
        await ctx.send(f'https://youtu.be/{found[0]}')

    @command(aliases=['ud', 'urban'])
    async def urbandictionary(self, ctx, *, word: str):
        """Urban Dictionary words' definition wrapper.
        Args: word (str): A word you want to know the definition of."""
        cs = self.bot.session
        r = await cs.get(f'{self.bot.config["API"]["ud_api"]}?term={word}')
        js = await r.json()
        source = js['list'][0]
        embed = self.bot.embed.default(ctx, description=f"**{source['definition'].replace('[', '').replace(']', '')}**")
        embed.set_author(
            name=word,
            url=source['permalink'],
            icon_url='https://is4-ssl.mzstatic.com/image/thumb/Purple111/v4/7e/49/85/7e498571-a905-d7dc-26c5-33dcc0dc04a8/source/64x64bb.jpg'
        ).add_field(name='Example:', value=js['list'][0]['example'].replace('[', '').replace(']', ''))
        embed.set_footer(text=f'{source["thumbs_up"]}👍 | {source["thumbs_down"]}👎 | {source["written_on"][0:10]}')
        await ctx.send(embed=embed)

    @command(aliases=['calculate', 'calculator'])
    async def calc(self, ctx, *, expression: str):
        """A simple calculator that supports useful features.
        Args: expression (str): Maths expression to solve."""
        lexer = calclex.CalcLexer()
        parser = calcparse.CalcParser()
        reg = ''.join([i for i in expression if i in '()'])
        try:
            if not parser.match(reg):
                raise UnclosedBrackets()
            for i in range(len(expression) - 1):
                if expression[i] == '(' and expression[i + 1] == ')':
                    raise EmptyBrackets()
            result = parser.parse(lexer.tokenize(expression))
        except Exception as e:
            if isinstance(e, Overflow):
                return await ctx.send('Overflow number given.')
            if isinstance(e, UndefinedVariable):
                return await ctx.send(e.exc)
            if isinstance(e, KeywordAlreadyTaken):
                return await ctx.send('The given variable name is shadowing a reserved keyword argument.')
            if isinstance(e, UnclosedBrackets):
                return await ctx.send('Given expression has unclosed brackets.')
            if isinstance(e, EmptyBrackets):
                return await ctx.send('Given expression has empty brackets.')
            if isinstance(e, decimal.InvalidOperation):
                return await ctx.send('Invalid expression given.')
        res = '\n'.join([str(i) for i in result])
        embed = self.bot.embed.default(ctx)
        embed.add_field(name='Input', value=f'```\n{expression}\n```', inline=False)
        embed.add_field(name='Output', value=f'```\n{res}\n```', inline=False)
        await ctx.send(embed=embed)

    @command(aliases=['song', 'lyric'])
    async def lyrics(self, ctx, *, args: str):
        '''Powerful lyrics command.
        Ex: lyrics believer.
        Has no limits.
        You can find lyrics for song that you want.
        Raises an exception if song does not exist in API data.'''
        cs = self.bot.session
        r = await cs.get(f'https://some-random-api.ml/lyrics?title={args.replace(" ", "%20")}')
        js = await r.json()
        try:
            song = wrap(str(js['lyrics']), 1000, drop_whitespace=False, replace_whitespace=False)
            embed_list = []
            for lyrics in song:
                embed = self.bot.embed.default(
                    ctx,
                    title=f'{js["author"]} — {js["title"]}',
                    description=lyrics
                ).set_thumbnail(url=js['thumbnail']['genius'])
                embed_list.append(embed)
            await MyPages(EmbedPageSource(embed_list)).start(ctx)
        except KeyError:
            await ctx.send(f'Could not find lyrics for **{args}**')

    @command(aliases=['colour'])
    async def color(self, ctx, *, color: ColorConverter):
        """Color command.
        Example: **color green**
        Args: color (ColorConverter): Color that you specify.
        It can be either RGB, HEX, or even a human-friendly word."""
        rgb = color.to_rgb()
        embed = self.bot.embed(
            color=discord.Color.from_rgb(*rgb)
        ).set_thumbnail(url=f'https://kal-byte.co.uk/colour/{"/".join(str(i) for i in rgb)}')
        embed.add_field(name='Hex', value=str(color), inline=False)
        embed.add_field(name='RGB', value=str(rgb), inline=False)
        await ctx.send(embed=embed)

    @command(aliases=['ncov', 'coronavirus'])
    async def covid(self, ctx, *, country: Optional[str]):
        '''Coronavirus command.
        Returns world statistics if no country is mentioned.
        • Cases, deaths, recovered cases, active cases, critical cases'''
        cs = self.bot.session
        if not country:
            r = await cs.get(f'{self.bot.config["API"]["covid_api"]}all?yesterday=true&twoDaysAgo=true')
            js = await r.json()
            title = 'Covid-19 World Statistics'
            field = ('Affected Countries', str(js['affectedCountries']))
            url = 'https://www.isglobal.org/documents/10179/7759027/Coronavirus+SARS-CoV-2+de+CDC+en+Unsplash'
        if country:
            r = await cs.get(f'{self.bot.config["API"]["covid_api"]}countries/{country}?yesterday=true&twoDaysAgo=true&strict=true')
            js = await r.json()
            country = country.replace(' ', '+')
            title = f'Covid-19 Statistics for {country}'
            field = ('Continent', str(js['continent']))
            url = str(js['countryInfo']['flag'])

        embed = self.bot.embed.default(ctx).set_thumbnail(url=url)
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
        embed.set_author(name=title, icon_url=ctx.author.avatar_url_as(size=64))
        for name, value in fields:
            embed.add_field(name=name, value=value)
        await ctx.send(embed=embed)

    @command(aliases=['temp', 'temperature'])
    async def weather(self, ctx, *, city: str.capitalize):
        '''Simply gets weather statistics of a given city.
        Gives: Description, temperature, humidity%, atmospheric pressure (hPa)'''
        cs = self.bot.session
        r = await cs.get(f'{self.bot.config["API"]["weather_api"]}appid={self.bot.config["API"]["weather_id"]}&q={city}')
        x = await r.json()
        if x['cod'] != '404':
            y = x['main']
            z = x['weather']
            embed = self.bot.embed.default(ctx, title=f'Weather in {city}')
            embed.set_thumbnail(url='https://i.ibb.co/CMrsxdX/weather.png')
            fields = [
                ('Description', f'**{z[0]["description"]}**', False),
                ('Temperature', f'**{y["temp"] - 273.15:.0f}°C**', False),
                ('Humidity', f'**{y["humidity"]}%**', False),
                ('Atmospheric Pressure', f'**{y["pressure"]}hPa**', False)
            ]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'City `{city}` not found.')

    @command()
    async def translate(self, ctx, language, *, sentence):
        '''Translates a given text to language you want.
        It also shows the pronunciation of a text.
        Ex: **translate ru hello world!**'''
        t = Translator()
        a = t.translate(sentence, dest=language)
        embed = self.bot.embed.default(ctx, title=f'Translating from {a.src} to {a.dest}:')
        embed.add_field(name='Translation:', value=f'```{a.text}```', inline=False)
        embed.add_field(name='Pronunciation:', value=f'```{a.pronunciation}```', inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Useful(bot))
