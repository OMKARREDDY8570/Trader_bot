"""
strategies/ema.py - EMA Crossover Strategy
"""

import pandas as pd
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)


def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def analyze(df):
    try:
        close  = df["close"]
        ema9   = calculate_ema(close, config.EMA_SHORT)
        ema21  = calculate_ema(close, config.EMA_LONG)
        ema50  = calculate_ema(close, config.EMA_MID)
        ema200 = calculate_ema(close, config.EMA_TREND)

        e9_now,  e9_prev  = ema9.iloc[-1],  ema9.iloc[-2]
        e21_now, e21_prev = ema21.iloc[-1], ema21.iloc[-2]
        e50_now  = ema50.iloc[-1]
        e200_now = ema200.iloc[-1]
        price    = close.iloc[-1]

        bull_trend = e50_now > e200_now
        bear_trend = e50_now < e200_now

        reasons   = []
        base_conf = 50
        signal    = "HOLD"

        if e9_prev <= e21_prev and e9_now > e21_now:
            signal, base_conf = "BUY", 70
            reasons.append("EMA9 crossed above EMA21 — bullish crossover")
        elif e9_prev >= e21_prev and e9_now < e21_now:
            signal, base_conf = "SELL", 70
            reasons.append("EMA9 crossed below EMA21 — bearish crossover")
        elif e9_now > e21_now:
            signal, base_conf = "BUY", 55
            reasons.append("EMA9 above EMA21 — short-term bullish")
        elif e9_now < e21_now:
            signal, base_conf = "SELL", 55
            reasons.append("EMA9 below EMA21 — short-term bearish")

        if signal == "BUY" and bull_trend:
            base_conf = min(95, base_conf + 15)
            reasons.append("EMA50 > EMA200 confirms bullish trend")
        elif signal == "SELL" and bear_trend:
            base_conf = min(95, base_conf + 15)
            reasons.append("EMA50 < EMA200 confirms bearish trend")
        elif signal != "HOLD":
            base_conf = max(40, base_conf - 10)
            reasons.append("Signal against major trend — lower confidence")

        if price > e50_now > e200_now:
            reasons.append("Price above EMA50 & EMA200 — strong uptrend")
        elif price < e50_now < e200_now:
            reasons.append("Price below EMA50 & EMA200 — strong downtrend")

        if not reasons:
            reasons.append("EMAs — no clear crossover signal")

        return {"signal": signal, "confidence": base_conf, "reason": "; ".join(reasons)}

    except Exception as e:
        logger.error(f"EMA error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"EMA error: {e}"}
