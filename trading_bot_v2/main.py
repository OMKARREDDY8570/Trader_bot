"""
main.py - Entry point for the Trading Signal Bot
"""

import logging
import os
import sys

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

BANNER = """
╔══════════════════════════════════════════════════════════╗
║          🤖  TRADING SIGNAL BOT  v1.0                   ║
║   Multi-Strategy Ensemble | Paper Trading | Telegram     ║
╚══════════════════════════════════════════════════════════╝
"""


def validate_config():
    import config
    errors = []
    if config.TELEGRAM_BOT_TOKEN in ("", "YOUR_BOT_TOKEN_HERE"):
        errors.append("TELEGRAM_BOT_TOKEN is not set")
    if config.TELEGRAM_CHAT_ID in ("", "YOUR_CHAT_ID_HERE"):
        errors.append("TELEGRAM_CHAT_ID is not set")
    if errors:
        for err in errors:
            logger.error(f"Config error: {err}")
        logger.error("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as environment variables.")
        sys.exit(1)


def main():
    print(BANNER)
    logger.info("Starting Trading Signal Bot...")
    validate_config()
    from tg.bot import run_bot
    run_bot()


if __name__ == "__main__":
    main()
