from PyQt6.QtCore import qInfo
from PyQt6.QtWidgets import (
        QComboBox)

from .. import schema
from .. import settings
from ..dependencies import get_odoo


class OdooComboBox(QComboBox):
    """ """

    domain: list = []

    def __init__(self, models: list[schema.OdooModel] = None, **kwargs):
        QComboBox.__init__(self)
        if models:
            for model in models:
                self.addItem(model.display_name, userData=model.id)

        if 'domain' in kwargs:
            self.domain += kwargs['domain']

    def loadModel(self, model_name: str, domain: list = []):
        odoo = get_odoo(settings.conf)
        _domain = domain + self.domain
        ids = odoo.env[model_name].search(_domain)
        qInfo("OdooComboBox: "
              "Loading model {name} with domain {domain} records: {ids}"
              .format(name=model_name, domain=_domain, ids=ids))
        models = odoo.execute_kw(
                            model_name,
                            'read', [ids], {'fields': ['id', 'display_name']})
        for m in models:
            self.addItem(m['display_name'], userData=m['id'])
