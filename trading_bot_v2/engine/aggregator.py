"""
engine/aggregator.py - Ensemble signal aggregation with weighted voting
"""

import logging
import json
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from strategies import rsi, macd, ema, volume, breakout, ml_model

logger = logging.getLogger(__name__)

STRATEGIES = {
    "rsi":      rsi,
    "macd":     macd,
    "ema":      ema,
    "volume":   volume,
    "breakout": breakout,
    "ml_model": ml_model,
}

RISK_LEVELS = {
    (0,  40): "Very Low",
    (40, 55): "Low",
    (55, 70): "Medium",
    (70, 85): "High",
    (85, 101): "Very High",
}


def _get_risk_level(confidence):
    for (lo, hi), label in RISK_LEVELS.items():
        if lo <= confidence < hi:
            return label
    return "Unknown"


def _adjust_weights():
    weights = dict(config.STRATEGY_WEIGHTS)
    try:
        if not os.path.exists(config.PERF_LOG_FILE):
            return weights
        with open(config.PERF_LOG_FILE) as f:
            perf = json.load(f)
        adjusted = {}
        total = 0
        for name, w in weights.items():
            win_rate = perf.get(name, {}).get("win_rate", 0.5)
            factor   = 0.5 + win_rate
            adjusted[name] = w * factor
            total += adjusted[name]
        return {k: v / total for k, v in adjusted.items()}
    except Exception:
        return weights


def run_all_strategies(df):
    results = {}
    for name, module in STRATEGIES.items():
        try:
            results[name] = module.analyze(df)
        except Exception as e:
            logger.error(f"Strategy {name} failed: {e}")
            results[name] = {"signal": "HOLD", "confidence": 0, "reason": str(e)}
    return results


def aggregate(df, symbol="ASSET"):
    strategy_results = run_all_strategies(df)
    weights = _adjust_weights()

    buy_score = sell_score = hold_score = 0.0

    for name, result in strategy_results.items():
        w    = weights.get(name, 0)
        sig  = result.get("signal", "HOLD")
        conf = result.get("confidence", 0) / 100.0
        wc   = w * conf
        if sig == "BUY":   buy_score  += wc
        elif sig == "SELL": sell_score += wc
        else:               hold_score += wc

    total    = buy_score + sell_score + hold_score or 1.0
    buy_pct  = (buy_score  / total) * 100
    sell_pct = (sell_score / total) * 100
    hold_pct = (hold_score / total) * 100

    if buy_pct > sell_pct and buy_pct > hold_pct:
        final_signal, final_conf = "BUY",  int(buy_pct)
    elif sell_pct > buy_pct and sell_pct > hold_pct:
        final_signal, final_conf = "SELL", int(sell_pct)
    else:
        final_signal, final_conf = "HOLD", int(hold_pct)

    return {
        "symbol":             symbol,
        "signal":             final_signal,
        "confidence":         final_conf,
        "risk_level":         _get_risk_level(final_conf),
        "current_price":      float(df["close"].iloc[-1]),
        "buy_score":          round(buy_pct,  2),
        "sell_score":         round(sell_pct, 2),
        "hold_score":         round(hold_pct, 2),
        "individual_results": strategy_results,
        "weights_used":       {k: round(v, 4) for k, v in weights.items()},
    }
