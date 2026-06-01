from typing import Literal

from pydantic import BaseModel, Field


class StrategyParameter(BaseModel):
    name: str
    label: str
    type: Literal["number", "integer", "boolean", "select"]
    default: float | int | bool | str
    description: str
    min_value: float | None = None
    max_value: float | None = None
    options: list[str] = Field(default_factory=list)


class StrategyTemplate(BaseModel):
    strategy_id: str
    display_name: str
    description: str
    version: str
    supported_scopes: list[Literal["single_stock", "fixed_portfolio"]]
    supported_frequencies: list[str]
    parameters: list[StrategyParameter]
    output_contract: list[str]


ROLLING_T_GRID = StrategyTemplate(
    strategy_id="rolling_t_grid",
    display_name="Rolling T / Grid Strategy",
    description=(
        "Rule-based rolling T strategy for a fixed stock or portfolio. "
        "It uses grid thresholds and an optional moving-average filter."
    ),
    version="0.1.0",
    supported_scopes=["single_stock", "fixed_portfolio"],
    supported_frequencies=["1m", "5m", "15m", "30m", "60m", "1d"],
    parameters=[
        StrategyParameter(
            name="grid_percent",
            label="Grid Percent",
            type="number",
            default=1.5,
            min_value=0.1,
            max_value=20,
            description="Price movement percentage that triggers a grid buy/sell signal.",
        ),
        StrategyParameter(
            name="base_position_percent",
            label="Base Position Percent",
            type="number",
            default=50,
            min_value=0,
            max_value=100,
            description="Baseline position percentage kept for rolling T operations.",
        ),
        StrategyParameter(
            name="trade_position_percent",
            label="Trade Position Percent",
            type="number",
            default=10,
            min_value=1,
            max_value=100,
            description="Position percentage used by each grid trade.",
        ),
        StrategyParameter(
            name="enable_ma_filter",
            label="Enable MA Filter",
            type="boolean",
            default=True,
            description="Enable moving-average trend filter before generating signals.",
        ),
        StrategyParameter(
            name="ma_window",
            label="MA Window",
            type="integer",
            default=20,
            min_value=2,
            max_value=250,
            description="Moving-average window used when the filter is enabled.",
        ),
    ],
    output_contract=[
        "metrics",
        "equity_curve",
        "benchmark_curve",
        "drawdown_curve",
        "candles",
        "trade_markers",
        "position_curve",
        "trade_table",
        "risk_disclosure",
    ],
)


def get_strategy_registry() -> list[StrategyTemplate]:
    return [ROLLING_T_GRID]
