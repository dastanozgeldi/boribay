import logging


# https://github.com/nickofolas/neo/blob/master/neo/core/__init__.py
# Thanks for this awesome way of logging!
class ColoredFormatter(logging.Formatter):
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
    """Files' logger initializer."""
    logger = logging.getLogger(logger_name)
    handler = logging.StreamHandler()

    formatter = ColoredFormatter(fmt='[%(asctime)s %(levelname)s: %(name)s] -> %(message)s')
    formatter.datefmt = '\x1b[38;2;132;206;255m' + '%d:%m:%Y %H:%M:%S' + formatter.codes['_RESET']
    handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
