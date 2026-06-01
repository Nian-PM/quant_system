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


def import_custom_bars(client: TestClient, token: str, instrument_id: int, rows: list[tuple[str, float]]) -> None:
    csv_text = "timestamp,open,high,low,close,volume\n" + "\n".join(
        f"{timestamp},{close},{close},{close},{close},1000" for timestamp, close in rows
    )
    response = client.post(
        "/api/market-data/import-csv",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "instrument_id": instrument_id,
            "frequency": "5m",
            "source": "csv",
            "csv_text": csv_text,
        },
    )
    assert response.status_code == 200


def create_portfolio(client: TestClient, token: str, positions: list[dict]) -> int:
    response = client.post(
        "/api/portfolios",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Backtest basket",
            "description": "Fixed basket for portfolio backtest tests.",
            "positions": positions,
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


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


def test_admin_can_create_fixed_portfolio_backtest() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        first_instrument_id = create_instrument(client, token, "TBT101")
        second_instrument_id = create_instrument(client, token, "TBT102")
        parameter_set_id = create_parameter_set(client, token)
        import_custom_bars(
            client,
            token,
            first_instrument_id,
            [
                ("2026-01-02 09:35:00", 10.0),
                ("2026-01-02 09:40:00", 10.5),
                ("2026-01-02 09:45:00", 11.0),
            ],
        )
        import_custom_bars(
            client,
            token,
            second_instrument_id,
            [
                ("2026-01-02 09:35:00", 20.0),
                ("2026-01-02 09:40:00", 19.0),
                ("2026-01-02 09:45:00", 18.0),
            ],
        )
        portfolio_id = create_portfolio(
            client,
            token,
            [
                {"instrument_id": first_instrument_id, "weight": 0.6},
                {"instrument_id": second_instrument_id, "weight": 0.4},
            ],
        )

        response = client.post(
            "/api/backtests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_id": portfolio_id,
                "frequency": "5m",
                "parameter_set_id": parameter_set_id,
                "initial_cash": 100000,
            },
        )

        assert response.status_code == 200
        backtest = response.json()
        assert backtest["config"]["scope"] == "portfolio"
        assert backtest["config"]["portfolio_id"] == portfolio_id
        assert backtest["metrics"]["bar_count"] == 3
        assert backtest["metrics"]["cumulative_return"] == 0.02
        assert backtest["result_payload"]["scope"] == "portfolio"
        assert len(backtest["result_payload"]["portfolio_legs"]) == 2


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


def test_portfolio_backtest_fails_when_position_bars_are_missing() -> None:
    with TestClient(app) as client:
        token = login_token(client)
        first_instrument_id = create_instrument(client, token, "TBT201")
        second_instrument_id = create_instrument(client, token, "TBT202")
        parameter_set_id = create_parameter_set(client, token)
        import_custom_bars(
            client,
            token,
            first_instrument_id,
            [
                ("2026-01-02 09:35:00", 10.0),
                ("2026-01-02 09:40:00", 10.5),
            ],
        )
        portfolio_id = create_portfolio(
            client,
            token,
            [
                {"instrument_id": first_instrument_id, "weight": 0.5},
                {"instrument_id": second_instrument_id, "weight": 0.5},
            ],
        )

        response = client.post(
            "/api/backtests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "portfolio_id": portfolio_id,
                "frequency": "5m",
                "parameter_set_id": parameter_set_id,
            },
        )

        assert response.status_code == 400
        assert "No bars found for portfolio instrument" in response.json()["detail"]
