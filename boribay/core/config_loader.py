import toml


class BotPart:
    __slots__ = {'version', 'beta', 'token', 'dbl_token',
                 'exts', 'news_channel', 'errors_channel', 'owner_exts'}

    def __init__(self, data: dict):
        self.version = data.get('version', 'development')
        self.beta = data.get('beta', False)
        self.token = data['token']
        self.dbl_token = data['dbl_token']
        self.exts = data.get('exts', [])
        self.news_channel = data.get('news_channel')
        self.errors_channel = data.get('errors_channel')
        self.owner_exts = data.get('owner_exts', [])


class LinksPart:
    __slots__ = {'log_url', 'invite_url', 'github_url', 'support_url', 'topgg_url'}

    def __init__(self, data: dict):
        self.log_url = data.get('log_url')
        self.invite_url = data.get('invite_url')
        self.github_url = data.get('github_url')
        self.support_url = data.get('support_url')
        self.topgg_url = data.get('topgg_url')


class ApiPart:
    __slots__ = {'anime', 'ud', 'qr', 'trivia', 'screenshot', 'quote',
                 'caption', 'weather', 'covid', 'google_key', 'dagpi', 'alex'}

    def __init__(self, data: dict):
        self.anime = data.get('anime')
        self.ud = data.get('ud')
        self.qr = data.get('qr')
        self.trivia = data.get('trivia')
        self.screenshot = data.get('screenshot')
        self.quote = data.get('quote')
        self.caption = data.get('caption')
        self.weather = data.get('weather', [])  # A list which is like [url, id]
        self.covid = data.get('covid')
        self.google_key = data.get('google_key')
        self.dagpi = data.get('dagpi', [])  # A list which is like [url, token]
        self.alex = data.get('alex', [])  # A list which is like [url, token]


class ConfigLoader:
    __slots__ = {'config', 'values', 'main', 'database', 'links', 'api', 'ipc'}

    def __init__(self, path: str):
        self.config = path
        self.values = {}
        self.reload()

    def reload(self):
        self.values = toml.load(self.config)
        self.set_attributes()

    def set_attributes(self):
        self.main = BotPart(self.values['bot'])
        self.database = self.values.get('database', {})
        self.links = LinksPart(self.values.get('links', {}))
        self.api = ApiPart(self.values.get('API', {}))
        self.ipc = self.values.get('IPC', {})
