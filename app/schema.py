from pydantic import BaseModel


def _is_upper(c: str) -> bool:
    return c >= 'A' and c <= 'Z'


class OdooModel(BaseModel):

    id: int | None
    name: str | None
    display_name: str | None

    @staticmethod
    def odooClassName(name: str):
        clas = ""
        makeUpper = False
        for idx, letter in enumerate(name):
            if letter == '.':
                makeUpper = True
                continue

            if not idx or makeUpper:
                letter = str.upper(letter)
                makeUpper = False

            clas += letter

        return clas

    @staticmethod
    def odooDbName(name: str):
        clas = ""
        for idx, letter in enumerate(name):
            if idx and _is_upper(letter):
                clas += "."

            clas += letter.lower()

        return clas

    @property
    def __name__(self):
        OdooModel.odooDbName(self.__class__.__name__)


class ResCompany(OdooModel):
    pass


class ProductTemplate(OdooModel):
    type: str = "product"
    available_in_pos: bool = True
    barcode: str
    default_code: str | None
    list_price: float | None  # sale price
    standard_price: float | None  # cost price
    taxes_id: list[int]
    supplier_taxes_id: list[int]
    categ_id: int
    company_id: int | None


class AccountTax(OdooModel):
    company_id: int | None


class ProductCategory(OdooModel):
    pass
