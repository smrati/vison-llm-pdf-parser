"""Synchronous and asynchronous LLM clients for OpenAI-compatible vision APIs."""

from __future__ import annotations

from openai import AsyncOpenAI, OpenAI

from pdf2md.config import LLMConfig
from pdf2md.exceptions import LLMError
from pdf2md.llm.prompts import MERGE_PROMPT, SYSTEM_PROMPT, build_page_prompt


class LLMClient:
    """Synchronous client for OpenAI-compatible vision APIs."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    def convert_page(
        self,
        image_base64: str,
        page_num: int,
        total_pages: int,
        system_prompt: str | None = None,
        page_prompt: str | None = None,
    ) -> str:
        """Send a page image to the vision model and get markdown back."""
        sys_prompt = system_prompt or SYSTEM_PROMPT
        usr_prompt = page_prompt or build_page_prompt(page_num, total_pages)

        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": usr_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.choices[0].message.content
        if not content:
            raise LLMError.empty_response(self._config.model)
        return content.strip()

    def merge_content(self, prev_content: str, current_content: str) -> str:
        """Ask the LLM to intelligently merge two adjacent page contents."""
        prompt = MERGE_PROMPT.format(prev_content=prev_content, current_content=current_content)

        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                temperature=0.0,
                max_tokens=self._config.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.choices[0].message.content
        if not content:
            return prev_content + "\n\n" + current_content
        return content.strip()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LLMClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncLLMClient:
    """Asynchronous client for OpenAI-compatible vision APIs."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def convert_page(
        self,
        image_base64: str,
        page_num: int,
        total_pages: int,
        system_prompt: str | None = None,
        page_prompt: str | None = None,
    ) -> str:
        """Send a page image to the vision model and get markdown back."""
        sys_prompt = system_prompt or SYSTEM_PROMPT
        usr_prompt = page_prompt or build_page_prompt(page_num, total_pages)

        try:
            response = await self._client.chat.completions.create(
                model=self._config.model,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": usr_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    },
                ],
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.choices[0].message.content
        if not content:
            raise LLMError.empty_response(self._config.model)
        return content.strip()

    async def merge_content(self, prev_content: str, current_content: str) -> str:
        """Ask the LLM to intelligently merge two adjacent page contents."""
        prompt = MERGE_PROMPT.format(prev_content=prev_content, current_content=current_content)

        try:
            response = await self._client.chat.completions.create(
                model=self._config.model,
                temperature=0.0,
                max_tokens=self._config.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.choices[0].message.content
        if not content:
            return prev_content + "\n\n" + current_content
        return content.strip()

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> AsyncLLMClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
