from utils import Boribay

bot = Boribay(description='An awesome Discord Bot created to make people smile.')


@bot.ipc.route()
async def get_general_stats(data):
    return {
        'invite_url': bot.config['links']['invite_url'],
        'guild_count': len(bot.guilds),
        'command_count': len(bot.all_commands),
        'command_usage': await bot.pool.fetchval('SELECT command_usage FROM bot_stats')
    }

if __name__ == '__main__':
    bot.run(bot.config['bot']['token'])
