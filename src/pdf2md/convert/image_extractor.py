"""Extract embedded images from PDF documents."""

from __future__ import annotations

import logging

from pdf2md.models import ExtractedImage
from pdf2md.pdf.loader import PDFDocument

logger = logging.getLogger(__name__)


class ImageExtractor:
    """Extract embedded images from a PDF document."""

    def extract_from_page(self, pdf: PDFDocument, page_num: int) -> list[ExtractedImage]:
        """Extract all embedded images from a single page."""
        raw_images = pdf.extract_embedded_images(page_num)
        images: list[ExtractedImage] = []
        for idx, img in enumerate(raw_images):
            images.append(
                ExtractedImage(
                    page_number=page_num,
                    image_index=idx,
                    data=img["data"],
                    format=img["format"],
                    width=img["width"],
                    height=img["height"],
                )
            )
        return images

    def extract_all(self, pdf: PDFDocument) -> list[ExtractedImage]:
        """Extract all embedded images from all pages."""
        all_images: list[ExtractedImage] = []
        for page_num in range(pdf.page_count):
            try:
                page_images = self.extract_from_page(pdf, page_num)
                all_images.extend(page_images)
            except Exception:
                logger.warning("Failed to extract images from page %d, skipping", page_num)
                continue
        return all_images
