from fastapi.testclient import TestClient

from app.main import app


def login_token(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["access_token"]


def create_instrument(client: TestClient, token: str) -> int:
    response = client.post(
        "/api/instruments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "symbol": "000001",
            "exchange": "SZ",
            "name": "Ping An Bank",
            "asset_type": "stock",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_portfolios_require_admin_token() -> None:
    with TestClient(app) as client:
        response = client.get("/api/portfolios")

        assert response.status_code == 401


def test_admin_can_create_and_list_fixed_portfolios() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        instrument_id = create_instrument(client, token)

        create_response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Core A-share Basket",
                "description": "Fixed demo portfolio for V1 backtests.",
                "positions": [{"instrument_id": instrument_id, "weight": 1.0}],
            },
        )

        assert create_response.status_code == 200
        portfolio = create_response.json()
        assert portfolio["name"] == "Core A-share Basket"
        assert portfolio["positions"][0]["instrument"]["symbol"] == "000001"
        assert portfolio["positions"][0]["weight"] == 1.0

        list_response = client.get(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert list_response.status_code == 200
        portfolios = list_response.json()
        assert any(item["name"] == "Core A-share Basket" for item in portfolios)

        logs_response = client.get(
            "/api/operation-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        actions = [item["action"] for item in logs_response.json()]
        assert "portfolio.create" in actions
