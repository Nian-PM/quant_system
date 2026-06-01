from fastapi.testclient import TestClient

from app.main import app


def login_token(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["access_token"]


def create_instrument(client: TestClient, token: str, symbol: str) -> int:
    response = client.post(
        "/api/instruments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "symbol": symbol,
            "exchange": "SH",
            "name": f"{symbol} test stock",
            "asset_type": "stock",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_admin_can_import_and_query_csv_bars() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        instrument_id = create_instrument(client, token, "TCSV01")

        import_response = client.post(
            "/api/market-data/import-csv",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "instrument_id": instrument_id,
                "frequency": "5m",
                "source": "csv",
                "csv_text": (
                    "timestamp,open,high,low,close,volume\n"
                    "2026-01-02 09:35:00,10,10.5,9.8,10.2,1000\n"
                    "2026-01-02 09:40:00,10.2,10.8,10.1,10.7,1200\n"
                ),
            },
        )

        assert import_response.status_code == 200
        task = import_response.json()
        assert task["status"] == "succeeded"
        assert task["rows_imported"] == 2

        bars_response = client.get(
            f"/api/market-data/bars?instrument_id={instrument_id}&frequency=5m&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert bars_response.status_code == 200
        bars = bars_response.json()
        assert len(bars) == 2
        assert bars[0]["timestamp"].startswith("2026-01-02T09:35:00")
        assert bars[1]["close"] == 10.7

        logs_response = client.get(
            "/api/operation-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        actions = [item["action"] for item in logs_response.json()]
        assert "market_data.import_csv.succeeded" in actions


def test_reimport_updates_existing_bar_without_duplicates() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        instrument_id = create_instrument(client, token, "TCSV02")

        payload = {
            "instrument_id": instrument_id,
            "frequency": "1d",
            "source": "csv",
            "csv_text": (
                "timestamp,open,high,low,close,volume\n"
                "2026-01-02 00:00:00,10,11,9,10.5,1000\n"
            ),
        }
        first_response = client.post(
            "/api/market-data/import-csv",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        assert first_response.status_code == 200

        second_response = client.post(
            "/api/market-data/import-csv",
            headers={"Authorization": f"Bearer {token}"},
            json={**payload, "csv_text": "timestamp,open,high,low,close,volume\n2026-01-02 00:00:00,10,12,8,11.5,1500\n"},
        )
        assert second_response.status_code == 200
        assert second_response.json()["rows_updated"] == 1

        bars_response = client.get(
            f"/api/market-data/bars?instrument_id={instrument_id}&frequency=1d&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        bars = bars_response.json()
        assert len(bars) == 1
        assert bars[0]["close"] == 11.5
        assert bars[0]["volume"] == 1500


def test_invalid_csv_import_fails_without_partial_bars() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        instrument_id = create_instrument(client, token, "TCSV03")

        response = client.post(
            "/api/market-data/import-csv",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "instrument_id": instrument_id,
                "frequency": "5m",
                "source": "csv",
                "csv_text": (
                    "timestamp,open,high,low,close,volume\n"
                    "2026-01-02 09:35:00,10,10.5,9.8,10.2,1000\n"
                    "bad-time,10.2,10.8,10.1,10.7,1200\n"
                ),
            },
        )

        assert response.status_code == 400
        assert "Invalid timestamp" in response.json()["detail"]

        bars_response = client.get(
            f"/api/market-data/bars?instrument_id={instrument_id}&frequency=5m&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert bars_response.json() == []
