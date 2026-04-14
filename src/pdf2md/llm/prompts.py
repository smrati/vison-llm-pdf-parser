"""Prompt templates for vision LLM page conversion and merging."""

SYSTEM_PROMPT = """\
You are a document conversion assistant. Your task is to convert PDF page images \
into clean, well-structured Markdown.

Rules:
1. Preserve the document structure exactly as shown in the image.
2. Use proper Markdown headings (# ## ### etc.) matching the visual hierarchy.
3. Preserve all tables using Markdown table syntax.
4. Preserve lists (ordered and unordered) with correct nesting.
5. Preserve code blocks with language hints where identifiable.
6. Preserve bold, italic, and other inline formatting.
7. For equations, use LaTeX notation ($...$ or $$...$$).
8. If a paragraph appears to be split across pages (ends mid-sentence), \
end your output with "[CONTINUED]" on a new line.
9. For images/charts/diagrams in the page, describe them briefly \
in an HTML comment: <!-- image: brief description -->
10. Output ONLY the Markdown. No preamble, no explanation.
"""


def build_page_prompt(page_num: int, total_pages: int) -> str:
    """Build the user prompt for converting a single page."""
    return f"""\
Convert this PDF page (page {page_num + 1} of {total_pages}) to Markdown.

Pay special attention to:
- Whether the first line continues from the previous page
- Whether the last line continues onto the next page
- Any headers, footers, or page numbers to exclude

Output clean Markdown only."""


MERGE_PROMPT = """\
You are merging two consecutive pages of Markdown content from a PDF conversion.

Page A (earlier page's markdown):
---
{prev_content}
---

Page B (later page's markdown):
---
{current_content}
---

Task:
1. If Page A ends mid-sentence and Page B starts mid-sentence, join them seamlessly.
2. If Page B starts with a continuation of a heading, paragraph, or list from Page A, merge them.
3. If the pages have independent content, simply concatenate them with a blank line.
4. Remove any "[CONTINUED]" markers.
5. Remove duplicate headers/footers/page numbers.
6. Output the merged Markdown only. No explanation.

Merged Markdown:"""
