"""
strategies/ml_model.py - Lightweight ML Strategy (Logistic Regression)

Features used:
  - RSI
  - MACD histogram
  - EMA9/EMA21 spread
  - Volume ratio
  - 5-bar return
  - ATR-normalized candle body
"""

import numpy as np
import pandas as pd
import logging
import pickle
import os

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

logger = logging.getLogger(__name__)

MODEL_FILE  = "logs/ml_model.pkl"
SCALER_FILE = "logs/ml_scaler.pkl"

# Minimum bars required before training
MIN_TRAIN_BARS = 60


def _compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute feature matrix for ML model."""
    close  = df["close"]
    volume = df["volume"]
    high   = df["high"]
    low    = df["low"]

    # RSI
    delta   = close.diff()
    gain    = delta.where(delta > 0, 0).ewm(com=13, min_periods=14).mean()
    loss    = (-delta.where(delta < 0, 0)).ewm(com=13, min_periods=14).mean()
    rs      = gain / loss.replace(0, np.nan)
    rsi     = 100 - (100 / (1 + rs))

    # MACD histogram
    ema12   = close.ewm(span=12, adjust=False).mean()
    ema26   = close.ewm(span=26, adjust=False).mean()
    macd    = ema12 - ema26
    sig     = macd.ewm(span=9, adjust=False).mean()
    hist    = macd - sig

    # EMA spread
    ema9    = close.ewm(span=9,  adjust=False).mean()
    ema21   = close.ewm(span=21, adjust=False).mean()
    ema_spread = (ema9 - ema21) / close

    # Volume ratio
    avg_vol = volume.rolling(20).mean()
    vol_ratio = volume / avg_vol.replace(0, np.nan)

    # 5-bar momentum
    momentum = close.pct_change(5)

    # ATR-normalized body
    atr  = (high - low).rolling(14).mean()
    body = (close - close.shift(1)).abs() / atr.replace(0, np.nan)

    feats = pd.DataFrame({
        "rsi":        rsi,
        "macd_hist":  hist,
        "ema_spread": ema_spread,
        "vol_ratio":  vol_ratio,
        "momentum":   momentum,
        "body":       body,
    })

    return feats.dropna()


def _generate_labels(df: pd.DataFrame, forward_bars: int = 3, threshold: float = 0.005) -> pd.Series:
    """
    Generate labels based on forward returns.
    1 = BUY, -1 = SELL, 0 = HOLD
    """
    fwd_return = df["close"].shift(-forward_bars) / df["close"] - 1
    labels = pd.Series(0, index=df.index)
    labels[fwd_return >  threshold] = 1
    labels[fwd_return < -threshold] = -1
    return labels


def train_model(df: pd.DataFrame) -> tuple:
    """Train the logistic regression on historical data."""
    feats  = _compute_features(df)
    labels = _generate_labels(df)

    # Align
    common = feats.index.intersection(labels.index)
    X = feats.loc[common].values
    y = labels.loc[common].values

    # Remove future-lookahead rows (last forward_bars rows)
    X = X[:-3]
    y = y[:-3]

    if len(X) < MIN_TRAIN_BARS:
        logger.warning(f"Not enough data to train ML model ({len(X)} rows)")
        return None, None

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=1000, multi_class="ovr")
    model.fit(X_scaled, y)

    # Persist
    os.makedirs("logs", exist_ok=True)
    with open(MODEL_FILE,  "wb") as f: pickle.dump(model,  f)
    with open(SCALER_FILE, "wb") as f: pickle.dump(scaler, f)

    logger.info(f"ML model trained on {len(X)} samples")
    return model, scaler


def load_model():
    """Load persisted model and scaler if available."""
    try:
        if os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
            with open(MODEL_FILE,  "rb") as f: model  = pickle.load(f)
            with open(SCALER_FILE, "rb") as f: scaler = pickle.load(f)
            return model, scaler
    except Exception as e:
        logger.warning(f"Could not load ML model: {e}")
    return None, None


def analyze(df: pd.DataFrame) -> dict:
    """
    ML Strategy Analysis.

    Returns:
        dict with keys: signal, confidence, reason
    """
    try:
        model, scaler = load_model()

        if model is None:
            # Train on the fly if enough data
            if len(df) >= MIN_TRAIN_BARS + 10:
                model, scaler = train_model(df)
            else:
                return {
                    "signal":     "HOLD",
                    "confidence": 0,
                    "reason":     "ML model not yet trained (insufficient data)",
                }

        if model is None:
            return {
                "signal":     "HOLD",
                "confidence": 0,
                "reason":     "ML model training failed",
            }

        feats = _compute_features(df)
        if feats.empty:
            return {"signal": "HOLD", "confidence": 0, "reason": "ML: feature error"}

        X_latest = scaler.transform(feats.iloc[[-1]].values)
        pred     = model.predict(X_latest)[0]
        proba    = model.predict_proba(X_latest)[0]
        max_prob = float(max(proba)) * 100

        label_map = {1: "BUY", -1: "SELL", 0: "HOLD"}
        signal    = label_map.get(pred, "HOLD")
        confidence = min(90, int(max_prob))
        reason    = f"ML model predicts {signal} with {max_prob:.1f}% probability"

        return {"signal": signal, "confidence": confidence, "reason": reason}

    except Exception as e:
        logger.error(f"ML analysis error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"ML error: {e}"}
