"""
strategies/rsi.py - RSI Strategy
"""

import pandas as pd
import numpy as np
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def calculate_rsi(series, period=config.RSI_PERIOD):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0.0)
    loss  = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def analyze(df):
    try:
        rsi         = calculate_rsi(df["close"])
        current_rsi = rsi.iloc[-1]
        prev_rsi    = rsi.iloc[-2]

        if current_rsi <= config.RSI_OVERSOLD:
            depth      = config.RSI_OVERSOLD - current_rsi
            confidence = min(95, 60 + int(depth * 1.5))
            reason     = f"RSI oversold at {current_rsi:.1f}"
            if prev_rsi < current_rsi:
                confidence = min(95, confidence + 5)
                reason += " — momentum recovering"
            return {"signal": "BUY", "confidence": confidence, "reason": reason}

        elif current_rsi >= config.RSI_OVERBOUGHT:
            depth      = current_rsi - config.RSI_OVERBOUGHT
            confidence = min(95, 60 + int(depth * 1.5))
            reason     = f"RSI overbought at {current_rsi:.1f}"
            if prev_rsi > current_rsi:
                confidence = min(95, confidence + 5)
                reason += " — momentum fading"
            return {"signal": "SELL", "confidence": confidence, "reason": reason}

        elif 45 <= current_rsi <= 55:
            return {"signal": "HOLD", "confidence": 40, "reason": f"RSI neutral at {current_rsi:.1f}"}

        elif current_rsi < 45:
            return {"signal": "BUY",  "confidence": 45, "reason": f"RSI mildly bearish at {current_rsi:.1f}"}

        else:
            return {"signal": "SELL", "confidence": 45, "reason": f"RSI mildly bullish at {current_rsi:.1f}"}

    except Exception as e:
        logger.error(f"RSI error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"RSI error: {e}"}
