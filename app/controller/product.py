from __future__ import annotations

import base64
from typing import Any


class ProductController:
    """Read and write product.template records through the existing Odoo RPC API."""

    def __init__(self, conn):
        self.conn = conn

    def _fields(self) -> dict[str, Any]:
        return self.conn.execute_kw("product.template", "fields_get", [], {})

    def find_by_barcode(self, barcode: str) -> dict[str, Any] | None:
        barcode = str(barcode).strip()
        if not barcode:
            return None
        available = self._fields()
        wanted = ["id", "barcode", "default_code", "name", "description", "description_sale", "image_1920", "product_tag_ids"]
        fields = [field for field in wanted if field in available]
        records = self.conn.execute_kw(
            "product.template", "search_read", [[("barcode", "=", barcode)]], {"fields": fields, "limit": 1}
        )
        return records[0] if records else None

    def save(self, values: dict[str, Any], product_id: int | None = None) -> int:
        available = self._fields()
        clean = {key: value for key, value in values.items() if key in available and value is not None}
        if product_id is None:
            return self.conn.execute_kw("product.template", "create", [clean])
        self.conn.execute_kw("product.template", "write", [[product_id], clean])
        return product_id

    def tag_ids(self, names: str) -> list[int]:
        values = [name.strip() for name in names.split(",") if name.strip()]
        if not values:
            return []
        fields = self._fields()
        if "product_tag_ids" not in fields:
            return []
        ids = []
        for name in values:
            found = self.conn.execute_kw("product.tag", "search_read", [[("name", "=", name)]], {"fields": ["id"], "limit": 1})
            ids.append(found[0]["id"] if found else self.conn.execute_kw("product.tag", "create", [{"name": name}]))
        return ids

    @staticmethod
    def image_to_base64(image: bytes | None) -> str | None:
        return base64.b64encode(image).decode("ascii") if image else None
