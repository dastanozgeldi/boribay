from typing import NoReturn, Union

import discord
from asyncpg.pool import Pool

from .logger import create_logger

THING_DIRS = {
    'users': 'user',
    'guild_config': 'guild'
}

CACHE_DIRS = {
    'users': 'user_cache',
    'guild_config': 'guild_cache'
}


class DatabaseManager(Pool):
    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool
        self.logger = create_logger('Database')

    def route(self, table: str, *keys):
        """Let's assume you have an ordered tuple:
        ('user_cache', 12345678, 'wallet'). This method does the following:
        self.user_cache.get('user_cache', {}).get(12345678, {}).get('wallet', {})

        Tries to route every key given in the cache.
        """
        temp = getattr(self.bot, CACHE_DIRS[table])
        for key in keys:
            temp = temp.get(key, {})

        return temp or None

    async def fetch_data(self, table: str, user: discord.Member, column: str = None):
        """Database Manager data fetching method.

        Args:
            table (str): The table name.
            user (discord.Member): The user to specify in WHERE clause.
            column (str, optional): The specific column. Defaults to None.
        """
        thing = THING_DIRS[table]

        get_query = f'SELECT * FROM "{table}" WHERE "{thing}_id" = $1;'
        if not (got := await self.pool.fetchrow(get_query, user.id)):
            query = f'INSERT INTO "{table}" ("{thing}_id") VALUES ($1);'
            await self.pool.execute(query, user.id)
            got = await self.pool.fetchrow(get_query, user.id)

        base = getattr(self.bot, CACHE_DIRS[table])
        if not column:
            await base.refresh()
            return got

        result = got[column]
        await base.refresh()
        return result

    async def getch(self, table: str, user: discord.Member, column: str = None):
        """Database Manager get or fetch, AKA getch method.

        Firstly tries to get from cache, then fetches on fail.

        Args:
            table (str): The table name.
            user (discord.Member): The user to get data of.
            column (str, optional): The specific column name. Defaults to None.
        """
        if route := self.route(table, user.id, column):
            return route  # try to get from cache firstly.

        return await self.fetch_data(table, user, column)

    async def _operate(self, op: str, column: str, user: discord.Member, amount: Union[int, float]) -> NoReturn:
        query = f'''
        UPDATE "users"
        SET "{column}" = "{column}" {op} $1
        WHERE "user_id" = $2;
        '''
        await self.pool.execute(query, amount, user.id)
        await self.bot.user_cache.refresh()

    async def add(self, *args) -> NoReturn:
        """Database Manager add method to ease up mostly Economics manipulation.

        Args:
            column (str): The table-column name.
            user (discord.Member): The user to specify in WHERE clause.
            amount (Union[int, float]): Amount of (xp/money) to add.
        """
        await self._operate('+', *args)

    async def take(self, *args):
        """Database Manager take method to ease up mostly Economics manipulation.

        Args:
            column (str): The table-column name.
            user (discord.Member): The user to specify in WHERE clause.
            amount (Union[int, float]): Amount of (xp/money) to take.
        """
        await self._operate('-', *args)

    async def double(self, choice: str, amount: int, reducer: discord.Member, adder: discord.Member):
        reducer_query = f'UPDATE users SET {choice} = {choice} - $1 WHERE user_id = $2'
        adder_query = f'UPDATE users SET {choice} = {choice} + $1 WHERE user_id = $2'

        await self.pool.execute(reducer_query, amount, reducer.id)
        await self.pool.execute(adder_query, amount, adder.id)

        await self.bot.user_cache.refresh()

    async def set(self, table: str, column: str, user: discord.Member, value: str) -> NoReturn:
        """Database Manager set method that is attainable for all tables.

        Args:
            table (str): The table name.
            column (str): The column name of the table.
            user (discord.Member): The user to specify in WHERE clause.
            value ([type]): A new value to replace old one with.
        """
        thing = THING_DIRS[table]
        query = f'UPDATE "{table}" SET "{column}" = $1 WHERE "{thing}_id" = $2'
        await self.pool.execute(query, value, user.id)
        await self.bot.user_cache.refresh()

    async def check_guilds(self) -> NoReturn:
        """Database Manager guild-check method."""

        # This is needed when the bot gone offline for a while
        # and got added/removed to some servers. Since the bot
        # was offline they arent accordingly existing in the database/cache
        # which makes fresh servers' users unable to use the bot.
        guild_config = await self.pool.fetch('SELECT * FROM guild_config;')

        # preparing the guild id's to compare
        bot_guild_ids = {guild.id for guild in self.bot.guilds}
        db_guild_ids = {row['guild_id'] for row in guild_config}

        if difference := list(bot_guild_ids - db_guild_ids):  # check for new guilds.
            self.logger.info(f'New {len(difference)} guilds are being inserted.')
            for guild_id in difference:
                await self.pool.execute('INSERT INTO guild_config(guild_id) VALUES($1);', guild_id)

        if difference := list(db_guild_ids - bot_guild_ids):  # check for old guilds.
            self.logger.info(f'Old {len(difference)} guilds are being deleted.')
            for guild_id in difference:
                await self.pool.execute('DELETE FROM guild_config WHERE guild_id = $1;', guild_id)

        await self.bot.guild_cache.refresh()
