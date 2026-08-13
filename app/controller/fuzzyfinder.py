"""Small, dependency-free fuzzy matching helpers for imported column headers."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Mapping


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
    # Comparing both the Odoo technical name and its display label makes
    # headers such as "Código de barras" match the field "barcode".
    return max(SequenceMatcher(None, source, technical).ratio(),
               SequenceMatcher(None, source, display).ratio())


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
