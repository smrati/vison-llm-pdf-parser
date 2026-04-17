# API Reference

## Convenience Functions

### `convert(pdf_path, **kwargs) -> ConversionResult`

One-shot synchronous conversion. Creates a converter with the given keyword arguments, converts, and returns the result.

```python
from pdf2md import convert

result = convert("document.pdf")
result = convert("document.pdf", backend="ollama", model="gemma3", dpi=200)
```

Accepts any field from `LLMConfig` or `ConversionOptions` as keyword arguments. Automatically routes them to the correct config object.

### `aconvert(pdf_path, **kwargs) -> ConversionResult`

Async equivalent of `convert()`. Same interface, must be awaited.

```python
from pdf2md import aconvert
import asyncio

result = asyncio.run(aconvert("document.pdf", concurrency=5))
```

---

## Converters

### `PDFToMarkdownConverter`

Stateful synchronous converter. Reuses the LLM connection across multiple calls.

```python
from pdf2md import PDFToMarkdownConverter, LLMConfig, ConversionOptions

converter = PDFToMarkdownConverter(
    llm_config=LLMConfig(model="gemma3", backend="ollama"),
    options=ConversionOptions(dpi=200),
)

result = converter.convert("doc.pdf")
page = converter.convert_page("doc.pdf", page_num=0)
pages = converter.convert_pages("doc.pdf", pages=[0, 2, 4])
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `convert(pdf_path)` | `ConversionResult` | Convert entire PDF |
| `convert_page(pdf_path, page_num)` | `PageResult` | Convert a single page (0-indexed) |
| `convert_pages(pdf_path, pages)` | `list[PageResult]` | Convert specific pages |

### `AsyncPDFToMarkdownConverter`

Async counterpart. Same API, all methods are `async`.

```python
from pdf2md import AsyncPDFToMarkdownConverter, ConversionOptions

converter = AsyncPDFToMarkdownConverter(options=ConversionOptions(concurrency=5))
result = await converter.convert("doc.pdf")
```

---

## Models

### `ConversionResult`

The main result object returned by all conversion methods.

```python
result.markdown        # str  — final merged markdown
result.pages           # list[PageResult] — per-page results
result.images          # list[ExtractedImage] — embedded images
result.metadata        # PDFMetadata — PDF metadata
result.page_count      # int — number of pages (property)
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `save(path)` | `Self` | Write markdown to file. Returns self for chaining. |
| `save_images(directory, prefix="image")` | `list[Path]` | Save extracted images. Creates directory if needed. |

### `PageResult`

Result of converting a single page.

```python
page.page_number    # int — 0-indexed page number
page.markdown       # str — markdown content for this page
page.width          # int — rendered width in pixels
page.height         # int — rendered height in pixels
```

### `ExtractedImage`

An image extracted from the PDF.

```python
img.page_number     # int — page the image was found on
img.image_index     # int — index within the page
img.data            # bytes — raw image bytes
img.format          # str — "png", "jpeg", etc.
img.width           # int — width in pixels
img.height          # int — height in pixels
```

### `PDFMetadata`

Metadata extracted from the PDF.

```python
meta.title          # str
meta.author         # str
meta.subject        # str
meta.creator        # str
meta.producer       # str
meta.page_count     # int
meta.file_path      # str
```

---

## Exceptions

All exceptions inherit from `PDF2MDError`.

```python
from pdf2md import PDF2MDError, PDFLoadError, LLMError, ConversionError, ImageExtractionError
```

| Exception | When | Example |
|-----------|------|---------|
| `PDFLoadError` | PDF file not found or corrupted | `PDFLoadError.file_not_found("doc.pdf")` |
| `LLMError` | Connection failure, timeout, empty response | `LLMError.connection_failed("http://...", detail)` |
| `ConversionError` | General conversion failure | Image extraction failure |
| `ImageExtractionError` | Failed to extract images | Corrupt image stream in PDF |

Each exception has class method constructors for ergonomic creation:

```python
raise PDFLoadError.file_not_found("/path/to/file.pdf")
raise PDFLoadError.corrupted("/path/to/file.pdf", "invalid xref table")
raise LLMError.connection_failed("http://localhost:11434/v1", "Connection refused")
raise LLMError.timeout("http://localhost:11434/v1", 120.0)
raise LLMError.empty_response("gemma3")
```
