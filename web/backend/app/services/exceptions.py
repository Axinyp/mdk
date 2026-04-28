"""Domain-level exception types.

Routers do not translate these to HTTP responses themselves; the global
handler in ``app.main`` reads ``status_code`` and ``code`` and emits a
stable JSON envelope.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base for all business-rule errors. Subclasses set status_code + code."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code

    @property
    def message(self) -> str:
        return self.args[0] if self.args else self.__class__.__name__


class SessionNotFound(DomainError):
    """Returned for both missing and not-owned sessions; do not distinguish
    to avoid leaking session existence to non-owners."""

    status_code = 404
    code = "SESSION_NOT_FOUND"


class InvalidStageTransition(DomainError):
    """Wraps services.session_state.InvalidTransition with HTTP semantics."""

    status_code = 409
    code = "INVALID_STAGE_TRANSITION"


class ConcurrentTransition(DomainError):
    """Optimistic-lock conflict — another request transitioned the session first."""

    status_code = 409
    code = "CONCURRENT_TRANSITION"


class LLMResponseInvalid(DomainError):
    """LLM produced a response we cannot parse (e.g. malformed JSON)."""

    status_code = 502
    code = "LLM_RESPONSE_INVALID"


class LLMUnavailable(DomainError):
    """No LLM is configured or upstream is unreachable."""

    status_code = 502
    code = "LLM_UNAVAILABLE"


class GenerationNotComplete(DomainError):
    """Result requested before generation finished."""

    status_code = 400
    code = "GENERATION_NOT_COMPLETE"


class SessionInputInvalid(DomainError):
    """User-provided input failed validation (e.g. empty description)."""

    status_code = 400
    code = "SESSION_INPUT_INVALID"


class ProtocolSubmissionInvalid(DomainError):
    status_code = 400
    code = "PROTOCOL_SUBMISSION_INVALID"


class ProtocolSubmissionFileTooLarge(DomainError):
    status_code = 400
    code = "PROTOCOL_SUBMISSION_TOO_LARGE"
