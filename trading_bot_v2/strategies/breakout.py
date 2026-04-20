"""
strategies/breakout.py - Support/Resistance Breakout Strategy
"""

import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def find_levels(df, lookback=config.BREAKOUT_LOOKBACK):
    window     = df.iloc[-lookback - 1:-1]
    resistance = window["high"].max()
    support    = window["low"].min()
    return support, resistance


def analyze(df):
    try:
        support, resistance   = find_levels(df)
        current_close = df["close"].iloc[-1]
        prev_close    = df["close"].iloc[-2]
        channel_width = resistance - support

        if current_close > resistance and prev_close <= resistance:
            pct  = ((current_close - resistance) / resistance) * 100
            conf = min(90, 70 + int(pct * 5))
            return {"signal": "BUY",  "confidence": conf,
                    "reason": f"Bullish breakout above resistance ${resistance:.4f} (+{pct:.2f}%)"}

        elif current_close < support and prev_close >= support:
            pct  = ((support - current_close) / support) * 100
            conf = min(90, 70 + int(pct * 5))
            return {"signal": "SELL", "confidence": conf,
                    "reason": f"Bearish breakdown below support ${support:.4f} (-{pct:.2f}%)"}

        elif channel_width > 0:
            pct_in = (current_close - support) / channel_width
            if pct_in >= 0.85:
                return {"signal": "SELL", "confidence": 55,
                        "reason": f"Price near resistance (top {(1-pct_in)*100:.1f}% of range)"}
            elif pct_in <= 0.15:
                return {"signal": "BUY",  "confidence": 55,
                        "reason": f"Price near support (bottom {pct_in*100:.1f}% of range)"}

        return {"signal": "HOLD", "confidence": 40,
                "reason": f"Price within range [${support:.4f} - ${resistance:.4f}]"}

    except Exception as e:
        logger.error(f"Breakout error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"Breakout error: {e}"}
