from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def unique_email() -> str:
    return f"auth-{uuid4().hex}@example.com"


def test_register_login_refresh_and_me_flow() -> None:
    with TestClient(create_app()) as client:
        email = unique_email()
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "secure-password-123",
                "display_name": "Brain Learner",
            },
        )
        assert register_response.status_code == 201
        register_body = register_response.json()
        assert register_body["access_token"]
        assert register_body["refresh_token"]
        assert register_body["user"]["email"] == email

        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {register_body['access_token']}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == email

        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "secure-password-123"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["access_token"]

        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": login_response.json()["refresh_token"]},
        )
        assert refresh_response.status_code == 200
        assert refresh_response.json()["access_token"]


def test_register_rejects_duplicate_email() -> None:
    with TestClient(create_app()) as client:
        email = unique_email()
        payload = {
            "email": email,
            "password": "secure-password-123",
            "display_name": "Brain Learner",
        }

        assert client.post("/api/auth/register", json=payload).status_code == 201
        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 409


def test_protected_endpoint_requires_token() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/materials/999999/concepts/extract")

        assert response.status_code == 401


def test_production_rejects_default_jwt_secret() -> None:
    production_settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret_key="change-this-development-secret",
    )

    with pytest.raises(RuntimeError):
        production_settings.validate_runtime_security()


def test_production_accepts_strong_custom_jwt_secret() -> None:
    production_settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret_key="synaptor-production-secret-at-least-32-chars",
    )

    production_settings.validate_runtime_security()
