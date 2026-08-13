"""Small, dependency-free fuzzy matching helpers for imported column headers."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Mapping


# Product identification aliases.
BARCODE_ALIASES = (
    "ean", "ean13", "ean 13", "upc", "isbn", "gtin", "barcode", "codigo de barras",
)
INTERNAL_REFERENCE_ALIASES = (
    "sku", "internal reference", "item code", "product code", "referencia interna",
)

# Product pricing aliases.
LIST_PRICE_ALIASES = (
    "price", "sales price", "sale price", "retail price", "precio", "pvp", "precio venta",
)

# Product tax and category aliases.
CUSTOMER_TAX_ALIASES = (
    "tax", "tax id", "sales tax", "customer tax", "iva", "impuesto", "impuestos",
)
SUPPLIER_TAX_ALIASES = (
    "purchase tax", "vendor tax", "supplier tax", "iva compra", "impuesto compra",
)
CATEGORY_ALIASES = ("category", "product category", "categoria", "categoría")

# Product descriptive aliases.
NAME_ALIASES = ("title", "product name", "item name", "nombre", "producto")
DESCRIPTION_ALIASES = (
    "details", "product description", "long description", "descripcion", "descripción",
)

COMMON_TERMS = {
    "barcode": BARCODE_ALIASES,
    "default_code": INTERNAL_REFERENCE_ALIASES,
    "list_price": LIST_PRICE_ALIASES,
    "taxes_id": CUSTOMER_TAX_ALIASES,
    "supplier_taxes_id": SUPPLIER_TAX_ALIASES,
    "categ_id": CATEGORY_ALIASES,
    "name": NAME_ALIASES,
    "description": DESCRIPTION_ALIASES,
}


def _normalise(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _score(header: object, field: str, label: object) -> float:
    source = _normalise(header)
    technical = _normalise(field)
    display = _normalise(label)
    if source == technical or source == display:
        return 1.0
    aliases = tuple(_normalise(term) for term in COMMON_TERMS.get(field, ()))
    if source in aliases:
        return 1.0
    # Comparing both the Odoo technical name and its display label makes
    # headers such as "Código de barras" match the field "barcode".
    return max(
        SequenceMatcher(None, source, technical).ratio(),
        SequenceMatcher(None, source, display).ratio(),
        *(SequenceMatcher(None, source, alias).ratio() for alias in aliases),
    )


def match_headers(
    headers: list[object] | tuple[object, ...],
    fields: Mapping[str, Mapping[str, object]],
    threshold: float = 0.62,
) -> tuple[str | None, ...]:
    """Match imported headers to Odoo fields, at most once per field.

    Returns one technical field name (or ``None``) for every input header.
    ``threshold`` deliberately leaves uncertain headers unmatched so the user
    can choose the key in the table header selector.
    """
    available = tuple(fields.keys())
    result: list[str | None] = []
    used: set[str] = set()
    for header in headers:
        ranked = sorted(
            (
                (_score(header, field, fields[field].get("string", field)), field)
                for field in available
                if field not in used
            ),
            reverse=True,
        )
        if not ranked or ranked[0][0] < threshold:
            result.append(None)
        else:
            field = ranked[0][1]
            result.append(field)
            used.add(field)
    return tuple(result)
