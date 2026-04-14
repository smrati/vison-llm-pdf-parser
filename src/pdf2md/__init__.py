"""pdf2md - Convert PDFs to Markdown using local vision LLMs."""

from pdf2md._version import __version__
from pdf2md.config import ConversionOptions, LLMConfig
from pdf2md.convert.converter import AsyncPDFToMarkdownConverter, PDFToMarkdownConverter
from pdf2md.exceptions import (
    ConversionError,
    ImageExtractionError,
    LLMError,
    PDF2MDError,
    PDFLoadError,
)
from pdf2md.models import ConversionResult, ExtractedImage, PDFMetadata, PageResult

__all__ = [
    "__version__",
    # Converters
    "PDFToMarkdownConverter",
    "AsyncPDFToMarkdownConverter",
    # Config
    "LLMConfig",
    "ConversionOptions",
    # Models
    "ConversionResult",
    "PageResult",
    "ExtractedImage",
    "PDFMetadata",
    # Exceptions
    "PDF2MDError",
    "PDFLoadError",
    "LLMError",
    "ConversionError",
    "ImageExtractionError",
    # Convenience functions
    "convert",
    "aconvert",
]


def convert(pdf_path: str, **kwargs: object) -> ConversionResult:
    """One-shot synchronous conversion."""
    llm_kwargs = {k: v for k, v in kwargs.items() if k in LLMConfig.__dataclass_fields__}
    opt_kwargs = {k: v for k, v in kwargs.items() if k in ConversionOptions.__dataclass_fields__}

    llm_config = LLMConfig(**llm_kwargs)  # type: ignore[arg-type]
    options = ConversionOptions(**opt_kwargs)  # type: ignore[arg-type]
    converter = PDFToMarkdownConverter(llm_config=llm_config, options=options)
    return converter.convert(pdf_path)


async def aconvert(pdf_path: str, **kwargs: object) -> ConversionResult:
    """One-shot asynchronous conversion."""
    llm_kwargs = {k: v for k, v in kwargs.items() if k in LLMConfig.__dataclass_fields__}
    opt_kwargs = {k: v for k, v in kwargs.items() if k in ConversionOptions.__dataclass_fields__}

    llm_config = LLMConfig(**llm_kwargs)  # type: ignore[arg-type]
    options = ConversionOptions(**opt_kwargs)  # type: ignore[arg-type]
    converter = AsyncPDFToMarkdownConverter(llm_config=llm_config, options=options)
    return await converter.convert(pdf_path)
