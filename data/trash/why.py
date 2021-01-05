from utils.CustomEmbed import Embed
from discord.ext import commands


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
