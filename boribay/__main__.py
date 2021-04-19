import argparse
import os

from boribay import Boribay

bot = Boribay(description='A Discord Bot created to make people smile.')

parser = argparse.ArgumentParser(description='Put some arguments before starting the bot.')
parser.add_argument('--ipc', action='store_true', help='Start the IPC server.')
parser.add_argument('--exclude', nargs='+',
                    help='Specify Cogs you don\'t want to include on startup!')


if __name__ == '__main__':
    os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
    os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'
    os.environ['JISHAKU_HIDE'] = 'True'

    args = parser.parse_args()

    if args.ipc:
        bot.ipc.start()

    if args.exclude:
        extensions = set(bot.config.main.exts) - set(args.exclude)

    else:
        extensions = bot.config.main.exts

    bot.run(extensions)
