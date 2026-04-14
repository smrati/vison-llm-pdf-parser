# vison-llm-pdf-parser

Convert PDFs to Markdown using local vision LLMs. Works with Ollama, LM Studio, vLLM, and any OpenAI-compatible API.

## Setup

**Prerequisites:** Python 3.13+, [uv](https://docs.astral.sh/uv/)

```bash
# Clone and install
git clone <repo-url>
cd vison-llm-pdf-parser
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

# Point to a different backend
result = convert(
    "document.pdf",
    base_url="http://localhost:1234/v1",  # LM Studio
    model="pixtral",
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
    base_url="http://localhost:11434/v1",  # Ollama default
    model="llama3.2-vision",
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
    prompts.py               System, page, and merge prompt templates

  convert/
    converter.py             PDFToMarkdownConverter + AsyncPDFToMarkdownConverter
    merger.py                PageMerger — heuristic-gated cross-page merging
    image_extractor.py       ImageExtractor — pulls embedded images from PDF
```

**Conversion pipeline:**

```
PDF file
  │
  ▼
PDFDocument (PyMuPDF)
  │  Renders each page to a PNG/JPEG image
  ▼
LLMClient (openai SDK)
  │  Sends base64 image to vision model → gets Markdown per page
  ▼
PageMerger
  │  Detects cross-page content (mid-sentence breaks, [CONTINUED] markers)
  │  Uses LLM to merge only where needed (heuristic skips clean boundaries)
  ▼
ImageExtractor
  │  Pulls embedded images from PDF (optional)
  ▼
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

## License

MIT
