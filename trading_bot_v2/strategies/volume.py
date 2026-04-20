"""
strategies/volume.py - Volume Spike Detection Strategy
"""

import numpy as np
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def analyze(df):
    try:
        close  = df["close"]
        volume = df["volume"]

        avg_vol   = volume.iloc[-config.VOLUME_LOOKBACK:-1].mean()
        curr_vol  = volume.iloc[-1]
        vol_ratio = curr_vol / avg_vol if avg_vol > 0 else 1.0

        price_change     = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
        is_bullish       = price_change > 0
        spike            = vol_ratio >= config.VOLUME_SPIKE_MULTIPLIER

        if spike:
            bonus = min(20, int((vol_ratio - 2) * 5))
            if is_bullish:
                return {"signal": "BUY",  "confidence": min(90, 65 + bonus),
                        "reason": f"Volume spike {vol_ratio:.1f}x avg with bullish candle (+{price_change*100:.2f}%)"}
            else:
                return {"signal": "SELL", "confidence": min(90, 65 + bonus),
                        "reason": f"Volume spike {vol_ratio:.1f}x avg with bearish candle ({price_change*100:.2f}%)"}

        elif vol_ratio > 1.3:
            sig = "BUY" if is_bullish else "SELL"
            return {"signal": sig, "confidence": 50,
                    "reason": f"Mild volume increase ({vol_ratio:.1f}x) on {'green' if is_bullish else 'red'} candle"}

        recent_vols = volume.iloc[-5:]
        vol_trend   = np.polyfit(range(len(recent_vols)), recent_vols.values, 1)[0]
        conf        = 35 if vol_trend < 0 else 40
        return {"signal": "HOLD", "confidence": conf,
                "reason": f"Volume {vol_ratio:.1f}x avg — no significant spike"}

    except Exception as e:
        logger.error(f"Volume error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"Volume error: {e}"}
