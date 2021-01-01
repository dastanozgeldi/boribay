from discord.ext import commands, menus
from utils.HelpCommand import Cog, MyPages
from dotenv import load_dotenv
from utils.CustomEmbed import Embed
load_dotenv()


class TodoPageSource(menus.ListPageSource):
    def __init__(self, ctx, data):
        super().__init__(data, per_page=10)
        self.ctx = ctx

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page + 1
        embed = Embed()
        if len(entries) < 1:
            embed.description = '''Currently you have no to-do\'s.
            To set them use **todo add** command.'''
        else:
            maximum = self.get_max_pages()
            if maximum > 1:
                embed.set_author(
                    name=f'Page {menu.current_page + 1} of {maximum} ({len(self.entries)} todos)',
                    icon_url=self.ctx.author.avatar_url
                )
            embed.description = '\n'.join(f'{i}. {v}' for i, v in enumerate(entries, start=offset))
        return embed


class Todo(Cog, name='To-Do'):
    def __init__(self, bot):
        self.bot = bot
        self.name = '📃 To-Do'

    @commands.group(invoke_without_command=True, aliases=['to-do'], brief='todo help command.')
    async def todo(self, ctx):
        """Todo commands parent.
        It just basically sends the help for its category.
        Call for this command to learn how to use to-do commands."""
        await ctx.send_help('todo')

    @todo.command(name='list')
    async def list_todo(self, ctx):
        '''Basically, shows author's todo list.
        Have nothing to explain, so try it and see.'''
        todos = await self.bot.todos.find_one({'_id': ctx.author.id})
        todo_list = todos['todo']
        todo_list = todo_list[1:]
        p = MyPages(source=TodoPageSource(ctx, todo_list), clear_reactions_after=True, timeout=60.0)
        return await p.start(ctx)

    @todo.command(name='add')
    async def add_todo(self, ctx, *, message: str):
        '''To-do add command. The message you send will be added to your to-do list.
        Ex: **todo add art project.**'''
        if ctx.author == self.bot.user:
            return
        await self.bot.todos.update_one(
            {"_id": ctx.author.id},
            {"$addToSet": {"todo": message}}
        )
        await ctx.message.add_reaction('✅')

    @todo.command(name='edit')
    async def edit_todo(self, ctx, number: int, *, new_todo: str):
        '''Lets you edit todo with a given number, for example, if you messed up some details.
        Ex: **todo edit 5 play rocket league with teammate at 5 pm**'''
        await self.bot.todos.update_one(
            {'_id': ctx.author.id},
            {'$set': {f'todo.{number}': new_todo}}
        )
        await ctx.message.add_reaction('✅')

    @todo.command(name='switch')
    async def switch_todo(self, ctx, task_1: int, task_2: int):
        '''Lets user switch their tasks. It is useful when you got more important task.
        Ex: **todo switch 1 12** — switches places of 1st and 12th tasks.'''
        todos = await self.bot.todos.find_one({'_id': ctx.author.id})
        todo_list = todos['todo']
        first = todo_list[task_1]
        second = todo_list[task_2]
        await self.bot.todos.update_one({'_id': ctx.author.id}, {'$set': {f'todo.{task_1}': second, f'todo.{task_2}': first}})
        await ctx.message.add_reaction('✅')

    @todo.command(name="remove", aliases=['delete', 'rm'])
    async def remove_todo(self, ctx, *numbers: int):
        '''Removes specific to-do from the list
        Ex: **todo remove 7**'''
        if ctx.author == self.bot.user:
            return
        todos = await self.bot.todos.find_one({'_id': ctx.author.id})
        todo_list = todos['todo']
        if len(todo_list) <= 1:
            await ctx.send(f'''
                You have no tasks to delete.
                To add a task type `{ctx.prefix}todo add <your task here>`
            ''')
        for number in numbers:
            if number >= len(todo_list):
                return await ctx.send(f'Could not find todo #{number}')
            await self.bot.todos.update_one({'_id': ctx.author.id}, {'$unset': {f'todo.{number}': 1}})
            await self.bot.todos.update_one({'_id': ctx.author.id}, {'$pull': {'todo': None}})
        await ctx.message.add_reaction('✅')

    @todo.command(name='reset', aliases=['clear'])
    async def reset_todo(self, ctx):
        '''Resets all elements from user's to-do list'''
        if ctx.author == self.bot.user:
            return
        await self.bot.todos.update_one(
            {"_id": ctx.author.id},
            {"$set": {"todo": ["nothing yet."]}}
        )
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Todo(bot))
