"""
strategies/macd.py - MACD Crossover Strategy
"""

import pandas as pd
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def calculate_macd(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Compute MACD line, Signal line, and Histogram.
    Returns: (macd, signal, histogram)
    """
    ema_fast   = series.ewm(span=config.MACD_FAST,   adjust=False).mean()
    ema_slow   = series.ewm(span=config.MACD_SLOW,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=config.MACD_SIGNAL, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def analyze(df: pd.DataFrame) -> dict:
    """
    MACD Strategy Analysis.

    Returns:
        dict with keys: signal, confidence, reason
    """
    try:
        macd, signal_line, histogram = calculate_macd(df["close"])

        macd_now  = macd.iloc[-1]
        macd_prev = macd.iloc[-2]
        sig_now   = signal_line.iloc[-1]
        sig_prev  = signal_line.iloc[-2]
        hist_now  = histogram.iloc[-1]
        hist_prev = histogram.iloc[-2]

        result = {"signal": "HOLD", "confidence": 50, "reason": "MACD — no clear crossover"}

        # Golden cross: MACD crosses above Signal
        if macd_prev <= sig_prev and macd_now > sig_now:
            confidence = 75
            above_zero = macd_now > 0
            if above_zero:
                confidence = 85
            reason = (
                f"MACD bullish crossover ({'above' if above_zero else 'below'} zero line), "
                f"MACD={macd_now:.4f}, Signal={sig_now:.4f}"
            )
            result = {"signal": "BUY", "confidence": confidence, "reason": reason}

        # Death cross: MACD crosses below Signal
        elif macd_prev >= sig_prev and macd_now < sig_now:
            confidence = 75
            below_zero = macd_now < 0
            if below_zero:
                confidence = 85
            reason = (
                f"MACD bearish crossover ({'below' if below_zero else 'above'} zero line), "
                f"MACD={macd_now:.4f}, Signal={sig_now:.4f}"
            )
            result = {"signal": "SELL", "confidence": confidence, "reason": reason}

        # Histogram expansion (trend strengthening)
        elif hist_now > 0 and hist_now > hist_prev:
            result = {
                "signal":     "BUY",
                "confidence": 55,
                "reason":     f"MACD histogram expanding bullishly ({hist_now:.4f})",
            }

        elif hist_now < 0 and hist_now < hist_prev:
            result = {
                "signal":     "SELL",
                "confidence": 55,
                "reason":     f"MACD histogram expanding bearishly ({hist_now:.4f})",
            }

        return result

    except Exception as e:
        logger.error(f"MACD analysis error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"MACD error: {e}"}
