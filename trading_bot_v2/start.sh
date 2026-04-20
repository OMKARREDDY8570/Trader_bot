#!/usr/bin/env bash
set -e
echo "========================================"
echo "  Trading Signal Bot — Starting Up"
echo "========================================"
mkdir -p logs
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then echo "ERROR: TELEGRAM_BOT_TOKEN not set!"; exit 1; fi
if [ -z "$TELEGRAM_CHAT_ID" ];   then echo "ERROR: TELEGRAM_CHAT_ID not set!";   exit 1; fi
echo "✅ Config validated"
exec python main.py
