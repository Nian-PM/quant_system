from dataclasses import dataclass
from datetime import datetime

from app.models import Bar


FREQUENCY_INTERVAL_MINUTES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "60m": 60,
    "1h": 60,
    "1d": 1440,
    "d": 1440,
    "daily": 1440,
}


@dataclass(frozen=True)
class DataCompleteness:
    instrument_id: int
    frequency: str
    bar_count: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None
    expected_interval_minutes: int | None
    expected_bar_count: int | None
    missing_bar_count: int | None
    completeness_ratio: float | None
    gap_count: int
    largest_gap_minutes: float | None
    status: str
    message: str


def expected_interval_minutes(frequency: str) -> int | None:
    return FREQUENCY_INTERVAL_MINUTES.get(frequency.strip().lower())


def assess_bar_completeness(
    *,
    instrument_id: int,
    frequency: str,
    bars: list[Bar],
) -> DataCompleteness:
    normalized_frequency = frequency.strip().lower()
    interval_minutes = expected_interval_minutes(normalized_frequency)

    if not bars:
        return DataCompleteness(
            instrument_id=instrument_id,
            frequency=normalized_frequency,
            bar_count=0,
            first_timestamp=None,
            last_timestamp=None,
            expected_interval_minutes=interval_minutes,
            expected_bar_count=None,
            missing_bar_count=None,
            completeness_ratio=None,
            gap_count=0,
            largest_gap_minutes=None,
            status="empty",
            message="No bars found for selected instrument and frequency.",
        )

    sorted_bars = sorted(bars, key=lambda bar: bar.timestamp)
    first_timestamp = sorted_bars[0].timestamp
    last_timestamp = sorted_bars[-1].timestamp
    largest_gap_minutes: float | None = None
    gap_count = 0
    missing_bar_count: int | None = None
    expected_bar_count: int | None = None
    completeness_ratio: float | None = None

    if interval_minutes:
        missing_bar_count = 0
        for previous, current in zip(sorted_bars, sorted_bars[1:], strict=False):
            gap_minutes = (current.timestamp - previous.timestamp).total_seconds() / 60
            largest_gap_minutes = max(largest_gap_minutes or gap_minutes, gap_minutes)
            missing_in_gap = max(round(gap_minutes / interval_minutes) - 1, 0)
            if missing_in_gap > 0:
                gap_count += 1
                missing_bar_count += missing_in_gap

        expected_bar_count = len(sorted_bars) + missing_bar_count
        completeness_ratio = round(len(sorted_bars) / expected_bar_count, 6) if expected_bar_count else None

    status = "ok"
    message = "Data continuity looks usable for the selected frequency."
    if interval_minutes is None:
        status = "unknown_frequency"
        message = "Frequency is not mapped to an expected interval; continuity gaps were not evaluated."
    elif gap_count:
        status = "warning"
        message = f"Detected {gap_count} interval gap(s) before running backtests."

    return DataCompleteness(
        instrument_id=instrument_id,
        frequency=normalized_frequency,
        bar_count=len(sorted_bars),
        first_timestamp=first_timestamp,
        last_timestamp=last_timestamp,
        expected_interval_minutes=interval_minutes,
        expected_bar_count=expected_bar_count,
        missing_bar_count=missing_bar_count,
        completeness_ratio=completeness_ratio,
        gap_count=gap_count,
        largest_gap_minutes=round(largest_gap_minutes, 6) if largest_gap_minutes is not None else None,
        status=status,
        message=message,
    )
