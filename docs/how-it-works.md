# How It Works

## The Core Idea

Instead of trying to parse PDF structure programmatically (which is fragile and lossy), this library treats PDF conversion as a **vision task**: it renders each page as an image and asks a vision-capable LLM to describe what it sees in Markdown.

This approach has a fundamental advantage: the LLM understands layout, tables, equations, and visual hierarchy the same way a human does. It doesn't need to understand PDF internals.

## The Conversion Pipeline

```
                         PDF file
                            |
                            v
                  +-------------------+
                  |   PDFDocument     |   (PyMuPDF)
                  |                   |
                  | Opens the PDF,    |
                  | renders each page |
                  | to a PNG/JPEG     |
                  | image at the      |
                  | configured DPI.   |
                  +-------------------+
                            |
                  list of PDFPage objects
                  (base64 image + metadata)
                            |
                            v
            +-------------------------------+
            |        LLM Client             |
            |  (per page, parallelizable)   |
            |                               |
            | Sends the page image to a     |
            | vision LLM with a system      |
            | prompt that instructs it to   |
            | produce clean Markdown.       |
            +-------------------------------+
                            |
                  list of PageResult objects
                  (markdown string per page)
                            |
                            v
               +-------------------------+
               |      PageMerger         |
               |  (heuristic-gated)      |
               |                         |
               | For each page boundary: |
               | 1. Check if content is  |
               |    split across pages   |
               | 2. If yes -> ask LLM   |
               |    to merge seamlessly  |
               | 3. If no  -> simple     |
               |    concatenation        |
               +-------------------------+
                            |
                            v
               +-------------------------+
               |    ImageExtractor       |  (optional)
               |                         |
               | Pulls embedded images   |
               | (photos, logos, etc.)   |
               | from the PDF using      |
               | PyMuPDF.                |
               +-------------------------+
                            |
                            v
                   ConversionResult
                    .markdown       final merged markdown
                    .pages          per-page results
                    .images         extracted embedded images
                    .metadata       PDF metadata
```

## Step-by-Step Walkthrough

### Step 1: PDF Loading

`PDFDocument` uses PyMuPDF (`fitz`) to open the PDF. It does NOT parse the text content. Instead, it:

1. Reads PDF metadata (title, author, page count)
2. For each page, renders it to an image using `page.get_pixmap(matrix=...)`
3. The matrix scales by `dpi / 72` (PDF points are 72 DPI by default)
4. The image bytes are base64-encoded and stored in a `PDFPage` object

A standard letter page at 150 DPI produces a ~1250x1650 pixel image.

### Step 2: LLM Vision Conversion

Each page image is sent to the vision LLM as a base64 data URI. The message format differs by backend:

**OpenAI-compatible (LM Studio, vLLM):**
```json
{
  "messages": [
    {"role": "system", "content": "Convert to Markdown..."},
    {"role": "user", "content": [
      {"type": "text", "text": "Convert page 1 of 5..."},
      {"type": "image_url", "image_url": {
        "url": "data:image/png;base64,...",
        "detail": "high"
      }}
    ]}
  ]
}
```

**Ollama native:**
```json
{
  "model": "gemma3",
  "messages": [
    {"role": "system", "content": "Convert to Markdown..."},
    {"role": "user", "content": "Convert page 1 of 5...", "images": ["<base64>"]}
  ]
}
```

The system prompt instructs the model to:
- Preserve document structure (headings, tables, lists, code blocks)
- Use LaTeX for equations
- Mark split paragraphs with `[CONTINUED]`
- Describe images/charts in HTML comments

### Step 3: Page Merging

Pages are converted independently (the "map" phase), then merged sequentially (the "reduce" phase).

The `PageMerger` uses a **heuristic gate** to avoid unnecessary LLM calls:

```
For each adjacent page pair (prev, current):
  Does prev end with [CONTINUED]?           -> merge via LLM
  Does prev's last line end mid-sentence?    -> merge via LLM
  Otherwise                                  -> simple concatenation
```

A line is considered "mid-sentence" if it doesn't end with a sentence-terminating character (`.`, `!`, `?`, `:`, `;`) or a structural marker (`#`, `|`, `` ``` ``, `---`).

When LLM merging is triggered, both pages are sent to the LLM with a merge prompt that asks it to seamlessly join split content while removing `[CONTINUED]` markers and duplicate headers/footers.

### Step 4: Image Extraction (Optional)

`ImageExtractor` uses PyMuPDF's `page.get_images()` and `doc.extract_image(xref)` to pull embedded images from the PDF. These are the original images stored in the PDF (photos, logos, diagrams), not the rendered page images.

### Step 5: Result Assembly

Everything is assembled into a `ConversionResult` Pydantic model that provides:
- The final merged markdown
- Per-page markdown with dimensions
- Extracted images with metadata
- PDF metadata
- Convenience methods (`save()`, `save_images()`)

## Async and Concurrency

The async converter (`AsyncPDFToMarkdownConverter`) processes pages in parallel using `asyncio.Semaphore`:

```
Page 0 ──┐
Page 1 ──┤  Semaphore(concurrency=3)
Page 2 ──┤  → max 3 concurrent LLM calls
Page 3 ──┤
Page 4 ──┘
     │
     v
Merge all pages sequentially (order matters)
```

Merging is always sequential because each merge depends on the accumulated result of all previous merges.
