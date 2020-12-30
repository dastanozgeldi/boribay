import os
import re
from io import BytesIO

import discord
from discord.ext.commands import Cog, ExtensionError, command
from dotenv import load_dotenv
from mystbin import Client

myst = Client()
load_dotenv()


class Owner(Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @command()
    async def test(self, ctx, *, text: str):
        paste = await myst.post(text, syntax='python')
        await ctx.send(paste.url)

    @command(name='ocr')
    async def imagetotext(self, ctx, url: str = None):
        if url and not re.search("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url):
            return await ctx.send('Please leave a valid url!')
        if ctx.message.attachments and not url:
            url = ctx.message.attachments[0].url
        else:
            url = url
        async with ctx.timeit:
            cs = self.bot.session
            r = await cs.get(f'https://api.ocr.space/parse/imageurl?apikey={os.getenv("ocr")}&url={url}&detectOrientation=true&scale=true')
            output = await r.json()
            await ctx.send(f"```{output['ParsedResults'][0]['ParsedText']}```")

    @command(aliases=['ss'], brief="see a screenshot of a given url.")
    async def screenshot(self, ctx, url: str):
        if not re.search("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url):
            return await ctx.send("Please leave a valid url!")
        cs = self.bot.session
        r = await cs.get(f'https://image.thum.io/get/width/1920/crop/675/maxAge/1/noanimate/{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename="screenshot.png"))

    @command(aliases=['l'], brief='Loads a module.')
    async def load(self, ctx, *, module: str):
        try:
            self.bot.load_extension(module)
        except ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @command(aliases=['u'], brief='Unloads a module.')
    async def unload(self, ctx, *, module: str):
        try:
            self.bot.reload_extension(module)
        except ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @command(name='reload', aliases=['r'], brief='Reloads a module.')
    async def _reload(self, ctx, *, module: str):
        try:
            self.bot.reload_extension(module)
        except ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.message.add_reaction('🔄')


def setup(bot):
    bot.add_cog(Owner(bot))
