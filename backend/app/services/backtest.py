from dataclasses import dataclass

from app.models import Bar, StrategyParameterSet


@dataclass(frozen=True)
class BacktestResult:
    metrics: dict
    result_payload: dict


def run_single_instrument_backtest(
    *,
    bars: list[Bar],
    parameter_set: StrategyParameterSet,
    initial_cash: float,
) -> BacktestResult:
    if not bars:
        raise ValueError("No bars found for selected instrument and frequency")

    first_close = bars[0].close
    if first_close <= 0:
        raise ValueError("First close price must be positive")

    peak_equity = initial_cash
    equity_curve = []
    drawdown_curve = []
    position_curve = []
    candles = []
    trade_markers = []
    trades = []

    grid_percent = float(parameter_set.parameters.get("grid_percent", 1.5))
    reference_close = first_close

    for index, bar in enumerate(bars):
        equity = round(initial_cash * (bar.close / first_close), 2)
        peak_equity = max(peak_equity, equity)
        drawdown = round((equity - peak_equity) / peak_equity, 6) if peak_equity else 0

        timestamp = bar.timestamp.isoformat()
        equity_curve.append({"timestamp": timestamp, "value": equity})
        drawdown_curve.append({"timestamp": timestamp, "value": drawdown})
        position_curve.append({"timestamp": timestamp, "value": parameter_set.parameters.get("base_position_percent", 50)})
        candles.append(
            {
                "timestamp": timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
        )

        if index == 0:
            continue

        change_percent = ((bar.close - reference_close) / reference_close) * 100
        if abs(change_percent) >= grid_percent:
            side = "sell" if change_percent > 0 else "buy"
            marker = {"timestamp": timestamp, "side": side, "price": bar.close}
            trade_markers.append(marker)
            trades.append(
                {
                    "timestamp": timestamp,
                    "side": side,
                    "price": bar.close,
                    "change_percent": round(change_percent, 4),
                }
            )
            reference_close = bar.close

    cumulative_return = round((bars[-1].close / first_close) - 1, 6)
    max_drawdown = min((point["value"] for point in drawdown_curve), default=0)
    win_rate = 0
    if trades:
        wins = [trade for trade in trades if trade["side"] == "sell"]
        win_rate = round(len(wins) / len(trades), 6)

    metrics = {
        "bar_count": len(bars),
        "trade_count": len(trades),
        "cumulative_return": cumulative_return,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "profit_loss_ratio": 0,
    }
    result_payload = {
        "strategy_id": parameter_set.strategy_id,
        "parameters": parameter_set.parameters,
        "equity_curve": equity_curve,
        "benchmark_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "candles": candles,
        "trade_markers": trade_markers,
        "position_curve": position_curve,
        "trade_table": trades,
        "risk_disclosure": "Backtest results are simulated and do not represent real-money trading.",
    }
    return BacktestResult(metrics=metrics, result_payload=result_payload)
