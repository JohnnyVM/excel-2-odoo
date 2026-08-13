from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote
import logging
import subprocess
import sys


@dataclass
class AmazonProduct:
    name: str = ""
    description: str = ""
    image: bytes | None = None
    url: str = ""
    verified: bool = False


class AmazonScraper:
    """Best-effort Amazon page reader. It deliberately does not bypass challenges."""

    def __init__(self, marketplace: str = "www.amazon.com", timeout_ms: int = 15000):
        self.marketplace = marketplace
        self.timeout_ms = timeout_ms
        self.ensure_chromium()

    @staticmethod
    def chromium_installed() -> bool:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--list"],
                check=True, capture_output=True, text=True, timeout=30,
            )
            return "chromium" in result.stdout.lower()
        except (OSError, subprocess.SubprocessError):
            return False

    @classmethod
    def ensure_chromium(cls) -> None:
        if cls.chromium_installed():
            return
        logging.getLogger(__name__).info("Installing Playwright Chromium browser")
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True, timeout=180,
        )

    def search(self, barcode: str) -> AmazonProduct | None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Amazon lookup requires the optional 'playwright' package") from exc

        url = f"https://{self.marketplace}/s?k={quote(str(barcode).strip())}"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                body = (page.locator("body").inner_text(timeout=5000) or "").lower()
                if "captcha" in body or "robot check" in body or "access denied" in body:
                    raise RuntimeError("Amazon blocked the request (CAPTCHA/access denied)")
                if "lo sentimos" in body or "error al intentar procesar" in body:
                    raise RuntimeError("Amazon returned an error page; retry later or change marketplace")
                # Restrict this to actual search-result cards. A broad
                # div[data-asin] fallback can select Amazon's generic
                # navigation/result container whose title is just "Resultados".
                result = page.locator("div[data-component-type='s-search-result']").first
                if result.count() == 0:
                    result = page.locator("div[data-asin][data-index]").first
                if result.count() == 0:
                    return None
                title_locator = result.locator("h2, [data-cy='title-recipe'], span.a-text-normal").first
                title = title_locator.inner_text(timeout=5000) if title_locator.count() else ""
                description = "\n".join(result.locator(".a-size-base-plus, .a-size-small").all_inner_texts())
                image_locator = result.locator("img.s-image").first
                image_url = image_locator.get_attribute("src", timeout=3000) if image_locator.count() else None
                link_locator = result.locator("h2 a, a.a-link-normal").first
                item_url = link_locator.get_attribute("href", timeout=3000) if link_locator.count() else ""
                image = None
                if image_url:
                    response = page.request.get(image_url, timeout=self.timeout_ms)
                    if response.ok and response.headers.get("content-type", "").startswith("image/"):
                        image = response.body()
                # Search pages do not reliably expose EAN/UPC; mark this as unverified.
                return AmazonProduct(title.strip(), description.strip(), image, item_url, verified=False)
            finally:
                browser.close()
