# Configuration

## LLMConfig

Controls how the library communicates with the vision LLM. Immutable (frozen dataclass).

```python
from pdf2md import LLMConfig

config = LLMConfig(
    base_url="http://localhost:11434/v1",
    model="llama3.2-vision",
    api_key="not-needed",
    temperature=0.1,
    max_tokens=4096,
    timeout=120.0,
    max_retries=2,
)
```

### Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `base_url` | `str` | `http://localhost:11434/v1` | API endpoint URL. All backends expose `/v1/chat/completions`. |
| `model` | `str` | `llama3.2-vision` | Model identifier as recognized by the backend. Must be a **vision-capable** model. |
| `api_key` | `str` | `not-needed` | API key. Not required for local models. LM Studio accepts any string. |
| `temperature` | `float` | `0.1` | Sampling temperature. 0.0 = deterministic, higher = more creative. Low values recommended for faithful conversion. |
| `max_tokens` | `int` | `4096` | Maximum tokens per LLM response. Complex pages with tables may need more. |
| `timeout` | `float` | `120.0` | Request timeout in seconds. Vision requests can be slow on CPU-bound models. |
| `max_retries` | `int` | `2` | Number of retries on transient failures. |

### Common Configurations

```python
# Ollama
LLMConfig(
    base_url="http://localhost:11434/v1",
    model="gemma3",
)

# LM Studio
LLMConfig(
    base_url="http://localhost:1234/v1",
    model="allenai/olmocr-2-7b",
)

# vLLM
LLMConfig(
    base_url="http://localhost:8000/v1",
    model="Qwen/Qwen2-VL-2B-Instruct",
)

# Remote OpenAI-compatible API
LLMConfig(
    base_url="https://api.example.com/v1",
    model="gpt-4o",
    api_key="sk-...",
)
```

### Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `base_url` | `str` | `http://localhost:11434/v1` | API endpoint URL. Should include `/v1` for OpenAI-compatible backends. |
| `model` | `str` | `llama3.2-vision` | Model identifier as recognized by the backend. Must be a **vision-capable** model. |
| `api_key` | `str` | `not-needed` | API key. Not required for local models. LM Studio accepts any string. |
| `temperature` | `float` | `0.1` | Sampling temperature. 0.0 = deterministic, higher = more creative. Low values recommended for faithful conversion. |
| `max_tokens` | `int` | `4096` | Maximum tokens per LLM response. Complex pages with tables may need more. |
| `timeout` | `float` | `120.0` | Request timeout in seconds. Vision requests can be slow on CPU-bound models. |
| `max_retries` | `int` | `2` | Number of retries on transient failures. |
| `backend` | `str` | `openai` | API protocol: `"openai"` for OpenAI-compatible endpoints, `"ollama"` for Ollama's native API. |

### Backend Selection

| Backend | When to use | Image format |
|---------|-------------|-------------|
| `"openai"` | LM Studio, vLLM, any `/v1/chat/completions` server | `image_url` content block with base64 data URI |
| `"ollama"` | Ollama with native API | `images` field in message with base64 string |

### Common Configurations

```python
# Ollama (native API)
LLMConfig(
    base_url="http://localhost:11434/v1",
    model="gemma3",
    backend="ollama",
)

# LM Studio
LLMConfig(
    base_url="http://localhost:1234/v1",
    model="allenai/olmocr-2-7b",
    backend="openai",
)

# vLLM
LLMConfig(
    base_url="http://localhost:8000/v1",
    model="Qwen/Qwen2-VL-2B-Instruct",
    backend="openai",
)

# Remote OpenAI-compatible API
LLMConfig(
    base_url="https://api.example.com/v1",
    model="gpt-4o",
    api_key="sk-...",
    backend="openai",
)
```

---

## ConversionOptions

Controls how the PDF is processed and rendered. Immutable (frozen dataclass).

```python
from pdf2md import ConversionOptions

options = ConversionOptions(
    dpi=150,
    image_format="PNG",
    jpeg_quality=85,
    extract_images=True,
    merge_pages=True,
    concurrency=3,
    system_prompt=None,
    page_prompt=None,
)
```

### Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dpi` | `int` | `150` | Page render resolution. Higher = better quality but larger images and slower LLM processing. |
| `image_format` | `str` | `"PNG"` | Rendered page format: `"PNG"` (lossless) or `"JPEG"` (smaller). |
| `jpeg_quality` | `int` | `85` | JPEG quality (1-100). Ignored for PNG. Below 70 degrades text readability. |
| `extract_images` | `bool` | `True` | Whether to extract embedded images from the PDF. |
| `merge_pages` | `bool` | `True` | Enable smart cross-page merging. When `False`, pages are joined with `---` separators. |
| `concurrency` | `int` | `3` | Maximum parallel LLM calls (async mode only). |
| `system_prompt` | `str \| None` | `None` | Override the default system prompt sent to the LLM. |
| `page_prompt` | `str \| None` | `None` | Override the default per-page user prompt. |

### DPI Guidelines

| DPI | Rendered page size (letter) | Speed | Use case |
|-----|-----------------------------|-------|----------|
| 72 | ~600 x 800 px | Fast | Quick preview, small text OK to lose |
| 150 | ~1250 x 1650 px | Medium | Default, good balance |
| 200 | ~1650 x 2200 px | Slower | High quality, fine print |
| 300 | ~2500 x 3300 px | Slow | Maximum quality, large LLM payloads |

### Custom Prompts

Override the default prompts for specialized extraction tasks:

```python
# Extract only tables
ConversionOptions(
    system_prompt="You are a table extraction specialist. Output only Markdown tables.",
    page_prompt="Extract all tables from this page as Markdown tables.",
)

# Focus on equations
ConversionOptions(
    system_prompt="You convert math content. Use LaTeX notation for all equations.",
    page_prompt="Extract all mathematical equations and expressions from this page.",
)
```

**Caution:** The default prompts include instructions for `[CONTINUED]` markers which the merger relies on. If you override `system_prompt`, cross-page merging may stop working unless you include similar instructions.
