"""Verify that DomainError subclasses produce stable JSON envelopes."""

import pytest
from httpx import AsyncClient

from app.routers import gen as gen_router
from app.services.exceptions import GenerationNotComplete, SessionNotFound


async def test_session_not_found_produces_404_envelope(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raise(*args, **kwargs):
        raise SessionNotFound("Session not found")

    monkeypatch.setattr(gen_router.session_service, "get_completed_result", _raise)

    resp = await client.get("/api/gen/sessions/missing/result", headers=auth_headers)

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Session not found", "code": "SESSION_NOT_FOUND"}


async def test_generation_not_complete_produces_400_envelope(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _raise(*args, **kwargs):
        raise GenerationNotComplete("Not completed: parsing")

    monkeypatch.setattr(gen_router.session_service, "get_completed_result", _raise)

    resp = await client.get("/api/gen/sessions/in-progress/result", headers=auth_headers)

    assert resp.status_code == 400
    assert resp.json() == {"detail": "Not completed: parsing", "code": "GENERATION_NOT_COMPLETE"}


async def test_unauthenticated_request_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/gen/sessions/any/result")
    assert resp.status_code in (401, 403)
