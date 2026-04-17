"""Configuration dataclasses for pdf2md."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the LLM endpoint.

    backend: "openai" (default) uses the OpenAI-compatible /v1/chat/completions API.
             "ollama" uses Ollama's native /api/chat API with proper image handling.
    """

    base_url: str = "http://localhost:11434/v1"
    model: str = "llama3.2-vision"
    api_key: str = "not-needed"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: float = 120.0
    max_retries: int = 2
    backend: str = "openai"


@dataclass(frozen=True)
class ConversionOptions:
    """Options controlling PDF conversion behavior."""

    dpi: int = 150
    image_format: str = "PNG"
    jpeg_quality: int = 85
    extract_images: bool = True
    merge_pages: bool = True
    concurrency: int = 3
    system_prompt: str | None = None
    page_prompt: str | None = None
