"""
tg/bot.py - Telegram bot setup and auto-signal scheduler
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from tg.commands import (
    cmd_start, cmd_signal, cmd_auto, cmd_status,
    cmd_portfolio, cmd_daily, cmd_backtest, cmd_help,
)
import tg.commands as cmd_module
from engine import signal_generator, perf_tracker

logger = logging.getLogger(__name__)


async def auto_signal_job(context: ContextTypes.DEFAULT_TYPE):
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
    if datetime.now(timezone.utc).hour == config.DAILY_SUMMARY_HOUR:
        msg = perf_tracker.format_daily_summary_message()
        try:
            await context.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")


def build_app():
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("signal",    cmd_signal))
    app.add_handler(CommandHandler("auto",      cmd_auto))
    app.add_handler(CommandHandler("status",    cmd_status))
    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("daily",     cmd_daily))
    app.add_handler(CommandHandler("backtest",  cmd_backtest))
    job_queue = app.job_queue
    job_queue.run_repeating(auto_signal_job,   interval=config.AUTO_INTERVAL_SECONDS, first=60)
    job_queue.run_repeating(daily_summary_job, interval=3600, first=120)
    logger.info("Bot application built successfully")
    return app


def run_bot():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    app = build_app()
    logger.info("Starting Telegram bot polling...")
    app.run_polling(drop_pending_updates=True)
