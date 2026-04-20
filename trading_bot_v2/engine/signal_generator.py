"""
engine/signal_generator.py - Generates and formats trading signals
"""

import json
import logging
import os
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from data import fetcher
from engine import aggregator
from engine import paper_trader

logger = logging.getLogger(__name__)

SIGNAL_EMOJI = {"BUY": "📈", "SELL": "📉", "HOLD": "⏸"}
RISK_EMOJI   = {"Very Low": "🟢", "Low": "🟡", "Medium": "🟠", "High": "🔴", "Very High": "⛔"}


def generate_signal(symbol):
    df = fetcher.fetch_ohlcv(symbol)
    if df is None or len(df) < 50:
        logger.warning(f"Insufficient data for {symbol}")
        return None
    result = aggregator.aggregate(df, symbol)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    _log_signal(result)
    if config.PAPER_TRADING and result["confidence"] >= config.CONFIDENCE_THRESHOLD:
        paper_trader.record_trade(result)
    return result


def format_signal_message(result):
    signal = result["signal"]
    conf   = result["confidence"]
    symbol = result["symbol"]
    price  = result["current_price"]
    risk   = result["risk_level"]
    ts     = result.get("generated_at", "")

    reasons = []
    for name, r in result["individual_results"].items():
        if r["signal"] == signal and r.get("confidence", 0) >= 50:
            reasons.append(f"• {r['reason']}")
    if not reasons:
        for name, r in result["individual_results"].items():
            reasons.append(f"• [{name.upper()}] {r['reason']}")

    score_bar = (
        f"BUY {result['buy_score']:.0f}%  |  "
        f"HOLD {result['hold_score']:.0f}%  |  "
        f"SELL {result['sell_score']:.0f}%"
    )

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ASSET:</b> {symbol}\n"
        f"💰 <b>Price:</b> ${price:,.4f}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{SIGNAL_EMOJI.get(signal,'❓')} <b>SIGNAL:</b> {signal}\n"
        f"🎯 <b>CONFIDENCE:</b> {conf}%\n"
        f"{RISK_EMOJI.get(risk,'❓')} <b>RISK LEVEL:</b> {risk}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>REASONS:</b>\n{chr(10).join(reasons[:5])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚖️ <b>VOTE SCORES:</b>\n{score_bar}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {ts[:19].replace('T',' ')} UTC\n"
        f"⚠️ <i>{config.DISCLAIMER}</i>"
    )


def generate_all_signals(symbols=None):
    if symbols is None:
        symbols = config.DEFAULT_SYMBOLS
    results = []
    for symbol in symbols:
        result = generate_signal(symbol)
        if result:
            results.append(result)
    return results


def _log_signal(result):
    os.makedirs(config.LOG_DIR, exist_ok=True)
    logs = []
    if os.path.exists(config.SIGNAL_LOG_FILE):
        try:
            with open(config.SIGNAL_LOG_FILE) as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(result)
    logs = logs[-500:]
    with open(config.SIGNAL_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)
