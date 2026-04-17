# Design Decisions

## Why render pages as images instead of extracting text?

PDF text extraction is fragile. PDFs don't store "text" in any reliable way — they store drawing commands, font references, and positioned glyphs. Two-column layouts, tables, equations, and rotated text are notoriously hard to extract correctly.

Rendering pages to images and using a vision LLM sidesteps all of this. The LLM sees the page exactly as a human would and produces structured output. The tradeoff is speed and cost (vision calls are slower than text extraction), but the quality is dramatically better for complex layouts.

## Why the map-reduce pattern?

Each page is converted independently (map), then merged sequentially (reduce).

**Benefits:**
- Pages can be processed in parallel (async mode), significantly speeding up multi-page PDFs
- Each page only needs one image in the LLM context, avoiding context window limits on long documents
- A failure on one page doesn't block others

**Tradeoff:**
- Cross-page content (sentences split across pages) isn't detected during conversion, only during merging
- The merge step is sequential and can't be parallelized because each merge depends on previous results

## Why heuristic-gated merging?

Without the heuristic, every page boundary would trigger an LLM merge call. For a 20-page PDF, that's 19 extra LLM calls — expensive and slow.

The heuristic checks if the previous page ends "cleanly" (with a period, heading, table row, etc.). If it does, the pages are simply concatenated with a blank line separator. Only ambiguous boundaries trigger an LLM merge call.

In practice, most well-formatted documents have clean page boundaries, so the heuristic skips the majority of merge calls.

## Why two separate client implementations?

Ollama's native API (`/api/chat`) uses a different image format than OpenAI's (`/v1/chat/completions`):

- **OpenAI:** Images go in a `content` array as `image_url` objects with data URIs
- **Ollama:** Images go in a top-level `images` field in the message

Rather than adding conditional logic inside a single client, the library uses separate client classes with a factory function. This keeps each client simple and testable. The converter never needs to know which client it's using — they share the same interface.

## Why PyMuPDF over pdf2image?

- **No system dependencies:** `pdf2image` requires `poppler-utils` installed on the system. PyMuPDF is pure Python.
- **Embedded image extraction:** PyMuPDF can extract original images from the PDF. `pdf2image` can only render pages.
- **Metadata:** PyMuPDF gives access to PDF metadata for free.
- **Speed:** PyMuPDF is generally faster for page rendering.

## Why frozen dataclasses for config?

`LLMConfig` and `ConversionOptions` are frozen (immutable) dataclasses. This prevents accidental mutation after the converter is created. If you need different settings, create a new config object.

This is important because the converter and LLM client both hold references to the config. If config were mutable, changing it after creation could lead to confusing behavior.

## Why Pydantic for models?

`ConversionResult`, `PageResult`, `ExtractedImage`, and `PDFMetadata` use Pydantic because:
- Built-in validation (page numbers >= 0, required fields, etc.)
- Automatic serialization (`result.model_dump_json()`)
- Immutable by default
- `.save()` and `.save_images()` convenience methods are easy to add as methods

`PDFPage` (internal) also uses Pydantic for consistency, though it's not exported.

## Why a single OpenAI-compatible client for all backends?

Ollama, LM Studio, and vLLM all expose the same `/v1/chat/completions` endpoint with the same `image_url` format for vision. There is no need for per-backend client implementations. A single `LLMClient` using the `openai` Python SDK covers all backends — switching is just changing `base_url` and `model`. This keeps the codebase simple and avoids extra dependencies.
