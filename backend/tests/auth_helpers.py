from uuid import uuid4

from fastapi.testclient import TestClient


def auth_headers(client: TestClient) -> dict[str, str]:
    email = f"user-{uuid4().hex}@example.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "secure-password-123",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
