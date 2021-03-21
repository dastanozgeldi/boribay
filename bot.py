from utils import Boribay

bot = Boribay(description='An awesome Discord Bot created to make people smile.')


@bot.check
async def is_blacklisted(ctx):
    if not (user := bot.user_cache[ctx.author.id]):
        pass

    return not user.get('blacklisted', False)

if __name__ == '__main__':
    bot.run(bot.config['bot']['token'])
