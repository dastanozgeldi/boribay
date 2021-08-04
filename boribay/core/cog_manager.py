from boribay.core import utils


class CogManager(utils.Cog):
    """CogManager - a cog that helps us with cog management."""

    def __init__(self, bot) -> None:
        self.icon = '👨‍💼'
        self.bot = bot
        self.extensions = bot.extensions.keys()

    @utils.group(aliases=('ext',), invoke_without_command=True)
    async def cog(self, ctx: utils.Context) -> None:
        """Extension manager commands group.

        Here you can see commands that load, unload and reload extensions.
        """

    @cog.command(name='load')
    async def _ext_load(self, ctx: utils.Context, *extensions: str) -> None:
        """Load a cog.

        Examples
        --------
            **{p}ext load ~** - loads all extensions.
            **{p}ext load boribay.extensions.fun** - loads the "Fun" cog.

        Parameters
        ----------
        extensions : str
            A set of extensions to load, by default '~ (all)'
        """
        if extensions is None:
            return await ctx.send('Please specify extensions in order to load.')

        exts = self.extensions if extensions[0] == '~' else extensions
        [ctx.bot.load_extension(ext) for ext in exts]
        await ctx.send(f'Loaded extension{"s" if len(exts) else ""}: ' + ', '.join(exts))

    @cog.command(name='unload')
    async def _ext_unload(self, ctx: utils.Context, *extensions: str) -> None:
        """Unload a cog.

        Examples
        --------
            **{p}ext load ~** - loads all extensions.
            **{p}ext load boribay.extensions.fun** - loads the "Fun" cog.

        Parameters
        ----------
        extensions : str
            A set of extensions to load, by default '~ (all)'
        """
        if extensions is None:
            return await ctx.send('Please specify extensions in order to load.')

        exts = self.extensions if extensions[0] == '~' else extensions
        [ctx.bot.unload_extension(ext) for ext in exts]
        await ctx.send(f'Unloaded extension{"s" if len(exts) else ""}: ' + ', '.join(exts))

    @cog.command(name='reload')
    async def _ext_reload(self, ctx: utils.Context, *extensions: str) -> None:
        """Unload a cog.

        Examples
        --------
            **{p}ext load ~** - loads all extensions.
            **{p}ext load boribay.extensions.fun** - loads the "Fun" cog.

        Parameters
        ----------
        extensions : str
            A set of extensions to load, by default '~ (all)'
        """
        if extensions is None:
            return await ctx.send('Please specify extensions in order to load.')

        exts = self.extensions if extensions[0] == '~' else extensions
        [ctx.bot.reload_extension(ext) for ext in exts]
        await ctx.send(f'Reloaded extension{"s" if len(exts) else ""}: ' + ', '.join(exts))


def setup(bot):
    bot.add_cog(CogManager(bot))
