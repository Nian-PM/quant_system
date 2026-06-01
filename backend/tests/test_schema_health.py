from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import create_engine

from app.main import app
from app.services.schema import check_database_schema


def test_health_reports_database_schema_status() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["database"] == "ok"
        assert payload["schema"]["status"] == "ok"
        assert payload["schema"]["missing_tables"] == []
        assert payload["schema"]["missing_columns"] == {}


def test_schema_check_finds_missing_columns() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE instrument (id INTEGER PRIMARY KEY)"))

    report = check_database_schema(engine)

    assert report.status == "mismatch"
    assert "instrument" in report.missing_columns
    assert "symbol" in report.missing_columns["instrument"]
