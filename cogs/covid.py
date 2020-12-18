from discord.ext import commands
import aiohttp
import discord
from typing import Optional


class Covid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['ncov', 'coronavirus'], brief="coronavirus statistics, you can also specify a country to see statistics for a given one.")
    async def covid(self, ctx, *, country: Optional[str]):
        if country is None:
            async with aiohttp.ClientSession() as cs:
                async with cs.get('https://disease.sh/v3/covid-19/all?yesterday=true&twoDaysAgo=true') as r:
                    js = await r.json()
            covid_embed = discord.Embed(
                title="Covid-19 World Statistics",
                color=discord.Color.red()
            ).set_thumbnail(url='https://www.isglobal.org/documents/10179/7759027/Coronavirus+SARS-CoV-2+de+CDC+en+Unsplash')
            fields = [
                ('Total Cases', str(js['cases'])),
                ('Today Cases', str(js['todayCases'])),
                ('Deaths', str(js['deaths'])),
                ('Today Deaths', str(js['todayDeaths'])),
                ('Recovered', str(js['recovered'])),
                ('Today Recov', str(js['todayRecovered'])),
                ('Active Cases', str(js['active'])),
                ('Critical', str(js['critical'])),
                ('Countries', str(js['affectedCountries']))
            ]
            for name, value in fields:
                covid_embed.add_field(name=name, value=value)
            await ctx.send(embed=covid_embed)
        else:
            country = country.replace(' ', '+')
            async with aiohttp.ClientSession() as cs:
                async with cs.get(f'https://disease.sh/v3/covid-19/countries/{country}?yesterday=true&twoDaysAgo=true&strict=true') as r:
                    js = await r.json()
            flag = str(js['countryInfo']['flag'])
            cases = str(js['cases'])
            todayCases = str(js['todayCases'])
            deaths = str(js['deaths'])
            todayDeaths = str(js['todayDeaths'])
            recovered = str(js['recovered'])
            todayRecovered = str(js['todayRecovered'])
            active = str(js['active'])
            critical = str(js['critical'])
            continent = str(js['continent'])
            country_embed = discord.Embed(
                title=f"Covid-19 Statistics for {country}",
                color=ctx.author.color).set_thumbnail(url=flag)
            fields = [
                ('Continent', continent),
                ('Total Cases', cases),
                ('Today Cases', todayCases),
                ('Deaths', deaths),
                ('Today Deaths', todayDeaths),
                ('Recovered', recovered),
                ('Today Recov', todayRecovered),
                ('Active Cases', active),
                ('Critical', critical)
            ]
            for name, value in fields:
                country_embed.add_field(name=name, value=value)
            await ctx.send(embed=country_embed)

    @commands.command(brief="specific continent's covid statistics")
    async def continent(self, ctx, *, continent: str):
        continent = continent.replace(' ', '+')
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f'https://disease.sh/v3/covid-19/continents/{continent}?yesterday=true&twoDaysAgo=true') as r:
                js = await r.json()
        cases = str(js['cases'])
        todayCases = str(js['todayCases'])
        deaths = str(js['deaths'])
        todayDeaths = str(js['todayDeaths'])
        recovered = str(js['recovered'])
        todayRecovered = str(js['todayRecovered'])
        active = str(js['active'])
        critical = str(js['critical'])
        continent = str(js['continent'])
        tests = str(js['tests'])
        cont_embed = discord.Embed(
            title=f"**Covid-19 Statistics in {continent}**",
            color=ctx.author.color)
        fields = [
            ('Total Cases', cases),
            ('Today Cases', todayCases),
            ('Deaths', deaths),
            ('Today Deaths', todayDeaths),
            ('Recovered', recovered),
            ('Today Recov', todayRecovered),
            ('Active Cases', active),
            ('Critical', critical),
            ('Tests', tests)
        ]
        for name, value in fields:
            cont_embed.add_field(name=name, value=value)
        await ctx.send(embed=cont_embed)


def setup(bot):
    bot.add_cog(Covid(bot))
