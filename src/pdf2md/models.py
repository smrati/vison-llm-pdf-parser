"""Pydantic data models for pdf2md."""

from __future__ import annotations

from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field


class PDFMetadata(BaseModel):
    """Metadata extracted from the PDF document."""

    title: str = ""
    author: str = ""
    subject: str = ""
    creator: str = ""
    producer: str = ""
    page_count: int = 0
    file_path: str = ""


class PDFPage(BaseModel):
    """A single PDF page converted to an image for LLM processing."""

    model_config = {"arbitrary_types_allowed": True}

    page_number: int = Field(ge=0, description="0-indexed page number")
    image_base64: str = Field(description="Base64-encoded page image")
    image_mime: str = Field(default="image/png", description="MIME type of the rendered image")
    width: int = Field(description="Page width in pixels at render DPI")
    height: int = Field(description="Page height in pixels at render DPI")


class PageResult(BaseModel):
    """Result of converting a single page to Markdown."""

    page_number: int = Field(ge=0)
    markdown: str
    width: int = 0
    height: int = 0


class ExtractedImage(BaseModel):
    """An image extracted from the PDF."""

    page_number: int = Field(ge=0)
    image_index: int = Field(ge=0, description="Index of image within the page")
    data: bytes = Field(description="Raw image bytes")
    format: str = Field(description="Image format (png, jpeg, etc.)")
    width: int = 0
    height: int = 0


class ConversionResult(BaseModel):
    """Complete result of converting a PDF to Markdown."""

    markdown: str = Field(description="The final merged Markdown content")
    pages: list[PageResult] = Field(description="Per-page conversion results")
    images: list[ExtractedImage] = Field(default_factory=list, description="Extracted embedded images")
    metadata: PDFMetadata = Field(default_factory=PDFMetadata)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def save(self, path: str | Path) -> Self:
        """Save the final Markdown to a file."""
        Path(path).write_text(self.markdown, encoding="utf-8")
        return self

    def save_images(self, directory: str | Path, prefix: str = "image") -> list[Path]:
        """Save extracted images to a directory. Returns list of saved file paths."""
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        saved: list[Path] = []
        for img in self.images:
            filename = f"{prefix}_p{img.page_number}_{img.image_index}.{img.format}"
            filepath = dir_path / filename
            filepath.write_bytes(img.data)
            saved.append(filepath)
        return saved
