import discord
from typing import Union


TABLES = {
    'guild_config': 'guild_cache',
    'users': 'user_cache'
}


class DatabaseManager:
    def __init__(self, db, bot):
        self.cache = {}
        self.calls = []
        self.pool = db
        self.bot = bot

    def update_cache(self, table: str, _id: int, column: str, new):
        self.cache.update({table: self.route(table) or {}})
        self.cache[table].update({_id: self.route(table, _id) or {}})
        self.cache[table][_id][column] = new

    async def _fetch_data(self, table: str, user: discord.Member, column=None):
        _pointer = "guild" if user.__class__.__name__ == "Guild" else "user"

        get_query = 'SELECT * FROM "{0}" WHERE "{1}_id"=$1'.format(table, _pointer)
        insert_query = 'INSERT INTO "{0}"("{1}_id") VALUES($1)'.format(table, _pointer)

        got = await self.pool.fetchrow(get_query, user.id)

        if not got:
            await self.pool.execute(insert_query, user.id)
            got = await self.pool.fetchrow(get_query, user.id)

        if not column:
            self.overwrite_cache_entry(table, user.id, dict(got))
            return got

        res = got[column]
        self.update_cache(table, user.id, column, res)
        return res

    def route(self, *directions):
        """ Take a tuple like ('guilds', 1234, 'prefixes') and
            convert that into something like cache.get('guilds', {}).get(1234, {}).get('prefixes')
            Very similar to self.get, but it does not fetch from db if not found
        """
        final = self.cache
        for direction in directions:
            final = final.get(direction, {})

        return final or None

    async def get(self, table: int, user: discord.Member, column=None):
        """A method that firstly tries to get the data from cache,
        if it fails, fetches from the database accordingly.

        Args:
            table (int): The table name.
            user (discord.Member): A member to get the ID of.
            column (str, optional): The specific column name. Defaults to None.
        """
        # Since database calls are expensive,
        # We firstly try to get the required data from cache.
        # This helps us a lot in the database optimization.
        if route := self.route(table, user.id, column):
            return route

        return await self._fetch_data(table, user, column)

    async def count(self, table: str, user: discord.Member, *columns):
        total = 0
        for column in columns:
            amount = await self.get(table, user, column)
            total += amount

        return total

    async def add(self, table: str, column: str, user: discord.Member, amount: Union[int, float]):
        await self.get(table, user)
        _pointer = "user" if user.__class__.__name__ in ('User', 'Member', 'Object') else "guild"
        query = 'UPDATE "{0}" SET "{1}"="{1}"+$1 WHERE "{2}_id"=$2'.format(
            table, column, _pointer)

        try:
            self.cache[table][user.id][column] += amount

        except KeyError:
            await self._fetch_data(table, user, column)  # Updates the cache

        return await self.execute(query, amount, user.id)

    async def set(self, table, column, user, value):
        await self.get(table, user)
        _pointer = "user" if user.__class__.__name__ in ('User', 'Member', 'Object') else "guild"
        query = 'UPDATE "{0}" SET "{1}"=$1 WHERE "{2}_id"=$2'.format(table, column, _pointer)

        self.cache[table][user.id][column] = value
        return await self.execute(query, value, user.id)
