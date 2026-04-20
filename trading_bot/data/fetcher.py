"""
data/fetcher.py - Market data fetcher using Binance public API via CCXT
"""

import time
import logging
import ccxt
import pandas as pd
from functools import lru_cache
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)

# ─── Simple in-memory cache ──────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 60  # seconds


def _cache_key(symbol: str, timeframe: str, limit: int) -> str:
    return f"{symbol}:{timeframe}:{limit}"


def get_exchange() -> ccxt.Exchange:
    """Return a configured Binance public exchange instance."""
    exchange = ccxt.binance({
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    return exchange


def fetch_ohlcv(
    symbol: str,
    timeframe: str = config.DEFAULT_TIMEFRAME,
    limit: int = config.CANDLE_LIMIT,
    exchange: Optional[ccxt.Exchange] = None,
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV candlestick data.

    Returns a DataFrame with columns: timestamp, open, high, low, close, volume
    Returns None on error.
    """
    key = _cache_key(symbol, timeframe, limit)
    now = time.time()

    # Return cached data if still fresh
    if key in _cache:
        df, ts = _cache[key]
        if now - ts < CACHE_TTL:
            logger.debug(f"Cache hit for {key}")
            return df

    try:
        if exchange is None:
            exchange = get_exchange()

        raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not raw:
            logger.warning(f"No data returned for {symbol}")
            return None

        df = pd.DataFrame(
            raw, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.astype(
            {"open": float, "high": float, "low": float, "close": float, "volume": float}
        )
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

        _cache[key] = (df, now)
        logger.info(f"Fetched {len(df)} candles for {symbol} [{timeframe}]")
        return df

    except ccxt.NetworkError as e:
        logger.error(f"Network error fetching {symbol}: {e}")
    except ccxt.ExchangeError as e:
        logger.error(f"Exchange error fetching {symbol}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching {symbol}: {e}")

    return None


def get_ticker(symbol: str, exchange: Optional[ccxt.Exchange] = None) -> Optional[dict]:
    """Fetch current ticker (price, volume, change)."""
    try:
        if exchange is None:
            exchange = get_exchange()
        ticker = exchange.fetch_ticker(symbol)
        return ticker
    except Exception as e:
        logger.error(f"Error fetching ticker for {symbol}: {e}")
        return None


def get_current_price(symbol: str) -> Optional[float]:
    """Return the latest close price for a symbol."""
    ticker = get_ticker(symbol)
    if ticker:
        return ticker.get("last")
    return None


def clear_cache():
    """Clear the data cache."""
    global _cache
    _cache = {}
    logger.info("Data cache cleared")
