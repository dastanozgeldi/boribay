import random
from io import BytesIO
from typing import Optional
import discord
from discord.ext import commands
from utils.Cog import Cog
from utils.Bottom import from_bottom, to_bottom


class Fun(Cog):
    '''Fun extension. Hope the name makes sense and commands correspond
    their parent.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '🎉 Fun'

    @commands.group(invoke_without_command=True)
    async def bottom(self, ctx):
        """Bottom is an encoding format made by a set of "bottom" emojis.
        You can find bottom-related repositories at https://github.com/bottom-software-foundation
        Run `bottom encode hello world` to see how it works."""
        await ctx.send_help('bottom')

    @bottom.command()
    async def encode(self, ctx, text):
        """Encode the normal text into bottom."""
        await ctx.send(to_bottom(text))

    @bottom.command()
    async def decode(self, ctx, text):
        """Decode the normal text into bottom."""
        await ctx.send(from_bottom(text))

    @commands.command(name='random')
    async def random_command(self, ctx):
        """Executes a random command that the bot has.
        Perfect feature when you want to use Boribay but don't even know
        what to call."""
        denied = ['random', 'jishaku', 'dev']
        command = random.choice([cmd.name for cmd in self.bot.commands if len(cmd.signature.split()) == 0 and cmd.name not in denied])
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
