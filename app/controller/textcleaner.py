"""Text cleanup for values read from CSV and Excel files."""

from __future__ import annotations

import unicodedata


def clean_import_text(value: object) -> object:
    """Clean imported text while leaving numbers, dates and empty values intact."""
    if not isinstance(value, str):
        return value

    text = value.replace("\ufffd", "")
    # Repair the common UTF-8-read-as-Latin-1 form, e.g. CÃ³digo -> Código.
    if any(marker in text for marker in ("Ã", "Â", "â", "ð")):
        try:
            repaired = text.encode("latin-1").decode("utf-8")
            if repaired:
                text = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    cleaned = []
    for char in unicodedata.normalize("NFC", text):
        category = unicodedata.category(char)
        if category in {"Cc", "Cf", "Cs", "Co", "Cn"}:
            continue
        if category.startswith("So") or category.startswith("Sk"):
            continue
        cleaned.append(char)
    return "".join(cleaned).strip()
