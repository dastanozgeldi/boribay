import random
import re
from io import BytesIO
from typing import Optional
import discord
from discord.ext import commands
from utils.Cog import Cog


class Fun(Cog):
    '''Fun extension. Hope the name makes sense and commands correspond
    their parent.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '🎉 Fun'

    @commands.command(name='random')
    async def random_command(self, ctx):
        """Executes a random command that the bot has.
        Perfect feature when you want to use Boribay but don't even know
        what to call."""
        denied = ['random', 'jishaku', 'dev']
        command = random.choice([cmd.name for cmd in self.bot.commands if len(cmd.signature.split()) <= 1 and cmd.name not in denied])
        cmd = self.bot.get_command(command)
        await ctx.send('Invoking command `%s`...' % command)
        await cmd(ctx)

    @commands.command()
    async def eject(self, ctx, color: str.lower, is_impostor: bool, *, name: Optional[str]):
        '''Among Us ejected meme maker.
        Colors: black • blue • brown • cyan • darkgreen • lime • orange • pink • purple • red • white • yellow.
        Ex: eject blue True Dosek.'''
        name = name or ctx.author.display_name
        cs = self.bot.session
        r = await cs.get(f'https://vacefron.nl/api/ejected?name={name}&impostor={is_impostor}&crewmate={color}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename='ejected.png'))

    @commands.command(aliases=['ss'])
    async def screenshot(self, ctx, url: str):
        """Screenshot command.
        Args: url (str): a web-site that you want to get a screenshot from."""
        if not re.search("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url):
            return await ctx.send("Please leave a valid url!")
        cs = self.bot.session
        r = await cs.get(f'{self.bot.config["API"]["screenshot_api"]}{url}')
        io = BytesIO(await r.read())
        await ctx.send(file=discord.File(fp=io, filename="screenshot.png"))

    @commands.command(aliases=['pp', 'penis'])
    async def peepee(self, ctx, member: discord.Member = None):
        """Basically, returns your PP size."""
        member = member or ctx.author
        random.seed(member.id)
        sz = 100 if member.id in self.bot.owner_ids else random.randint(1, 10)
        await ctx.send(f'{member.display_name}\'s pp size is:\n||%s||' % f'8{"=" * sz}D')

    @commands.command()
    async def uselessfact(self, ctx):
        """Returns an useless fact."""
        cs = self.bot.session
        r = await cs.get('https://uselessfacts.jsph.pl/random.json?language=en')
        js = await r.json()
        await ctx.send(embed=self.bot.embed.default(ctx, description=js['text']))


def setup(bot):
    bot.add_cog(Fun(bot))
