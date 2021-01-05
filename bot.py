import logging
import os
from logging.handlers import RotatingFileHandler

from discord import AllowedMentions, Game, Intents, Status
from discord.ext.ipc import Server
from discord.flags import MemberCacheFlags
from dotenv import load_dotenv

from utils.CustomBot import Bot

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    filename='./data/logs/discord.log',
    filemode='w'
)

log = logging.getLogger(__name__)
handler = RotatingFileHandler(
    './data/logs/discord.log',
    maxBytes=5242880,
    backupCount=1
)

log.addHandler(handler)
intents = Intents.all()

bot = Bot(
    status=Status.dnd,
    activity=Game(name='.help'),
    case_insensitive=True,
    max_messages=1000,
    allowed_mentions=AllowedMentions(everyone=False, roles=False),
    intents=intents,
    member_cache_flags=MemberCacheFlags.from_intents(intents),
    chunk_guilds_at_startup=False
)
bot_ipc = Server(
    bot=bot,
    host=os.getenv('host'),
    port=os.getenv('port'),
    secret_key=os.getenv('secret_key')
)

bot.version = '0.8.0'
bot.description = '''Created to make life easier and funny.
I have general-purpose features that might help you somewhere :)'''
bot.owner_ids = {682950658671902730, 735489760491077742}
bot.exts = [
    'cogs.events',
    'cogs.owner',
    'cogs.admin',
    'cogs.games',
    'cogs.useful',
    'cogs.canvas',
    'cogs.misc',
    'cogs.anime',
    'cogs.info',
    'cogs.networks',
    'cogs.help',
    'cogs.errors',  # cogs.better
    'cogs.economics',
    'cogs.fun',
    'cogs.todo',
    'cogs.nsfw',
    'jishaku'
]

os.environ['JISHAKU_HIDE'] = 'True'
os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'

for ext in bot.exts:
    bot.load_extension(ext)
    log.info(f'-> [MODULE] {ext[5:] if ext != "jishaku" else ext} loaded.')


@bot.event
async def on_ready():
    log.info(f'Logged in as -> {bot.user.name}')
    log.info(f'Client ID -> {bot.user.id}')
    log.info(f'Guild Count -> {len(bot.guilds)}')


@bot.event
async def on_ipc_ready():
    log.info('IPC ready to go.')


@bot_ipc.route()
async def get_stats_page(data):
    return f'''
        Guilds: {sum(1 for g in bot.guilds)}</br>
        Users: {sum(i.member_count for i in bot.guilds)}</br>
        Commands: {sum(1 for i in bot.commands)}</br>
        Contact the Developer: {await bot.dosek}</br>
    '''


if __name__ == '__main__':
    bot_ipc.start()
    bot.run(os.getenv('TOKEN'))
