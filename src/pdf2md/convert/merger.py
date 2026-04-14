"""Intelligent page merging for consecutive PDF page markdown."""

from __future__ import annotations

from pdf2md.llm.client import AsyncLLMClient, LLMClient


class PageMerger:
    """Synchronous page merger with heuristic-gated LLM merging."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    def merge_two(self, prev_markdown: str, current_markdown: str) -> str:
        """Merge two adjacent pages, handling cross-page content."""
        if not self._needs_merging(prev_markdown, current_markdown):
            return prev_markdown + "\n\n" + current_markdown
        return self._llm.merge_content(prev_markdown, current_markdown)

    def merge_all(self, page_markdowns: list[str]) -> str:
        """Merge a list of page markdowns sequentially."""
        if not page_markdowns:
            return ""
        result = page_markdowns[0]
        for i in range(1, len(page_markdowns)):
            result = self.merge_two(result, page_markdowns[i])
        return result

    def _needs_merging(self, prev: str, current: str) -> bool:
        """Heuristic to determine if LLM-based merging is needed."""
        prev_stripped = prev.rstrip()
        if prev_stripped.endswith("[CONTINUED]"):
            return True
        last_line = prev_stripped.split("\n")[-1].strip()
        if last_line and not last_line.endswith((".", "!", "?", ":", ";", "#", "|", "```", "---")):
            return True
        return False


class AsyncPageMerger:
    """Asynchronous page merger with heuristic-gated LLM merging."""

    def __init__(self, llm: AsyncLLMClient) -> None:
        self._llm = llm

    async def merge_two(self, prev_markdown: str, current_markdown: str) -> str:
        """Merge two adjacent pages, handling cross-page content."""
        if not self._needs_merging(prev_markdown, current_markdown):
            return prev_markdown + "\n\n" + current_markdown
        return await self._llm.merge_content(prev_markdown, current_markdown)

    async def merge_all(self, page_markdowns: list[str]) -> str:
        """Merge a list of page markdowns sequentially."""
        if not page_markdowns:
            return ""
        result = page_markdowns[0]
        for i in range(1, len(page_markdowns)):
            result = await self.merge_two(result, page_markdowns[i])
        return result

    def _needs_merging(self, prev: str, current: str) -> bool:
        """Heuristic to determine if LLM-based merging is needed."""
        prev_stripped = prev.rstrip()
        if prev_stripped.endswith("[CONTINUED]"):
            return True
        last_line = prev_stripped.split("\n")[-1].strip()
        if last_line and not last_line.endswith((".", "!", "?", ":", ";", "#", "|", "```", "---")):
            return True
        return False
