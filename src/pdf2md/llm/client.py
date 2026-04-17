"""LLM clients for vision-based PDF conversion.

Supports two backends:
- "openai": OpenAI-compatible /v1/chat/completions (LM Studio, vLLM, etc.)
- "ollama": Ollama native /api/chat with proper image handling
"""

from __future__ import annotations

from openai import AsyncOpenAI, OpenAI

from pdf2md.config import LLMConfig
from pdf2md.exceptions import LLMError
from pdf2md.llm.prompts import MERGE_PROMPT, SYSTEM_PROMPT, build_page_prompt

try:
    from ollama import AsyncClient as _OllamaAsyncClient
    from ollama import Client as _OllamaSyncClient

    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


def _ollama_host(base_url: str) -> str:
    """Convert an OpenAI-style base_url to an Ollama host URL."""
    host = base_url.rstrip("/")
    if host.endswith("/v1"):
        host = host[:-3]
    return host


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
        image_mime: str = "image/png",
    ) -> str:
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
                                    "url": f"data:{image_mime};base64,{image_base64}",
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
        image_mime: str = "image/png",
    ) -> str:
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
                                    "url": f"data:{image_mime};base64,{image_base64}",
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


class OllamaLLMClient:
    """Synchronous client using Ollama's native API for vision models."""

    def __init__(self, config: LLMConfig) -> None:
        if not HAS_OLLAMA:
            raise ImportError(
                "The 'ollama' package is required for the Ollama backend. "
                "Install it with: pip install vision-llm-pdf-parser[ollama]"
            )
        self._config = config
        self._client = _OllamaSyncClient(host=_ollama_host(config.base_url))

    def convert_page(
        self,
        image_base64: str,
        page_num: int,
        total_pages: int,
        system_prompt: str | None = None,
        page_prompt: str | None = None,
        image_mime: str = "image/png",
    ) -> str:
        sys_prompt = system_prompt or SYSTEM_PROMPT
        usr_prompt = page_prompt or build_page_prompt(page_num, total_pages)

        try:
            response = self._client.chat(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": usr_prompt, "images": [image_base64]},
                ],
                options={
                    "temperature": self._config.temperature,
                    "num_predict": self._config.max_tokens,
                },
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.message.content
        if not content:
            raise LLMError.empty_response(self._config.model)
        return content.strip()

    def merge_content(self, prev_content: str, current_content: str) -> str:
        prompt = MERGE_PROMPT.format(prev_content=prev_content, current_content=current_content)

        try:
            response = self._client.chat(
                model=self._config.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0, "num_predict": self._config.max_tokens},
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.message.content
        if not content:
            return prev_content + "\n\n" + current_content
        return content.strip()

    def close(self) -> None:
        pass

    def __enter__(self) -> OllamaLLMClient:
        return self

    def __exit__(self, *exc: object) -> None:
        pass


class AsyncOllamaLLMClient:
    """Asynchronous client using Ollama's native API for vision models."""

    def __init__(self, config: LLMConfig) -> None:
        if not HAS_OLLAMA:
            raise ImportError(
                "The 'ollama' package is required for the Ollama backend. "
                "Install it with: pip install vision-llm-pdf-parser[ollama]"
            )
        self._config = config
        self._client = _OllamaAsyncClient(host=_ollama_host(config.base_url))

    async def convert_page(
        self,
        image_base64: str,
        page_num: int,
        total_pages: int,
        system_prompt: str | None = None,
        page_prompt: str | None = None,
        image_mime: str = "image/png",
    ) -> str:
        sys_prompt = system_prompt or SYSTEM_PROMPT
        usr_prompt = page_prompt or build_page_prompt(page_num, total_pages)

        try:
            response = await self._client.chat(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": usr_prompt, "images": [image_base64]},
                ],
                options={
                    "temperature": self._config.temperature,
                    "num_predict": self._config.max_tokens,
                },
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.message.content
        if not content:
            raise LLMError.empty_response(self._config.model)
        return content.strip()

    async def merge_content(self, prev_content: str, current_content: str) -> str:
        prompt = MERGE_PROMPT.format(prev_content=prev_content, current_content=current_content)

        try:
            response = await self._client.chat(
                model=self._config.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0, "num_predict": self._config.max_tokens},
            )
        except Exception as e:
            raise LLMError.connection_failed(self._config.base_url, str(e)) from e

        content = response.message.content
        if not content:
            return prev_content + "\n\n" + current_content
        return content.strip()

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> AsyncOllamaLLMClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        pass


def create_sync_client(config: LLMConfig) -> LLMClient | OllamaLLMClient:
    """Factory: return the appropriate sync client based on config.backend."""
    if config.backend == "ollama":
        return OllamaLLMClient(config)
    return LLMClient(config)


def create_async_client(config: LLMConfig) -> AsyncLLMClient | AsyncOllamaLLMClient:
    """Factory: return the appropriate async client based on config.backend."""
    if config.backend == "ollama":
        return AsyncOllamaLLMClient(config)
    return AsyncLLMClient(config)
