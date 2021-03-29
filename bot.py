from discord.ext import commands
from utils import Boribay

bot = Boribay(description='An awesome Discord Bot created to make people smile.')


@bot.check
async def is_blacklisted(ctx):
    if not (user := bot.user_cache[ctx.author.id]):
        pass

    return not user.get('blacklisted', False)


@bot.check
async def is_on_maintenance(ctx):
    if bot.cache.get('maintenance_mode') and ctx.author.id not in bot.owner_ids:
        raise commands.CheckFailure('The bot is currently in maintenance mode.')

    return True

if __name__ == '__main__':
    bot.run(bot.config['bot']['token'])
