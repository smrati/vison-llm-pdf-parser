"""Main PDF to Markdown converters (sync and async)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from pdf2md.config import ConversionOptions, LLMConfig
from pdf2md.convert.image_extractor import ImageExtractor
from pdf2md.convert.merger import AsyncPageMerger, PageMerger
from pdf2md.exceptions import ConversionError
from pdf2md.llm.client import AsyncLLMClient, LLMClient
from pdf2md.models import ConversionResult, PageResult
from pdf2md.pdf.loader import PDFDocument


class PDFToMarkdownConverter:
    """Synchronous PDF to Markdown converter using vision LLMs."""

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
        options: ConversionOptions | None = None,
    ) -> None:
        self._llm_config = llm_config or LLMConfig()
        self._options = options or ConversionOptions()

    def convert(self, pdf_path: str | Path) -> ConversionResult:
        """Convert an entire PDF to Markdown."""
        pdf_path = Path(pdf_path)
        with PDFDocument(pdf_path, self._options) as pdf:
            pages = pdf.get_all_pages()
            metadata = pdf.metadata

        with LLMClient(self._llm_config) as llm:
            page_results = self._convert_all_pages(llm, pages)

            extracted_images = self._extract_images(pdf_path)

            final_markdown = self._merge_pages(llm, page_results)

        return ConversionResult(
            markdown=final_markdown,
            pages=page_results,
            images=extracted_images,
            metadata=metadata,
        )

    def convert_page(self, pdf_path: str | Path, page_num: int) -> PageResult:
        """Convert a single page to Markdown."""
        with PDFDocument(pdf_path, self._options) as pdf:
            page = pdf.get_page(page_num)
            total = pdf.page_count

        with LLMClient(self._llm_config) as llm:
            md = llm.convert_page(
                image_base64=page.image_base64,
                page_num=page.page_number,
                total_pages=total,
                system_prompt=self._options.system_prompt,
                page_prompt=self._options.page_prompt,
                image_mime=page.image_mime,
            )

        return PageResult(
            page_number=page.page_number,
            markdown=md,
            width=page.width,
            height=page.height,
        )

    def convert_pages(self, pdf_path: str | Path, pages: list[int]) -> list[PageResult]:
        """Convert specific pages to Markdown."""
        with PDFDocument(pdf_path, self._options) as pdf:
            pdf_pages = [pdf.get_page(p) for p in pages]
            total = pdf.page_count

        with LLMClient(self._llm_config) as llm:
            return self._convert_all_pages(llm, pdf_pages, total)

    def _convert_all_pages(
        self,
        llm: LLMClient,
        pages: list,
        total_pages: int | None = None,
    ) -> list[PageResult]:
        total = total_pages or len(pages)
        results: list[PageResult] = []
        for page in pages:
            md = llm.convert_page(
                image_base64=page.image_base64,
                page_num=page.page_number,
                total_pages=total,
                system_prompt=self._options.system_prompt,
                page_prompt=self._options.page_prompt,
                image_mime=page.image_mime,
            )
            results.append(
                PageResult(
                    page_number=page.page_number,
                    markdown=md,
                    width=page.width,
                    height=page.height,
                )
            )
        return results

    def _extract_images(self, pdf_path: Path) -> list:
        if not self._options.extract_images:
            return []
        try:
            with PDFDocument(pdf_path, self._options) as pdf:
                extractor = ImageExtractor()
                return extractor.extract_all(pdf)
        except Exception as e:
            raise ConversionError(f"Image extraction failed: {e}") from e

    def _merge_pages(self, llm: LLMClient, page_results: list[PageResult]) -> str:
        if not self._options.merge_pages or len(page_results) <= 1:
            return "\n\n---\n\n".join(r.markdown for r in page_results)
        merger = PageMerger(llm)
        return merger.merge_all([r.markdown for r in page_results])


class AsyncPDFToMarkdownConverter:
    """Asynchronous PDF to Markdown converter using vision LLMs."""

    def __init__(
        self,
        llm_config: LLMConfig | None = None,
        options: ConversionOptions | None = None,
    ) -> None:
        self._llm_config = llm_config or LLMConfig()
        self._options = options or ConversionOptions()

    async def convert(self, pdf_path: str | Path) -> ConversionResult:
        """Convert an entire PDF to Markdown (pages processed concurrently)."""
        pdf_path = Path(pdf_path)
        with PDFDocument(pdf_path, self._options) as pdf:
            pages = pdf.get_all_pages()
            metadata = pdf.metadata

        async with AsyncLLMClient(self._llm_config) as llm:
            page_results = await self._convert_all_pages_async(llm, pages)

            extracted_images = self._extract_images(pdf_path)

            final_markdown = await self._merge_pages_async(llm, page_results)

        return ConversionResult(
            markdown=final_markdown,
            pages=page_results,
            images=extracted_images,
            metadata=metadata,
        )

    async def convert_page(self, pdf_path: str | Path, page_num: int) -> PageResult:
        """Convert a single page to Markdown."""
        with PDFDocument(pdf_path, self._options) as pdf:
            page = pdf.get_page(page_num)
            total = pdf.page_count

        async with AsyncLLMClient(self._llm_config) as llm:
            md = await llm.convert_page(
                image_base64=page.image_base64,
                page_num=page.page_number,
                total_pages=total,
                system_prompt=self._options.system_prompt,
                page_prompt=self._options.page_prompt,
                image_mime=page.image_mime,
            )

        return PageResult(
            page_number=page.page_number,
            markdown=md,
            width=page.width,
            height=page.height,
        )

    async def convert_pages(self, pdf_path: str | Path, pages: list[int]) -> list[PageResult]:
        """Convert specific pages to Markdown (concurrently)."""
        with PDFDocument(pdf_path, self._options) as pdf:
            pdf_pages = [pdf.get_page(p) for p in pages]
            total = pdf.page_count

        async with AsyncLLMClient(self._llm_config) as llm:
            return await self._convert_all_pages_async(llm, pdf_pages, total)

    async def _convert_all_pages_async(
        self,
        llm: AsyncLLMClient,
        pages: list,
        total_pages: int | None = None,
    ) -> list[PageResult]:
        total = total_pages or len(pages)
        semaphore = asyncio.Semaphore(self._options.concurrency)

        async def process_page(page: object) -> PageResult:
            async with semaphore:
                md = await llm.convert_page(
                    image_base64=page.image_base64,
                    page_num=page.page_number,
                    total_pages=total,
                    system_prompt=self._options.system_prompt,
                    page_prompt=self._options.page_prompt,
                    image_mime=page.image_mime,
                )
                return PageResult(
                    page_number=page.page_number,
                    markdown=md,
                    width=page.width,
                    height=page.height,
                )

        tasks = [process_page(p) for p in pages]
        return list(await asyncio.gather(*tasks))

    def _extract_images(self, pdf_path: Path) -> list:
        if not self._options.extract_images:
            return []
        try:
            with PDFDocument(pdf_path, self._options) as pdf:
                extractor = ImageExtractor()
                return extractor.extract_all(pdf)
        except Exception as e:
            raise ConversionError(f"Image extraction failed: {e}") from e

    async def _merge_pages_async(self, llm: AsyncLLMClient, page_results: list[PageResult]) -> str:
        if not self._options.merge_pages or len(page_results) <= 1:
            return "\n\n---\n\n".join(r.markdown for r in page_results)
        merger = AsyncPageMerger(llm)
        return await merger.merge_all([r.markdown for r in page_results])
