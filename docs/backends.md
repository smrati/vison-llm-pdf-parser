# Backends

The library uses a single API protocol — OpenAI's `/v1/chat/completions` — to communicate with any vision-capable LLM. Ollama, LM Studio, and vLLM all implement this same endpoint, so switching backends is just changing `base_url` and `model`.

## Backend Overview

| Backend | base_url | Default Port | Setup |
|---------|----------|-------------|-------|
| Ollama | `http://localhost:11434/v1` | 11434 | `ollama serve` |
| LM Studio | `http://localhost:1234/v1` | 1234 | Start Local Server in app |
| vLLM | `http://localhost:8000/v1` | 8000 | `python -m vllm.entrypoints.openai.api_server` |
| Any other | varies | varies | Must expose `/v1/chat/completions` |

All backends use the same image format: `image_url` content blocks with base64 data URIs. No special per-backend configuration needed.

## Ollama

### Setup

```bash
ollama pull llama3.2-vision
ollama serve
```

### Configuration

```python
from pdf2md import LLMConfig

config = LLMConfig(
    base_url="http://localhost:11434/v1",
    model="llama3.2-vision",  # Or: gemma3, llava, minicpm-v
)
```

Ollama exposes an OpenAI-compatible API at `/v1/chat/completions`. The library communicates with it using the same `openai` Python SDK and the same `image_url` message format as every other backend.

### Supported vision models

| Model | Notes |
|-------|-------|
| `llama3.2-vision` | Good general-purpose vision model |
| `gemma3` | Google's vision model, works well |
| `llava` | Popular open-source vision model |
| `minicpm-v` | Lightweight vision model |

---

## LM Studio

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
    model="allenai/olmocr-2-7b",
)
```

### WSL Note

If running LM Studio on Windows and the script inside WSL2, `localhost` may not reach the Windows host. Solutions:

1. Enable `networkingMode=mirrored` in `C:\Users\<you>\.wslconfig`:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```
2. Or bind LM Studio's server to `0.0.0.0` instead of `127.0.0.1`

---

## vLLM

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
)
```

---

## Vision Model Requirements

The model must support image input. Text-only models will either error or silently ignore the image.

**Vision-capable:** llama3.2-vision, gemma3, llava, Qwen2-VL, pixtral, gpt-4o, olmocr-2-7b

**Not vision-capable:** llama3, mistral, qwen2, gemma2 (these are text-only)

Check your backend's model list (`/v1/models`) to see what's available.
