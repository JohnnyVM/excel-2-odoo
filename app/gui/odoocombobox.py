from PyQt6.QtCore import qInfo
from PyQt6.QtWidgets import (
        QComboBox)

from .. import schema
from .. import settings
from ..dependencies import get_odoo


class OdooComboBox(QComboBox):
    """ """

    def __init__(self, model: str = None, **kwargs):
        QComboBox.__init__(self)
        self.model = model
        self.domain = []
        if 'domain' in kwargs:
            self.domain += kwargs['domain']

    def loadModels(self, models: list[schema.OdooModel] = None, **kwargs):
        QComboBox.__init__(self)
        if models:
            for model in models:
                self.addItem(model.display_name, userData=model.id)

    def update(self, domain: list = []):
        odoo = get_odoo(settings.conf)
        _domain = domain + self.domain
        qInfo("OdooComboBox: "
              "Loading model {name} with domain {domain}"
              .format(name=self.model, domain=_domain))
        ids = odoo.env[self.model].search(_domain)
        models = odoo.execute_kw(
                            self.model,
                            'read', [ids], {'fields': ['id', 'display_name']})
        for m in models:
            self.addItem(m['display_name'], userData=m['id'])
