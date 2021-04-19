from discord.ext import ipc
from quart import Quart

from .config import config


def create_app(config_class=None):
    app = Quart(__name__)
    app.config.from_object(config.qd)
    app.web_ipc = ipc.Client(**config.IPC)

    from website.errors.handlers import errors
    from website.main.routes import main

    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app
