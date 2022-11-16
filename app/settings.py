from configparser import ConfigParser


class Settings(dict):
    __values = {
        "odoo": {
            "port": 8069,
            "host": "localhost"
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

        return self.__getitem__(key)
