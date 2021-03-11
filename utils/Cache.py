from collections import defaultdict


class Cache(defaultdict):
    def __init__(self, query, key, db):
        super().__init__(dict)
        self.query = query
        self.key = key
        self.db = db

    def __await__(self):
        return self.cache_db().__await__()

    async def cache_db(self):
        records = await self.db.fetch(self.query)

        for record in records:
            d = dict(record)
            self[d.pop(self.key)] = d

        return self

    async def refresh(self):
        self.clear()
        await self.cache_db()
        return self
