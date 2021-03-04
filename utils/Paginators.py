import asyncio
import copy
from discord import HTTPException
from discord.ext import menus


class MyPages(menus.MenuPages):
    """My own paginator implementation.
    Subclasses menus.MenuPages. Takes page-source as a main parameter.
    Tries to delete a message when timeout comes, returns if any exceptions."""

    def __init__(self, source, **kwargs):
        super().__init__(source, check_embeds=True, **kwargs)

    async def finalize(self, timed_out):
        try:
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except HTTPException:
            pass


class MusicPageSource(menus.ListPageSource):
    """Player queue paginator class."""

    def __init__(self, ctx, entries, *, per_page=8):
        super().__init__(entries, per_page=per_page)
        self.ctx = ctx

    async def format_page(self, menu, page):
        embed = self.ctx.bot.embed.default(self.ctx, title='Coming Up...')
        embed.description = '\n'.join(f'`{index}. {title}`' for index, title in enumerate(page, 1))

        return embed

    def is_paginating(self):
        # We always want to embed even on 1 page of results...
        return True


class InteractiveController(menus.Menu):
    """The Players interactive controller menu class."""

    def __init__(self, *, embed, player):
        super().__init__(timeout=None)

        self.embed = embed
        self.player = player

    def update_context(self, payload):
        """Update our context with the user who reacted."""
        ctx = copy.copy(self.ctx)
        ctx.author = payload.member

        return ctx

    def reaction_check(self, payload):
        if payload.event_type == 'REACTION_REMOVE':
            return False

        if not payload.member:
            return False
        if payload.member.bot:
            return False
        if payload.message_id != self.message.id:
            return False
        if payload.member not in self.bot.get_channel(int(self.player.channel_id)).members:
            return False

        return payload.emoji in self.buttons

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)

    @menus.button(emoji='\u25B6')
    async def resume_command(self, payload):
        """Resume button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('resume')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u23F8')
    async def pause_command(self, payload):
        """Pause button"""
        ctx = self.update_context(payload)

        command = self.bot.get_command('pause')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u23F9')
    async def stop_command(self, payload):
        """Stop button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('stop')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u23ED')
    async def skip_command(self, payload):
        """Skip button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('skip')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\U0001F500')
    async def shuffle_command(self, payload):
        """Shuffle button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('shuffle')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u2795')
    async def volup_command(self, payload):
        """Volume up button"""
        ctx = self.update_context(payload)

        command = self.bot.get_command('vol_up')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\u2796')
    async def voldown_command(self, payload):
        """Volume down button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('vol_down')
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji='\U0001F1F6')
    async def queue_command(self, payload):
        """Player queue button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command('queue')
        ctx.command = command

        await self.bot.invoke(ctx)


class TodoPageSource(menus.ListPageSource):
    """TodoPageSource, a special paginator created for the todo commands parent.
    Takes the list of data, enumerates, then paginates through."""

    def __init__(self, ctx, data):
        super().__init__(data, per_page=10)
        self.ctx = ctx

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page + 1
        embed = self.ctx.bot.embed.default(self.ctx)

        if len(entries) < 1:
            embed.description = 'Currently, you have no to-do\'s.\n'
            'To set them use **todo add** command.'

        else:
            maximum = self.get_max_pages()
            embed.set_author(
                name=f'Page {menu.current_page + 1} of {maximum} ({len(self.entries)} todos)',
                icon_url=self.ctx.author.avatar_url
            )
            embed.description = '\n'.join(f'[{i}]({v[1]}). {v[0]}' for i, v in enumerate(entries, start=offset))

        return embed


class SQLListPageSource(menus.ListPageSource):
    def __init__(self, ctx, data, *, per_page=5):
        super().__init__(data, per_page=per_page)
        self.ctx = ctx

    async def format_page(self, menu, page):
        embed = self.ctx.bot.embed.default(
            self.ctx, description='```py\n' + '\n'.join(page) + '\n```'
        ).set_author(name=f'Page {menu.current_page + 1} / {self.get_max_pages()}')
        return embed


class EmbedPageSource(menus.ListPageSource):
    """EmbedPageSource, a paginator that takes a list of embeds."""

    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, embed):
        maximum = self.get_max_pages()
        embed.set_author(name=f'Page {menu.current_page + 1} / {maximum}')
        return embed


class Trivia:
    def __init__(self, entries, title, timeout=30.0):
        self.entries = entries
        self.title = title
        self.timeout = timeout

    async def pagination(self, ctx, loc=None, user=None):
        if len(self.entries) < 2 or len(self.entries) > 10:
            raise ValueError('Poll limits have reached.')
        e = ctx.bot.embed.default(ctx, title=self.title, description='')
        self.emojis = []
        for i, c in enumerate(self.entries):
            if i < 9:
                self.emojis.append(f'{i + 1}\u20E3')
            else:
                self.emojis.append('\U0001F51F')
            e.description = f'{e.description}{self.emojis[i]} {c}\n'

        self.controller = e
        return await self.reactions(ctx, user, loc)

    async def reactions(self, ctx, user, loc):
        if not loc:
            mes = await ctx.send(embed=self.controller)
        else:
            mes = await loc.send(embed=self.controller)

        for emoji in self.emojis:
            await mes.add_reaction(emoji)

        user = loc if loc else user

        def check(r, u):
            if str(r) not in self.emojis or u.id == ctx.bot.user.id or r.message.id != mes.id:
                return False
            if not user:
                if u.id != ctx.author.id:
                    return False
            else:
                if u.id != user.id:
                    return False
            return True

        try:
            r, u = await ctx.bot.wait_for('reaction_add', check=check, timeout=self.timeout)
        except asyncio.TimeoutError:
            await self.stop(mes)

        await self.stop(mes)
        return self.entries[self.emojis.index(str(r))]

    async def stop(self, msg):
        try:
            await msg.delete()
        except HTTPException:
            pass
