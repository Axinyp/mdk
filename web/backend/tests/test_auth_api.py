"""Integration tests for the /api/auth endpoints."""

import pytest
from httpx import AsyncClient


async def test_login_success(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin1234!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["must_change_password"] is True


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


async def test_login_unknown_user_returns_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "whatever"},
    )
    assert resp.status_code == 401


async def test_me_with_valid_token_returns_user(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/auth/me")
    assert resp.status_code in (401, 403)  # HTTPBearer raises 401/403 depending on Starlette version


async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert resp.status_code == 401
