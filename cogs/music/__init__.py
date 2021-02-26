import re
import typing as t
from textwrap import wrap

import discord
import wavelink
from discord.ext import commands
from utils.Cog import Cog
from utils.Exceptions import NoPreviousTracks, PlayerIsAlreadyPaused, QueueIsEmpty
from utils.Paginators import EmbedPageSource, MyPages

from .tools import Player


class Music(Cog, wavelink.WavelinkMixin):
    '''A Music extension that supports simple music commands with features.
    Use it if you have no other choice, like really. Btw this does not require
    loading music to drive :)'''
    icon = '🎵'
    name = 'Music'

    def __init__(self, bot):
        self.bot = bot
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    def __str__(self):
        return '{0.icon} {0.name}'.format(self)

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and not after.channel:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        self.bot.log.info(f'[MUSIC] Wavelink node -> `{node.identifier}` is ready.')

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')
    async def on_player_stop(self, node, payload):
        await payload.player.advance()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send('Music commands are not available in DMs.')
            return False
        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        nodes = {'MAIN': {
            'host': '127.0.0.1',
            'port': 8080,
            'rest_uri': 'http://127.0.0.1:8080',
            'password': 'youshallnotpass',
            'identifier': 'MAIN',
            'region': 'europe'
        }}
        for n in nodes.values():
            await self.wavelink.initiate_node(**n)

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    @commands.command(aliases=['join'])
    async def connect(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        """Connect command. Makes bot join to the current channel, and specific
        one, if specified.
        Args: channel (optional): Channel that you want bot to join to."""
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        await ctx.send(f'Connected to `{channel.name}`.')

    @commands.command(aliases=['leave'])
    async def disconnect(self, ctx):
        """Disconnect command. Makes bot leave the current channel."""
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def play(self, ctx, *, query: t.Optional[str]):
        """Play command. Search through or give it a URL.
        Args: query: The thing that you want to play. Either searching words or URL.
        Raises: QueueIsEmpty: If no query is specified."""
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)
        if not query:
            if player.queue.is_empty:
                raise QueueIsEmpty
            await player.set_pause(False)
            await ctx.send('Playback successfully resumed.')
        else:
            query = query.strip('<>')
            if not re.match(self.bot.regex['URL_REGEX'], query):
                query = f'ytsearch:{query}'
            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @commands.command(aliases=['song', 'lyric'])
    async def lyrics(self, ctx, *, song: str):
        '''Powerful lyrics command.
        You can find lyrics for song that you want.'''
        cs = self.bot.session
        r = await cs.get(f'https://some-random-api.ml/lyrics?title={song.replace(" ", "%20")}')
        js = await r.json()
        song = wrap(str(js['lyrics']), 1000, drop_whitespace=False, replace_whitespace=False)
        embed_list = []
        for lyrics in song:
            embed = self.bot.embed.default(
                ctx,
                title=f'{js["author"]} — {js["title"]}',
                description=lyrics
            ).set_thumbnail(url=js['thumbnail']['genius'])
            embed_list.append(embed)
        await MyPages(EmbedPageSource(embed_list)).start(ctx)

    @commands.command(aliases=['vol'])
    async def volume(self, ctx, *, vol: int):
        """Change the players volume, between 1 and 100.
        Raises: PlayerIsAlreadyPaused: If none of songs are playing."""
        player = self.get_player(ctx)
        if not player.is_connected:
            return
        if not 0 < vol < 101:
            return await ctx.send('Please enter a value between 1 and 100.')
        await player.set_volume(vol)
        await ctx.send(f'Set the volume to **{vol}**%')

    @commands.command(aliases=['eq'])
    async def equalizer(self, ctx, *, equalizer):
        """Changes the player's equalizer."""
        player = self.get_player(ctx)
        if not player.is_connected:
            return
        eqs = {
            'flat': wavelink.Equalizer.flat(),
            'boost': wavelink.Equalizer.boost(),
            'metal': wavelink.Equalizer.metal(),
            'piano': wavelink.Equalizer.piano()
        }
        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            return await ctx.send('Invalid EQ provided. Valid EQs:\n%s' % '\n'.join(eqs.keys()))

        await ctx.send(f'Successfully changed equalizer to {equalizer}')
        await player.set_eq(eq)

    @commands.command()
    async def pause(self, ctx):
        """Pause the currently playing song."""
        player = self.get_player(ctx)
        if player.is_paused or not player.is_connected:
            raise PlayerIsAlreadyPaused
        await ctx.send('DJ has paused the player.')
        return await player.set_pause(True)

    @commands.command()
    async def stop(self, ctx):
        """Stop command. Actually resets the queue."""
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.send('Playback successfully stopped.')

    @commands.command(aliases=['next'])
    async def skip(self, ctx):
        """Next command. Makes bot play next song in the queue.
        Returns: Stops music if no songs are incoming."""
        player = self.get_player(ctx)
        if not player.queue.upcoming:
            return await self.stop(ctx)
        await player.stop()
        await ctx.send('Playing next track in queue...')

    @commands.command()
    async def previous(self, ctx):
        """Previous command. Makes bot play previous track in the queue.
        Raises: NoPreviousTracks: If no tracks were before."""
        player = self.get_player(ctx)
        if not player.queue.history:
            raise NoPreviousTracks
        player.queue.position -= 2
        await player.stop()
        await ctx.send('Playing previous track in queue...')

    @commands.command(aliases=['q'])
    async def queue(self, ctx, show: t.Optional[int] = 10):
        """Queue command. Shows the current queue.
        Args: show: Number of songs you want to see in the queue.
        Raises: QueueIsEmpty: If no songs are there in the queue."""
        player = self.get_player(ctx)
        if player.queue.is_empty:
            raise QueueIsEmpty
        embed = self.bot.embed.default(
            ctx, title='Queue', description=f'Showing up to next {show} tracks'
        ).set_author(name='Query Results')
        embed.add_field(name='Currently playing...', value=player.queue.current_track.title, inline=False)
        if upcoming := player.queue.upcoming:
            embed.add_field(name='Next up', value='\n'.join(t.title for t in upcoming), inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))
