import json

__all__ = ("Config",)


class BotPart:
    __slots__ = {"beta", "token", "exts", "errors_log"}

    def __init__(self, data: dict):
        self.beta = data.get("beta", False)
        self.token = data["token"]
        self.exts = data.get("exts", [])
        self.errors_log = data.get("errors_log")


class ApiPart:
    __slots__ = {"weather", "dagpi"}

    def __init__(self, data: dict):
        self.weather = data.get("weather")
        self.dagpi = data.get("dagpi")


class Config:
    """Configuration loader class for Boribay.

    All file-configuration stuff is controlled here using `.json` files.
    """

    __slots__ = {"path", "values", "main", "database", "api"}

    def __init__(self, path: str):
        self.path = path
        self.values = {}
        self.reload()

    def reload(self):
        with open(self.path, "r") as fp:
            self.values = json.load(fp)
        self.set_attributes()

    def set_attributes(self):
        self.main = BotPart(self.values["bot"])
        self.database = self.values.get("database", {})
        self.api = ApiPart(self.values.get("api", {}))
