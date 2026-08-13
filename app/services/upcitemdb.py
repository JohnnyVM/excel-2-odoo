from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


class UPCItemDBRateLimitError(RuntimeError):
    pass


@dataclass
class UPCProduct:
    name: str = ""
    description: str = ""
    image_url: str = ""


class UPCItemDB:
    endpoint = "https://api.upcitemdb.com/prod/trial/lookup"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def search(self, barcode: str) -> UPCProduct | None:
        url = f"{self.endpoint}?upc={urllib.parse.quote(str(barcode).strip())}"
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "excel-2-odoo/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status == 429:
                    raise UPCItemDBRateLimitError("UPCitemdb rate limit reached (HTTP 429)")
                payload = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise UPCItemDBRateLimitError("UPCitemdb rate limit reached (HTTP 429)") from exc
            if exc.code == 404:
                return None
            raise RuntimeError(f"UPCitemdb request failed (HTTP {exc.code})") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"UPCitemdb connection failed: {exc.reason}") from exc

        items = payload.get("items") or []
        if not items:
            return None
        item = items[0]
        images = item.get("images") or []
        return UPCProduct(item.get("title", ""), item.get("description", ""), images[0] if images else "")
