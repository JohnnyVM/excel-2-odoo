from __future__ import annotations

import base64
import logging
import urllib.request

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QFileDialog,
    QPlainTextEdit, QVBoxLayout, QWidget,
)

from ...controller.product import ProductController
from ...dependencies import get_odoo
from ...services.amazon import AmazonScraper
from ...services.upcitemdb import UPCItemDB, UPCItemDBRateLimitError
from ... import settings

logger = logging.getLogger(__name__)


class _LookupWorker(QObject):
    finished = pyqtSignal(object, object)
    progress = pyqtSignal(str)

    def __init__(self, barcode: str, amazon_only: bool = False):
        super().__init__()
        self.barcode = barcode
        self.amazon_only = amazon_only

    def run(self):
        try:
            if self.amazon_only:
                self._progress("Amazon-only search started")
                self._search_amazon()
                return
            self._progress("Connecting to Odoo...")
            controller = ProductController(get_odoo(settings.conf))
            self._progress(f"Checking barcode {self.barcode} in product.template...")
            existing = controller.find_by_barcode(self.barcode)
            if existing:
                self._progress("Product found in Odoo")
                missing_description = not (existing.get("description") or existing.get("description_sale"))
                missing_image = not existing.get("image_1920")
                if missing_description or missing_image:
                    result = self._search_missing_data(existing, missing_description, missing_image)
                    self.finished.emit(result, None)
                else:
                    self.finished.emit({"odoo": existing}, None)
                return
            self._progress("Barcode not found in Odoo")
            if not self.amazon_only:
                try:
                    self._progress("Searching UPCitemdb...")
                    upc = UPCItemDB().search(self.barcode)
                    if upc:
                        image = self._download_image(upc.image_url)
                        self._progress("UPCitemdb product found")
                        self.finished.emit({"upc": upc, "image": image}, None)
                        return
                    self._progress("UPCitemdb returned no product")
                except UPCItemDBRateLimitError as exc:
                    self._progress(f"BLOCKED: {exc}; trying Amazon fallback")
                except Exception as exc:
                    self._progress(f"UPCitemdb unavailable: {exc}; trying Amazon fallback")
            try:
                self._progress("Opening Amazon search...")
                amazon_cfg = settings.conf["amazon"]
                amazon = AmazonScraper(
                    marketplace=amazon_cfg.get("marketplace", "www.amazon.com"),
                    timeout_ms=int(amazon_cfg.get("timeout_ms", 15000)),
                ).search(self.barcode)
                self._progress("Amazon search finished")
            except Exception as exc:
                self.finished.emit({"amazon_error": str(exc)}, None)
                return
            self.finished.emit({"amazon": amazon}, None)
        except Exception as exc:
            self.finished.emit(None, str(exc))

    def _search_missing_data(self, existing, missing_description, missing_image):
        """Enrich an Odoo match without replacing values already stored there."""
        result = {"odoo": existing}
        upc = None
        try:
            self._progress("Description or image missing; searching UPCitemdb...")
            upc = UPCItemDB().search(self.barcode)
            if upc:
                result["upc"] = upc
                result["image"] = self._download_image(upc.image_url)
                self._progress("UPCitemdb fallback finished")
            else:
                self._progress("UPCitemdb returned no product; trying Amazon fallback")
        except UPCItemDBRateLimitError as exc:
            self._progress(f"BLOCKED: {exc}; trying Amazon fallback")
        except Exception as exc:
            self._progress(f"UPCitemdb unavailable: {exc}; trying Amazon fallback")

        upc_has_description = bool(upc and upc.description)
        upc_has_image = bool(result.get("image"))
        if (missing_description and not upc_has_description) or (missing_image and not upc_has_image):
            try:
                self._progress("Opening Amazon fallback...")
                amazon_cfg = settings.conf["amazon"]
                result["amazon"] = AmazonScraper(
                    marketplace=amazon_cfg.get("marketplace", "www.amazon.com"),
                    timeout_ms=int(amazon_cfg.get("timeout_ms", 15000)),
                ).search(self.barcode)
                self._progress("Amazon fallback finished")
            except Exception as exc:
                result["amazon_error"] = str(exc)
                self._progress(f"Amazon fallback unavailable: {exc}")
        return result

    def _search_amazon(self):
        try:
            self._progress("Opening Amazon search...")
            amazon_cfg = settings.conf["amazon"]
            amazon = AmazonScraper(
                marketplace=amazon_cfg.get("marketplace", "www.amazon.com"),
                timeout_ms=int(amazon_cfg.get("timeout_ms", 15000)),
            ).search(self.barcode)
            self._progress("Amazon search finished")
            self.finished.emit({"amazon": amazon}, None)
        except Exception as exc:
            self.finished.emit({"amazon_error": str(exc)}, None)

    @staticmethod
    def _download_image(url):
        if not url:
            return None
        request = urllib.request.Request(url, headers={"User-Agent": "excel-2-odoo/1.0"})
        with urllib.request.urlopen(request, timeout=10) as response:
            if not response.headers.get_content_type().startswith("image/"):
                return None
            return response.read(10 * 1024 * 1024 + 1)

    def _progress(self, message):
        logger.info(message)
        self.progress.emit(message)


class ProductFormWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._product_id = None
        self._image_bytes = None
        self._thread = None
        self._worker = None

        self.barcode_search = QLineEdit()
        self.barcode_search.setPlaceholderText("Barcode")
        self.search_button = QPushButton("Search")
        self.amazon_search_button = QPushButton("Amazon search")
        search_row = QHBoxLayout()
        search_row.addWidget(self.barcode_search)
        search_row.addWidget(self.search_button)
        search_column = QVBoxLayout()
        search_column.addLayout(search_row)
        search_column.addWidget(self.amazon_search_button)

        self.tags = QLineEdit()
        self.name = QLineEdit()
        self.barcode = QLineEdit()
        self.list_price = QLineEdit()
        self.list_price.setPlaceholderText("0.00")
        self.description = QPlainTextEdit()
        self.default_code = QLineEdit()
        self.image_url = QLineEdit()
        self.image_url.setPlaceholderText("https://...")
        self.load_url_button = QPushButton("Load URL")
        self.load_file_button = QPushButton("Load file")
        image_sources = QHBoxLayout()
        image_sources.addWidget(self.image_url)
        image_sources.addWidget(self.load_url_button)
        image_sources.addWidget(self.load_file_button)
        self.image = QLabel("No image")
        self.image.setMinimumSize(180, 180)
        self.image.setScaledContents(True)
        self.status = QLabel()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(130)
        self.save_button = QPushButton("Create")
        self.cancel_button = QPushButton("Cancel")

        form = QFormLayout()
        form.addRow("Search barcode", search_column)
        form.addRow("Tags", self.tags)
        form.addRow("Name", self.name)
        form.addRow("Barcode", self.barcode)
        form.addRow("Internal reference", self.default_code)
        form.addRow("List price", self.list_price)
        form.addRow("Description", self.description)
        form.addRow("Image source", image_sources)
        form.addRow("Image", self.image)
        form.addRow("Status", self.status)
        form.addRow("Activity log", self.log)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.search_button.clicked.connect(self.lookup)
        self.amazon_search_button.clicked.connect(self.lookup_amazon)
        self.barcode_search.returnPressed.connect(self.lookup)
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reset)
        self.load_file_button.clicked.connect(self.load_file)
        self.load_url_button.clicked.connect(self.load_url)

    def lookup(self):
        self._start_lookup(amazon_only=False)

    def lookup_amazon(self):
        self._start_lookup(amazon_only=True)

    def _start_lookup(self, amazon_only=False):
        barcode = self.barcode_search.text().strip()
        if not barcode:
            self.status.setText("Enter a barcode")
            return
        self._set_busy(True, "Searching Odoo and Amazon...")
        self.log.clear()
        self._append_log("Search started")
        self._thread = QThread(self)
        worker = _LookupWorker(barcode, amazon_only=amazon_only)
        self._worker = worker
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.progress.connect(self._append_log)
        worker.finished.connect(self._lookup_finished)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._lookup_thread_finished)
        self._thread.start()

    def _lookup_thread_finished(self):
        self._worker = None

    def _lookup_finished(self, result, error):
        self._set_busy(False)
        if error:
            self._append_log(f"ERROR: {error}")
            self.status.setText(error)
            return
        self.reset(keep_search=True, keep_log=True)
        if result.get("odoo"):
            data = result["odoo"]
            self._product_id = data.get("id")
            self.name.setText(data.get("name") or "")
            self.barcode.setText(data.get("barcode") or self.barcode_search.text())
            self.default_code.setText(data.get("default_code") or "")
            list_price = data.get("list_price")
            self.list_price.setText(str(list_price) if list_price is not None else "")
            description = data.get("description") or data.get("description_sale") or ""
            if not description:
                for provider in (result.get("upc"), result.get("amazon")):
                    description = getattr(provider, "description", "") or description
            self.description.setPlainText(description)
            tag_values = data.get("product_tag_ids") or []
            self.tags.setText(", ".join(
                value[1] if isinstance(value, (list, tuple)) and len(value) > 1 else str(value)
                for value in tag_values
            ))
            self.status.setText("Existing product loaded")
            self.save_button.setText("Update")
            if data.get("image_1920"):
                self._set_image(base64.b64decode(data["image_1920"]))
            elif result.get("image"):
                self._set_image(result["image"])
            elif result.get("amazon") and result["amazon"].image:
                self._set_image(result["amazon"].image)
            if result.get("upc") or result.get("amazon"):
                self.status.setText("Existing product loaded; missing fields enriched from providers")
            return
        upc = result.get("upc")
        if upc:
            self.name.setText(upc.name)
            self.barcode.setText(self.barcode_search.text().strip())
            self.description.setPlainText(upc.description)
            self._set_image(result.get("image"))
            self.status.setText("UPCitemdb suggestion (review before creating)")
            return
        amazon = result.get("amazon")
        if amazon:
            self.name.setText(amazon.name)
            self.barcode.setText(self.barcode_search.text().strip())
            self.description.setPlainText(amazon.description)
            self._set_image(amazon.image)
            self.status.setText("Amazon suggestion (review before creating)")
        else:
            self.barcode.setText(self.barcode_search.text().strip())
            self.status.setText(result.get("amazon_error", "No Amazon result; enter product details manually"))

    def save(self):
        barcode = self.barcode.text().strip()
        name = self.name.text().strip()
        if not barcode or not name:
            self.status.setText("Name and barcode are required")
            return
        try:
            list_price_text = self.list_price.text().strip().replace(",", ".")
            values = {
                "name": name,
                "barcode": barcode,
                "default_code": self.default_code.text().strip(),
                "description": self.description.toPlainText(),
            }
            if list_price_text:
                values["list_price"] = float(list_price_text)
            controller = ProductController(get_odoo(settings.conf))
            tag_ids = controller.tag_ids(self.tags.text())
            if tag_ids:
                values["product_tag_ids"] = [(6, 0, tag_ids)]
            if self._image_bytes:
                values["image_1920"] = ProductController.image_to_base64(self._image_bytes)
            product_id = controller.save(values, self._product_id)
            self._append_log(f"Product {'updated' if self._product_id else 'created'} in Odoo (id {product_id})")
            self.status.setText(f"Product saved ({product_id})")
            self._product_id = product_id
        except Exception as exc:
            self._append_log(f"ERROR saving product: {exc}")
            QMessageBox.critical(self, "Odoo error", str(exc))

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select product image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not filename:
            return
        try:
            with open(filename, "rb") as image_file:
                self._set_image(image_file.read())
            self.status.setText("Image loaded from file")
        except OSError as exc:
            self.status.setText(f"Could not load image: {exc}")

    def load_url(self):
        url = self.image_url.text().strip()
        if not url.lower().startswith(("http://", "https://")):
            self.status.setText("Enter a valid HTTP or HTTPS image URL")
            return
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "excel-2-odoo/1.0"})
            with urllib.request.urlopen(request, timeout=10) as response:
                content_type = response.headers.get_content_type()
                if not content_type.startswith("image/"):
                    raise ValueError("URL does not return an image")
                data = response.read(10 * 1024 * 1024 + 1)
            if len(data) > 10 * 1024 * 1024:
                raise ValueError("Image is larger than 10 MB")
            self._set_image(data)
            self.status.setText("Image loaded from URL")
        except Exception as exc:
            self.status.setText(f"Could not load image URL: {exc}")

    def reset(self, keep_search=False, keep_log=False):
        if not keep_search:
            self.barcode_search.clear()
        self.tags.clear(); self.name.clear(); self.barcode.clear(); self.default_code.clear(); self.list_price.clear(); self.description.clear(); self.image_url.clear()
        if not keep_log:
            self.log.clear()
        self.image.clear(); self.image.setText("No image"); self.status.clear()
        self._product_id = None; self._image_bytes = None; self.save_button.setText("Create")

    def _set_image(self, image_bytes):
        self._image_bytes = image_bytes
        if image_bytes:
            pixmap = QPixmap(); pixmap.loadFromData(image_bytes)
            self.image.setPixmap(pixmap)

    def _set_busy(self, busy, message=None):
        self.search_button.setEnabled(not busy); self.amazon_search_button.setEnabled(not busy); self.save_button.setEnabled(not busy)
        self.barcode_search.setEnabled(not busy)
        if message: self.status.setText(message)

    def _append_log(self, message):
        self.log.appendPlainText(message)
        self.status.setText(message)
