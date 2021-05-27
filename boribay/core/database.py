from typing import NoReturn, Union

import discord
from asyncpg.pool import Pool

__all__ = ('DatabaseManager',)


class DatabaseManager(Pool):
    def __init__(self, bot):
        self.bot = bot
        self.pool = bot.pool

    async def _operate(
        self, op: str, column: str,
        user: discord.Member, amount: Union[int, float]
    ) -> NoReturn:
        """The operate method made to ease up database manipulation.

        Args:
            op (str): An operator to use in the SQL query.
            column (str): Column name to use in the query consequently.
            user (discord.Member): The user to use in the query.
            amount (Union[int, float]): Amount of currency to manipulate with.

        Returns:
            NoReturn: Means that the method returns nothing.
        """
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

        Returns:
            NoReturn: Means that the method returns nothing.
        """
        await self._operate('+', *args)

    async def take(self, *args) -> NoReturn:
        """Database Manager take method to ease up mostly Economics manipulation.

        Args:
            column (str): The table-column name.
            user (discord.Member): The user to specify in WHERE clause.
            amount (Union[int, float]): Amount of (xp/money) to take.

        Returns:
            NoReturn: Means that the method returns nothing.
        """
        await self._operate('-', *args)

    async def double(
        self, choice: str, amount: int,
        reducer: discord.Member, adder: discord.Member
    ) -> NoReturn:
        """The "double" method to ease up database manipulation.

        Args:
            choice (str): The column value.
            amount (int): Amount of currency to manipulate.
            reducer (discord.Member): The user the money will be taken from.
            adder (discord.Member): The user the money will be added to.

        Returns:
            NoReturn: Means that the method returns nothing.
        """
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
            value (str): A new value to replace old one with.

        Returns:
            NoReturn: Means that the method returns nothing.
        """
        dirs = {'users': 'user', 'guild_config': 'guild'}
        query = f'UPDATE "{table}" SET "{column}" = $1 WHERE "{dirs[table]}_id" = $2'
        await self.pool.execute(query, value, user.id)
        await self.bot.user_cache.refresh()
