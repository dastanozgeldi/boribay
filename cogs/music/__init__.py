import re
import typing as t
import discord
import wavelink
from discord.ext import commands
from utils.Exceptions import (
    AlreadyConnectedToChannel,
    NoVoiceChannel,
    QueueIsEmpty,
    PlayerIsAlreadyPaused,
    NoMoreTracks,
    NoPreviousTracks
)
from .music import Player
from utils.Cog import Cog


class Music(Cog, wavelink.WavelinkMixin):
    '''A Music extension that supports simple music commands with features.
    Use it if you have no other choice, like really. Btw this does not require
    loading music to drive :)'''

    def __init__(self, bot):
        self.bot = bot
        self.name = '🎵 Music'
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        self.bot.log.info(f'Wavelink node `{node.identifier}` ready.')

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        await payload.player.advance()

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs.")
            return False
        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()
        nodes = {
            'MAIN': {
                'host': self.bot.config['music']['host'],
                'port': self.bot.config['music']['port'],
                'rest_uri': self.bot.config['music']['rest_uri'],
                'password': self.bot.config['music']['password'],
                'identifier': self.bot.config['music']['identifier'],
                'region': self.bot.config['music']['region'],
            }
        }
        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

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
        await ctx.send(f"Connected to `{channel.name}`.")

    @connect.error
    async def connect_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            await ctx.send("Already connected to a voice channel.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("No suitable voice channel was provided.")

    @commands.command(aliases=['leave'])
    async def disconnect(self, ctx):
        """Disconnect command. Makes bot leave the current channel."""
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.send("Disconnected from the current channel.")

    @commands.command()
    async def play(self, ctx, *, query: t.Optional[str]):
        """Play command. This lets you join youtube URL or search through bot
        itself to the query.
        Args: query (t.Optional[str]): The thing that you want to play. Either
        searching words or URL.
        Raises: QueueIsEmpty: If no query is specified."""
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)
        if query is None:
            if player.queue.is_empty:
                raise QueueIsEmpty
            await player.set_pause(False)
            await ctx.send('Playback successfully resumed.')
        else:
            query = query.strip("<>")
            if not re.match(self.bot.regex['URL_REGEX'], query):
                query = f"ytsearch:{query}"
            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @play.error
    async def play_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send('No songs to play as the queue is empty.')

    @commands.command()
    async def pause(self, ctx):
        """Pause command. Lets you pause the current playing query.
        Raises: PlayerIsAlreadyPaused: If none of songs are playing."""
        player = self.get_player(ctx)
        if player.is_paused:
            raise PlayerIsAlreadyPaused
        await player.set_pause(True)
        await ctx.send('Playback successfully paused.')

    @pause.error
    async def pause_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send('Playback is already paused.')

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
        Returns: Stop Command: Stops music if no songs are incoming."""
        player = self.get_player(ctx)
        if not player.queue.upcoming:
            return await self.stop(ctx)
        await player.stop()
        await ctx.send('Playing next track in queue...')

    @skip.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send('Next track could not be executed as the queue is currently empty.')
        elif isinstance(exc, NoMoreTracks):
            await ctx.send('There are no more tracks in the queue.')

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

    @previous.error
    async def previous_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send('Previous track could not be executed as the queue is currently empty.')

        elif isinstance(exc, NoPreviousTracks):
            await ctx.send('There are no previous tracks in the queue.')

    @commands.command(aliases=['q'])
    async def queue(self, ctx, show: t.Optional[int] = 10):
        """Queue command. Shows the current queue.
        Args: show (optional): Number of songs you want to see in the queue.
        Defaults to 10.
        Raises: QueueIsEmpty: If no songs are there in the queue."""
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        embed = self.bot.embed.default(
            ctx=ctx,
            title='Queue',
            description=f'Showing up to next {show} tracks'
        ).set_author(name='Query Results')
        embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
        embed.add_field(name='Currently playing...', value=player.queue.current_track.title, inline=False)
        if upcoming := player.queue.upcoming:
            embed.add_field(
                name='Next up',
                value='\n'.join(t.title for t in upcoming),
                inline=False
            )
        await ctx.send(embed=embed)

    @queue.error
    async def queue_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send('The queue is currently empty.')


def setup(bot):
    bot.add_cog(Music(bot))
