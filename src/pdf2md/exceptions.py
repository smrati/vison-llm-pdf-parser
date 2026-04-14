"""Custom exception hierarchy for pdf2md."""


class PDF2MDError(Exception):
    """Base exception for all pdf2md errors."""


class PDFLoadError(PDF2MDError):
    """Failed to open or read a PDF file."""

    @classmethod
    def file_not_found(cls, path: str) -> "PDFLoadError":
        return cls(f"PDF file not found: {path}")

    @classmethod
    def corrupted(cls, path: str, detail: str = "") -> "PDFLoadError":
        msg = f"Failed to open PDF: {path}"
        if detail:
            msg += f". {detail}"
        return cls(msg)


class LLMError(PDF2MDError):
    """Error communicating with the LLM API."""

    @classmethod
    def connection_failed(cls, base_url: str, detail: str = "") -> "LLMError":
        msg = f"Cannot connect to LLM at {base_url}"
        if detail:
            msg += f". {detail}"
        return cls(msg)

    @classmethod
    def timeout(cls, base_url: str, timeout: float) -> "LLMError":
        return cls(f"LLM request timed out after {timeout}s: {base_url}")

    @classmethod
    def empty_response(cls, model: str) -> "LLMError":
        return cls(f"LLM returned empty response for model: {model}")


class ConversionError(PDF2MDError):
    """Error during the conversion process."""


class ImageExtractionError(PDF2MDError):
    """Error extracting images from PDF."""
