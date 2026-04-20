"""
engine/aggregator.py - Ensemble signal aggregation with weighted voting
"""

import logging
import pandas as pd
from typing import Optional

import sys, os
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

SIGNAL_VALUES = {"BUY": 1, "HOLD": 0, "SELL": -1}
RISK_LEVELS   = {
    (0,  40): "Very Low",
    (40, 55): "Low",
    (55, 70): "Medium",
    (70, 85): "High",
    (85, 101): "Very High",
}


def _get_risk_level(confidence: float) -> str:
    for (lo, hi), label in RISK_LEVELS.items():
        if lo <= confidence < hi:
            return label
    return "Unknown"


def _adjust_weights_for_performance(weights: dict) -> dict:
    """
    Dynamically adjust weights based on recent strategy performance.
    Reads from performance log if available.
    """
    try:
        import json
        if not os.path.exists(config.PERF_LOG_FILE):
            return weights

        with open(config.PERF_LOG_FILE) as f:
            perf = json.load(f)

        adjusted = {}
        total = 0
        for name, w in weights.items():
            win_rate = perf.get(name, {}).get("win_rate", 0.5)
            # Boost good performers, penalize bad ones
            factor = 0.5 + win_rate   # range [0.5, 1.5]
            adjusted[name] = w * factor
            total += adjusted[name]

        # Re-normalize
        adjusted = {k: v / total for k, v in adjusted.items()}
        return adjusted

    except Exception:
        return weights


def run_all_strategies(df: pd.DataFrame) -> dict:
    """
    Run every strategy against the OHLCV dataframe.
    Returns a dict of strategy_name → result_dict
    """
    results = {}
    for name, module in STRATEGIES.items():
        try:
            result = module.analyze(df)
            results[name] = result
            logger.debug(f"[{name.upper()}] {result}")
        except Exception as e:
            logger.error(f"Strategy {name} failed: {e}")
            results[name] = {"signal": "HOLD", "confidence": 0, "reason": str(e)}
    return results


def aggregate(df: pd.DataFrame, symbol: str = "ASSET") -> dict:
    """
    Run all strategies and produce a single ensemble signal.

    Returns:
        {
          symbol, signal, confidence, risk_level,
          individual_results, buy_score, sell_score, hold_score
        }
    """
    strategy_results = run_all_strategies(df)
    weights = _adjust_weights_for_performance(dict(config.STRATEGY_WEIGHTS))

    buy_score  = 0.0
    sell_score = 0.0
    hold_score = 0.0

    for name, result in strategy_results.items():
        w   = weights.get(name, 0)
        sig = result.get("signal", "HOLD")
        conf = result.get("confidence", 0) / 100.0  # normalize to 0-1

        weighted_conf = w * conf

        if sig == "BUY":
            buy_score  += weighted_conf
        elif sig == "SELL":
            sell_score += weighted_conf
        else:
            hold_score += weighted_conf

    total = buy_score + sell_score + hold_score or 1.0
    buy_pct  = (buy_score  / total) * 100
    sell_pct = (sell_score / total) * 100
    hold_pct = (hold_score / total) * 100

    # Determine final signal
    if buy_pct > sell_pct and buy_pct > hold_pct:
        final_signal     = "BUY"
        final_confidence = int(buy_pct)
    elif sell_pct > buy_pct and sell_pct > hold_pct:
        final_signal     = "SELL"
        final_confidence = int(sell_pct)
    else:
        final_signal     = "HOLD"
        final_confidence = int(hold_pct)

    risk_level = _get_risk_level(final_confidence)

    # Current price
    current_price = float(df["close"].iloc[-1])

    return {
        "symbol":             symbol,
        "signal":             final_signal,
        "confidence":         final_confidence,
        "risk_level":         risk_level,
        "current_price":      current_price,
        "buy_score":          round(buy_pct,  2),
        "sell_score":         round(sell_pct, 2),
        "hold_score":         round(hold_pct, 2),
        "individual_results": strategy_results,
        "weights_used":       {k: round(v, 4) for k, v in weights.items()},
    }
