import argparse

from boribay import Boribay

description = 'A Discord Bot created to make people smile.'

bot = Boribay(description=description)
parser = argparse.ArgumentParser(description=description)
parser.add_argument('--exclude', nargs='+',
                    help='Specify Cogs you don\'t want to include on startup!')

if __name__ == '__main__':
    extensions = bot.config.main.exts

    args = parser.parse_args()
    if args.exclude:
        extensions = set(bot.config.main.exts) - set(args.exclude)

    bot.run(extensions)
