"""
config.py - Central configuration for the Trading Bot
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "YOUR_CHAT_ID_HERE")

# ─── Trading Symbols ─────────────────────────────────────────────────────────
DEFAULT_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
]

# ─── Timeframe ───────────────────────────────────────────────────────────────
DEFAULT_TIMEFRAME = "5m"
CANDLE_LIMIT      = 200

# ─── Signal Engine ───────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD  = 70
AUTO_INTERVAL_SECONDS = 300

# ─── Strategy Weights (must sum to 1.0) ─────────────────────────────────────
STRATEGY_WEIGHTS = {
    "rsi":       0.20,
    "macd":      0.20,
    "ema":       0.20,
    "volume":    0.15,
    "breakout":  0.15,
    "ml_model":  0.10,
}

# ─── RSI ─────────────────────────────────────────────────────────────────────
RSI_PERIOD     = 14
RSI_OVERSOLD   = 30
RSI_OVERBOUGHT = 70

# ─── MACD ────────────────────────────────────────────────────────────────────
MACD_FAST   = 12
MACD_SLOW   = 26
MACD_SIGNAL = 9

# ─── EMA ─────────────────────────────────────────────────────────────────────
EMA_SHORT = 9
EMA_LONG  = 21
EMA_MID   = 50
EMA_TREND = 200

# ─── Volume ──────────────────────────────────────────────────────────────────
VOLUME_SPIKE_MULTIPLIER = 2.0
VOLUME_LOOKBACK         = 20

# ─── Breakout ────────────────────────────────────────────────────────────────
BREAKOUT_LOOKBACK = 20

# ─── Paper Trading ───────────────────────────────────────────────────────────
PAPER_TRADING         = True
PAPER_INITIAL_CAPITAL = 10_000.0

# ─── Logging / Files ─────────────────────────────────────────────────────────
LOG_DIR          = "logs"
TRADE_LOG_FILE   = "logs/trades.json"
SIGNAL_LOG_FILE  = "logs/signals.json"
PERF_LOG_FILE    = "logs/performance.json"

# ─── Daily Summary ───────────────────────────────────────────────────────────
DAILY_SUMMARY_HOUR = 20

# ─── Disclaimer ──────────────────────────────────────────────────────────────
DISCLAIMER = "⚠️ Not financial advice. Trade at your own risk."
