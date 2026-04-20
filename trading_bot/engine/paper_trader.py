"""
engine/paper_trader.py - Paper trading simulation
Tracks virtual trades without real money
"""

import json
import os
import logging
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)

STATE_FILE = "logs/paper_state.json"

DEFAULT_STATE = {
    "capital":    config.PAPER_INITIAL_CAPITAL,
    "positions":  {},   # symbol → {qty, entry_price, entry_signal}
    "trade_log":  [],
    "total_pnl":  0.0,
    "win_count":  0,
    "loss_count": 0,
}


def _load_state() -> dict:
    os.makedirs(config.LOG_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return dict(DEFAULT_STATE)


def _save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def record_trade(signal_result: dict):
    """
    Simulate a trade based on signal.
    - BUY  → open/add to position
    - SELL → close position if open
    - HOLD → no action
    """
    state  = _load_state()
    symbol = signal_result["symbol"]
    signal = signal_result["signal"]
    price  = signal_result["current_price"]
    ts     = datetime.now(timezone.utc).isoformat()

    positions = state.get("positions", {})

    if signal == "BUY" and symbol not in positions:
        # Allocate 10% of capital per trade
        allocation = state["capital"] * 0.10
        qty        = allocation / price if price > 0 else 0

        if qty > 0 and state["capital"] >= allocation:
            positions[symbol] = {
                "qty":          qty,
                "entry_price":  price,
                "entry_signal": signal_result["confidence"],
                "entry_time":   ts,
            }
            state["capital"] -= allocation
            trade_record = {
                "type":   "BUY",
                "symbol": symbol,
                "price":  price,
                "qty":    qty,
                "time":   ts,
                "confidence": signal_result["confidence"],
            }
            state["trade_log"].append(trade_record)
            logger.info(f"[PAPER] BUY {qty:.6f} {symbol} @ ${price:.4f}")

    elif signal == "SELL" and symbol in positions:
        pos        = positions.pop(symbol)
        qty        = pos["qty"]
        entry      = pos["entry_price"]
        pnl        = (price - entry) * qty
        pnl_pct    = ((price - entry) / entry) * 100 if entry > 0 else 0

        state["capital"] += qty * price
        state["total_pnl"] = state.get("total_pnl", 0) + pnl

        if pnl > 0:
            state["win_count"] = state.get("win_count", 0) + 1
        else:
            state["loss_count"] = state.get("loss_count", 0) + 1

        trade_record = {
            "type":    "SELL",
            "symbol":  symbol,
            "price":   price,
            "qty":     qty,
            "pnl":     round(pnl, 4),
            "pnl_pct": round(pnl_pct, 2),
            "time":    ts,
        }
        state["trade_log"].append(trade_record)
        logger.info(
            f"[PAPER] SELL {qty:.6f} {symbol} @ ${price:.4f} | PnL: ${pnl:.2f} ({pnl_pct:.1f}%)"
        )

    state["positions"] = positions
    state["trade_log"] = state["trade_log"][-200:]
    _save_state(state)


def get_portfolio_summary() -> dict:
    """Return current paper trading portfolio status."""
    state = _load_state()
    wins  = state.get("win_count", 0)
    losses = state.get("loss_count", 0)
    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    return {
        "capital":      round(state["capital"], 2),
        "initial":      config.PAPER_INITIAL_CAPITAL,
        "total_pnl":    round(state.get("total_pnl", 0), 2),
        "positions":    state.get("positions", {}),
        "open_trades":  len(state.get("positions", {})),
        "win_count":    wins,
        "loss_count":   losses,
        "win_rate":     round(win_rate, 1),
        "total_trades": total_trades,
        "last_trades":  state.get("trade_log", [])[-5:],
    }


def format_portfolio_message() -> str:
    p = get_portfolio_summary()
    pnl_sign = "+" if p["total_pnl"] >= 0 else ""
    pos_str  = "\n".join(
        [f"  • {sym}: {data['qty']:.6f} @ ${data['entry_price']:.4f}"
         for sym, data in p["positions"].items()]
    ) or "  None"

    return (
        f"💼 <b>PAPER PORTFOLIO</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Capital:     ${p['capital']:,.2f}\n"
        f"📊 Total PnL:   {pnl_sign}${p['total_pnl']:,.2f}\n"
        f"🏆 Win Rate:    {p['win_rate']}% ({p['win_count']}W / {p['loss_count']}L)\n"
        f"📂 Open Trades: {p['open_trades']}\n"
        f"{pos_str}\n"
        f"⚠️ <i>{config.DISCLAIMER}</i>"
    )
