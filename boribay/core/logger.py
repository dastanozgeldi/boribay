import logging

__all__ = ('create_logger',)


# https://github.com/nickofolas/neo/blob/master/neo/core/__init__.py
# Thanks for this awesome way of logging!
class ColoredFormatter(logging.Formatter):
    """The fancy way of formatting the logger."""

    prefix = '\x1b[38;5;'
    codes = {
        'INFO': f'{prefix}2m',
        'WARN': f'{prefix}100m',
        'DEBUG': f'{prefix}26m',
        'ERROR': f'{prefix}1m',
        'WARNING': f'{prefix}220m',
        '_RESET': '\x1b[0m',
    }

    def format(self, record: logging.LogRecord):
        if record.levelname in self.codes:
            record.msg = self.codes[record.levelname] + str(record.msg) + self.codes['_RESET']
            record.levelname = self.codes[record.levelname] + record.levelname + self.codes['_RESET']

        return super().format(record)


def create_logger(logger_name: str, level=logging.INFO) -> logging.Logger:
    """The logger initializing method used to ease up the logging manipulation.

    Args:
        logger_name (str): The logger name you would like to set.
        level (optional): The minimal logging level, anything below will be
        accordingly ignored. Defaults to logging.INFO.

    Returns:
        logging.Logger: A logger object that consequently logs events.
    """
    logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler()

    formatter = ColoredFormatter(fmt='[%(asctime)s %(levelname)s: %(name)s] -> %(message)s')
    formatter.datefmt = '\x1b[38;2;132;206;255m' + '%d:%m:%Y %H:%M:%S' + formatter.codes['_RESET']
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
