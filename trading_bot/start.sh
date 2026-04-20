#!/usr/bin/env bash
set -e

echo "========================================"
echo "  Trading Signal Bot — Starting Up"
echo "========================================"

# Create log directory
mkdir -p logs

# Check required env vars
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN is not set!"
  exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "ERROR: TELEGRAM_CHAT_ID is not set!"
  exit 1
fi

echo "✅ Config validated"
echo "🚀 Launching bot..."

exec python main.py
