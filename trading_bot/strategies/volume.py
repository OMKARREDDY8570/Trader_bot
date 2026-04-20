"""
strategies/volume.py - Volume Spike Detection Strategy
"""

import pandas as pd
import numpy as np
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def analyze(df: pd.DataFrame) -> dict:
    """
    Volume Spike Detection Strategy.

    A volume spike combined with price direction gives BUY/SELL bias.

    Returns:
        dict with keys: signal, confidence, reason
    """
    try:
        close  = df["close"]
        volume = df["volume"]

        avg_vol   = volume.iloc[-config.VOLUME_LOOKBACK:-1].mean()
        curr_vol  = volume.iloc[-1]
        vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1.0

        price_change    = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
        is_bullish_candle = price_change > 0

        spike   = vol_ratio >= config.VOLUME_SPIKE_MULTIPLIER
        signal  = "HOLD"
        confidence = 40
        reason  = f"Volume {vol_ratio:.1f}x avg — no significant spike"

        if spike:
            multiplier_bonus = min(20, int((vol_ratio - 2) * 5))

            if is_bullish_candle:
                signal     = "BUY"
                confidence = min(90, 65 + multiplier_bonus)
                reason     = (
                    f"Volume spike {vol_ratio:.1f}x avg with bullish candle "
                    f"(+{price_change * 100:.2f}%) — accumulation signal"
                )
            else:
                signal     = "SELL"
                confidence = min(90, 65 + multiplier_bonus)
                reason     = (
                    f"Volume spike {vol_ratio:.1f}x avg with bearish candle "
                    f"({price_change * 100:.2f}%) — distribution/dump signal"
                )
        elif vol_ratio > 1.3:
            # Mild volume increase
            if is_bullish_candle:
                signal     = "BUY"
                confidence = 50
                reason     = f"Mild volume increase ({vol_ratio:.1f}x) on green candle"
            else:
                signal     = "SELL"
                confidence = 50
                reason     = f"Mild volume increase ({vol_ratio:.1f}x) on red candle"

        # Decreasing volume = weakening trend
        recent_vols = volume.iloc[-5:]
        vol_trend = np.polyfit(range(len(recent_vols)), recent_vols.values, 1)[0]
        if vol_trend < 0 and not spike:
            confidence = max(30, confidence - 10)
            reason += " | Volume declining — trend weakening"

        return {"signal": signal, "confidence": int(confidence), "reason": reason}

    except Exception as e:
        logger.error(f"Volume analysis error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"Volume error: {e}"}
