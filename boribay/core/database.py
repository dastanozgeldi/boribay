from collections import defaultdict
from typing import Union

import discord
from asyncpg.pool import Pool


class Cache(defaultdict):
    """Cache loader for Boribay created in order to use less DB calls.

    Any kind of caching stuff is done by this class.

    This class inherits from `collections.defaultdict`.
    """

    def __init__(self, query: str, key: str, db: Pool):
        super().__init__(dict)
        self.query = query
        self.key = key
        self.db = db

    def __await__(self):  # await Cache(...
        return self.cache_db().__await__()

    async def cache_db(self):
        """Cache database method."""
        records = await self.db.fetch(self.query)

        for record in records:
            d = dict(record)
            self[d.pop(self.key)] = d

        return self

    async def refresh(self):
        """Refresh cache method."""
        self.clear()
        await self.cache_db()
        return self


class DatabaseManager(Pool):
    """Database manager for Boribay created in order to ease up manipulation.

    This class inherits from `asyncpg.pool.Pool`.
    """

    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool

    async def _operate(
        self,
        op: str,
        column: str,
        user: discord.Member,
        amount: Union[int, float]
    ) -> None:
        """The operate method made to ease up database manipulation.

        Args:
            op (str): An operator to use in the SQL query.
            column (str): Column name to use in the query consequently.
            user (discord.Member): The user to use in the query.
            amount (Union[int, float]): Amount of currency to manipulate with.

        Returns:
            None: Means that the method returns nothing.
        """
        await self.pool.execute(
            f'UPDATE "users" SET "{column}" = "{column}" {op} $1 WHERE "user_id" = $2;',
            amount,
            user.id
        )
        await self.bot.user_cache.refresh()

    async def add(self, *args) -> None:
        """Database Manager add method to ease up mostly Economics manipulation.

        Args:
            column (str): The table-column name.
            user (discord.Member): The user to specify in WHERE clause.
            amount (Union[int, float]): Amount of (xp/money) to add.

        Returns:
            None: Means that the method returns nothing.
        """
        await self._operate('+', *args)

    async def take(self, *args) -> None:
        """Database Manager take method to ease up mostly Economics manipulation.

        Args:
            column (str): The table-column name.
            user (discord.Member): The user to specify in WHERE clause.
            amount (Union[int, float]): Amount of (xp/money) to take.

        Returns:
            None: Means that the method returns nothing.
        """
        await self._operate('-', *args)

    async def push(self, query: str, *args, **kwargs):
        """Just a method to save up 1 line in the code.

        Parameters
        ----------
        query : str
            A query to get executed.
        """
        await self.pool.execute(query, *args, **kwargs)
        await self.bot.user_cache.refresh()

    async def double(
        self,
        choice: str,
        amount: int,
        reducer: discord.Member,
        adder: discord.Member
    ) -> None:
        """The "double" method to ease up database manipulation.

        Args:
            choice (str): The column value.
            amount (int): Amount of currency to manipulate.
            reducer (discord.Member): The user the money will be taken from.
            adder (discord.Member): The user the money will be added to.

        Returns:
            None: Means that the method returns nothing.
        """
        reducer_query = f'UPDATE users SET {choice} = {choice} - $1 WHERE user_id = $2'
        adder_query = f'UPDATE users SET {choice} = {choice} + $1 WHERE user_id = $2'

        await self.pool.execute(reducer_query, amount, reducer.id)
        await self.pool.execute(adder_query, amount, adder.id)
        await self.bot.user_cache.refresh()

    async def set(
        self, table: str, column: str, user: discord.Member, value: str
    ) -> None:
        """Database Manager set method that is attainable for all tables.

        Args:
            table (str): The table name.
            column (str): The column name of the table.
            user (discord.Member): The user to specify in WHERE clause.
            value (str): A new value to replace old one with.

        Returns:
            None: Means that the method returns nothing.
        """
        dirs = {'users': 'user', 'guild_config': 'guild'}
        query = f'UPDATE "{table}" SET "{column}" = $1 WHERE "{dirs[table]}_id" = $2'
        await self.pool.execute(query, value, user.id)
        await self.bot.user_cache.refresh()
