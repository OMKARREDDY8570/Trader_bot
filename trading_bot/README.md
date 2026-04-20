# 🤖 Trading Signal Bot

A production-ready, modular crypto trading signal bot with a multi-strategy ensemble engine, Telegram integration, paper trading simulation, backtesting, and daily performance summaries.

> ⚠️ **Not financial advice. All signals are for educational purposes only. Trade at your own risk.**

---

## 📦 Features

| Feature | Details |
|---|---|
| **Strategies** | RSI, MACD, EMA Crossover, Volume Spike, Breakout, ML Model |
| **Ensemble Engine** | Weighted voting + dynamic confidence scoring |
| **Telegram Bot** | Commands, auto alerts, status, portfolio |
| **Paper Trading** | Simulated trades, P&L tracking, win/loss log |
| **Backtesting** | Walk-forward test on historical data |
| **Daily Summary** | Auto-sent performance report via Telegram |
| **Free Deployment** | Render.com free tier ready |

---

## 🗂 Project Structure

```
trading_bot/
├── main.py                  # Entry point
├── config.py                # All settings
├── requirements.txt
├── render.yaml              # Render deployment config
├── start.sh                 # Launch script
├── .env.example             # Environment variable template
│
├── strategies/
│   ├── rsi.py               # RSI overbought/oversold
│   ├── macd.py              # MACD crossover
│   ├── ema.py               # EMA 9/21 & 50/200 crossover
│   ├── volume.py            # Volume spike detection
│   ├── breakout.py          # Support/Resistance breakout
│   └── ml_model.py          # Lightweight logistic regression
│
├── engine/
│   ├── aggregator.py        # Weighted ensemble aggregator
│   ├── signal_generator.py  # Full pipeline + message formatter
│   ├── paper_trader.py      # Paper trading simulation
│   ├── perf_tracker.py      # Strategy performance tracker
│   └── backtester.py        # Walk-forward backtester
│
├── telegram/
│   ├── bot.py               # Bot setup + scheduler
│   └── commands.py          # All command handlers
│
└── data/
    └── fetcher.py           # Binance public API via CCXT
```

---

## 🚀 Quick Start (Local)

### 1. Clone / unzip the project

```bash
cd trading_bot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your Telegram bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow prompts → copy the **BOT TOKEN**
3. Start a chat with your new bot
4. Get your **CHAT ID**:
   - Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Send a message to your bot, then refresh the URL
   - Look for `"chat":{"id": YOUR_CHAT_ID}`

### 5. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

### 6. Run the bot

```bash
python main.py
```

---

## ☁️ Deploy to Render (Free)

1. Push the project folder to a **GitHub repository**
2. Go to [render.com](https://render.com) → **New → Blueprint**
3. Connect your GitHub repo
4. Render detects `render.yaml` automatically
5. In the Render dashboard, set **Environment Variables**:
   - `TELEGRAM_BOT_TOKEN` → your token
   - `TELEGRAM_CHAT_ID` → your chat ID
6. Click **Deploy** — done! ✅

> The bot runs as a **worker** (no web server needed) on Render's free tier.

---

## 📲 Telegram Commands

| Command | Description |
|---|---|
| `/start` | Welcome message & command list |
| `/signal` | Get signals for all default symbols |
| `/signal BTC/USDT` | Signal for a specific symbol |
| `/auto on` | Enable auto-signals every hour |
| `/auto off` | Disable auto-signals |
| `/status` | Bot health + last signal info |
| `/portfolio` | Paper trading portfolio & P&L |
| `/backtest BTC/USDT` | Run walk-forward backtest |
| `/daily` | Today's performance summary |

---

## ⚙️ Configuration (config.py)

| Setting | Default | Description |
|---|---|---|
| `DEFAULT_SYMBOLS` | BTC/USDT, ETH/USDT... | Symbols to track |
| `DEFAULT_TIMEFRAME` | `1h` | Candle timeframe |
| `CONFIDENCE_THRESHOLD` | `70` | Min % to fire alert |
| `AUTO_INTERVAL_SECONDS` | `3600` | Auto scan interval |
| `PAPER_TRADING` | `True` | Enable paper trade sim |
| `PAPER_INITIAL_CAPITAL` | `10000` | Starting capital (USD) |
| `DAILY_SUMMARY_HOUR` | `20` | UTC hour for daily report |

### Strategy weights (must sum to 1.0)

```python
STRATEGY_WEIGHTS = {
    "rsi":       0.20,
    "macd":      0.20,
    "ema":       0.20,
    "volume":    0.15,
    "breakout":  0.15,
    "ml_model":  0.10,
}
```

---

## 📊 Signal Format

```
━━━━━━━━━━━━━━━━━━━━━━
📊 ASSET: BTC/USDT
💰 Price: $67,243.1200
━━━━━━━━━━━━━━━━━━━━━━
📈 SIGNAL: BUY
🎯 CONFIDENCE: 78%
🟠 RISK LEVEL: Medium
━━━━━━━━━━━━━━━━━━━━━━
📈 REASONS:
• RSI oversold at 28.3 — momentum recovering
• MACD bullish crossover above zero line
• Volume spike 2.4x avg with bullish candle
━━━━━━━━━━━━━━━━━━━━━━
⚖️ VOTE SCORES:
BUY 78%  |  HOLD 12%  |  SELL 10%
━━━━━━━━━━━━━━━━━━━━━━
⚠️ Not financial advice. Trade at your own risk.
```

---

## 🔬 Adding New Strategies

1. Create `strategies/my_strategy.py` with an `analyze(df) → dict` function
2. Register it in `engine/aggregator.py`:
   ```python
   from strategies import my_strategy
   STRATEGIES["my_strategy"] = my_strategy
   ```
3. Add its weight in `config.py` (re-normalize to 1.0)

---

## 📁 Log Files

| File | Contents |
|---|---|
| `logs/bot.log` | Runtime logs |
| `logs/signals.json` | All generated signals |
| `logs/paper_state.json` | Paper trading state |
| `logs/performance.json` | Strategy win/loss tracker |
| `logs/ml_model.pkl` | Trained ML model |

---

## ⚠️ Disclaimer

This bot is for **educational and research purposes only**.
- It does **not** guarantee profits
- Past performance does **not** predict future results
- Never invest more than you can afford to lose
- Always do your own research (DYOR)
