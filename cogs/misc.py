from time import time
from discord.ext import commands
from utils.CustomCog import Cog
from utils.Exceptions import TooManyOptions, NotEnoughOptions


class Miscellaneous(Cog):
    '''Misc commands extension. Here owner includes commands that aren't related to other categories.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '💫 Miscellaneous'

    @commands.command(aliases=['hi', 'hey'], brief="greeting, nothing else.")
    async def hello(self, ctx):
        """Introduction"""
        await ctx.send(f'Hello there! I am {self.bot.user}, created by {self.bot.dosek}')

    @commands.command()
    async def prefix(self, ctx):
        """See bot\'s prefix."""
        prefix = await self.bot.pool.fetchval('SELECT prefix FROM guild_config WHERE guild_id = $1', ctx.guild.id)
        await ctx.send(embed=self.bot.embed(description=f'Hey, I see, someone mentioned me.\n'
                                            f'The current prefix for this server is: `{prefix}`\n'
                                            'But you can still use my features by mentioning me.'))

    @commands.command()
    async def invite(self, ctx):
        """Some useful invites (support server and the bot itself)"""
        embed = self.bot.embed(
            description=f'To invite me to your server click [here]({self.bot.invite_url})\n'
                        f'If you have some issues you can join to my support server clicking [here]({self.bot.support_url})'
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Check latency of the bot and its system."""
        start = time()
        message = await ctx.send("Pinging...")
        end = time()
        embed = self.bot.embed()
        embed.add_field(name='<a:loading:787357834232332298> Websocket:', value=f'{round(self.bot.latency * 1000)}ms')
        embed.add_field(name='<a:typing:787357087843745792> Typing:', value=f'{round((end - start) * 1000)}ms')
        embed.add_field(name='<:pg:795005204289421363> Database:', value=await self.bot.db_latency())
        await message.edit(embed=embed)

    @commands.command(aliases=['vote'])
    async def poll(self, ctx, question, *options):
        """Make a simple poll using this command. You can also add an image.
        Args: question (str): title of the poll. write it in quotes.
        options (str): maximum count is 10. separate options by quotes, I mean,
        write each option in its own quotation marks, "like this"."""
        limit = 10
        if len(options) > limit:
            raise TooManyOptions('There were too many options to create a poll.')
        elif len(options) < 2:
            raise NotEnoughOptions('There were not enough options to create a poll.')
        elif len(options) == 2 and options[0].lower() == 'yes' and options[1].lower() == 'no':
            reactions = ['<:thumbs_up:746352051717406740>', '<:thumbs_down:746352095510265881>']
        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        description = []
        for x, option in enumerate(options):
            description += f'\n {reactions[x]} {option}'
        embed = self.bot.embed(title=question.replace('\n', ''), description=''.join(description))
        if ctx.message.attachments:
            embed.set_image(url=ctx.message.attachments[0].url)
        message = await ctx.send(embed=embed)

        for emoji in reactions[:len(options)]:
            await message.add_reaction(emoji)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
