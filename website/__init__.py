from quart import Quart
from quart_discord import DiscordOAuth2Session

from .config import Config


def create_app(config_class=Config):
    app = Quart(__name__)
    app.config.from_object(Config)
    app.discord = DiscordOAuth2Session(app)

    from website.errors.handlers import errors
    from website.main.routes import main

    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app
