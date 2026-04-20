"""
data/fetcher.py - Market data fetcher using Binance public API via CCXT
"""

import time
import logging
import ccxt
import pandas as pd
from typing import Optional

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)

_cache: dict = {}
CACHE_TTL = 60


def _cache_key(symbol, timeframe, limit):
    return f"{symbol}:{timeframe}:{limit}"


def get_exchange():
    return ccxt.binance({
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })


def fetch_ohlcv(symbol, timeframe=config.DEFAULT_TIMEFRAME, limit=config.CANDLE_LIMIT, exchange=None):
    key = _cache_key(symbol, timeframe, limit)
    now = time.time()
    if key in _cache:
        df, ts = _cache[key]
        if now - ts < CACHE_TTL:
            return df
    try:
        if exchange is None:
            exchange = get_exchange()
        raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not raw:
            return None
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        _cache[key] = (df, now)
        logger.info(f"Fetched {len(df)} candles for {symbol} [{timeframe}]")
        return df
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return None


def get_ticker(symbol, exchange=None):
    try:
        if exchange is None:
            exchange = get_exchange()
        return exchange.fetch_ticker(symbol)
    except Exception as e:
        logger.error(f"Error fetching ticker for {symbol}: {e}")
        return None


def get_current_price(symbol):
    ticker = get_ticker(symbol)
    return ticker.get("last") if ticker else None


def clear_cache():
    global _cache
    _cache = {}
