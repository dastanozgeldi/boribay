import json

__all__ = ('Config',)


class BotPart:
    __slots__ = {'beta', 'token', 'exts', 'errors_log'}

    def __init__(self, data: dict):
        self.beta = data.get('beta', False)
        self.token = data['token']
        self.exts = data.get('exts', [])
        self.errors_log = data.get('errors_log')


class LinksPart:
    __slots__ = {'webhook', 'invite', 'github', 'support', 'top_gg'}

    def __init__(self, data: dict):
        self.webhook = data.get('webhook')
        self.invite = data.get('invite')
        self.github = data.get('github')
        self.support = data.get('support')
        self.top_gg = data.get('top_gg')


class ApiPart:
    __slots__ = {'weather', 'dagpi', 'alex'}

    def __init__(self, data: dict):
        self.weather = data.get('weather')
        self.dagpi = data.get('dagpi')
        self.alex = data.get('alex')


class Config:
    """Configuration loader class for Boribay.

    All file-configuration stuff is controlled here using `.json` files.
    """
    __slots__ = {'path', 'values', 'main', 'database', 'links', 'api'}

    def __init__(self, path: str):
        self.path = path
        self.values = {}
        self.reload()

    def reload(self):
        with open(self.path, 'r') as fp:
            self.values = json.load(fp)
        self.set_attributes()

    def set_attributes(self):
        self.main = BotPart(self.values['bot'])
        self.database = self.values.get('database', {})
        self.links = LinksPart(self.values.get('links', {}))
        self.api = ApiPart(self.values.get('api', {}))
