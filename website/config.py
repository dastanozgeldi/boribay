from toml import load
from types import SimpleNamespace

__all__ = ('Config')

t = load('website/config.toml')
config = SimpleNamespace(**t)


class Config:
    SECRET_KEY = config.secret_key
    # DISCORD_CLIENT_ID = config.client_id
    # DISCORD_CLIENT_SECRET = config.client_secret
    # DISCORD_REDIRECT_URI = 
    # TODO add PostgreSQL database credentials.
