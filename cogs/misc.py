import platform
from datetime import datetime, timedelta
from time import time

import psutil as p
from discord.ext import commands
from utils.CustomCog import Cog
from utils.CustomEmbed import Embed


class Misc(Cog):
    '''Misc commands extension. Here owner includes commands that aren't related to other categories.'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '💫 Miscellaneous'
        self.numbers = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟')

    @commands.command(aliases=['hi', 'hey'], brief="greeting, nothing else.")
    async def hello(self, ctx):
        await ctx.send(f'Hello there! I am {self.bot.user}, created by {self.bot.dosek}')

    @commands.command(name='invite', brief='invite me to your server!')
    async def invite_command(self, ctx):
        embed = Embed(
            description=f'''To invite me to your server click [here]({self.bot.invite_url})
            If you have some issues you can join to my support server clicking [here]({self.bot.support_url})'''
        )
        await ctx.send(embed=embed)

    @commands.command(name="system", aliases=['sys'], brief="shows the characteristics of my system")
    async def system_info(self, ctx):
        embed = Embed(title="System Info").set_thumbnail(url="https://cdn.discordapp.com/attachments/735725378433187901/776524927708692490/data-server.png")
        pr = p.Process()
        info = {
            'System': {
                'Username': pr.as_dict(attrs=["username"])['username'],
                'Host OS': platform.platform(),
                'Uptime': timedelta(seconds=time() - p.boot_time()),
                'Boot time': datetime.fromtimestamp(p.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            },
            'CPU': {
                'Frequency': f"{p.cpu_freq(percpu=True)[0][0]} MHz",
                'CPU Used': f"{p.cpu_percent(interval=1)}%",
                'Time on CPU': timedelta(seconds=p.cpu_times().system + p.cpu_times().user),
            },
            'Memory': {
                'RAM Used': f"{p.virtual_memory().percent}%",
                'RAM Available': f"{p.virtual_memory().available/(1024**3):,.3f} GB",
                'Disk Used': f"{p.disk_usage('/').percent}%",
                'Disk Free': f"{p.disk_usage('/').free/(1024**3):,.3f} GB",
            }
        }
        embed.add_field(name="**➤ System**", value="\n".join([f"**{key}** : {value}" for key, value in info['System'].items()]), inline=False)
        embed.add_field(name="**➤ CPU**", value="\n".join([f"**{key}** : {value}" for key, value in info['CPU'].items()]), inline=False)
        embed.add_field(name="**➤ Memory**", value="\n".join([f"**{key}** : {value}" for key, value in info['Memory'].items()]), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        start = time()
        message = await ctx.send("Pinging...")
        end = time()
        embed = Embed()
        embed.add_field(name='<a:loading:787357834232332298> Websocket:', value=f'{round(self.bot.latency * 1000)}ms')
        embed.add_field(name='<a:typing:787357087843745792> Typing:', value=f'{round((end - start) * 1000)}ms')
        embed.add_field(name='<:mongo:791421726915297290> Database:', value=await self.bot.db_latency())
        await message.edit(embed=embed)

    @commands.command(aliases=['vote'], brief="create a cool poll!")
    async def poll(self, ctx, question, *options):
        limit = 10
        if len(options) > limit:
            await ctx.send('You can only add a maximum of 10 responses per vote!')
            return
        elif len(options) < 2:
            await ctx.send('You should type at least 2 responses to create a vote!')
            return

        elif len(options) == 2 and options[0].lower() == 'yes' and options[1].lower() == 'no':
            reactions = ['👍', '👎']
        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        description = []
        for x, option in enumerate(options):
            description += f'\n {reactions[x]} {option}'
        embed = Embed(title=question.replace('\n', ''), description=''.join(description))
        if ctx.message.attachments:
            embed.set_image(url=ctx.message.attachments[0].url)
        embed.set_thumbnail(url="https://cdn0.iconfinder.com/data/icons/kirrkle-internet-and-websites/60/12_-_Poll-256.png")
        message = await ctx.send(embed=embed)

        for emoji in reactions[:len(options)]:
            await message.add_reaction(emoji)


def setup(bot):
    bot.add_cog(Misc(bot))
