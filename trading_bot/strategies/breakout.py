"""
strategies/breakout.py - Support/Resistance Breakout Strategy
"""

import pandas as pd
import numpy as np
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def find_levels(df: pd.DataFrame, lookback: int = config.BREAKOUT_LOOKBACK) -> tuple[float, float]:
    """
    Identify support and resistance from recent swing highs/lows.
    Returns (support, resistance).
    """
    window = df.iloc[-lookback - 1:-1]  # exclude current candle
    resistance = window["high"].max()
    support    = window["low"].min()
    return support, resistance


def analyze(df: pd.DataFrame) -> dict:
    """
    Breakout Strategy Analysis.

    BUY  when price breaks above resistance.
    SELL when price breaks below support.

    Returns:
        dict with keys: signal, confidence, reason
    """
    try:
        support, resistance = find_levels(df)
        current_close = df["close"].iloc[-1]
        prev_close    = df["close"].iloc[-2]
        current_high  = df["high"].iloc[-1]
        current_low   = df["low"].iloc[-1]

        channel_width = resistance - support
        channel_pct   = (channel_width / support * 100) if support > 0 else 0

        signal     = "HOLD"
        confidence = 40
        reason     = (
            f"Price ${current_close:.4f} within range "
            f"[${support:.4f} - ${resistance:.4f}]"
        )

        # ── Bullish breakout ──────────────────────────────────────────────────
        if current_close > resistance and prev_close <= resistance:
            breakout_pct = ((current_close - resistance) / resistance) * 100
            confidence   = min(90, 70 + int(breakout_pct * 5))
            signal       = "BUY"
            reason       = (
                f"Bullish breakout above resistance ${resistance:.4f} "
                f"(+{breakout_pct:.2f}% through level)"
            )

        # ── Bearish breakdown ─────────────────────────────────────────────────
        elif current_close < support and prev_close >= support:
            breakdown_pct = ((support - current_close) / support) * 100
            confidence    = min(90, 70 + int(breakdown_pct * 5))
            signal        = "SELL"
            reason        = (
                f"Bearish breakdown below support ${support:.4f} "
                f"(-{breakdown_pct:.2f}% through level)"
            )

        # ── Near resistance (potential sell zone) ─────────────────────────────
        elif channel_width > 0:
            pct_in_channel = (current_close - support) / channel_width
            if pct_in_channel >= 0.85:
                signal     = "SELL"
                confidence = 55
                reason     = f"Price near resistance (top {((1 - pct_in_channel)*100):.1f}% of range)"
            elif pct_in_channel <= 0.15:
                signal     = "BUY"
                confidence = 55
                reason     = f"Price near support (bottom {(pct_in_channel*100):.1f}% of range)"

        return {"signal": signal, "confidence": int(confidence), "reason": reason}

    except Exception as e:
        logger.error(f"Breakout analysis error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"Breakout error: {e}"}
