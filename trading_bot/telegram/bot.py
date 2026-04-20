"""
telegram/bot.py - Telegram bot setup and auto-signal scheduler
"""

import asyncio
import logging
from datetime import datetime, timezone

from telegram import Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from telegram.commands import (
    cmd_start, cmd_signal, cmd_auto, cmd_status,
    cmd_portfolio, cmd_daily, cmd_backtest, cmd_help,
    auto_enabled,
)
import telegram.commands as cmd_module
from engine import signal_generator, perf_tracker

logger = logging.getLogger(__name__)


async def auto_signal_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job: send signals if auto mode is on."""
    if not cmd_module.auto_enabled:
        return

    logger.info("Running auto signal scan...")
    results = signal_generator.generate_all_signals()

    for result in results:
        if result["confidence"] >= config.CONFIDENCE_THRESHOLD:
            msg = signal_generator.format_signal_message(result)
            try:
                await context.bot.send_message(
                    chat_id=config.TELEGRAM_CHAT_ID,
                    text=msg,
                    parse_mode=ParseMode.HTML,
                )
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Failed to send auto signal: {e}")


async def daily_summary_job(context: ContextTypes.DEFAULT_TYPE):
    """Send daily summary at configured hour."""
    hour_now = datetime.now(timezone.utc).hour
    if hour_now == config.DAILY_SUMMARY_HOUR:
        msg = perf_tracker.format_daily_summary_message()
        try:
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")


def build_app() -> Application:
    """Build and configure the Telegram bot application."""
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("signal",    cmd_signal))
    app.add_handler(CommandHandler("auto",      cmd_auto))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("daily",     cmd_daily))
    app.add_handler(CommandHandler("backtest",  cmd_backtest))

    # Schedule jobs
    job_queue = app.job_queue
    job_queue.run_repeating(
        auto_signal_job,
        interval=config.AUTO_INTERVAL_SECONDS,
        first=60,           # first run after 1 minute
    )
    job_queue.run_repeating(
        daily_summary_job,
        interval=3600,      # check every hour
        first=120,
    )

    logger.info("Telegram bot application built successfully")
    return app


def run_bot():
    """Start the bot (blocking)."""
    os.makedirs(config.LOG_DIR, exist_ok=True)
    app = build_app()
    logger.info("Starting Telegram bot polling...")
    app.run_polling(drop_pending_updates=True)
