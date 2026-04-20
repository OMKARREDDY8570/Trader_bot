"""
strategies/ml_model.py - Lightweight ML Strategy (Logistic Regression)
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
MIN_TRAIN_BARS = 60


def _compute_features(df):
    close  = df["close"]
    volume = df["volume"]
    high   = df["high"]
    low    = df["low"]

    delta    = close.diff()
    gain     = delta.where(delta > 0, 0).ewm(com=13, min_periods=14).mean()
    loss     = (-delta.where(delta < 0, 0)).ewm(com=13, min_periods=14).mean()
    rs       = gain / loss.replace(0, np.nan)
    rsi      = 100 - (100 / (1 + rs))

    ema12    = close.ewm(span=12, adjust=False).mean()
    ema26    = close.ewm(span=26, adjust=False).mean()
    macd     = ema12 - ema26
    sig      = macd.ewm(span=9, adjust=False).mean()
    hist     = macd - sig

    ema9     = close.ewm(span=9,  adjust=False).mean()
    ema21    = close.ewm(span=21, adjust=False).mean()
    ema_spread = (ema9 - ema21) / close

    avg_vol  = volume.rolling(20).mean()
    vol_ratio = volume / avg_vol.replace(0, np.nan)

    momentum = close.pct_change(5)
    atr      = (high - low).rolling(14).mean()
    body     = (close - close.shift(1)).abs() / atr.replace(0, np.nan)

    return pd.DataFrame({
        "rsi": rsi, "macd_hist": hist, "ema_spread": ema_spread,
        "vol_ratio": vol_ratio, "momentum": momentum, "body": body,
    }).dropna()


def _generate_labels(df, forward_bars=3, threshold=0.005):
    fwd_return = df["close"].shift(-forward_bars) / df["close"] - 1
    labels = pd.Series(0, index=df.index)
    labels[fwd_return >  threshold] =  1
    labels[fwd_return < -threshold] = -1
    return labels


def train_model(df):
    feats  = _compute_features(df)
    labels = _generate_labels(df)
    common = feats.index.intersection(labels.index)
    X = feats.loc[common].values[:-3]
    y = labels.loc[common].values[:-3]

    if len(X) < MIN_TRAIN_BARS:
        return None, None

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)

    os.makedirs("logs", exist_ok=True)
    with open(MODEL_FILE,  "wb") as f: pickle.dump(model,  f)
    with open(SCALER_FILE, "wb") as f: pickle.dump(scaler, f)
    return model, scaler


def load_model():
    try:
        if os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
            with open(MODEL_FILE,  "rb") as f: model  = pickle.load(f)
            with open(SCALER_FILE, "rb") as f: scaler = pickle.load(f)
            return model, scaler
    except Exception as e:
        logger.warning(f"Could not load ML model: {e}")
    return None, None


def analyze(df):
    try:
        model, scaler = load_model()
        if model is None:
            if len(df) >= MIN_TRAIN_BARS + 10:
                model, scaler = train_model(df)
            else:
                return {"signal": "HOLD", "confidence": 0, "reason": "ML model not yet trained"}

        if model is None:
            return {"signal": "HOLD", "confidence": 0, "reason": "ML training failed"}

        feats = _compute_features(df)
        if feats.empty:
            return {"signal": "HOLD", "confidence": 0, "reason": "ML: feature error"}

        X_latest = scaler.transform(feats.iloc[[-1]].values)
        pred     = model.predict(X_latest)[0]
        proba    = model.predict_proba(X_latest)[0]
        max_prob = float(max(proba)) * 100

        label_map  = {1: "BUY", -1: "SELL", 0: "HOLD"}
        signal     = label_map.get(pred, "HOLD")
        confidence = min(90, int(max_prob))
        return {"signal": signal, "confidence": confidence,
                "reason": f"ML model predicts {signal} with {max_prob:.1f}% probability"}

    except Exception as e:
        logger.error(f"ML error: {e}")
        return {"signal": "HOLD", "confidence": 0, "reason": f"ML error: {e}"}
