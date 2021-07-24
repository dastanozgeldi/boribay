import toml

__all__ = ('Config',)


class BotPart:
    __slots__ = {'beta', 'token', 'exts', 'errors_channel'}

    def __init__(self, data: dict):
        self.beta = data.get('beta', False)
        self.token = data['token']
        self.exts = data.get('exts', [])
        self.errors_channel = data.get('errors_channel')


class LinksPart:
    __slots__ = {'log_url', 'invite_url', 'github_url', 'support_url', 'topgg_url'}

    def __init__(self, data: dict):
        self.log_url = data.get('log_url')
        self.invite_url = data.get('invite_url')
        self.github_url = data.get('github_url')
        self.support_url = data.get('support_url')
        self.topgg_url = data.get('topgg_url')


class ApiPart:
    __slots__ = {'weather', 'dagpi', 'alex'}

    def __init__(self, data: dict):
        self.weather = data.get('weather')
        self.dagpi = data.get('dagpi')
        self.alex = data.get('alex')


class Config:
    """Configuration loader class for Boribay.

    All file-configuration stuff is controlled here using `.toml` files.
    """
    __slots__ = {'path', 'values', 'main', 'database', 'links', 'api'}

    def __init__(self, path: str):
        self.path = path
        self.values = {}
        self.reload()

    def reload(self):
        self.values = toml.load(self.path)
        self.set_attributes()

    def set_attributes(self):
        self.main = BotPart(self.values['bot'])
        self.database = self.values.get('database', {})
        self.links = LinksPart(self.values.get('links', {}))
        self.api = ApiPart(self.values.get('API', {}))
