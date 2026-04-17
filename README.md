# vision-llm-pdf-parser

Convert PDFs to Markdown using local vision LLMs. Works with Ollama, LM Studio, vLLM, and any OpenAI-compatible API.

## Setup

**Prerequisites:** Python 3.13+, [uv](https://docs.astral.sh/uv/)

```bash
# Clone and install
git clone <repo-url>
cd vision-llm-pdf-parser
uv sync

# Install dev tools (linting, testing)
uv sync --dev
```

**Start a vision model** (one of these):

```bash
# Ollama
ollama pull llama3.2-vision
ollama serve

# LM Studio — open app, load a vision model, start server on port 1234

# vLLM
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2-VL-2B-Instruct --port 8000
```

## Usage

```python
from pdf2md import convert

# One-shot conversion (defaults to Ollama)
result = convert("document.pdf")
print(result.markdown)

# Point to a different backend — just change base_url and model
result = convert(
    "document.pdf",
    base_url="http://localhost:1234/v1",
    model="allenai/olmocr-2-7b",
)

# Save output
result.save("output.md")
result.save_images("./images/")
```

**Configured converter** (reuses the LLM connection across multiple files):

```python
from pdf2md import PDFToMarkdownConverter, LLMConfig

config = LLMConfig(base_url="http://localhost:11434/v1", model="llama3.2-vision")
converter = PDFToMarkdownConverter(llm_config=config)

result1 = converter.convert("doc1.pdf")
result2 = converter.convert("doc2.pdf")
```

**Single page:**

```python
page = converter.convert_page("doc.pdf", page_num=0)
print(page.markdown)
```

**Async with concurrency:**

```python
import asyncio
from pdf2md import AsyncPDFToMarkdownConverter, ConversionOptions

async def main():
    converter = AsyncPDFToMarkdownConverter(
        options=ConversionOptions(concurrency=5, dpi=200)
    )
    result = await converter.convert("large.pdf")
    print(result.markdown)

asyncio.run(main())
```

## Configuration

```python
from pdf2md import LLMConfig, ConversionOptions

# LLM connection
config = LLMConfig(
    base_url="http://localhost:11434/v1",  # All backends use /v1/chat/completions
    model="llama3.2-vision",               # Must be vision-capable
    temperature=0.1,
    max_tokens=4096,
    timeout=120.0,
)

# Conversion behavior
options = ConversionOptions(
    dpi=150,                # Page render resolution
    image_format="PNG",     # PNG or JPEG
    extract_images=True,    # Extract embedded images
    merge_pages=True,       # Smart cross-page merging
    concurrency=3,          # Parallel LLM calls (async mode)
    system_prompt=None,     # Override default system prompt
    page_prompt=None,       # Override default per-page prompt
)
```

## Architecture

```
src/pdf2md/
  config.py                 LLMConfig + ConversionOptions (frozen dataclasses)
  models.py                 Pydantic models (ConversionResult, PageResult, etc.)
  exceptions.py             PDF2MDError hierarchy

  pdf/
    loader.py               PDFDocument — loads PDFs, renders pages to images via PyMuPDF

  llm/
    client.py               LLMClient + AsyncLLMClient — wraps openai SDK
    prompts.py              System, page, and merge prompt templates

  convert/
    converter.py            PDFToMarkdownConverter + AsyncPDFToMarkdownConverter
    merger.py               PageMerger — heuristic-gated cross-page merging
    image_extractor.py      ImageExtractor — pulls embedded images from PDF
```

**Conversion pipeline:**

```
PDF file
  |
  v
PDFDocument (PyMuPDF)
  |  Renders each page to a PNG/JPEG image
  v
LLMClient (openai SDK)
  |  Sends base64 image to vision model via /v1/chat/completions
  |  Works with Ollama, LM Studio, vLLM — same protocol for all
  v
PageMerger
  |  Detects cross-page content (mid-sentence breaks, [CONTINUED] markers)
  |  Uses LLM to merge only where needed (heuristic skips clean boundaries)
  v
ImageExtractor
  |  Pulls embedded images from PDF (optional)
  v
ConversionResult
   .markdown    — final merged Markdown
   .pages       — per-page results
   .images      — extracted embedded images
   .metadata    — PDF metadata
```

**Key design decisions:**

- **Single `openai` SDK adapter** — Ollama, LM Studio, and vLLM all speak the same `/v1/chat/completions` protocol. Changing backends is just changing `base_url`.
- **Map-reduce pattern** — pages are converted independently (parallelizable in async mode), then merged sequentially. This avoids context window limits on long documents.
- **Heuristic-gated merging** — the merger checks for `[CONTINUED]` markers and mid-sentence breaks before making an LLM merge call, skipping expensive API hits for pages with clean boundaries.
- **PyMuPDF over pdf2image** — pure Python, no system dependencies (poppler). Also gives embedded image extraction for free.

## Documentation

Full documentation is in the [docs/](docs/) directory:

- [How It Works](docs/how-it-works.md) — the core idea and conversion pipeline
- [Architecture](docs/architecture.md) — module structure, class hierarchy, data flow
- [Configuration](docs/configuration.md) — LLMConfig and ConversionOptions reference
- [API Reference](docs/api-reference.md) — public API, models, and exceptions
- [Backends](docs/backends.md) — Ollama, LM Studio, vLLM, and custom endpoints
- [Design Decisions](docs/design-decisions.md) — why things are built the way they are

## License

MIT
