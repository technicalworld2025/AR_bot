# bot.py
import os
import sqlite3
import time
import telebot
from telebot import types

TOKEN = os.getenv("MVBD_TOKEN")  # set via Render/Env or export locally
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "MVPMCC")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)

if not TOKEN:
    raise SystemExit("Error: MVBD_TOKEN not set")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# simple DB
DB_PATH = "mvbd_index.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS posts(
    message_id INTEGER,
    channel_id INTEGER,
    channel_username TEXT,
    title TEXT,
    caption TEXT,
    file_name TEXT,
    timestamp INTEGER,
    PRIMARY KEY(channel_id, message_id)
)
""")
conn.commit()

def index_message(msg):
    message_id = msg.message_id
    ch_id = msg.chat.id
    caption = msg.caption or ""
    text = msg.text or ""
    file_name = ""
    if hasattr(msg, 'document') and msg.document:
        file_name = getattr(msg.document, "file_name", "") or ""
    elif hasattr(msg, 'video') and msg.video:
        file_name = getattr(msg.video, "file_name", "") or ""
    title = caption.strip() or text.strip() or file_name.strip() or ""
    title_short = title.lower()
    ts = int(time.time())
    try:
        cur.execute("""
        INSERT OR REPLACE INTO posts(message_id, channel_id, channel_username, title, caption, file_name, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (message_id, ch_id, CHANNEL_USERNAME, title_short, caption, file_name, ts))
        conn.commit()
    except Exception as e:
        print("DB insert error:", e)

@bot.channel_post_handler(func=lambda m: True)
def handle_channel_post(message):
    try:
        index_message(message)
        print("Indexed channel post:", message.message_id)
    except Exception as e:
        print("channel index error:", e)

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and m.text is not None)
def group_search_handler(message):
    text = message.text.strip()
    lower = text.lower()
    if len(lower) < 2:
        return

    if lower == "movie":
        bot.send_message(message.chat.id, "আপনি কি এই মুভিটির সঠিক নাম গুগল এ গিয়ে সার্চ করে দেখেছেন?")
        return

    sent = bot.send_message(message.chat.id, f"🔍 Searching for {text} ...")
    try:
        pattern = f"%{lower}%"
        cur.execute("""
          SELECT message_id, channel_id, channel_username, title, caption, file_name, timestamp
          FROM posts
          WHERE title LIKE ? OR caption LIKE ? OR file_name LIKE ?
          ORDER BY timestamp DESC
          LIMIT 8
        """, (pattern, pattern, pattern))
        rows = cur.fetchall()
        if rows:
            texts = []
            for r in rows:
                link = f"https://t.me/{(r[2] or CHANNEL_USERNAME)}/{r[0]}"
                display = r[3] or r[4] or r[5] or "Untitled"
                snippet = (display[:80] + '...') if len(display) > 80 else display
                texts.append(f"• <a href=\"{link}\">{snippet}</a>")
            reply = "I found these results:\n\n" + "\n".join(texts)
            bot.edit_message_text(chat_id=sent.chat.id, message_id=sent.message_id, text=reply, parse_mode="HTML", disable_web_page_preview=True)
        else:
            bot.edit_message_text(chat_id=sent.chat.id, message_id=sent.message_id, text="না পাওয়া গেছে — আগে গিয়ে মুভির নাম এবং সাল টা সঠিক ভাবে দেখে আসেন।\nঅথবা এখানে মুভির নাম ও সাল লিখে দিন, আমরা admin-কে জানিয়ে দেব।")
            if ADMIN_ID:
                bot.send_message(ADMIN_ID, f"Search miss by @{message.from_user.username or message.from_user.first_name} in group {message.chat.title}:\nQuery: {text}")
    except Exception as e:
        bot.edit_message_text(chat_id=sent.chat.id, message_id=sent.message_id, text=f"❌ Error during search: {e}")

@bot.message_handler(func=lambda m: m.chat.type in ("group","supergroup") and any(ch.isdigit() for ch in (m.text or "")))
def year_handler(message):
    text = message.text.strip()
    if ADMIN_ID:
        bot.send_message(ADMIN_ID, f"User {message.from_user.first_name} requested movie: {text}\nFrom group: {message.chat.title}")
        bot.reply_to(message, "ধন্যবাদ — আপনার অনুরোধ অ্যাডমিনের কাছে পাঠানো হলো। অনুগ্রহ করে অপেক্ষা করুন।")
    else:
        bot.reply_to(message, "ধন্যবাদ — আপনার অনুরোধ নোট করা হলো।")

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
