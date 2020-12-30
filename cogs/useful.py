import inspect
import os
import re
from textwrap import wrap
from typing import Optional, Union

import discord
import numexpr
import requests
import wikipedia
from discord.ext import commands
from dotenv import load_dotenv
from googletrans import Translator
from utils.Converters import ColorConverter
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed

load_dotenv()

URL_REGEX = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
USER_REGEX = '<@[!]?\d*>'


class Useful(Cog, command_attrs=dict(cooldown=commands.Cooldown(1, 5, commands.BucketType.user))):
    def __init__(self, bot):
        self.bot = bot
        self.name = '📐 Useful'

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
        if not country:
            r = await cs.get('https://disease.sh/v3/covid-19/all?yesterday=true&twoDaysAgo=true')
            js = await r.json()
            title = 'Covid-19 World Statistics'
            field = ('Countries', str(js['affectedCountries']))
            url = 'https://www.isglobal.org/documents/10179/7759027/Coronavirus+SARS-CoV-2+de+CDC+en+Unsplash'
        if country:
            r = await cs.get(f'https://disease.sh/v3/covid-19/countries/{country}?yesterday=true&twoDaysAgo=true&strict=true')
            js = await r.json()
            country = country.replace(' ', '+')
            title = f'Covid-19 Statistics for {country}'
            field = ('Continent', str(js['continent']))
            url = str(js['countryInfo']['flag'])

        embed = Embed(title=title).set_thumbnail(url=url)
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

    @commands.command(brief="specific continent's covid statistics")
    async def continent(self, ctx, *, continent: str):
        continent = continent.replace(' ', '+')
        cs = self.bot.session
        r = await cs.get(f'https://disease.sh/v3/covid-19/continents/{continent}?yesterday=true&twoDaysAgo=true')
        js = await r.json()

        embed = Embed(
            title=f"**Covid-19 Statistics in {str(js['continent'])}**")
        fields = [
            ('Total Cases', str(js['cases'])),
            ('Today Cases', str(js['todayCases'])),
            ('Deaths', str(js['deaths'])),
            ('Today Deaths', str(js['todayDeaths'])),
            ('Recovered', str(js['recovered'])),
            ('Today Recov', str(js['todayRecovered'])),
            ('Active Cases', str(js['active'])),
            ('Critical', str(js['critical'])),
            ('Tests', str(js['tests']))
        ]
        for name, value in fields:
            embed.add_field(name=name, value=value)
        await ctx.send(embed=embed)

    @commands.command(aliases=['src'])
    async def source(self, ctx, *, command: str = None):
        '''Displays my full source code or for a specific command.
        Able to show source code of a:
            • command;
            • group
        To display the source code of a subcommand you can separate it by periods.
        Ex: **source todo.add** — for the add subcommand of the todo command.'''
        source_url = 'https://github.com/Dositan/Boribay'
        branch = 'master'
        if command is None:
            return await ctx.send(embed=Embed(
                title='Source Code Here.',
                description='''
                If you are about using my code please star my repo⭐
                You can specify a command name to get its source code.
                ''',
                url=source_url
            ).set_thumbnail(url=self.bot.user.avatar_url))

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
            branch = 'master'

        final_url = f'{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'
        await ctx.send(embed=Embed(
            title='Source Code Here.',
            description='If you are about using my code please star my repo⭐',
            url=final_url
        ).set_thumbnail(url=self.bot.user.avatar_url))

    @commands.command(brief='caption for an image(attachment) or user avatar.')
    async def caption(self, ctx, argument: Union[discord.Member, str] = None):
        '''Caption for an image.
        This command describes a given image being just a piece of code.
        Can handle:
            • Image URL;
            • Member Avatar;
            • Image Attachment.
        Ex: **caption Dosek**'''
        if isinstance(argument, discord.Member):
            image = str(argument.avatar_url)
        elif argument and not isinstance(argument, discord.Member) and re.match(URL_REGEX, argument):
            image = argument
        elif not argument and ctx.message.attachments:
            image = ctx.message.attachments[0].url
        else:
            image = str(ctx.author.avatar_url)
        url = 'https://captionbot.azurewebsites.net/api/messages'
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        payload = {'Content': image, 'Type': 'CaptionRequest'}
        cs = self.bot.session
        r = await cs.post(url, headers=headers, json=payload)
        data = await r.text()
        embed = Embed(title=data).set_image(url=image)
        await ctx.send(embed=embed)

    @commands.command(aliases=["temp", "temperature"], brief="displays weather for a given city")
    async def weather(self, ctx, *, city: str):
        '''Simply gets weather statistics of a given city.
        Gives:
            • Description of weather in city;
            • Temperature in °C;
            • Humidity % in city;
            • Atmospheric Pressure data (hPa) in a current city.'''
        city = city.capitalize()
        appid = os.getenv('app_id')
        response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?appid={appid}&q={city}')
        x = response.json()
        if x["cod"] != "404":
            async with ctx.typing():
                y = x["main"]
                z = x["weather"]
                embed = Embed(title=f"Weather in {city}").set_thumbnail(url="https://i.ibb.co/CMrsxdX/weather.png")
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
            await ctx.send("City not found.")

    @commands.command(aliases=['t'], brief="translates text to given language")
    async def translate(self, ctx, lang, *, args):
        '''Translates a given text to language you want.
        It also shows the pronunciation of a text.
        Ex: **translate ru hello world!**'''
        t = Translator()
        a = t.translate(args, dest=lang)
        embed = Embed(title=f"Translating from {a.src} to {a.dest}:")
        embed.add_field(name="Translation:", value=f"```{a.text}```", inline=False)
        embed.add_field(name="Pronunciation:", value=f"```{a.pronunciation}```", inline=False)
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
                await ctx.channel.send("Sorry, could not find any results.")

            else:
                new_search = results[0]
                wiki = wikipedia.page(new_search)
                text = wrap(wiki.summary, 500, break_long_words=True, replace_whitespace=False)
                embed = Embed(title=wiki.title, description=f'{text[0]}...', url=wiki.url)
                await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Useful(bot))
