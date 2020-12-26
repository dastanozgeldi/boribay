import logging
import os
from logging.handlers import RotatingFileHandler

from discord import AllowedMentions, Game, Intents, Status
from discord.ext import commands
from discord.flags import MemberCacheFlags
from dotenv import load_dotenv

from utils.CustomBot import Bot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='./logs/discord.log',
    filemode='w'
)

log = logging.getLogger(__name__)
handler = RotatingFileHandler(
    './logs/discord.log',
    maxBytes=5242880,
    backupCount=1
)

log.addHandler(handler)
new_guilds = False
my_mentions = AllowedMentions(everyone=False, roles=False)
my_intents = Intents.all()
my_intents.members = True
stuff_to_cache = MemberCacheFlags.from_intents(my_intents)

bot = Bot(
    status=Status.dnd,
    activity=Game(name='.help'),
    case_insensitive=True,
    max_messages=1000,
    allowed_mentions=my_mentions,
    intents=my_intents,
    member_cache_flags=stuff_to_cache,
    chunk_guilds_at_startup=False
)

bot.version = '0.6.9'
bot.description = '''Created to make life easier and funny.
I have general-purpose features that might help you somewhere :)'''
bot.owner_ids = {682950658671902730, 735489760491077742}
bot.exts = [
    'cogs.events',
    'cogs.owner',
    'cogs.admin',
    'cogs.fun',
    'cogs.useful',
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
    'cogs.test',
    'jishaku'
]

os.environ['JISHAKU_HIDE'] = 'True'
os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'

for ext in bot.exts:
    bot.load_extension(ext)
    log.info(f'-> [MODULE] {ext[5:]} loaded.')


@bot.event
async def on_ready():
    log.info(f'Logged in as -> {bot.user.name}')
    log.info(f'Client ID -> {bot.user.id}')
    log.info(f'Guild Count -> {len(bot.guilds)}')


@bot.command(brief='See bot\'s prefix.')
async def prefix(ctx):
    prefix = bot.prefixes.find_one({'_id': ctx.guild.id})['prefix']
    await ctx.send(f'The current prefix for this server is: {prefix}')


bot.run(os.getenv('TOKEN'))
