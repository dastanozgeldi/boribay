import asyncio
import random
import textwrap
from io import BytesIO
from time import time
from typing import Optional

import nextcord
from boribay.core import Boribay, utils
from nextcord.ext import commands


class Fun(utils.Cog):
    """The fun commands extension."""

    def __init__(self, bot: Boribay):
        self.icon = '🎉'
        self.bot = bot

    async def alex_image(self, url: str, fn: str = None) -> nextcord.File:
        """Quick-Alex-image making function.

        Args:
            url (str): The URL of an image.
            fn (str, optional): Filename to take. Defaults to None.

        Returns:
            nextcord.File: A done to send file.
        """
        key = self.bot.config.api.alex
        r = await self.bot.session.get(
            'https://api.alexflipnote.dev/' + url,
            headers={'Authorization': key}
        )
        fp = BytesIO(await r.read())
        return nextcord.File(fp, fn or 'alex.png')

    async def dagpi_image(self, url: str, fn: str = None) -> nextcord.File:
        """Quick-Dagpi-image making function.

        Args:
            url (str): The URL of an image.
            fn (str, optional): Filename to take. Defaults to None.

        Returns:
            nextcord.File: A done to send file.
        """
        key = self.bot.config.api.dagpi
        r = await self.bot.session.get(
            'https://beta.dagpi.xyz/image/' + url,
            headers={'Authorization': key}
        )
        fp = BytesIO(await r.read())
        return nextcord.File(fp, fn or 'dagpi.png')

    @utils.command(aliases=('rps',))
    async def rockpaperscissors(self, ctx: utils.Context) -> None:
        """The Rock-Paper-Scissors game.

        There are three different reactions:
        ------------------------------------
        🪨 - for rock; 📄 - for paper; ✂ - for scissors.
        """
        rps_logic = {
            '🪨': {'🪨': 'draw', '📄': 'lose', '✂': 'win'},
            '📄': {'🪨': 'win', '📄': 'draw', '✂': 'lose'},
            '✂': {'🪨': 'lose', '📄': 'win', '✂': 'draw'}
        }
        choice = random.choice([*rps_logic.keys()])
        embed = ctx.embed(description='**Choose one 👇**')
        msg = await ctx.send(embed=embed.set_footer(text='10 seconds left⏰'))

        for r in rps_logic:
            await msg.add_reaction(r)

        try:
            r, u = await ctx.bot.wait_for(
                'reaction_add', timeout=10,
                check=lambda re, us: us == ctx.author and str(re) in rps_logic.keys() and re.message.id == msg.id
            )
            game = rps_logic.get(str(r.emoji))
            embed = ctx.embed(
                description=f'Result: **{game[choice].upper()}**\n'
                f'My choice: **{choice}**\n'
                f'Your choice: **{r.emoji}**'
            )
            await msg.edit(embed=embed)

        except asyncio.TimeoutError:
            await ctx.try_delete(msg)

    @utils.command(aliases=('tr', 'typerace'))
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    async def typeracer(self, ctx: utils.Context, timeout: float = 60.0) -> None:
        """Typeracer game. Compete with others and find out the best typist.

        If you don't like the given quote, react with a wastebasket to close the game.

        Example
        -------
            **{p}tr** - the default round for 60 seconds.
            **{p}typeracer --timeout 30** - makes a round for 30 seconds.**

        Parameters
        ----------
        timeout : float, optional
            Set your own time given for typing, by default 60.0

        Raises
        ------
        commands.BadArgument
            When the provided time does not fit the limits (10 < x < 120).
        """
        if not 10.0 < timeout < 120.0:
            raise commands.BadArgument('Timeout limit has been reached. Specify between 10 and 120.')

        async with ctx.loading:
            r = await ctx.bot.session.get('https://api.quotable.io/random')
            quote = await r.json()
            content = quote['content']
            buffer = await utils.Manip.typeracer('\n'.join(textwrap.wrap(content, 30)))

        embed = ctx.embed(
            title='Typeracer', description='see who is the fastest at typing.'
        ).set_image(url='attachment://typeracer.png')
        embed.set_footer(text=f'© {quote["author"]}')

        race = await ctx.send(file=nextcord.File(buffer, 'typeracer.png'), embed=embed)
        await race.add_reaction('🗑')
        start = time()

        try:
            done, pending = await asyncio.wait([
                ctx.bot.wait_for(
                    'raw_reaction_add',
                    check=lambda p: str(p.emoji) == '🗑' and p.user_id == ctx.author.id and p.message_id == race.id
                ),
                ctx.bot.wait_for(
                    'message',
                    check=lambda m: m.content == content,
                    timeout=timeout
                )
            ], return_when=asyncio.FIRST_COMPLETED)

            stuff = done.pop().result()

            if isinstance(stuff, nextcord.RawReactionActionEvent):
                return await race.delete()

            final = round(time() - start, 2)
            embed = ctx.embed(
                title=f'{stuff.author} won!',
                description=f'**Done in**: {final}s\n'
                f'**Average WPM**: {quote["length"] / 5 / (final / 60):.0f} words\n'
                f'**Original text:**```diff\n+ {content}```',
            )
            await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            await ctx.try_delete(race)

    @utils.command()
    async def dadjoke(self, ctx: utils.Context):
        resp = await self.bot.session.get(
            'https://icanhazdadjoke.com/',
            headers={'Accept': 'text/plain'}
        )
        if resp.status != 200:
            return await ctx.send('Could not fetch the joke. Please try again later!')

        joke = await resp.text()
        embed = ctx.embed(title='Here is yo joke:', description=joke)
        await ctx.send(embed=embed)

    @utils.command(aliases=('ph',))
    async def pornhub(
        self, ctx: utils.Context, left_text: str, right_text: str = 'Hub'
    ) -> None:
        """PornHub logo maker.

        Example:
            **{p}ph Dosek** - a logo "DosekHub".**
            **{p}ph Bori bay** - Bori and bay in the orange box.**

        Args:
            left_text (str): Text for the left side
            right_text (str, optional): Text to the right side. Defaults to 'Hub'.
        """
        left_text = left_text.replace(' ', '%20')
        right_text = right_text.replace(' ', '%20')

        file = await self.alex_image(f'pornhub?text={left_text}&text2={right_text}')
        await ctx.send(file=file)

    @utils.command()
    async def qr(self, ctx: utils.Context, url: Optional[str]) -> None:
        """Make QR-code from a given URL.
        URL can be an atttachment or a user avatar.

        Args:
            url (Optional[str]): URL to make the QR-code from.

        Example:
            **{p}qr @Dosek** - sends the QR code using Dosek's avatar.
        """
        url = await utils.make_image(ctx, url, return_url=True)
        r = await ctx.bot.session.get(
            'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + url
        )
        io = BytesIO(await r.read())
        await ctx.send(file=nextcord.File(io, 'qr.png'))

    @utils.command()
    async def caption(self, ctx: utils.Context, image: Optional[str]) -> None:
        """Get caption for an image.

        Example:
            **{p}caption @Dosek** - sends caption for Dosek's avatar.

        Args:
            image (Optional[str]): An image you want to get caption for.
        """
        image = await utils.make_image(ctx, image, return_url=True)

        r = await ctx.bot.session.post(
            'https://captionbot.azurewebsites.net/api/messages',
            json={'Content': image, 'Type': 'CaptionRequest'}
        )
        embed = ctx.embed(title=await r.text())
        await ctx.send(embed=embed.set_image(url=image))

    @utils.command(aliases=('dym',))
    async def didyoumean(self, ctx: utils.Context, search: str, did_you_mean: str) -> None:
        """Google search "Did you mean" meme.

        Example:
            **{p}didyoumean "looping" "recursion"**

        Args:
            search (str): The "searched" query.
            did_you_mean (str): Query not found, the "did you mean" text.
        """
        file = await self.alex_image(f'didyoumean?top={search}&bottom={did_you_mean}')
        await ctx.send(file=file)

    @utils.command()
    async def achieve(self, ctx: utils.Context, *, text: str) -> None:
        """Minecraft "Achievement Get!" meme maker.

        Example:
            **{p}achieve sleep more than 6 hours**

        Args:
            text (str): A text for the achievement.
        """
        text = text.replace(' ', '%20')
        icon = random.randint(1, 44)

        file = await self.alex_image(f'achievement?text={text}&icon={icon}')
        await ctx.send(file=file)

    @utils.command()
    async def challenge(self, ctx: utils.Context, *, text: str) -> None:
        """Minecraft "Challenge Complete!" meme maker.

        Example:
            **{p}challenge slept more than 6 hours**

        Args:
            text (str): A text for the challenge.
        """
        text = text.replace(' ', '%20')
        icon = random.randint(1, 45)

        file = await self.alex_image(f'challenge?text={text}&icon={icon}')
        await ctx.send(file=file)

    @utils.command()
    async def triggered(self, ctx: utils.Context, image: Optional[str]) -> None:
        """Make the "TrIgGeReD" meme.

        Example:
            **{p}triggered @Dosek** - triggers Dosek.

        Args:
            image (Optional[str]): An image you want to get "triggered".
        """
        image = await utils.make_image(ctx, image, return_url=True)
        file = await self.dagpi_image(f'triggered?url={image}', 'triggered.gif')
        await ctx.send(file=file)

    @utils.command(name='ascii')
    async def ascii_command(self, ctx: utils.Context, image: Optional[str]) -> None:
        """Get the ASCII version of an image.

        Example:
            **{p}ascii @Dosek** - sends ASCII version of Dosek's avatar.

        Args:
            image (Optional[str]): An image you want to ASCII'ize.
        """
        image = await utils.make_image(ctx, image, return_url=True)
        file = await self.dagpi_image(f'ascii?url={image}', 'ascii.png')
        await ctx.send(file=file)

    @utils.command()
    async def coinflip(self, ctx: utils.Context) -> None:
        """Play the simple coinflip game.

        Chances:
        --------
        **head → 49.5%**; **tail → 49.5%**; **side → 1%**
        """
        choice = random.choices(
            population=['head', 'tail', 'side'],
            weights=[0.49, 0.49, 0.02],
            k=1
        )[0]

        if choice == 'side':
            return await ctx.send('Coin was flipped **to the side**!')

        await ctx.send(f'Coin flipped to the `{choice}`, no reward.')

    @utils.command()
    async def eject(
        self,
        ctx: utils.Context,
        color: str.lower,
        *,
        name: Optional[str]
    ) -> None:
        """Among Us "ejected" meme maker.

        Example:
            **{p}eject blue yes Dosek** - blue impostor with the nick "Dosek".

        Args:
            color (str.lower): Color of an ejected guy.
            name (Optional[str]): The name for the impostor.

        Available colors:
            black • blue • brown • cyan • darkgreen • lime
            • orange • pink • purple • red • white • yellow
        """
        # This check is still bad since the API colors are limited
        # and ImageColor.getrgb supports more colors.
        if not utils.color_exists(color):
            raise commands.BadArgument(
                f'Color {color} does not exist. '
                f'Choose one from `{ctx.prefix}help {ctx.command}`'
            )

        url = f'https://vacefron.nl/api/ejected?name={name}&impostor=true&crewmate={color}'

        # Calling the API.
        r = await self.bot.session.get(url)
        # Bufferizing the fetched image.
        io = BytesIO(await r.read())

        # Sending to the utils.Contextual channel.
        await ctx.send(file=nextcord.File(fp=io, filename='ejected.png'))

    @utils.command(name='pp', aliases=('peepee',))
    async def command_pp(
        self, ctx: utils.Context, member: Optional[nextcord.Member]
    ) -> None:
        """Get the random size of your PP.

        Example:
            **{p}pp @Dosek** - sends Dosek's pp size.

        Args:
            member (Optional[nextcord.Member]): A member to check the pp size of.
            Takes you as the member if no one was mentioned.
        """
        member = member or ctx.author
        sz = 100 if member.id in self.bot.owner_ids else random.randint(1, 10)
        await ctx.send(f"{member}'s pp size is:\n3{'=' * sz}D")
