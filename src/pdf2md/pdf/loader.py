"""PDF loading and page-to-image conversion using PyMuPDF."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from pdf2md.config import ConversionOptions
from pdf2md.exceptions import PDFLoadError
from pdf2md.models import PDFMetadata, PDFPage


class PDFDocument:
    """Loads a PDF and converts pages to base64-encoded images."""

    def __init__(self, path: str | Path, options: ConversionOptions | None = None) -> None:
        self._path = Path(path)
        if not self._path.exists():
            raise PDFLoadError.file_not_found(str(self._path))
        self._options = options or ConversionOptions()
        try:
            self._doc: fitz.Document = fitz.open(str(self._path))
        except Exception as e:
            raise PDFLoadError.corrupted(str(self._path), str(e)) from e

    @property
    def metadata(self) -> PDFMetadata:
        """Extract PDF metadata."""
        meta = self._doc.metadata
        return PDFMetadata(
            title=meta.get("title", "") or "",
            author=meta.get("author", "") or "",
            subject=meta.get("subject", "") or "",
            creator=meta.get("creator", "") or "",
            producer=meta.get("producer", "") or "",
            page_count=len(self._doc),
            file_path=str(self._path),
        )

    @property
    def page_count(self) -> int:
        return len(self._doc)

    def get_page(self, page_num: int) -> PDFPage:
        """Convert a single page to a PDFPage with base64 image."""
        if page_num < 0 or page_num >= len(self._doc):
            raise IndexError(f"Page {page_num} out of range (0-{len(self._doc) - 1})")
        image_bytes = self._render_page(page_num)
        page = self._doc[page_num]
        rect = page.rect
        zoom = self._options.dpi / 72
        fmt = self._options.image_format.lower()
        return PDFPage(
            page_number=page_num,
            image_base64=base64.b64encode(image_bytes).decode("ascii"),
            image_mime=f"image/{'jpeg' if fmt == 'jpeg' else 'png'}",
            width=int(rect.width * zoom),
            height=int(rect.height * zoom),
        )

    def get_all_pages(self) -> list[PDFPage]:
        """Convert all pages to PDFPage objects."""
        return [self.get_page(i) for i in range(len(self._doc))]

    def get_page_image(self, page_num: int) -> bytes:
        """Get raw image bytes for a page."""
        return self._render_page(page_num)

    def extract_embedded_images(self, page_num: int) -> list[dict[str, Any]]:
        """Extract raw embedded images from a specific page.

        Returns list of dicts with keys: data, format, width, height.
        """
        page = self._doc[page_num]
        images: list[dict[str, Any]] = []
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            try:
                base_image = self._doc.extract_image(xref)
                images.append(
                    {
                        "data": base_image["image"],
                        "format": base_image["ext"],
                        "width": base_image["width"],
                        "height": base_image["height"],
                    }
                )
            except Exception:
                continue
        return images

    def _render_page(self, page_num: int) -> bytes:
        """Render a page to PNG or JPEG bytes."""
        page = self._doc[page_num]
        zoom = self._options.dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)
        if self._options.image_format.upper() == "JPEG":
            return pixmap.tobytes(output="jpg")
        return pixmap.tobytes(output="png")

    def close(self) -> None:
        self._doc.close()

    def __enter__(self) -> PDFDocument:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
