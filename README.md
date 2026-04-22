# vision-llm-pdf-parser

## About

Convert PDFs to clean, structured Markdown using local vision LLMs — no cloud APIs, no API keys, no data leaving your machine.

**The problem:** Traditional PDF-to-text extraction is unreliable. PDFs store drawing commands, not structured text. Tables get mangled, columns merge, equations disappear, and layouts break. Tools like `pdf2image`, `pymupdf` text extraction, or `marker` all struggle with complex layouts.

**This library's approach:** Instead of trying to parse PDF internals, it renders each page as an image and sends it to a vision-capable LLM (running locally on your machine). The LLM sees the page exactly as a human would — it understands tables, equations, multi-column layouts, and visual hierarchy — and produces clean Markdown.

**How it's different:**

| | This library | Text extraction tools | Cloud OCR services |
|---|---|---|---|
| Layout understanding | LLM sees full page visually | Fragile, rule-based | Good but cloud-only |
| Tables & equations | Preserved accurately | Often broken | Varies |
| Privacy | 100% local, no data leaves your machine | Local | Data sent to cloud |
| Cost | Free (local models) | Free | Per-page charges |
| Speed | Depends on local GPU/CPU | Fast | Fast (network latency) |

Works with any local vision LLM: Ollama, LM Studio, vLLM, or any server that exposes an OpenAI-compatible `/v1/chat/completions` endpoint.

## Installation

### Use in your own project

**Prerequisites:** Python 3.13+, [uv](https://docs.astral.sh/uv/)

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/vision-llm-pdf-parser.git

# 2. Install into your project (from your project directory)
cd your-project
uv add --editable ../vision-llm-pdf-parser
```

Use **editable mode** (`--editable`) so that pulling updates in the cloned repo takes effect immediately — no reinstall needed.

Or configure it in your `pyproject.toml`:

```toml
[project]
dependencies = [
    "vision-llm-pdf-parser",
]

[tool.uv.sources]
vision-llm-pdf-parser = { path = "../vision-llm-pdf-parser", editable = true }
```

With this setup, pulling updates is just:

```bash
cd vision-llm-pdf-parser
git pull
# Changes are live immediately — no uv sync needed
```

If you used a **non-editable** install (`uv add ../vision-llm-pdf-parser`), you must reinstall after pulling:

```bash
uv sync --reinstall-package vision-llm-pdf-parser
```

### Install from GitHub (no local clone needed)

Install directly from the GitHub repo — no need to clone the library separately:

```bash
# Latest on default branch
uv add git+https://github.com/smrati/vison-llm-pdf-parser.git

# Specific branch
uv add git+https://github.com/smrati/vison-llm-pdf-parser.git --branch private/smrati/dev

# Pin to a specific commit
uv add git+https://github.com/smrati/vison-llm-pdf-parser.git --rev 799aba69c65876e22c4eb014025e9f7f355790dc
```

Or configure it in your `pyproject.toml`:

```toml
[project]
dependencies = [
    "vision-llm-pdf-parser",
]

[tool.uv.sources]
vision-llm-pdf-parser = { git = "https://github.com/smrati/vison-llm-pdf-parser.git", rev = "799aba69c65876e22c4eb014025e9f7f355790dc" }
```

To get updates, change the `rev` to the latest commit hash and run:

```bash
uv sync
```

### Develop this library

```bash
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
