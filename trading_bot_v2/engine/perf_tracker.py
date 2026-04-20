"""
engine/perf_tracker.py - Strategy performance tracker
"""

import json
import os
import logging
from datetime import datetime, timezone
from collections import defaultdict

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def load_performance():
    if os.path.exists(config.PERF_LOG_FILE):
        try:
            with open(config.PERF_LOG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_performance(perf):
    os.makedirs(config.LOG_DIR, exist_ok=True)
    with open(config.PERF_LOG_FILE, "w") as f:
        json.dump(perf, f, indent=2)


def compute_daily_summary():
    if not os.path.exists(config.SIGNAL_LOG_FILE):
        return {}
    try:
        with open(config.SIGNAL_LOG_FILE) as f:
            signals = json.load(f)
    except Exception:
        return {}

    today         = str(datetime.now(timezone.utc).date())
    today_signals = [s for s in signals if s.get("generated_at", "").startswith(today)]
    by_signal     = defaultdict(int)
    confidences   = []

    for s in today_signals:
        by_signal[s.get("signal", "HOLD")] += 1
        confidences.append(s.get("confidence", 0))

    return {
        "date":           today,
        "total_signals":  len(today_signals),
        "buy_signals":    by_signal["BUY"],
        "sell_signals":   by_signal["SELL"],
        "hold_signals":   by_signal["HOLD"],
        "avg_confidence": round(sum(confidences) / len(confidences), 1) if confidences else 0,
    }


def format_daily_summary_message():
    from engine.paper_trader import get_portfolio_summary
    summary   = compute_daily_summary()
    portfolio = get_portfolio_summary()
    if not summary:
        return "📊 No signals recorded today."
    sign = "+" if portfolio["total_pnl"] >= 0 else ""
    return (
        f"📅 <b>DAILY SUMMARY — {summary['date']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total Signals:    {summary['total_signals']}\n"
        f"📈 BUY Signals:      {summary['buy_signals']}\n"
        f"📉 SELL Signals:     {summary['sell_signals']}\n"
        f"⏸ HOLD Signals:     {summary['hold_signals']}\n"
        f"🎯 Avg Confidence:   {summary['avg_confidence']}%\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💼 Portfolio PnL:    {sign}${portfolio['total_pnl']:,.2f}\n"
        f"🏆 Win Rate:         {portfolio['win_rate']}%\n"
        f"🔢 Total Trades:     {portfolio['total_trades']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <i>{config.DISCLAIMER}</i>"
    )
