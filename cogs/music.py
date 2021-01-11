import asyncio
import re
import typing as t
import discord
import wavelink
from discord.ext import commands
from utils.CustomCog import Cog

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
OPTIONS = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4,
}


class AlreadyConnectedToChannel(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class PlayerIsAlreadyPaused(commands.CommandError):
    pass


class NoMoreTracks(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0

    @property
    def is_empty(self):
        return not self._queue

    @property
    def first_track(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[0]

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

        self.position += 1

        if self.position > len(self._queue) - 1:
            return None

        return self._queue[self.position]

    def empty(self):
        self._queue.clear()


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            raise NoTracksFound

        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            await ctx.send(f"Added `{tracks[0].title}` to the queue.")
        else:
            if (track := await self.choose_track(ctx, tracks)) is not None:
                self.queue.add(track)
                await ctx.send(f"Added `{track.title}` to the queue.")

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys() and u == ctx.author and r.message.id == msg.id
            )

        embed = self.bot.embed.default(
            ctx=ctx,
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i + 1}.** {t.title} ({t.length // 60000}:{str(t.length % 60).zfill(2)})"
                    for i, t in enumerate(tracks[:5])
                )
            )
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.first_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                await self.play(track)
        except QueueIsEmpty:
            pass


class Music(Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot
        self.name = '🎵 Music'
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f" Wavelink node `{node.identifier}` ready.")

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

    @commands.command(aliases=['join'], brief='connects to the current voice channel.')
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

    @commands.command(aliases=['leave'], brief='leaves current voice channel.')
    async def disconnect(self, ctx):
        """Disconnect command. Makes bot leave the current channel."""
        player = self.get_player(ctx)
        await player.teardown()
        await ctx.send("Disconnected from the current channel.")

    @commands.command(brief='play command. you can search through command or provide a url (youtube-only).')
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
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"

            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @play.error
    async def play_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send('No songs to play as the queue is empty.')

    @commands.command(brief='pauses song.')
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

    @commands.command(brief='stops song (removes from queue).')
    async def stop(self, ctx):
        """Stop command. Actually resets the queue."""
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()
        await ctx.send('Playback successfully stopped.')

    @commands.command(name='skip', aliases=['next'])
    async def next_command(self, ctx):
        """Next command. Makes bot play next song in the queue.
        Returns: Stop Command: Stops music if no songs are incoming."""
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            return await self.stop(ctx)

        await player.stop()
        await ctx.send('Playing next track in queue...')

    @next_command.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send('Next track could not be executed as the queue is currently empty.')

        elif isinstance(exc, NoMoreTracks):
            await ctx.send('There are no more tracks in the queue.')

    @commands.command(brief='plays previous song in queue (if queue is empty command raises an exception).')
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

    @commands.command(aliases=['q'], brief='shows music queue.')
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
