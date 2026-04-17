# Architecture

## Module Structure

```
src/pdf2md/
├── __init__.py                  Public API surface + convenience functions
├── _version.py                  Version string
├── config.py                    LLMConfig + ConversionOptions (frozen dataclasses)
├── models.py                    Pydantic models (ConversionResult, PageResult, etc.)
├── exceptions.py                PDF2MDError hierarchy
│
├── pdf/
│   ├── __init__.py
│   └── loader.py                PDFDocument — loads PDFs, renders pages to images
│
├── llm/
│   ├── __init__.py
│   ├── client.py                LLMClient, AsyncLLMClient, OllamaLLMClient,
│   │                            AsyncOllamaLLMClient, factory functions
│   └── prompts.py               System, page, and merge prompt templates
│
└── convert/
    ├── __init__.py
    ├── converter.py              PDFToMarkdownConverter + AsyncPDFToMarkdownConverter
    ├── merger.py                 PageMerger + AsyncPageMerger (heuristic-gated)
    └── image_extractor.py        ImageExtractor — pulls embedded images from PDF
```

## Class Hierarchy

```
                        LLMConfig (frozen dataclass)
                        ConversionOptions (frozen dataclass)
                                    |
                                    v
               +------------------------------------------+
               |       PDFToMarkdownConverter (sync)      |
               |   AsyncPDFToMarkdownConverter (async)    |
               +------------------------------------------+
                    |              |              |
                    v              v              v
            PDFDocument     LLM Client       PageMerger
            (PyMuPDF)       (backend)        (heuristic)
                                |
                +---------------+---------------+
                |                               |
         OpenAI-compatible               Ollama native
          ┌─────────────┐             ┌──────────────────┐
          │  LLMClient   │             │ OllamaLLMClient   │
          │ (sync)       │             │ (sync)            │
          │              │             │                    │
          │ AsyncLLMClient│             │ AsyncOllamaLLMClient│
          │ (async)      │             │ (async)            │
          └─────────────┘             └──────────────────┘
                |                               |
          openai SDK                      ollama package
         (/v1/chat/completions)          (/api/chat)
```

## Data Models (Pydantic)

```
ConversionResult
├── markdown: str                 Final merged markdown
├── pages: list[PageResult]       Per-page results
│   └── PageResult
│       ├── page_number: int      0-indexed
│       ├── markdown: str
│       ├── width: int
│       └── height: int
├── images: list[ExtractedImage]  Embedded images
│   └── ExtractedImage
│       ├── page_number: int
│       ├── image_index: int
│       ├── data: bytes
│       ├── format: str
│       ├── width: int
│       └── height: int
└── metadata: PDFMetadata
    ├── title: str
    ├── author: str
    ├── subject: str
    ├── creator: str
    ├── producer: str
    ├── page_count: int
    └── file_path: str

PDFPage (internal, not exported)
├── page_number: int
├── image_base64: str
├── image_mime: str               "image/png" or "image/jpeg"
├── width: int
└── height: int
```

## Exception Hierarchy

```
PDF2MDError (base)
├── PDFLoadError                  Failed to open/read PDF
│   .file_not_found(path)         Class method constructor
│   .corrupted(path, detail)      Class method constructor
├── LLMError                      Error communicating with LLM
│   .connection_failed(url, detail)
│   .timeout(url, timeout)
│   .empty_response(model)
├── ConversionError               Error during conversion
└── ImageExtractionError          Error extracting images
```

All exceptions have class method constructors for ergonomic error creation.

## Data Flow Through the Converter

### Sync path (`PDFToMarkdownConverter.convert`)

```
1. PDFDocument(path, options)          Opens PDF, no rendering yet
   .get_all_pages()                    Renders ALL pages to images
   .metadata                           Extracts PDF metadata
   .close()                            Releases PDF handle

2. create_sync_client(llm_config)      Factory picks Ollama or OpenAI client

3. _convert_all_pages(llm, pages)      Sequential: page 0, page 1, ...
   for each page:
     llm.convert_page(base64, ...)     LLM call with image

4. _extract_images(pdf_path)           Re-opens PDF, extracts embedded images
   ImageExtractor.extract_all(pdf)

5. _merge_pages(llm, page_results)     Sequential merge
   PageMerger.merge_all([md0, md1, ...])
     merge_two(md0, md1)               Heuristic check -> maybe LLM merge
     merge_two(result, md2)            Accumulate
     ...

6. ConversionResult(...)               Assemble and return
```

### Async path (`AsyncPDFToMarkdownConverter.convert`)

Same flow but:
- Step 3 uses `asyncio.gather()` with `Semaphore(concurrency)` for parallel page conversion
- Step 5 uses `await` for each sequential merge
- Image extraction (step 4) is still sync (PyMuPDF is synchronous)

## Dependency Graph

```
pydantic        models.py, exceptions.py
pymupdf (fitz)  pdf/loader.py
openai          llm/client.py (LLMClient, AsyncLLMClient)
ollama          llm/client.py (OllamaLLMClient, AsyncOllamaLLMClient) [optional]
```

No external dependencies beyond these. Pydantic handles validation, PyMuPDF handles PDF operations, and the LLM clients handle API communication.
