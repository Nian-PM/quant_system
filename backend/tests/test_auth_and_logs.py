from fastapi.testclient import TestClient

from app.main import app


def test_default_admin_can_login_and_read_profile_and_logs() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin"},
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        profile_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["username"] == "admin"

        logs_response = client.get(
            "/api/operation-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logs_response.status_code == 200
        actions = [item["action"] for item in logs_response.json()]
        assert "auth.login.success" in actions
        assert logs_response.json()[0]["created_at"]


def test_invalid_login_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )

        assert response.status_code == 401
