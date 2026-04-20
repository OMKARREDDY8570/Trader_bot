"""
telegram/commands.py - All Telegram bot command handlers
"""

import logging
import asyncio
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from engine import signal_generator, paper_trader, perf_tracker, backtester

logger = logging.getLogger(__name__)

# Global auto-signal state
auto_enabled  = False
auto_task_ref = None

WELCOME_MESSAGE = (
    "👋 <b>Welcome to the Crypto Trading Signal Bot!</b>\n\n"
    "I analyze markets using an ensemble of strategies:\n"
    "  • RSI (Overbought/Oversold)\n"
    "  • MACD Crossover\n"
    "  • EMA Crossover (9/21 & 50/200)\n"
    "  • Volume Spike Detection\n"
    "  • Breakout / Support-Resistance\n"
    "  • ML Probability Model\n\n"
    "📋 <b>Commands:</b>\n"
    "/signal — Get signals for all symbols\n"
    "/signal BTC/USDT — Signal for specific symbol\n"
    "/auto on — Enable auto signals every hour\n"
    "/auto off — Disable auto signals\n"
    "/status — Bot health & last signal info\n"
    "/portfolio — Paper trading portfolio\n"
    "/backtest BTC/USDT — Run backtest\n"
    "/daily — Today's performance summary\n\n"
    f"⚠️ <i>{config.DISCLAIMER}</i>"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode=ParseMode.HTML)


async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signal or /signal SYMBOL"""
    args = context.args or []

    if args:
        symbols = [args[0].upper().replace("-", "/")]
    else:
        symbols = config.DEFAULT_SYMBOLS

    await update.message.reply_text(
        f"⏳ Fetching signals for {', '.join(symbols)}..."
    )

    for symbol in symbols:
        try:
            result = signal_generator.generate_signal(symbol)
            if result is None:
                await update.message.reply_text(
                    f"❌ Could not fetch data for <b>{symbol}</b>",
                    parse_mode=ParseMode.HTML,
                )
                continue

            msg = signal_generator.format_signal_message(result)
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

        except Exception as e:
            logger.error(f"Signal command error for {symbol}: {e}")
            await update.message.reply_text(f"❌ Error processing {symbol}: {e}")

        await asyncio.sleep(0.5)  # avoid flooding


async def cmd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /auto on | /auto off"""
    global auto_enabled, auto_task_ref

    args = context.args or []
    if not args or args[0].lower() not in ("on", "off"):
        await update.message.reply_text("Usage: /auto on  or  /auto off")
        return

    if args[0].lower() == "on":
        auto_enabled = True
        interval_min = config.AUTO_INTERVAL_SECONDS // 60
        await update.message.reply_text(
            f"✅ Auto signals <b>ENABLED</b> — signals every {interval_min} minutes.\n"
            f"Only signals with ≥{config.CONFIDENCE_THRESHOLD}% confidence will fire.",
            parse_mode=ParseMode.HTML,
        )
        logger.info("Auto signals enabled")

    else:
        auto_enabled = False
        await update.message.reply_text("🛑 Auto signals <b>DISABLED</b>.", parse_mode=ParseMode.HTML)
        logger.info("Auto signals disabled")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status"""
    import json

    last_signal = "N/A"
    last_symbol = "N/A"
    signal_count = 0

    if os.path.exists(config.SIGNAL_LOG_FILE):
        try:
            with open(config.SIGNAL_LOG_FILE) as f:
                logs = json.load(f)
            signal_count = len(logs)
            if logs:
                latest = logs[-1]
                last_signal = f"{latest.get('signal')} ({latest.get('confidence')}%)"
                last_symbol = latest.get("symbol", "N/A")
        except Exception:
            pass

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    msg = (
        f"🟢 <b>BOT STATUS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Server Time:     {now}\n"
        f"🔄 Auto Mode:       {'✅ ON' if auto_enabled else '🛑 OFF'}\n"
        f"⏱ Interval:        {config.AUTO_INTERVAL_SECONDS // 60} min\n"
        f"🎯 Min Confidence:  {config.CONFIDENCE_THRESHOLD}%\n"
        f"📊 Signals Logged:  {signal_count}\n"
        f"📌 Last Symbol:     {last_symbol}\n"
        f"📌 Last Signal:     {last_signal}\n"
        f"💹 Symbols:         {', '.join(config.DEFAULT_SYMBOLS)}\n"
        f"📈 Mode:            {'📄 Paper Trading' if config.PAPER_TRADING else '💰 Live'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <i>{config.DISCLAIMER}</i>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /portfolio"""
    msg = paper_trader.format_portfolio_message()
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /daily — daily performance summary"""
    msg = perf_tracker.format_daily_summary_message()
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_backtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /backtest SYMBOL"""
    args = context.args or []
    symbol = args[0].upper().replace("-", "/") if args else "BTC/USDT"

    await update.message.reply_text(
        f"⏳ Running backtest for <b>{symbol}</b>... (this may take a moment)",
        parse_mode=ParseMode.HTML,
    )

    try:
        result = backtester.run_backtest(symbol)
        msg = backtester.format_backtest_message(result)
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        await update.message.reply_text(f"❌ Backtest failed: {e}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode=ParseMode.HTML)
