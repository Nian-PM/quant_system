from dataclasses import dataclass
from datetime import datetime
import csv
from io import StringIO

from sqlmodel import Session, select

from app.models import Bar


REQUIRED_CSV_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}


@dataclass(frozen=True)
class ParsedBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class ImportResult:
    rows_imported: int
    rows_updated: int


def parse_csv_bars(csv_text: str) -> list[ParsedBar]:
    reader = csv.DictReader(StringIO(csv_text.strip()))
    if not reader.fieldnames:
        raise ValueError("CSV header is required")

    missing_columns = REQUIRED_CSV_COLUMNS - set(reader.fieldnames)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing CSV columns: {missing}")

    bars: list[ParsedBar] = []
    for line_number, row in enumerate(reader, start=2):
        try:
            timestamp = datetime.fromisoformat(row["timestamp"].strip())
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp on line {line_number}") from exc

        try:
            bars.append(
                ParsedBar(
                    timestamp=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
        except ValueError as exc:
            raise ValueError(f"Invalid numeric value on line {line_number}") from exc

    if not bars:
        raise ValueError("CSV must contain at least one bar row")

    return bars


def import_csv_bars(
    session: Session,
    *,
    instrument_id: int,
    frequency: str,
    source: str,
    csv_text: str,
) -> ImportResult:
    parsed_bars = parse_csv_bars(csv_text)
    rows_imported = 0
    rows_updated = 0

    for parsed in parsed_bars:
        statement = select(Bar).where(
            Bar.instrument_id == instrument_id,
            Bar.frequency == frequency,
            Bar.timestamp == parsed.timestamp,
        )
        existing_bar = session.exec(statement).first()
        if existing_bar:
            existing_bar.open = parsed.open
            existing_bar.high = parsed.high
            existing_bar.low = parsed.low
            existing_bar.close = parsed.close
            existing_bar.volume = parsed.volume
            existing_bar.source = source
            rows_updated += 1
        else:
            session.add(
                Bar(
                    instrument_id=instrument_id,
                    frequency=frequency,
                    timestamp=parsed.timestamp,
                    open=parsed.open,
                    high=parsed.high,
                    low=parsed.low,
                    close=parsed.close,
                    volume=parsed.volume,
                    source=source,
                )
            )
            rows_imported += 1

    session.commit()
    return ImportResult(rows_imported=rows_imported, rows_updated=rows_updated)
