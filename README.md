# MVBD Telegram Bot

Simple Telegram bot that indexes channel posts and lets group users search for movies.

## Files
- `bot.py` - main bot script
- `requirements.txt` - python deps
- `.gitignore` - ignore list

## Usage (local)
1. export MVBD_TOKEN="YOUR_TOKEN"
2. export CHANNEL_USERNAME="MVPMCC"
3. export ADMIN_ID="YOUR_ADMIN_ID"
4. python bot.py

## Deploy
Recommended: Deploy to Render as Background Worker. Set MVBD_TOKEN, CHANNEL_USERNAME, ADMIN_ID as environment variables in Render.
