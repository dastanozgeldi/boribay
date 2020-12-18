import asyncio
import inspect
import os
import random
import re
from datetime import datetime
from io import BytesIO
from typing import Optional, Union

import discord
import requests
import wikipedia
from aiohttp import ClientSession
from discord.ext import commands
from dotenv import load_dotenv
from googletrans import Translator

load_dotenv()

URL_REGEX = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
USER_REGEX = '<@[!]?\d*>'


class Useful(commands.Cog, command_attrs=dict(cooldown=commands.Cooldown(1, 10, commands.BucketType.user))):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def gen_password(self, ctx, length: int, uppercase: bool = False, digit: bool = False, chars: bool = False):
        '''
        Basic Password Generator.
        Makes a password with given settings using random.
        '''
        password = ''
        lowercase_letters = 'abcdefghijklmnopqrstuvwxyz'
        uppercase_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        additional_chars = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        for _ in range(length):
            if uppercase is True and digit is False and chars is False:
                password += random.choice((lowercase_letters + uppercase_letters))

            if uppercase is True and digit is True and chars is False:
                password += random.choice((lowercase_letters + uppercase_letters + digits))

            if uppercase is False and digit is True and chars is True:
                password += random.choice((lowercase_letters + digits + additional_chars))

            if uppercase is False and digit is False and chars is True:
                password += random.choice((lowercase_letters + additional_chars))

            if uppercase is True and digit is True and chars is True:
                password += random.choice((lowercase_letters + uppercase_letters + digits + additional_chars))

            else:
                password += random.choice(lowercase_letters)

        await ctx.author.send(f'Generated password is: ```{password}```')

    @commands.command(aliases=['src'])
    async def source(self, ctx, *, command: str = None):
        '''
        Displays my full source code or for a specific command.
        Able to show source code of a:
            • command;
            • group
        To display the source code of a subcommand you can separate it by periods.
        Ex: todo.add — for the add subcommand of the todo command.
        '''
        source_url = 'https://github.com/Dositan/Boribay'
        branch = 'master'
        if command is None:
            return await ctx.send(embed=discord.Embed(
            title='Source Code Here.',
            description='''
            If you are about using my code please star my repo⭐
            You can specify a command name to get its source code.
            ''',
            color=discord.Color.dark_theme(),
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
            # not a built-in command
            location = os.path.relpath(filename).replace('\\', '/')
        else:
            location = module.replace('.', '/') + '.py'
            source_url = 'https://github.com/Rapptz/discord.py'
            branch = 'master'

        final_url = f'{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}'
        await ctx.send(embed=discord.Embed(
            title='Source Code Here.',
            description='If you are about using my code please star my repo⭐',
            color=discord.Color.dark_theme(),
            url=final_url
        ).set_thumbnail(url=self.bot.user.avatar_url))

    @commands.command(brief='caption for an image(attachment) or user avatar.')
    async def caption(self, ctx, member: Union[discord.Member, str] = None):
        '''
        Caption for an image.
        This command describes a given image being just a piece of code.
        Can handle:
            • Image URL;
            • Member Avatar;
            • Image Attachment.
        Ex: caption Dosek
        '''
        if isinstance(member, discord.Member):
            image = str(member.avatar_url)
        elif not isinstance(member, discord.Member) and re.match(URL_REGEX, member):
            image = member
        else:
            image = ctx.message.attachments[0].url
        url = 'https://captionbot.azurewebsites.net/api/messages'
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        payload = {'Content': image, 'Type': 'CaptionRequest'}
        async with ClientSession() as cs:
            async with cs.post(url, headers=headers, json=payload) as r:
                data = await r.text()
        await cs.close()
        embed = discord.Embed(
            color=discord.Color.dark_theme(),
            title=data
        ).set_image(url=image)
        await ctx.send(embed=embed)

    '''Command below is temporarily disabled due to API death.'''
    '''
    @commands.command(name="read", brief="converts an image into text. you can also specify image url instead of attaching something.")
    async def image_to_text(self, ctx, attachment: Optional[str]):
        if attachment is None:
            attachment = ctx.message.attachments[0].url
        try:
            async with ClientSession() as cs:
                async with cs.get(f'https://api.tsu.sh/google/ocr') as r:
                    output = await r.json()
                    await cs.close()
            try:
                await ctx.send(f'**Image to text** for __{ctx.author.display_name}__```{output["text"]}```')
            except discord.HTTPException:
                await ctx.send("Could not get the proper text, sorry.")
        except IndexError:
            await ctx.send("I see no attachments here to make the text.")
    '''

    @commands.command(aliases=["temp", "temperature"], brief="displays weather for a given city")
    async def weather(self, ctx, *, city: str):
        '''
        Simply gets weather statistics of a given city.
        Gives:
            • Description of weather in city;
            • Temperature in °C;
            • Humidity % in city;
            • Atmospheric Pressure data (hPa) in a current city.
        '''
        city = city.capitalize()
        appid = os.getenv('app_id')
        response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?appid={appid}&q={city}')
        x = response.json()
        if x["cod"] != "404":
            async with ctx.channel.typing():
                y = x["main"]
                z = x["weather"]
                weather_embed = discord.Embed(
                    title=f"Weather in {city}",
                    color=discord.Color.dark_theme(),
                    timestamp=ctx.message.created_at
                ).set_thumbnail(url="https://i.ibb.co/CMrsxdX/weather.png")
                fields = [
                    ('Description', f'**{z[0]["description"]}**', False),
                    ('Temperature', f'**{str(round(y["temp"] - 273.15))}°C**', False),
                    ('Humidity', f'**{y["humidity"]}%**', False),
                    ('Atmospheric Pressure', f'**{y["pressure"]}hPa**', False)
                ]
                for name, value, inline in fields:
                    weather_embed.add_field(name=name, value=value, inline=inline)
                await ctx.send(embed=weather_embed)
        else:
            await ctx.send("City not found.")

    @commands.command(aliases=['t'], brief="translates text to given language")
    async def translate(self, ctx, lang, *, args):
        '''
        Translates a given text to language you want.
        It also shows the pronunciation of a text.
        Ex: translate ru hello world!
        '''
        t = Translator()
        a = t.translate(args, dest=lang)
        trans_embed = discord.Embed(title=f"Translating from {a.src} to {a.dest}:", colour=0x0F91E8)
        trans_embed.add_field(name="Translation:", value=f"```{a.text}```", inline=False)
        trans_embed.add_field(name="Pronunciation:", value=f"```{a.pronunciation}```", inline=False)
        await ctx.send(embed=trans_embed)

    @commands.command(aliases=['wikipedia'], brief="wikipedia definitions in english")
    async def wiki(self, ctx, *, arg):
        '''
        Search from wikipedia.
        Has limits:
            • Max sentences: 3;
            • Max characters: 1000.
        In case if you want to search for a whole Wikipedia article,
        I'd recommend you to use .google command (.help google)
        Ex: wiki Coulomb
        '''
        def wiki_summary(arg):
            definition = wikipedia.summary(arg, sentences=3, chars=1000, auto_suggest=True, redirect=True)
            return definition
        wiki_embed = discord.Embed(colour=ctx.author.color, title=f"Definition for {arg}", description=wiki_summary(arg))
        await ctx.send(embed=wiki_embed)

    @commands.command(aliases=['cd'], brief="countdown for a given time")
    async def countdown(self, ctx, time: int, *, args):
        '''
        A very simple countdown function.
        Ex: countdown 10 A new day starts
        '''
        starting_time = time
        cd_embed = discord.Embed(title=args, description=f"{time} seconds left...", colour=discord.Color.gold(), timestamp=datetime.utcnow())
        await ctx.send(embed=cd_embed)
        while time > 0:
            time -= 1
            await asyncio.sleep(1)
        await ctx.send(f"{ctx.author}, a countdown for {starting_time} seconds has ended!")


def setup(bot):
    bot.add_cog(Useful(bot))
