import inspect
import os
from textwrap import wrap
from typing import Optional

import discord
import numexpr
import wikipedia
from discord.ext import commands
from dotenv import load_dotenv
from googletrans import Translator
from utils.Converters import ColorConverter
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed
from utils.Manipulation import make_image_url
from utils.Paginators import EmbedPageSource, MyPages

load_dotenv()

URL_REGEX = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
USER_REGEX = '<@[!]?\d*>'


class Useful(Cog, command_attrs=dict(cooldown=commands.Cooldown(1, 5, commands.BucketType.user))):
    def __init__(self, bot):
        self.bot = bot
        self.name = '📐 Useful'

    @commands.command(aliases=['song', 'track', 'lyric'], brief='find almost every song lyrics with this command.')
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
            song = str(js['lyrics'])
            song = wrap(song, 1000, drop_whitespace=False, replace_whitespace=False)
            embed_list = []
            for lyrics in song:
                embed = Embed(
                    title=f'{js["author"]} — {js["title"]}',
                    description=lyrics
                ).set_thumbnail(url=js['thumbnail']['genius'])
                embed_list.append(embed)
            p = MyPages(source=EmbedPageSource(embed_list))
            await p.start(ctx)
        except KeyError:
            await ctx.send(f'Could not find lyrics for **{args}**')

    @commands.command(aliases=['calculate', 'calculator'], brief='calculator command.')
    async def calc(self, ctx, *, equation: str):
        try:
            solution = numexpr.evaluate(str(equation)).item()
            embed = Embed.default(ctx)
            embed.add_field(name='Input:', value=f'```{equation}```', inline=False)
            embed.add_field(name='Output:', value=f'```{solution}```', inline=False)
            await ctx.send(embed=embed)
        except ZeroDivisionError:
            await ctx.send('Infinity')

    @commands.command(aliases=['colour'])
    async def color(self, ctx, *, color: ColorConverter):
        """Color command.
        Example: **color green**
        Args: color (ColorConverter): Color that you specify. It can be either RGB, HEX, or even a word.
        """
        rgb = color.to_rgb()
        embed = Embed.default(
            ctx=ctx, color=discord.Color.from_rgb(*rgb)
        ).set_thumbnail(url=f'https://kal-byte.co.uk/colour/{"/".join(str(i) for i in rgb)}')
        embed.add_field(name='Hex', value=str(color), inline=False)
        embed.add_field(name='RGB', value=str(rgb), inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['ncov', 'coronavirus'])
    async def covid(self, ctx, *, country: Optional[str]):
        '''Coronavirus command.
        Returns world statistics if no country is mentioned.
        • Total and today cases;
        • Total and today deaths;
        • Total and today recovered;
        • Active cases
        • Critical cases'''
        cs = self.bot.session
        url = os.getenv('covid')
        if not country:
            r = await cs.get(f'{url}all?yesterday=true&twoDaysAgo=true')
            js = await r.json()
            title = 'Covid-19 World Statistics'
            field = ('Affected Countries', str(js['affectedCountries']))
            url = 'https://www.isglobal.org/documents/10179/7759027/Coronavirus+SARS-CoV-2+de+CDC+en+Unsplash'
        if country:
            r = await cs.get(f'{url}countries/{country}?yesterday=true&twoDaysAgo=true&strict=true')
            js = await r.json()
            country = country.replace(' ', '+')
            title = f'Covid-19 Statistics for {country}'
            field = ('Continent', str(js['continent']))
            url = str(js['countryInfo']['flag'])

        embed = Embed().set_thumbnail(url=url)
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
        embed.set_author(name=title, icon_url=ctx.author.avatar_url_as(size=128))
        for name, value in fields:
            embed.add_field(name=name, value=value)
        await ctx.send(embed=embed)

    @commands.command(aliases=['src'])
    async def source(self, ctx, *, command: str = None):
        '''Displays my full source code or for a specific command.
        Able to show source code of either command or a group.
        To display the source code of a subcommand you can separate it by periods.
        Ex: **source todo.add** — for the add subcommand of the todo command.'''
        source_url = 'https://github.com/Dositan/Boribay'
        if command is None:
            return await ctx.send(source_url)

        if command == 'help':
            src = type(self.bot.help_command)
            module = src.__module__
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace('.', ' '))
            if obj is None:
                return await ctx.send(f'Command **{command}** not found.')

            src = obj.callback.__code__
            module = obj.callback.__module__
            filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith('discord'):
            location = os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'

        await ctx.send(f'{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}')

    @commands.command()
    async def caption(self, ctx, arg: Optional[str]):
        '''Caption for an image.
        This command describes a given image being just a piece of code.
        Can handle either image, member or even URL.
        Ex: **caption Dosek**'''
        image = await make_image_url(ctx, arg)
        cs = self.bot.session
        url = os.getenv('caption')
        r = await cs.post(url, json={'Content': image, 'Type': 'CaptionRequest'})
        await ctx.send(embed=Embed(title=await r.text()).set_image(url=image))

    @commands.command(aliases=['temp', 'temperature'])
    async def weather(self, ctx, *, city: str):
        '''Simply gets weather statistics of a given city.
        Gives:
            • Description of weather in city;
            • Temperature in °C;
            • Humidity % in city;
            • Atmospheric Pressure data (hPa) in a current city.'''
        cs = self.bot.session
        r = await cs.get(f'{os.getenv("weather")}appid={os.getenv("app_id")}&q={city}')
        x = await r.json()
        if x["cod"] != "404":
            y = x["main"]
            z = x["weather"]
            embed = Embed(title=f'Weather in {city.capitalize()}').set_thumbnail(url='https://i.ibb.co/CMrsxdX/weather.png')
            fields = [
                ('Description', f'**{z[0]["description"]}**', False),
                ('Temperature', f'**{str(round(y["temp"] - 273.15))}°C**', False),
                ('Humidity', f'**{y["humidity"]}%**', False),
                ('Atmospheric Pressure', f'**{y["pressure"]}hPa**', False)
            ]
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'City `{city}` not found.')

    @commands.command()
    async def translate(self, ctx, language, *, sentence):
        '''Translates a given text to language you want.
        It also shows the pronunciation of a text.
        Ex: **translate ru hello world!**'''
        t = Translator()
        a = t.translate(sentence, dest=language)
        embed = Embed(title=f'Translating from {a.src} to {a.dest}:')
        embed.add_field(name='Translation:', value=f'```{a.text}```', inline=False)
        embed.add_field(name='Pronunciation:', value=f'```{a.pronunciation}```', inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=['wiki'])
    async def wikipedia(self, ctx, *, search: str = None):
        '''Search from Wikipedia. Updated version.
        Command shows only summary of the page,
        so you can follow the link to see an article in your browser.
        Ex: **wikipedia Python**'''
        async with ctx.typing():
            results = wikipedia.search(search)
            if not len(results):
                return await ctx.send("Sorry, could not find any results.")
            new_search = results[0]
            wiki = wikipedia.page(new_search)
            text = wrap(wiki.summary, 500, break_long_words=True, replace_whitespace=False)
            embed = Embed(title=wiki.title, description=f'{text[0]}...', url=wiki.url)
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Useful(bot))
