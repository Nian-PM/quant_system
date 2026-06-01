from app.models import Bar, StrategyParameterSet
from app.services.backtest import BacktestResult, run_single_instrument_backtest


def run_single_instrument_paper_simulation(
    *,
    bars: list[Bar],
    parameter_set: StrategyParameterSet,
    initial_cash: float,
) -> BacktestResult:
    result = run_single_instrument_backtest(
        bars=bars,
        parameter_set=parameter_set,
        initial_cash=initial_cash,
    )
    latest_equity = result.result_payload["equity_curve"][-1]["value"]
    latest_position = result.result_payload["position_curve"][-1]["value"]
    latest_trade = result.result_payload["trade_table"][-1] if result.result_payload["trade_table"] else None

    result.metrics.update(
        {
            "latest_equity": latest_equity,
            "latest_position_percent": latest_position,
            "latest_signal": latest_trade["side"] if latest_trade else "hold",
        }
    )
    result.result_payload["paper_summary"] = {
        "latest_equity": latest_equity,
        "latest_position_percent": latest_position,
        "latest_signal": latest_trade["side"] if latest_trade else "hold",
        "latest_trade": latest_trade,
    }
    return result
