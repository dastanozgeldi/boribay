from utils.Bot import Bot

bot = Bot(description='An awesome Discord Bot made to make people smile.')

for ext in bot.config['bot']['exts']:
    bot.load_extension(ext)
    bot.log.info(f'-> [MODULE] {ext} loaded.')


@bot.ipc.route()
async def get_general_stats(data):
    return {
        'guild_count': len(bot.guilds),
        'command_count': sum(1 for c in bot.walk_commands()),
        'command_usage': await bot.pool.fetchval('SELECT command_usage FROM bot_stats')
    }

if __name__ == '__main__':
    bot.ipc.start()
    bot.run(bot.config['bot']['token'])
