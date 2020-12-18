import discord
from discord.ext import commands
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
cluster = MongoClient(f"mongodb+srv://{os.getenv('db_username')}:{os.getenv('db_password')}@{os.getenv('db_project')}.xyuwh.mongodb.net/{os.getenv('db')}?retryWrites=true&w=majority")
prefixes = cluster.Boribay.prefixes


def get_prefix(client, message):
    prefix = prefixes.find_one({"_id": message.guild.id})['prefix']
    return commands.when_mentioned_or(prefix)(client, message)


client = commands.Bot(command_prefix=get_prefix, intents=discord.Intents.all(), case_insensitive=True)


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Streaming(name=f"{str(len(client.guilds))} servers", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstleyVEVO"))
    print(f'{client.user} is ready!\n')
    extensions = [
        'cogs.events',
        'cogs.owner',
        'cogs.admin',
        'cogs.fun',
        'cogs.useful',
        'cogs.covid',
        'cogs.canvas',
        'cogs.misc',
        'cogs.anime',
        # 'cogs.music',
        'cogs.info',
        'cogs.networks',
        'cogs.help',
        'cogs.errors',
        'cogs.economics',
        'cogs.todo',
        'cogs.piltest',
        'jishaku'
    ]
    if __name__ == "__main__":
        for ext in extensions:
            client.load_extension(ext)
            print(f'[log] {ext} has been loaded.')


@client.command(brief="prefix change (bot owner only)", description="a command that changes a prefix for guild")
@commands.is_owner()
async def prefix(ctx, prefix: str):
    prefixes.update_one({'_id': ctx.guild.id},
                        {"$set": {"prefix": prefix}})
    await ctx.send(f"Prefix has been changed to: {prefix}")


client.run(os.getenv('TOKEN'))
