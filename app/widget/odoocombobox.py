from PyQt6.QtCore import qInfo
from PyQt6.QtWidgets import (
        QComboBox)

from .. import schema
from .. import settings
from ..dependencies import get_odoo


class OdooComboBox(QComboBox):
    """ """

    def __init__(self, models: list[schema.OdooModel] = None):
        QComboBox.__init__(self)
        if models:
            for model in models:
                self.addItem(model.display_name, userData=model.id)

    def loadModel(self, model_name: str, domain: list = []):
        odoo = get_odoo(settings.conf)
        ids = odoo.env[model_name].search(domain)
        qInfo("OdooComboBox: Loading model {name} with domain {domain} records: {ids}".format(
                            name=model_name, domain=domain, ids=ids))
        models = odoo.execute_kw(
                            model_name,
                            'read', [ids], {'fields': ['id', 'display_name']})
        for m in models:
            self.addItem(m['display_name'], userData=m['id'])
