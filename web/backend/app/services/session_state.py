"""Session lifecycle state machine.

Status transitions are enforced via an explicit table; any path not in
``TRANSITIONS[current]`` raises ``InvalidTransition``. Legacy string values
are coerced to ``ERROR`` with a warning rather than crashing.
"""

from __future__ import annotations

from enum import Enum

from loguru import logger


class SessionStatus(str, Enum):
    CREATED = "created"
    CLARIFYING = "clarifying"
    PARSING = "parsing"
    PARSED = "parsed"
    CONFIRMED = "confirmed"
    GENERATING = "generating"
    COMPLETED = "completed"
    ABORTED = "aborted"
    ERROR = "error"


TRANSITIONS: dict[SessionStatus, set[SessionStatus]] = {
    SessionStatus.CREATED:    {SessionStatus.PARSING, SessionStatus.ERROR},
    SessionStatus.CLARIFYING: {SessionStatus.PARSING, SessionStatus.ERROR, SessionStatus.ABORTED, SessionStatus.CONFIRMED},
    SessionStatus.PARSING:    {SessionStatus.CLARIFYING, SessionStatus.PARSED, SessionStatus.ERROR, SessionStatus.ABORTED},
    SessionStatus.PARSED:     {SessionStatus.CONFIRMED, SessionStatus.PARSING, SessionStatus.ERROR},
    SessionStatus.CONFIRMED:  {SessionStatus.GENERATING, SessionStatus.PARSING, SessionStatus.ERROR},
    SessionStatus.GENERATING: {SessionStatus.COMPLETED, SessionStatus.ERROR, SessionStatus.ABORTED},
    SessionStatus.COMPLETED:  {SessionStatus.GENERATING, SessionStatus.PARSING},
    SessionStatus.ABORTED:    {SessionStatus.PARSING, SessionStatus.GENERATING, SessionStatus.CONFIRMED},
    SessionStatus.ERROR:      {SessionStatus.PARSING, SessionStatus.GENERATING, SessionStatus.CONFIRMED},
}


class InvalidTransition(ValueError):
    """Requested state transition is not allowed by the transition table."""


def coerce_status(value: str | SessionStatus | None) -> SessionStatus:
    if isinstance(value, SessionStatus):
        return value
    if value is None:
        logger.warning("[FLOW] Missing session status; coercing to ERROR")
        return SessionStatus.ERROR
    try:
        return SessionStatus(value)
    except ValueError:
        logger.warning("[FLOW] Unknown legacy session status '{}'; coercing to ERROR", value)
        return SessionStatus.ERROR


def assert_transition(current: SessionStatus | str | None, target: SessionStatus) -> SessionStatus:
    normalized = coerce_status(current)
    allowed = TRANSITIONS[normalized]
    if target not in allowed:
        allowed_values = ", ".join(s.value for s in sorted(allowed, key=lambda s: s.value))
        raise InvalidTransition(
            f"Invalid session transition: {normalized.value} → {target.value} (allowed: {allowed_values})"
        )
    return normalized
