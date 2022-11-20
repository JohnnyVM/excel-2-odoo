from configparser import ConfigParser


class Settings(dict):
    """ refactor this """
    __values = {
        "odoo": {
            "port": 8069,
            "host": "localhost",
            "database": "odoo",
            }
        }

    def __init__(self, config: ConfigParser, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for ite in config:
            for key, val in config[ite].items():
                self.__values[ite][key] = val

    def __getitem__(self, key):
        if key in self.__values:
            return self.__values[key]

        return super().__getitem__(key)

    def __hash__(self):
        d = dict(self)
        d.update(self.__values)
        return hash(frozenset(d))


def init(config: ConfigParser, *args, **kwargs):
    global conf
    conf = Settings(config, *args, **kwargs)
