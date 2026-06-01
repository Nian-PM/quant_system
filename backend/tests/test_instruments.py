from fastapi.testclient import TestClient

from app.main import app


def login_token(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_instruments_require_admin_token() -> None:
    with TestClient(app) as client:
        response = client.get("/api/instruments")

        assert response.status_code == 401


def test_admin_can_create_and_list_instruments() -> None:
    with TestClient(app) as client:
        token = login_token(client)

        create_response = client.post(
            "/api/instruments",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "symbol": "600519",
                "exchange": "SH",
                "name": "Kweichow Moutai",
                "asset_type": "stock",
            },
        )

        assert create_response.status_code == 200
        instrument = create_response.json()
        assert instrument["symbol"] == "600519"
        assert instrument["exchange"] == "SH"

        list_response = client.get(
            "/api/instruments",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert list_response.status_code == 200
        instruments = list_response.json()
        assert any(item["symbol"] == "600519" and item["exchange"] == "SH" for item in instruments)

        logs_response = client.get(
            "/api/operation-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        actions = [item["action"] for item in logs_response.json()]
        assert "instrument.create" in actions
