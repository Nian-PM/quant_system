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
        json={"symbol": symbol, "exchange": "SH", "name": f"{symbol} test stock", "asset_type": "stock"},
    )
    assert response.status_code == 200
    return response.json()["id"]


def create_parameter_set(client: TestClient, token: str) -> int:
    response = client.post(
        "/api/strategy-parameter-sets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "strategy_id": "rolling_t_grid",
            "name": "Backtest config",
            "parameters": {"grid_percent": 1.0, "enable_ma_filter": False},
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def import_bars(client: TestClient, token: str, instrument_id: int) -> None:
    response = client.post(
        "/api/market-data/import-csv",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "instrument_id": instrument_id,
            "frequency": "5m",
            "source": "csv",
            "csv_text": (
                "timestamp,open,high,low,close,volume\n"
                "2026-01-02 09:35:00,10,10.5,9.8,10.0,1000\n"
                "2026-01-02 09:40:00,10.0,10.7,9.9,10.4,1200\n"
                "2026-01-02 09:45:00,10.4,10.9,10.2,10.8,1500\n"
                "2026-01-02 09:50:00,10.8,10.9,10.1,10.2,1300\n"
            ),
        },
    )
    assert response.status_code == 200


def test_admin_can_create_backtest_from_saved_parameter_set() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        instrument_id = create_instrument(client, token, "TBT001")
        parameter_set_id = create_parameter_set(client, token)
        import_bars(client, token, instrument_id)

        response = client.post(
            "/api/backtests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "instrument_id": instrument_id,
                "frequency": "5m",
                "parameter_set_id": parameter_set_id,
                "initial_cash": 100000,
            },
        )

        assert response.status_code == 200
        backtest = response.json()
        assert backtest["status"] == "succeeded"
        assert backtest["strategy_id"] == "rolling_t_grid"
        assert backtest["metrics"]["bar_count"] == 4
        assert backtest["metrics"]["cumulative_return"] == 0.02
        assert len(backtest["result_payload"]["equity_curve"]) == 4
        assert len(backtest["result_payload"]["drawdown_curve"]) == 4
        assert backtest["result_payload"]["trade_markers"]

        logs_response = client.get(
            "/api/operation-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        actions = [item["action"] for item in logs_response.json()]
        assert "backtest.create.succeeded" in actions


def test_backtest_fails_clearly_when_bars_are_missing() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        instrument_id = create_instrument(client, token, "TBT002")
        parameter_set_id = create_parameter_set(client, token)

        response = client.post(
            "/api/backtests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "instrument_id": instrument_id,
                "frequency": "5m",
                "parameter_set_id": parameter_set_id,
            },
        )

        assert response.status_code == 400
        assert "No bars found" in response.json()["detail"]
