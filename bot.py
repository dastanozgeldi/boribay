import logging
import os
from logging.handlers import RotatingFileHandler
from discord import AllowedMentions, Game, Intents
from discord.flags import MemberCacheFlags
from utils.Bot import Bot
from discord.ext.ipc import Server

logging.basicConfig(filename='./data/logs/discord.log', filemode='w', level=logging.INFO)
intents = Intents.default()
intents.members = True
bot = Bot(
    intents=intents,
    max_messages=1000,
    case_insensitive=True,
    activity=Game(name='.help'),
    chunk_guilds_at_startup=False,
    member_cache_flags=MemberCacheFlags.from_intents(intents),
    allowed_mentions=AllowedMentions(everyone=False, roles=False, replied_user=False),
)
bot.ipc = Server(
    bot=bot,
    host=bot.config['ipc']['host'],
    port=bot.config['ipc']['port'],
    secret_key=bot.config['ipc']['secret_key']
)
bot.log = logging.getLogger(__name__)
handler = RotatingFileHandler('./data/logs/discord.log', maxBytes=5242880, backupCount=1)
bot.log.addHandler(handler)

os.environ['JISHAKU_HIDE'] = 'True'
os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'

for ext in bot.exts:
    bot.load_extension(ext)
    bot.log.info(f'-> [MODULE] {ext} loaded.')


@bot.event
async def on_ready():
    bot.log.info(f'Logged in as -> {bot.user.name}')
    bot.log.info(f'Client ID -> {bot.user.id}')
    bot.log.info(f'Guild Count -> {len(bot.guilds)}')


@bot.ipc.route()
async def get_commands_page(self, data):
    return ' • '.join([i.name for i in self.bot.commands])


@bot.ipc.route()
async def get_stats_page(self, data):
    return f'''Guilds: {len(bot.guilds)}</br>
Users: {sum(g.member_count for g in bot.guilds)}</br>
Commands: {sum(1 for i in bot.commands)}</br>
Contact the developer: {bot.dosek}</br>'''


if __name__ == '__main__':
    bot.ipc.start()
    bot.run(bot.config['bot']['token'])
