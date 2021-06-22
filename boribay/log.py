"""
95% of this file was taken from Red.

Thanks Cog-Creators for this awesome way of logging!

Link
----
https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/logging.py
"""

import logging
import pathlib
import sys
from datetime import datetime
from os import isatty

import rich
from pygments.styles.monokai import MonokaiStyle
from pygments.token import (Comment, Error, Keyword, Name, Number, Operator,
                            String, Token)
from rich._log_render import LogRender
from rich.console import render_group
from rich.containers import Renderables
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.style import Style
from rich.syntax import ANSISyntaxTheme, PygmentsSyntaxTheme
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import PathHighlighter, Traceback

__all__ = ('init_logging',)

SYNTAX_THEME = {
    Token: Style(),
    Comment: Style(color='bright_black'),
    Keyword: Style(color='cyan', bold=True),
    Keyword.Constant: Style(color='bright_magenta'),
    Keyword.Namespace: Style(color='bright_red'),
    Operator: Style(bold=True),
    Operator.Word: Style(color='cyan', bold=True),
    Name.Builtin: Style(bold=True),
    Name.Builtin.Pseudo: Style(color='bright_red'),
    Name.Exception: Style(bold=True),
    Name.Class: Style(color='bright_green'),
    Name.Function: Style(color='bright_green'),
    String: Style(color='yellow'),
    Number: Style(color='cyan'),
    Error: Style(bgcolor='red'),
}


class FixedMonokaiStyle(MonokaiStyle):
    """The fixed version of the style `Monokai`.

    This class inherits from `pygments.styles.monokai.MonokaiStyle`.
    """
    styles = {**MonokaiStyle.styles, Token: "#f8f8f2"}


class CustomTraceback(Traceback):
    """The custom version of `rich.traceback.Traceback`."""

    @render_group()
    def _render_stack(self, stack):
        for obj in super()._render_stack.__wrapped__(self, stack):
            if obj != '':
                yield obj


class CustomLogRender(LogRender):
    """The custom version of `rich._log_render.LogRender`."""

    def __call__(
        self,
        console,
        renderables,
        log_time: datetime = None,
        time_format: datetime = None,
        level: str = '',
        path: str = None,
        line_no: int = None,
        link_path: str = None,
        logger_name: str = None,
    ):
        output = Table.grid(padding=(0, 1))
        output.expand = True
        if self.show_time:
            output.add_column(style='log.time')
        if self.show_level:
            output.add_column(style='log.level', width=self.level_width)

        output.add_column(ratio=1, style='log.message', overflow='fold')
        if self.show_path and path:
            output.add_column(style='log.path')

        if logger_name:
            output.add_column()

        row = []
        if self.show_time:
            log_time = log_time or console.get_datetime()
            log_time_display = log_time.strftime(time_format or self.time_format)

            if log_time_display == self._last_time:
                row.append(Text(' ' * len(log_time_display)))

            else:
                row.append(Text(log_time_display))
                self._last_time = log_time_display

        if self.show_level:
            row.append(level)

        row.append(Renderables(renderables))
        if self.show_path and path:
            path_text = Text()
            path_text.append(path, style=f'link file://{link_path}' if link_path else '')

            if line_no:
                path_text.append(f':{line_no}')
            row.append(path_text)

        if logger_name:
            logger_name_text = Text()
            logger_name_text.append(f'[{logger_name}]', style='bright_black')
            row.append(logger_name_text)

        output.add_row(*row)
        return output


class CustomRichHandler(RichHandler):
    """The custom RichHandler to adjust the path to a logger name."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_render = CustomLogRender(
            show_time=self._log_render.show_time,
            show_level=self._log_render.show_level,
            show_path=self._log_render.show_path,
            level_width=self._log_render.level_width,
        )

    def get_level_text(self, record: logging.LogRecord) -> Text:
        """Get the level name from the record.

        Parameters
        ----------
        record : logging.LogRecord
            Used to get the logging level.

        Returns
        -------
        Text
            A tuple of the level name.
        """
        level_text = super().get_level_text(record)
        level_text.stylize('bold')
        return level_text

    def emit(self, record: logging.LogRecord) -> None:
        """Func that gets invoked by logging.

        Parameters
        ----------
        record : logging.LogRecord
            Used to set the config up.
        """
        path = pathlib.Path(record.pathname).name
        level = self.get_level_text(record)
        message = self.format(record)
        time_format = None if self.formatter is None else self.formatter.datefmt
        log_time = datetime.fromtimestamp(record.created)

        traceback = None
        if self.rich_tracebacks and record.exc_info and record.exc_info != (None, None, None):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            traceback = CustomTraceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
                indent_guides=False,
            )
            message = record.getMessage()

        use_markup = record.markup if hasattr(record, 'markup') else self.markup
        if use_markup:
            message_text = Text.from_markup(message)
        else:
            message_text = Text(message)

        if self.highlighter:
            message_text = self.highlighter(message_text)
        if self.KEYWORDS:
            message_text.highlight_words(self.KEYWORDS, 'logging.keyword')

        self.console.print(
            self._log_render(
                self.console,
                [message_text],
                log_time=log_time,
                time_format=time_format,
                level=level,
                path=path,
                line_no=record.lineno,
                link_path=record.pathname if self.enable_link_path else None,
                logger_name=record.name,
            )
        )
        if traceback:
            self.console.print(traceback)


def init_logging(level: int) -> None:
    """Initialize logging features through this method.

    Parameters
    ----------
    level : int
        Logging level to set as the least.
    """
    root_logger = logging.getLogger()

    base_logger = logging.getLogger('bot')
    base_logger.setLevel(level)
    dpy_logger = logging.getLogger('discord')
    dpy_logger.setLevel(logging.WARNING)
    warnings_logger = logging.getLogger('py.warnings')
    warnings_logger.setLevel(logging.WARNING)

    rich_console = rich.get_console()
    rich.reconfigure(tab_size=4)
    rich_console.push_theme(
        Theme({
            'log.time': Style(dim=True),
            'logging.level.warning': Style(color='yellow'),
            'logging.level.critical': Style(color='white', bgcolor='red'),
            'repr.number': Style(color='cyan'),
            'repr.url': Style(underline=True, italic=True, bold=False, color='cyan'),
        })
    )
    rich_console.file = sys.stdout
    PathHighlighter.highlights = []
    enable_rich_logging = False

    if isatty(0):
        # Check if the bot thinks it has an active terminal.
        enable_rich_logging = True

    file_formatter = logging.Formatter(
        '[{asctime}] [{levelname}] {name}: {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{'
    )
    if enable_rich_logging:
        rich_formatter = logging.Formatter('{message}', datefmt='[%X]', style='{')

        stdout_handler = CustomRichHandler(
            rich_tracebacks=True,
            show_path=False,
            highlighter=NullHighlighter(),
            tracebacks_extra_lines=True,
            tracebacks_show_locals=True,
            tracebacks_theme=(
                PygmentsSyntaxTheme(FixedMonokaiStyle)
                if rich_console.color_system == 'truecolor'
                else ANSISyntaxTheme(SYNTAX_THEME)
            ),
        )
        stdout_handler.setFormatter(rich_formatter)
    else:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(file_formatter)

    root_logger.addHandler(stdout_handler)
    logging.captureWarnings(True)
