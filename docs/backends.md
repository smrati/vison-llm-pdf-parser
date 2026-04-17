# Backends

The library supports any vision-capable LLM that exposes an OpenAI-compatible chat completions API, plus Ollama's native API.

## Backend Overview

| Backend | API Protocol | Image Format | Port | Package |
|---------|-------------|-------------|------|---------|
| Ollama | Native `/api/chat` | `images` field in message | 11434 | `ollama` (optional) |
| LM Studio | OpenAI `/v1/chat/completions` | `image_url` content block | 1234 | `openai` (required) |
| vLLM | OpenAI `/v1/chat/completions` | `image_url` content block | 8000 | `openai` (required) |
| Any other | OpenAI `/v1/chat/completions` | `image_url` content block | varies | `openai` (required) |

## Ollama (Native API)

Uses the `ollama` Python package to call Ollama's native `/api/chat` endpoint. This is the recommended way to use Ollama because it uses Ollama's native image handling format.

### Setup

```bash
# Install with Ollama support
pip install vision-llm-pdf-parser[ollama]

# Or with uv
uv sync --extra ollama

# Pull and start a vision model
ollama pull llama3.2-vision
ollama serve
```

### Configuration

```python
from pdf2md import LLMConfig

config = LLMConfig(
    base_url="http://localhost:11434/v1",   # Ollama default
    model="llama3.2-vision",                # Or: gemma3, llava, etc.
    backend="ollama",                       # Use native API
)
```

### How it works

The `OllamaLLMClient` converts the `base_url` to an Ollama host by stripping `/v1`, then uses `ollama.Client.chat()` with the `images` parameter:

```python
# Internal implementation (simplified)
response = client.chat(
    model="llama3.2-vision",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt, "images": [base64_string]},
    ],
    options={"temperature": 0.1, "num_predict": 4096},
)
```

### Supported models

| Model | Notes |
|-------|-------|
| `llama3.2-vision` | Good general-purpose vision model |
| `gemma3` | Google's vision model, works well |
| `llava` | Popular open-source vision model |
| `minicpm-v` | Lightweight vision model |

### Important

- `max_tokens` is mapped to Ollama's `num_predict` parameter
- The `base_url` `/v1` suffix is automatically stripped to get the Ollama host
- The `ollama` package is optional; you'll get a clear error if it's not installed

---

## LM Studio (OpenAI-Compatible)

LM Studio exposes an OpenAI-compatible API at `/v1/chat/completions`.

### Setup

1. Open LM Studio
2. Download and load a vision-capable model
3. Go to the **Local Server** tab
4. Click **Start Server** (default port: 1234)

### Configuration

```python
from pdf2md import LLMConfig

config = LLMConfig(
    base_url="http://localhost:1234/v1",
    model="allenai/olmocr-2-7b",           # Model identifier from LM Studio
    backend="openai",                       # OpenAI-compatible (default)
)
```

### How it works

Uses the `openai` Python SDK to send requests to LM Studio's `/v1/chat/completions` endpoint. Images are sent as `image_url` content blocks with base64 data URIs.

### WSL Note

If running LM Studio on Windows and the script inside WSL2, `localhost` may not reach the Windows host. Solutions:

1. Enable `networkingMode=mirrored` in `C:\Users\<you>\.wslconfig`:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
2. Or bind LM Studio's server to `0.0.0.0` instead of `127.0.0.1`

---

## vLLM (OpenAI-Compatible)

vLLM serves models with an OpenAI-compatible API.

### Setup

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-VL-2B-Instruct \
    --port 8000
```

### Configuration

```python
from pdf2md import LLMConfig

config = LLMConfig(
    base_url="http://localhost:8000/v1",
    model="Qwen/Qwen2-VL-2B-Instruct",
    backend="openai",
)
```

---

## Custom / Remote Endpoints

Any server that implements the OpenAI `/v1/chat/completions` protocol with vision support works out of the box:

```python
config = LLMConfig(
    base_url="https://api.example.com/v1",
    model="gpt-4o",
    api_key="sk-your-key-here",
    backend="openai",
)
```

---

## Vision Model Requirements

The model must support image input. Text-only models will either error or silently ignore the image.

**Vision-capable:** llama3.2-vision, gemma3, llava, Qwen2-VL, pixtral, gpt-4o, olmocr-2-7b

**Not vision-capable:** llama3, mistral, qwen2, gemma2 (these are text-only)

Check your backend's model list (`/v1/models`) to see what's available.
