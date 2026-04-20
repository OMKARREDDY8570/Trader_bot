"""
engine/backtester.py - Walk-forward backtesting module
"""

import numpy as np
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from engine.aggregator import aggregate
from data.fetcher import fetch_ohlcv

logger = logging.getLogger(__name__)


def run_backtest(symbol, timeframe="1d", limit=365,
                 initial_capital=10_000.0,
                 confidence_threshold=config.CONFIDENCE_THRESHOLD):
    df = fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    if df is None or len(df) < 60:
        return {"error": "Insufficient historical data"}

    capital      = initial_capital
    position     = None
    trades       = []
    equity_curve = [capital]

    for i in range(50, len(df) - 1):
        window = df.iloc[:i + 1]
        try:
            result = aggregate(window, symbol)
        except Exception:
            continue

        signal = result["signal"]
        conf   = result["confidence"]
        price  = float(df["close"].iloc[i])

        if signal == "BUY" and position is None and conf >= confidence_threshold:
            qty      = (capital * 0.95) / price
            position = {"entry_price": price, "qty": qty, "entry_idx": i}
            capital -= qty * price

        elif signal == "SELL" and position is not None:
            pnl     = (price - position["entry_price"]) * position["qty"]
            capital += position["qty"] * price
            trades.append({
                "entry_price": position["entry_price"],
                "exit_price":  price,
                "qty":         position["qty"],
                "pnl":         round(pnl, 4),
                "pnl_pct":     round((price / position["entry_price"] - 1) * 100, 2),
                "bars_held":   i - position["entry_idx"],
            })
            position = None

        current_equity = capital + (position["qty"] * price if position else 0)
        equity_curve.append(current_equity)

    if position:
        price = float(df["close"].iloc[-1])
        pnl   = (price - position["entry_price"]) * position["qty"]
        capital += position["qty"] * price
        trades.append({
            "entry_price": position["entry_price"],
            "exit_price":  price,
            "qty":         position["qty"],
            "pnl":         round(pnl, 4),
            "pnl_pct":     round((price / position["entry_price"] - 1) * 100, 2),
            "bars_held":   len(df) - 1 - position["entry_idx"],
            "open_trade":  True,
        })

    total_return = ((capital - initial_capital) / initial_capital) * 100
    wins   = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_win  = np.mean([t["pnl_pct"] for t in wins])   if wins   else 0
    avg_loss = np.mean([t["pnl_pct"] for t in losses]) if losses else 0
    profit_factor = (
        abs(sum(t["pnl"] for t in wins)) / abs(sum(t["pnl"] for t in losses))
        if losses else float("inf")
    )

    equity_arr   = np.array(equity_curve)
    running_max  = np.maximum.accumulate(equity_arr)
    drawdowns    = (equity_arr - running_max) / running_max * 100
    max_drawdown = float(drawdowns.min())

    return {
        "symbol":            symbol,
        "timeframe":         timeframe,
        "bars_tested":       len(df) - 50,
        "initial_capital":   initial_capital,
        "final_capital":     round(capital, 2),
        "total_return_pct":  round(total_return, 2),
        "total_trades":      len(trades),
        "win_rate_pct":      round(win_rate, 1),
        "avg_win_pct":       round(avg_win, 2),
        "avg_loss_pct":      round(avg_loss, 2),
        "profit_factor":     round(profit_factor, 2),
        "max_drawdown_pct":  round(max_drawdown, 2),
        "trades":            trades[-10:],
    }


def format_backtest_message(result):
    if "error" in result:
        return f"❌ Backtest error: {result['error']}"
    pf   = f"{result['profit_factor']:.2f}" if result['profit_factor'] != float("inf") else "∞"
    sign = "+" if result["total_return_pct"] >= 0 else ""
    return (
        f"🔬 <b>BACKTEST — {result['symbol']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Timeframe:      {result['timeframe']} × {result['bars_tested']} bars\n"
        f"💰 Initial:        ${result['initial_capital']:,.2f}\n"
        f"💵 Final:          ${result['final_capital']:,.2f}\n"
        f"📊 Return:         {sign}{result['total_return_pct']}%\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔢 Trades:         {result['total_trades']}\n"
        f"🏆 Win Rate:       {result['win_rate_pct']}%\n"
        f"📈 Avg Win:        +{result['avg_win_pct']}%\n"
        f"📉 Avg Loss:       {result['avg_loss_pct']}%\n"
        f"⚖️ Profit Factor:  {pf}\n"
        f"🔻 Max Drawdown:   {result['max_drawdown_pct']}%\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <i>{config.DISCLAIMER}</i>"
    )
