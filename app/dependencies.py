from functools import lru_cache

import odoorpc

from . import settings


@lru_cache()
def get_odoo(_settings: settings.Settings) -> odoorpc.ODOO:
    """ TODO: verify lru_cache work as espected """
    odoo = odoorpc.ODOO(
            _settings['odoo']['host'],
            port=_settings['odoo']['port'])
    odoo.login(
            _settings['odoo']['database'],
            _settings['odoo']['user'],
            _settings['odoo']['password'])
    return odoo
