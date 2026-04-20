"""
strategies/ema.py - EMA Crossover Strategy (9/21 and 50/200)
"""

import pandas as pd
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def analyze(df: pd.DataFrame) -> dict:
    """
    EMA Crossover Strategy Analysis.

    Uses:
      - Short-term: EMA9 / EMA21
      - Long-term (trend filter): EMA50 / EMA200

    Returns:
        dict with keys: signal, confidence, reason
    """
    try:
        close  = df["close"]
        ema9   = calculate_ema(close, config.EMA_SHORT)
        ema21  = calculate_ema(close, config.EMA_LONG)
        ema50  = calculate_ema(close, config.EMA_MID)
        ema200 = calculate_ema(close, config.EMA_TREND)

        e9_now,  e9_prev   = ema9.iloc[-1],   ema9.iloc[-2]
        e21_now, e21_prev  = ema21.iloc[-1],  ema21.iloc[-2]
        e50_now            = ema50.iloc[-1]
        e200_now           = ema200.iloc[-1]
        price_now          = close.iloc[-1]

        # Trend filter
        bull_trend = e50_now > e200_now   # Golden cross on slower EMAs
        bear_trend = e50_now < e200_now

        reasons = []
        base_conf = 50
        signal = "HOLD"

        # Short-term crossover
        short_bull_cross = e9_prev <= e21_prev and e9_now > e21_now
        short_bear_cross = e9_prev >= e21_prev and e9_now < e21_now

        if short_bull_cross:
            signal    = "BUY"
            base_conf = 70
            reasons.append(f"EMA9 crossed above EMA21 (bullish crossover)")
        elif short_bear_cross:
            signal    = "SELL"
            base_conf = 70
            reasons.append(f"EMA9 crossed below EMA21 (bearish crossover)")
        elif e9_now > e21_now:
            signal    = "BUY"
            base_conf = 55
            reasons.append(f"EMA9 above EMA21 — short-term bullish")
        elif e9_now < e21_now:
            signal    = "SELL"
            base_conf = 55
            reasons.append(f"EMA9 below EMA21 — short-term bearish")

        # Align with long-term trend
        if signal == "BUY" and bull_trend:
            base_conf = min(95, base_conf + 15)
            reasons.append(f"EMA50 > EMA200 confirms bullish trend")
        elif signal == "SELL" and bear_trend:
            base_conf = min(95, base_conf + 15)
            reasons.append(f"EMA50 < EMA200 confirms bearish trend")
        elif signal != "HOLD":
            base_conf = max(40, base_conf - 10)
            reasons.append(f"Signal against major trend — lower confidence")

        # Price above/below key EMAs
        if price_now > e50_now > e200_now:
            reasons.append(f"Price above EMA50 & EMA200 — strong uptrend")
        elif price_now < e50_now < e200_now:
            reasons.append(f"Price below EMA50 & EMA200 — strong downtrend")

        if not reasons:
            reasons.append("EMAs — no clear crossover signal")

        return {
            "signal":     signal,
            "confidence": base_conf,
            "reason":     "; ".join(reasons),
        }

    except Exception as e:
        logger.error(f"EMA analysis error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"EMA error: {e}"}
