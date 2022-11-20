from PyQt6.QtWidgets import (
        QComboBox)

from .. import schema


class OdooComboBox(QComboBox):
    """ """

    def __init__(self, models: list[schema.OdooModel]):
        QComboBox.__init__(self)
        for model in models:
            self.addItem(model.display_name, userData=model.id)
